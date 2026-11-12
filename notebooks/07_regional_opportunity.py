"""Stage 7: Where are we under-selling?  Revenue per resident vs state income (IBGE data).

Run:  python notebooks/07_regional_opportunity.py
Writes reports/state_opportunity.csv
"""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "olist.db")

st = pd.read_sql("""
SELECT i.state_code, i.state_name, i.region, i.population, i.income_pc,
       COALESCE(r.revenue, 0) AS revenue, COALESCE(r.orders, 0) AS orders, COALESCE(r.customers, 0) AS customers,
       r.avg_freight_ratio, r.late_pct, r.avg_delivery_days
FROM stg_ibge_states i LEFT JOIN (
    SELECT customer_state, SUM(items_price) AS revenue, COUNT(*) AS orders,
           COUNT(DISTINCT customer_unique_id) AS customers,
           100.0 * SUM(freight_total) / SUM(items_price) AS avg_freight_ratio,
           100.0 * AVG(is_late) AS late_pct, AVG(delivery_days) AS avg_delivery_days
    FROM fact_orders WHERE is_revenue_order = 1 GROUP BY customer_state) r ON r.customer_state = i.state_code""", con)
st["rev_per_1000"] = st.revenue / st.population * 1000
st["orders_per_1000"] = st.orders / st.population * 1000
st = st.sort_values("rev_per_1000", ascending=False)
print(st[["state_code", "income_pc", "population", "revenue", "rev_per_1000", "orders_per_1000",
          "avg_freight_ratio", "late_pct"]].round(1).to_string(index=False))

# How much of the gap is explained by income? log-log fit across states, excluding SP (home market, saturated)
fit_df = st[st.state_code != "SP"].copy()
fit_df["ly"], fit_df["lx"] = np.log(fit_df.rev_per_1000), np.log(fit_df.income_pc)
m = smf.ols("ly ~ lx", data=fit_df).fit()
print(f"\nlog(revenue per 1,000 residents) ~ log(income): elasticity {m.params['lx']:.2f}, R-squared {m.rsquared:.2f}, p = {m.pvalues['lx']:.3g}")
print("(excludes SP)")
st["ly_pred"] = m.params["Intercept"] + m.params["lx"] * np.log(st.income_pc)
st["expected_rev_per_1000"] = np.exp(st.ly_pred)
st["penetration_vs_expected"] = st.rev_per_1000 / st.expected_rev_per_1000
st["gap_revenue"] = (st.expected_rev_per_1000 - st.rev_per_1000).clip(lower=0) * st.population / 1000

# same view for delivery cost / time as a possible barrier
corr = st[["rev_per_1000", "avg_freight_ratio", "late_pct", "avg_delivery_days", "income_pc"]].corr(method="spearman").round(2)
print("\nSpearman correlations across states\n", corr.to_string())

under = st[(st.penetration_vs_expected < 0.8) & (st.state_code != "SP")].sort_values("gap_revenue", ascending=False)
print("\nStates selling below 80% of what their income predicts")
print(under[["state_code", "income_pc", "population", "rev_per_1000", "expected_rev_per_1000", "penetration_vs_expected",
             "gap_revenue", "avg_freight_ratio", "avg_delivery_days"]].round(2).to_string(index=False))
hi = st[(st.income_pc >= 1373) & (st.state_code != "SP")].sort_values("penetration_vs_expected")
print("\nStates at or above national income (R$1,373), by penetration vs expected\n",
      hi[["state_code", "income_pc", "rev_per_1000", "penetration_vs_expected", "gap_revenue", "late_pct"]].round(2).to_string(index=False))
print(f"\nScenario: lift the {len(under)} states below 80% of expected to 80% of expected -> "
      f"R${(under.expected_rev_per_1000 * 0.8 - under.rev_per_1000).clip(lower=0).mul(under.population / 1000).sum():,.0f} "
      f"over the window ({100 * (under.expected_rev_per_1000 * 0.8 - under.rev_per_1000).clip(lower=0).mul(under.population / 1000).sum() / st.revenue.sum():.1f}% of window revenue)")
print(f"Scenario: lift ALL states below expected to expected (excl. SP) -> R${st.loc[st.state_code != 'SP', 'gap_revenue'].sum():,.0f} "
      f"({100 * st.loc[st.state_code != 'SP', 'gap_revenue'].sum() / st.revenue.sum():.1f}% of window revenue)")
st.round(3).to_csv(ROOT / "reports" / "state_opportunity.csv", index=False)
