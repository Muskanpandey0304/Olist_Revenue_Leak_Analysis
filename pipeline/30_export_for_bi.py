"""Export the star schema and summary tables as CSV for Power BI and Excel.

Run:  python pipeline/30_export_for_bi.py
Writes dashboard/data/*.csv  (star schema, large, not committed) and dashboard/summary/*.csv (small summaries)
"""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "olist.db")
star = ROOT / "dashboard" / "data"
summ = ROOT / "dashboard" / "summary"
star.mkdir(parents=True, exist_ok=True)
summ.mkdir(parents=True, exist_ok=True)

for t in ["fact_orders", "fact_order_items", "dim_customer", "dim_seller", "dim_product", "dim_date", "rfm_segments"]:
    df = pd.read_sql(f"SELECT * FROM {t}", con)
    df.to_csv(star / f"{t}.csv", index=False)
    print(f"{t}: {len(df):,} rows")

Q = {
"monthly_kpis": """
    SELECT d.year_month, ROUND(SUM(i.price), 2) AS revenue, COUNT(DISTINCT i.order_id) AS orders,
           COUNT(DISTINCT i.customer_unique_id) AS active_customers, ROUND(SUM(i.freight_value), 2) AS freight
    FROM fact_order_items i JOIN dim_date d ON d.date = i.purchase_date
    WHERE i.is_revenue_item = 1 GROUP BY d.year_month ORDER BY d.year_month""",
"category_summary": """
    SELECT p.category, ROUND(SUM(i.price), 2) AS revenue, COUNT(DISTINCT i.order_id) AS orders
    FROM fact_order_items i JOIN dim_product p ON p.product_id = i.product_id
    WHERE i.is_revenue_item = 1 GROUP BY p.category ORDER BY revenue DESC""",
"delivery_impact": """
    SELECT CASE WHEN is_late = 0 THEN '1 On time' WHEN delivery_days - estimated_days >= 7 THEN '3 Late 7+ days'
                ELSE '2 Late 1-6 days' END AS delivery, COUNT(*) AS orders, ROUND(SUM(items_price), 2) AS revenue,
           ROUND(AVG(review_score), 2) AS avg_review,
           ROUND(100.0 * AVG(CASE WHEN review_score <= 2 THEN 1.0 WHEN review_score IS NOT NULL THEN 0 END), 1) AS pct_low_review
    FROM fact_orders WHERE is_revenue_order = 1 GROUP BY delivery ORDER BY delivery""",
"customer_deciles": """
    WITH cust AS (SELECT customer_unique_id, SUM(price) AS spend FROM fact_order_items
                  WHERE is_revenue_item = 1 GROUP BY customer_unique_id),
    r AS (SELECT spend, NTILE(10) OVER (ORDER BY spend DESC) AS decile FROM cust)
    SELECT decile, COUNT(*) AS customers, ROUND(SUM(spend), 2) AS revenue, ROUND(AVG(spend), 2) AS avg_spend
    FROM r GROUP BY decile ORDER BY decile""",
}
for name, sql in Q.items():
    df = pd.read_sql(sql, con)
    df.to_csv(summ / f"{name}.csv", index=False)
    print(f"{name}: {len(df)} rows")

# files produced by the analysis scripts
for f in ["state_opportunity.csv", "rfm_segment_summary.csv", "seller_late_performance.csv"]:
    pd.read_csv(ROOT / "reports" / f).to_csv(summ / f, index=False)
