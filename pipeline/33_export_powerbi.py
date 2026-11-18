"""Build dashboard/powerbi/olist_powerbi_data.xlsx: every table Power BI needs, in one workbook.

Helper columns (delivery_bucket, distance_band, low_review) are added so the Power BI measures stay simple.
Run:  python pipeline/33_export_powerbi.py   (after pipeline/30_export_for_bi.py)
"""
from pathlib import Path
import json
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard" / "powerbi"
OUT.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(ROOT / "data" / "olist.db")
q = lambda sql: pd.read_sql(sql, con)

dim_date = q("SELECT date, year, month, year_month, quarter, weekday_num, is_weekend, is_holiday, holiday_name FROM dim_date")
dim_date["date"] = pd.to_datetime(dim_date["date"])

dim_customer = q("SELECT customer_unique_id, city, state, region FROM dim_customer")
dim_seller = q("SELECT seller_id, city, state, region FROM dim_seller")
dim_product = q("SELECT product_id, category, weight_g, volume_cm3 FROM dim_product")

fact_orders = q("""
SELECT order_id, customer_unique_id, customer_state, purchase_date, order_status, is_revenue_order,
       is_late, delivery_days, estimated_days, review_score, items_price, freight_total,
       avg_distance_km, n_items, main_payment_type
FROM fact_orders""")
fact_orders["purchase_date"] = pd.to_datetime(fact_orders["purchase_date"])
late = fact_orders.is_late == 1
severe = late & ((fact_orders.delivery_days - fact_orders.estimated_days) >= 7)
bucket = pd.Series(pd.NA, index=fact_orders.index, dtype="object")
bucket[fact_orders.is_late == 0] = "1 On time"
bucket[late] = "2 Late 1-6 days"
bucket[severe] = "3 Late 7+ days"
fact_orders["delivery_bucket"] = bucket
d = fact_orders.avg_distance_km
fact_orders["distance_band"] = pd.cut(d, [-1, 100, 300, 600, 1000, 1500, 99999],
                                      labels=["1 under 100 km", "2 100-300 km", "3 300-600 km",
                                              "4 600-1000 km", "5 1000-1500 km", "6 1500+ km"]).astype("object")
fact_orders["low_review"] = (fact_orders.review_score <= 2).astype("float").where(fact_orders.review_score.notna())

fact_items = q("""SELECT order_id, order_item_id, product_id, seller_id, price, freight_value, is_revenue_item, distance_km
                  FROM fact_order_items""")
rfm = q("SELECT customer_unique_id, frequency, monetary, recency_days, segment FROM rfm_segments")
rfm["decile"] = pd.qcut(rfm.monetary.rank(method="first", ascending=False), 10, labels=range(1, 11)).astype(int)   # 1 = highest spenders
states = pd.read_csv(ROOT / "reports" / "state_opportunity.csv")[
    ["state_code", "state_name", "region", "population", "income_pc", "revenue", "orders", "rev_per_1000",
     "expected_rev_per_1000", "penetration_vs_expected", "avg_freight_ratio", "late_pct", "avg_delivery_days"]]
sellers = pd.read_csv(ROOT / "reports" / "seller_late_performance.csv")
sellers = sellers[(sellers.orders >= 50) & (sellers.z > 2)][
    ["seller_id", "seller_state", "orders", "late", "late_pct", "expected_pct", "excess_late", "revenue"]
].rename(columns={"late": "late_orders"}).sort_values("excess_late", ascending=False)

tables = {"dim_date": dim_date, "dim_customer": dim_customer, "dim_seller": dim_seller, "dim_product": dim_product,
          "fact_orders": fact_orders, "fact_order_items": fact_items, "rfm_segments": rfm,
          "states": states, "seller_watchlist": sellers}
with pd.ExcelWriter(OUT / "olist_powerbi_data.xlsx", engine="openpyxl", datetime_format="yyyy-mm-dd") as xw:
    for name, df in tables.items():
        df.to_excel(xw, sheet_name=name, index=False)
        print(f"{name}: {len(df):,} rows, {df.shape[1]} columns")

# column types, read by pipeline/34_build_powerbi_project.py
schema = {name: {c: str(t) for c, t in df.dtypes.items()} for name, df in tables.items()}
(OUT / "schema.json").write_text(json.dumps(schema, indent=1), encoding="utf-8")

theme = {
    "name": "Olist",
    "dataColors": ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#6250D6", "#E34948"],
    "background": "#FCFCFB", "foreground": "#0B0B0B", "tableAccent": "#2A78D6",
    "textClasses": {"title": {"fontSize": 14, "fontFace": "Segoe UI Semibold", "color": "#0B0B0B"},
                    "label": {"fontSize": 11, "fontFace": "Segoe UI", "color": "#52514E"}},
}
(OUT / "olist_theme.json").write_text(json.dumps(theme, indent=2), encoding="utf-8")
print("saved", OUT)
