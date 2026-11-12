"""Stage 8: sizing the proposed experiments from the data (design only, no result is invented).

A. Parana geo-experiment: how small an order lift could be detected, by test length?
B. Win-back message to recent high-value one-time customers: how small a repeat lift could be detected?

Run:  python notebooks/08_experiment_power.py
"""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "olist.db")
rng = np.random.default_rng(7)

# ---------------- A. Parana: randomise 3-digit zip areas, compare change vs before ----------------
o = pd.read_sql("""SELECT f.purchase_date, f.customer_zip, f.freight_total, f.items_price
                   FROM fact_orders f WHERE f.is_revenue_order = 1 AND f.customer_state = 'PR'""", con,
                parse_dates=["purchase_date"])
o["area"] = o.customer_zip.astype(str).str.zfill(5).str[:3]
o = o[o.purchase_date >= "2018-01-01"]
o["week"] = ((o.purchase_date - pd.Timestamp("2018-01-01")).dt.days // 7)
o = o[o.week < 34]
w = o.groupby(["area", "week"]).size().unstack(fill_value=0).reindex(columns=range(34), fill_value=0)
w = w[w.sum(axis=1) >= 30]               # areas with enough orders to be useful
print(f"PR: {len(o):,} orders in 2018 weeks 0-33 | {len(w)} zip areas with 30+ orders | "
      f"mean {w.sum().mean():.0f} orders per week in those areas | avg freight R${o.freight_total.mean():.2f} "
      f"on avg order R${o.items_price.mean():.2f}")

PRE = 12


def null_sd(post_weeks, n_sim=3000):
    pre = w.iloc[:, :PRE].sum(axis=1).values
    post = w.iloc[:, PRE:PRE + post_weeks].sum(axis=1).values
    # stratify by size: sort areas by pre volume, randomise within consecutive pairs
    idx = np.argsort(pre)
    pairs = [idx[i:i + 2] for i in range(0, len(idx) - 1, 2)]
    out = []
    for _ in range(n_sim):
        t, c = [], []
        for p in pairs:
            a, b = rng.permutation(p)
            t.append(a), c.append(b)
        T_pre, T_post, C_pre, C_post = pre[t].sum(), post[t].sum(), pre[c].sum(), post[c].sum()
        out.append(np.log((T_post / T_pre) / (C_post / C_pre)))
    return np.std(out)


print("\nMinimum detectable lift in orders (80% power, 5% two-sided), 12 weeks of pre-period data")
rows = []
for pw in (4, 8, 12, 16):
    sd = null_sd(pw)
    rows.append((pw, round(sd, 3), round(100 * (np.exp(2.8 * sd) - 1), 1)))
print(pd.DataFrame(rows, columns=["test_weeks", "sd_log_ratio", "min_detectable_lift_pct"]).to_string(index=False))

# ---------------- B. Win-back message: sample size ----------------
c = pd.read_sql("SELECT * FROM rfm_segments WHERE segment = 'One-time high value - recent'", con)
n = len(c)
base = 0.0228     # 90-day repeat rate observed in Stage 3
print(f"\nB. win-back audience: {n:,} customers | baseline 90-day repeat rate {100 * base:.2f}%")
pw = NormalIndPower()
for lift in (0.01, 0.02, 0.03):
    es = proportion_effectsize(base + lift, base)
    need = pw.solve_power(effect_size=es, alpha=0.05, power=0.8, ratio=1)
    print(f"   to detect +{100 * lift:.0f} pt ({100 * base:.1f}% -> {100 * (base + lift):.1f}%): {need:,.0f} customers per arm "
          f"({2 * need:,.0f} total) {'- fits the audience' if 2 * need <= n else '- more than the audience'}")
es_all = pw.solve_power(nobs1=n / 2, alpha=0.05, power=0.8, ratio=1, effect_size=None)
mde = (es_all)   # Cohen's h detectable with the full audience
p1 = np.sin((2 * np.arcsin(np.sqrt(base)) + mde) / 2) ** 2
print(f"   with the whole audience split 50/50 the smallest detectable repeat rate is {100 * p1:.2f}% "
      f"(+{100 * (p1 - base):.2f} pts)")
