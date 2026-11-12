"""Key-level checks on raw Olist data that drive cleaning decisions."""
from pathlib import Path
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "olist"
rd = lambda n: pd.read_csv(RAW / f"olist_{n}_dataset.csv")

orders, items, pay = rd("orders"), rd("order_items"), rd("order_payments")
rev, cust = rd("order_reviews"), rd("customers")

print("order status:\n", orders.order_status.value_counts().to_string())
ts = pd.to_datetime(orders.order_purchase_timestamp)
print("\npurchase range:", ts.min(), "->", ts.max())
print("orders per month:\n", ts.dt.to_period("M").value_counts().sort_index().to_string())

print("\nunique customers:", cust.customer_unique_id.nunique(), "of", len(cust), "customer_ids")
print("orders w/o items:", (~orders.order_id.isin(items.order_id)).sum())
print("orders w/o payments:", (~orders.order_id.isin(pay.order_id)).sum())
print("orders w/o reviews:", (~orders.order_id.isin(rev.order_id)).sum())
print("orders with >1 review:", (rev.order_id.value_counts() > 1).sum())
print("duplicate review_id:", rev.review_id.duplicated().sum())

it = items.groupby("order_id").agg(items_price=("price", "sum"), freight=("freight_value", "sum"))
pv = pay.groupby("order_id").payment_value.sum().rename("paid")
m = it.join(pv, how="outer")
m["diff"] = m.paid - (m.items_price + m.freight)
print("\nitems+freight vs payments: orders", len(m), "| |diff|>0.05:", (m["diff"].abs() > 0.05).sum(),
      "| total items+freight:", round((m.items_price + m.freight).sum(), 2), "| total paid:", round(m.paid.sum(), 2))
print("payment_value == 0 rows:", (pay.payment_value == 0).sum(), "| payment types:", pay.payment_type.value_counts().to_dict())

d = orders.dropna(subset=["order_delivered_customer_date"]).copy()
d["days"] = (pd.to_datetime(d.order_delivered_customer_date) - pd.to_datetime(d.order_purchase_timestamp)).dt.days
d["late"] = pd.to_datetime(d.order_delivered_customer_date) > pd.to_datetime(d.order_estimated_delivery_date)
print("\ndelivered w/ date:", len(d), "| negative days:", (d.days < 0).sum(), "| late rate:", round(d.late.mean() * 100, 1), "%")
print("delivered status but no delivery date:", ((orders.order_status == "delivered") & orders.order_delivered_customer_date.isna()).sum())
print("customer states:", cust.customer_state.nunique(), "| zips in cust not in geo:",
      (~cust.customer_zip_code_prefix.isin(rd("geolocation").geolocation_zip_code_prefix)).sum())
