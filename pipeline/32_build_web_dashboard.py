"""Build the web dashboard: docs/index.html (single file, served by GitHub Pages).

Reads the summary tables and the database, embeds the data as JSON in dashboard/web/template.html.
Run:  python pipeline/32_build_web_dashboard.py   (after pipeline/30_export_for_bi.py)
"""
from pathlib import Path
import json
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "dashboard" / "summary"
con = sqlite3.connect(ROOT / "data" / "olist.db")


def records(df, nd=4):
    return json.loads(df.round(nd).to_json(orient="records"))


# headline numbers
k = con.execute("""SELECT SUM(price), COUNT(DISTINCT order_id), COUNT(DISTINCT customer_unique_id)
                   FROM fact_order_items WHERE is_revenue_item = 1""").fetchone()
rep = con.execute("""SELECT COUNT(*), SUM(n >= 2) FROM (SELECT customer_unique_id, COUNT(*) AS n
                     FROM fact_orders WHERE is_revenue_order = 1 GROUP BY customer_unique_id)""").fetchone()
late = con.execute("SELECT AVG(is_late) FROM fact_orders WHERE is_revenue_order = 1").fetchone()[0]
kpis = {"revenue": k[0], "orders": k[1], "customers": k[2], "aov": k[0] / k[1],
        "repeat_rate": 100 * rep[1] / rep[0], "late_rate": 100 * late}

monthly = pd.read_csv(S / "monthly_kpis.csv")
cats = pd.read_csv(S / "category_summary.csv")
cats["share"] = 100 * cats.revenue / cats.revenue.sum()
deciles = pd.read_csv(S / "customer_deciles.csv")
deciles["share"] = 100 * deciles.revenue / deciles.revenue.sum()
segments = pd.read_csv(S / "rfm_segment_summary.csv")
delivery = pd.read_csv(S / "delivery_impact.csv")
delivery["label"] = ["On time", "1-6 days late", "7+ days late"]
states = pd.read_csv(S / "state_opportunity.csv").sort_values("rev_per_1000", ascending=False)

dist = pd.read_sql("""
SELECT CASE WHEN avg_distance_km <= 100 THEN '1 <100 km' WHEN avg_distance_km <= 300 THEN '2 100-300 km'
            WHEN avg_distance_km <= 600 THEN '3 300-600 km' WHEN avg_distance_km <= 1000 THEN '4 600-1000 km'
            WHEN avg_distance_km <= 1500 THEN '5 1000-1500 km' ELSE '6 1500+ km' END AS band,
       COUNT(*) AS orders, 100.0 * AVG(is_late) AS late_pct
FROM fact_orders WHERE is_revenue_order = 1 AND n_sellers = 1 AND avg_distance_km IS NOT NULL
GROUP BY band ORDER BY band""", con)
dist["band"] = dist.band.str[2:]

late_states = states[states.orders >= 500].sort_values("late_pct", ascending=False).head(10)[["state_code", "late_pct", "orders"]]

sellers = pd.read_csv(S / "seller_late_performance.csv")
sellers = sellers[(sellers.orders >= 50) & (sellers.z > 2)].sort_values("excess_late", ascending=False).head(10)
sellers = sellers[["seller_id", "seller_state", "orders", "late_pct", "expected_pct", "excess_late"]]

data = {
    "kpis": kpis, "monthly": records(monthly, 2), "categories": records(cats.head(10), 2),
    "deciles": records(deciles, 2), "segments": records(segments, 2), "delivery": records(delivery, 2),
    "distance": records(dist, 2), "late_states": records(late_states, 2), "sellers": records(sellers, 2),
    "states": records(states[["state_code", "state_name", "income_pc", "revenue", "rev_per_1000",
                              "penetration_vs_expected", "late_pct", "avg_delivery_days"]], 3),
}
html = (ROOT / "dashboard" / "web" / "template.html").read_text(encoding="utf-8")
assert "/*DATA*/null" in html
out = ROOT / "docs" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
print("saved", out, f"({out.stat().st_size / 1024:.0f} KB)")
print({k_: (round(v, 2) if isinstance(v, float) else v) for k_, v in kpis.items()})
print(dist.round(1).to_string(index=False))
