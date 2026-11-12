"""Stage 3: customer segments (RFM-based, rule-based) and a revenue scenario.

Why rules and not the usual quintile scores: 97% of customers have frequency 1, so frequency
quintiles collapse into one bucket. Segments are built from frequency (one-time vs repeat),
recency (days since last delivered order at the snapshot) and monetary value (total item spend).

Run:  python notebooks/03_rfm_segments.py
Writes table `rfm_segments` to data/olist.db and reports/rfm_segment_summary.csv
"""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = pd.Timestamp("2018-09-01")      # day after the last day of the analysis window
RECENT_DAYS = 180                          # recent = ordered within the last 180 days

con = sqlite3.connect(ROOT / "data" / "olist.db")
o = pd.read_sql("""SELECT customer_unique_id, order_id, purchase_date, items_price
                   FROM fact_orders WHERE is_revenue_order = 1""", con, parse_dates=["purchase_date"])

c = o.groupby("customer_unique_id").agg(
    frequency=("order_id", "nunique"), monetary=("items_price", "sum"),
    last_order=("purchase_date", "max"), first_order=("purchase_date", "min")).reset_index()
c["recency_days"] = (SNAPSHOT - c.last_order).dt.days

hv_cut = c.loc[c.frequency == 1, "monetary"].quantile(0.8)     # top 20% of one-time buyers by spend
c["recent"] = c.recency_days <= RECENT_DAYS


def segment(r):
    if r.frequency >= 2:
        return "Repeat - active" if r.recent else "Repeat - lapsed"
    if r.monetary >= hv_cut:
        return "One-time high value - recent" if r.recent else "One-time high value - lapsed"
    return "One-time standard - recent" if r.recent else "One-time standard - lapsed"


c["segment"] = c.apply(segment, axis=1)
c.drop(columns=["recent"]).assign(last_order=c.last_order.dt.strftime("%Y-%m-%d"),
                                  first_order=c.first_order.dt.strftime("%Y-%m-%d")) \
    .to_sql("rfm_segments", con, if_exists="replace", index=False)

summary = c.groupby("segment").agg(customers=("customer_unique_id", "count"),
                                   revenue=("monetary", "sum"),
                                   avg_spend=("monetary", "mean"),
                                   median_recency_days=("recency_days", "median")).reset_index()
summary["pct_customers"] = (100 * summary.customers / summary.customers.sum()).round(1)
summary["pct_revenue"] = (100 * summary.revenue / summary.revenue.sum()).round(1)
summary = summary.sort_values("revenue", ascending=False).round({"revenue": 0, "avg_spend": 1})
summary.to_csv(ROOT / "reports" / "rfm_segment_summary.csv", index=False)
print(f"high-value cut-off (one-time buyers, top 20% spend): R${hv_cut:.2f}")
print(summary.to_string(index=False))

# Scenario: what is one more percentage point of customers placing a second order worth?
second = (o.sort_values(["customer_unique_id", "purchase_date"])
            .groupby("customer_unique_id").nth(1))
avg_second = second.items_price.mean()
n = len(c)
print(f"\ncustomers: {n:,} | second orders: {len(second):,} | average second-order value: R${avg_second:.2f}")
print(f"+1 percentage point of customers repeating = {n * 0.01:,.0f} customers x R${avg_second:.2f} "
      f"= R${n * 0.01 * avg_second:,.0f} (= {100 * n * 0.01 * avg_second / c.monetary.sum():.1f}% of window revenue)")
