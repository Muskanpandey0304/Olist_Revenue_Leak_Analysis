"""Stage 4: Is late delivery hurting us?  Tests on review scores and on repeat purchase.

Run:  python notebooks/04_late_delivery_tests.py
"""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import confint_proportions_2indep, proportions_ztest

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "olist.db")
rng = np.random.default_rng(42)

o = pd.read_sql("""SELECT order_id, customer_unique_id, purchase_date, order_purchase_timestamp, is_late,
                          delivery_days, estimated_days, review_score, items_price
                   FROM fact_orders WHERE is_revenue_order = 1""", con,
                parse_dates=["purchase_date", "order_purchase_timestamp"])
o["late"] = o.is_late.astype(int)
print(f"delivered orders in window: {len(o):,} | late: {o.late.sum():,} ({100 * o.late.mean():.2f}%)")

# ---- 1. Review scores: late vs on-time ----------------------------------------------
r = o.dropna(subset=["review_score"])
late, ontime = r[r.late == 1].review_score, r[r.late == 0].review_score
print(f"\n[1] review score | reviewed orders {len(r):,} | late n={len(late):,} mean={late.mean():.2f} "
      f"| on-time n={len(ontime):,} mean={ontime.mean():.2f}")
print("    score distribution is skewed (check):", r.review_score.value_counts(normalize=True).sort_index().round(3).to_dict())
u = stats.mannwhitneyu(late, ontime, alternative="two-sided")
cliff = 2 * u.statistic / (len(late) * len(ontime)) - 1       # Cliff's delta (negative = late scores lower)
diffs = [rng.choice(late.values, len(late)).mean() - rng.choice(ontime.values, len(ontime)).mean() for _ in range(2000)]
print(f"    Mann-Whitney U p-value = {u.pvalue:.2e} | Cliff's delta = {cliff:.3f}")
print(f"    mean difference (late - on-time) = {late.mean() - ontime.mean():.2f} "
      f"| 95% bootstrap CI [{np.percentile(diffs, 2.5):.2f}, {np.percentile(diffs, 97.5):.2f}]")
lo_l, lo_o = (late <= 2).mean(), (ontime <= 2).mean()
print(f"    low reviews (1-2 stars): late {100 * lo_l:.1f}% vs on-time {100 * lo_o:.1f}%")

# ---- 2. How late? review score by lateness bucket ---------------------------------------
o["days_vs_estimate"] = o.estimated_days - o.delivery_days        # negative = days late
bins = [-1000, -14, -7, -1, 0, 7, 1000]
labels = ["14+ days late", "7-13 days late", "1-6 days late", "on estimate date", "1-7 days early", "8+ days early"]
o["bucket"] = pd.cut(o.days_vs_estimate, bins=bins, labels=labels)
b = o.dropna(subset=["review_score"]).groupby("bucket", observed=True).agg(
    orders=("order_id", "count"), mean_score=("review_score", "mean"),
    pct_low=("review_score", lambda s: 100 * (s <= 2).mean())).round(2)
print("\n[2] review score by delivery vs estimate\n", b.to_string())

# ---- 3. Repeat purchase after a late first delivery -------------------------------------
o = o.sort_values(["customer_unique_id", "order_purchase_timestamp"])
o["n"] = o.groupby("customer_unique_id").cumcount() + 1
first = o[o.n == 1][["customer_unique_id", "order_purchase_timestamp", "late", "review_score"]]
second = o[o.n == 2][["customer_unique_id", "order_purchase_timestamp", "items_price"]].rename(
    columns={"order_purchase_timestamp": "t2", "items_price": "second_value"})
f = first.merge(second, on="customer_unique_id", how="left")
f = f[f.order_purchase_timestamp <= pd.Timestamp("2018-08-31") - pd.Timedelta(days=90)]
f["repeat90"] = ((f.t2 - f.order_purchase_timestamp).dt.days <= 90).astype(int)
g = f.groupby("late").agg(customers=("customer_unique_id", "count"), repeated=("repeat90", "sum"))
g["rate_pct"] = (100 * g.repeated / g.customers).round(2)
print("\n[3] repeat within 90 days, by lateness of FIRST order\n", g.to_string())
x1, n1 = g.loc[1, "repeated"], g.loc[1, "customers"]
x0, n0 = g.loc[0, "repeated"], g.loc[0, "customers"]
z, p = proportions_ztest([x1, x0], [n1, n0])
ci = confint_proportions_2indep(x1, n1, x0, n0, method="wald")
print(f"    difference (late - on-time) = {100 * (x1 / n1 - x0 / n0):.2f} pts | z-test p = {p:.3g} "
      f"| 95% CI [{100 * ci[0]:.2f}, {100 * ci[1]:.2f}] pts")

# by review score of first order (the likely mechanism)
rs = f.dropna(subset=["review_score"]).copy()
rs["low"] = rs.review_score <= 2
h = rs.groupby("low").agg(customers=("customer_unique_id", "count"), rate_pct=("repeat90", lambda s: 100 * s.mean())).round(2)
print("\n    repeat within 90 days by first-order review (low = 1-2 stars)\n", h.to_string())

# ---- 4. Money view -------------------------------------------------------------------------
avg_second = o[o.n == 2].items_price.mean()
all_first_late = first[first.late == 1]
gap = x0 / n0 - x1 / n1
months = 20
lost = gap * len(all_first_late) * avg_second
print(f"\n[4] money: customers whose FIRST order was late = {len(all_first_late):,}; "
      f"repeat gap = {100 * gap:.2f} pts; average second order = R${avg_second:.2f}")
print(f"    repeat revenue not earned from late first orders = R${lost:,.0f} over {months} months (upper bound; "
      f"assumes the whole gap is caused by lateness)")
print(f"    low-review effect if late orders had the on-time low-review rate: "
      f"{100 * (lo_l - lo_o):.1f} pts of low reviews are associated with lateness")
