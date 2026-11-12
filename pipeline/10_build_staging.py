"""Raw -> staging. Cleans each source table and writes stg_* tables to data/olist.db.

Decisions applied here are listed in reports/data_quality_log.md.
Run:  python pipeline/10_build_staging.py
"""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, EXT = ROOT / "data" / "raw" / "olist", ROOT / "data" / "raw" / "external"
DB = ROOT / "data" / "olist.db"

WINDOW_START, WINDOW_END = "2017-01-01", "2018-08-31"


def read(name):
    return pd.read_csv(RAW / f"olist_{name}_dataset.csv")


def stg_orders():
    o = read("orders")
    ts = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
          "order_delivered_customer_date", "order_estimated_delivery_date"]
    for c in ts:
        o[c] = pd.to_datetime(o[c])
    o["purchase_date"] = o.order_purchase_timestamp.dt.normalize()
    o["in_window"] = o.purchase_date.between(WINDOW_START, WINDOW_END).astype(int)
    delivered = o.order_delivered_customer_date.notna()
    o["has_delivery_date"] = delivered.astype(int)
    o["delivery_days"] = (o.order_delivered_customer_date - o.order_purchase_timestamp).dt.days
    o["is_late"] = (o.order_delivered_customer_date > o.order_estimated_delivery_date).astype(float)
    o.loc[~delivered, "is_late"] = pd.NA
    for c in ts:
        o[c] = o[c].dt.strftime("%Y-%m-%d %H:%M:%S")
    o["purchase_date"] = o.purchase_date.dt.strftime("%Y-%m-%d")   # date only, joins to dim_date
    return o


def stg_customers():
    c = read("customers").drop_duplicates()
    c["customer_city"] = c.customer_city.str.strip().str.lower()
    c["customer_state"] = c.customer_state.str.strip().str.upper()
    return c


def stg_items():
    i = read("order_items").drop_duplicates()
    i["shipping_limit_date"] = pd.to_datetime(i.shipping_limit_date).dt.strftime("%Y-%m-%d %H:%M:%S")
    return i


def stg_payments():
    p = read("order_payments").drop_duplicates()
    p["is_valid"] = ((p.payment_value > 0) & (p.payment_type != "not_defined")).astype(int)
    return p


def stg_reviews():
    r = read("order_reviews")
    for c in ["review_creation_date", "review_answer_timestamp"]:
        r[c] = pd.to_datetime(r[c])
    r = r.sort_values(["order_id", "review_answer_timestamp", "review_creation_date"])
    n_before = len(r)
    r = r.drop_duplicates("order_id", keep="last")  # latest review per order
    print(f"  reviews: {n_before:,} -> {len(r):,} (one per order, latest kept)")
    r["review_creation_date"] = r.review_creation_date.dt.strftime("%Y-%m-%d %H:%M:%S")
    r["review_answer_timestamp"] = r.review_answer_timestamp.dt.strftime("%Y-%m-%d %H:%M:%S")
    return r.drop(columns=["review_comment_title", "review_comment_message"])


def stg_products():
    p = read("products").rename(columns={"product_name_lenght": "product_name_length",
                                         "product_description_lenght": "product_description_length"})
    tr = pd.read_csv(RAW / "product_category_name_translation.csv")
    p = p.merge(tr, on="product_category_name", how="left")
    # categories missing from the translation file keep their Portuguese name
    p["category"] = p.product_category_name_english.fillna(p.product_category_name).fillna("unknown")
    return p.drop(columns=["product_category_name_english"])


def stg_sellers():
    s = pd.read_csv(RAW / "olist_sellers_dataset.csv").drop_duplicates()
    s["seller_city"] = s.seller_city.str.strip().str.lower()
    s["seller_state"] = s.seller_state.str.strip().str.upper()
    return s


def stg_geo():
    g = pd.read_csv(RAW / "olist_geolocation_dataset.csv")
    # drop coordinates that fall outside Brazil's bounding box (bad GPS rows)
    inside = g.geolocation_lat.between(-34, 6) & g.geolocation_lng.between(-74, -34)
    print(f"  geolocation: {(~inside).sum():,} rows outside Brazil dropped")
    g = g[inside]
    out = g.groupby("geolocation_zip_code_prefix").agg(
        lat=("geolocation_lat", "median"), lng=("geolocation_lng", "median"),
        state=("geolocation_state", lambda s: s.mode().iat[0])).reset_index()
    print(f"  geolocation: {len(g):,} rows -> {len(out):,} zip prefixes")
    return out.rename(columns={"geolocation_zip_code_prefix": "zip_prefix"})


INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_orders_id ON stg_orders(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_orders_cust ON stg_orders(customer_id)",
    "CREATE INDEX IF NOT EXISTS ix_items_order ON stg_order_items(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_items_seller ON stg_order_items(seller_id)",
    "CREATE INDEX IF NOT EXISTS ix_items_product ON stg_order_items(product_id)",
    "CREATE INDEX IF NOT EXISTS ix_pay_order ON stg_payments(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_rev_order ON stg_reviews(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_cust_id ON stg_customers(customer_id)",
    "CREATE INDEX IF NOT EXISTS ix_prod_id ON stg_products(product_id)",
    "CREATE INDEX IF NOT EXISTS ix_sell_id ON stg_sellers(seller_id)",
    "CREATE INDEX IF NOT EXISTS ix_geo_zip ON stg_geo_zip(zip_prefix)",
]


def main():
    tables = {
        "stg_orders": stg_orders, "stg_customers": stg_customers, "stg_order_items": stg_items,
        "stg_payments": stg_payments, "stg_reviews": stg_reviews, "stg_products": stg_products,
        "stg_sellers": stg_sellers, "stg_geo_zip": stg_geo,
    }
    with sqlite3.connect(DB) as con:
        for name, fn in tables.items():
            df = fn()
            df.to_sql(name, con, if_exists="replace", index=False)
            print(f"{name}: {len(df):,} rows")
        pd.read_csv(EXT / "ibge_states_2018.csv").to_sql("stg_ibge_states", con, if_exists="replace", index=False)
        pd.read_csv(EXT / "holidays_brazil.csv").to_sql("stg_holidays", con, if_exists="replace", index=False)
        for stmt in INDEXES:
            con.execute(stmt)
    print("staging written to", DB)


if __name__ == "__main__":
    main()
