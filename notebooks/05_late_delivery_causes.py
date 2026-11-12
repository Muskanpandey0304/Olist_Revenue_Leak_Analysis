"""Stage 5: Is late delivery a distance, seller or holiday problem?

Run:  python notebooks/05_late_delivery_causes.py
Writes reports/seller_late_performance.csv
"""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "olist.db")

o = pd.read_sql("""
SELECT f.order_id, f.customer_state, f.is_late, f.delivery_days, f.estimated_days, f.holidays_in_window,
       f.avg_distance_km AS dist, f.n_sellers, f.items_price, f.freight_total, f.purchase_date,
       s.order_delivered_carrier_date AS carrier_ts, s.order_purchase_timestamp AS purchase_ts,
       s.order_delivered_customer_date AS delivered_ts,
       (SELECT seller_id FROM fact_order_items i WHERE i.order_id = f.order_id ORDER BY order_item_id LIMIT 1) AS seller_id
FROM fact_orders f JOIN stg_orders s USING (order_id)
WHERE f.is_revenue_order = 1 AND f.n_sellers = 1""", con, parse_dates=["carrier_ts", "purchase_ts", "delivered_ts"])
sel = pd.read_sql("SELECT seller_id, state AS seller_state FROM dim_seller", con)
o = o.merge(sel, on="seller_id")
o["late"] = o.is_late.astype(int)
print(f"single-seller delivered orders analysed: {len(o):,} | late rate {100 * o.late.mean():.2f}%")

# ---- 1. Where does the time go? seller handling vs carrier transit ---------------------
o["seller_days"] = (o.carrier_ts - o.purchase_ts).dt.total_seconds() / 86400
o["transit_days"] = (o.delivered_ts - o.carrier_ts).dt.total_seconds() / 86400
t = o.dropna(subset=["seller_days", "transit_days"])
t = t[(t.seller_days >= 0) & (t.transit_days >= 0)]
cmp = t.groupby("late")[["seller_days", "transit_days", "delivery_days", "estimated_days"]].median().round(1)
print("\n[1] median days: purchase->carrier (seller) and carrier->customer (transit)\n", cmp.to_string())
extra = t[t.late == 1][["seller_days", "transit_days"]].median() - t[t.late == 0][["seller_days", "transit_days"]].median()
print("    extra median days in late orders vs on-time:", extra.round(1).to_dict())

# ---- 2. Distance -----------------------------------------------------------------------
d = o.dropna(subset=["dist"]).copy()
d["band"] = pd.cut(d.dist, [-1, 100, 300, 600, 1000, 1500, 5000],
                   labels=["<100 km", "100-300", "300-600", "600-1000", "1000-1500", "1500+"])
b = d.groupby("band", observed=True).agg(orders=("late", "size"), late_pct=("late", lambda s: 100 * s.mean()),
                                        median_days=("delivery_days", "median"),
                                        median_estimate=("estimated_days", "median")).round(1)
print("\n[2] late rate by seller-customer distance\n", b.to_string())

# ---- 3. Holidays -----------------------------------------------------------------------
h = o.groupby(o.holidays_in_window.clip(upper=2)).agg(orders=("late", "size"), late_pct=("late", lambda s: 100 * s.mean())).round(2)
print("\n[3] late rate by holidays inside the promised delivery window (2 = two or more)\n", h.to_string())

# ---- 4. Customer state -----------------------------------------------------------------
st = o.groupby("customer_state").agg(orders=("late", "size"), late_pct=("late", lambda s: 100 * s.mean()),
                                     median_dist=("dist", "median")).round(1)
st = st[st.orders >= 500].sort_values("late_pct", ascending=False)
print("\n[4] customer states with the highest late rate (500+ orders)\n", st.head(6).to_string())
print("    lowest:\n", st.tail(3).to_string())

# ---- 5. Multivariable view: what remains after controlling for the others? -----------
m = d.dropna(subset=["dist"]).copy()
m["dist100"] = m.dist / 100
m["hol"] = m.holidays_in_window.clip(upper=2)
m["freight_ratio"] = m.freight_total / m.items_price.clip(lower=1)
m["same_state"] = (m.customer_state == m.seller_state).astype(int)
fit = smf.logit("late ~ dist100 + C(hol) + same_state + np.log1p(items_price)", data=m).fit(disp=0)
print("\n[5] logistic regression, odds ratios (late = 1)")
print(pd.DataFrame({"odds_ratio": np.exp(fit.params), "p": fit.pvalues}).round(3).to_string())

# ---- 6. Seller effect: observed vs expected late rate given distance and state ---------
fit2 = smf.logit("late ~ dist100 + same_state + C(customer_state)", data=m).fit(disp=0)
m["expected"] = fit2.predict(m)
m["var"] = m.expected * (1 - m.expected)
g = m.groupby("seller_id").agg(orders=("late", "size"), late=("late", "sum"), expected=("expected", "sum"),
                              var=("var", "sum"), seller_state=("seller_state", "first"),
                              revenue=("items_price", "sum")).reset_index()
g["late_pct"] = 100 * g.late / g.orders
g["expected_pct"] = 100 * g.expected / g.orders
g["excess_late"] = g.late - g.expected
g["z"] = g.excess_late / np.sqrt(g["var"]).clip(lower=1e-9)   # normal approximation to the sum of Bernoulli draws
big = g[g.orders >= 50].copy()
worse = big[(big.z > 2)]
print(f"\n[6] sellers with 50+ orders: {len(big)} | significantly worse than expected (z>2): {len(worse)}")
print(f"    their orders: {worse.orders.sum():,} ({100 * worse.orders.sum() / len(m):.1f}% of analysed orders) | "
      f"late orders: {worse.late.sum():,.0f} = {100 * worse.late.sum() / m.late.sum():.1f}% of all late orders | "
      f"excess late orders: {worse.excess_late.sum():,.0f}")
top10 = g.sort_values("excess_late", ascending=False).head(10).excess_late.sum()
print(f"    the 10 sellers with the most excess late orders account for {top10:,.0f} of the {worse.excess_late.sum():,.0f} excess among significantly worse sellers")
g.drop(columns="var").sort_values("excess_late", ascending=False).round(2).to_csv(ROOT / "reports" / "seller_late_performance.csv", index=False)
print("\n    worst 5 sellers (50+ orders):")
print(worse.sort_values("excess_late", ascending=False).head(5)[["seller_id", "seller_state", "orders", "late_pct", "expected_pct", "revenue"]].round(1).to_string(index=False))
