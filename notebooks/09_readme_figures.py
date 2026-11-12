"""Static figures for the README. Writes PNG files to reports/figures/.

Run:  python notebooks/09_readme_figures.py   (after pipeline/30_export_for_bi.py)
"""
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "dashboard" / "summary"
OUT = ROOT / "reports" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2de"
BLUE, ORANGE = "#2a78d6", "#eb6834"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "font.size": 10,
})


def finish(fig, ax, title, subtitle, name, source="Source: Olist public dataset; delivered orders, Jan 2017 to Aug 2018"):
    fig.text(0.075, 0.955, title, fontsize=14, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.075, 0.895, subtitle, fontsize=10, color=INK2, ha="left", va="top")
    fig.text(0.075, 0.02, source, fontsize=8, color=INK2, ha="left")
    ax.grid(axis="x", visible=False) if name != "state_penetration" else None
    fig.savefig(OUT / f"{name}.png", dpi=170)
    plt.close(fig)
    print("saved", name)


# 1. Monthly revenue ---------------------------------------------------------------------------
m = pd.read_csv(S / "monthly_kpis.csv")
fig, ax = plt.subplots(figsize=(8, 4.5))
fig.subplots_adjust(top=0.78, bottom=0.15, left=0.09, right=0.95)
ax.plot(m.year_month, m.revenue / 1000, color=BLUE, linewidth=2, marker="o", markersize=5,
        markeredgecolor=SURFACE, markeredgewidth=1.5)
ax.set_ylim(0, 1100)
ax.set_ylabel("Revenue (R\$ thousand)")
ax.set_xticks(range(0, len(m), 3))
ax.set_xticklabels(m.year_month.iloc[::3])
pk = m.revenue.idxmax()
ax.annotate(f"Peak: R\${m.revenue[pk] / 1000:,.0f}k\n(Nov 2017)", (pk, m.revenue[pk] / 1000), xytext=(pk - 5.3, 1010),
            fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
last = len(m) - 1
ax.annotate(f"R\${m.revenue[last] / 1000:,.0f}k", (last, m.revenue[last] / 1000), xytext=(last - 1.2, 700),
            fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
finish(fig, ax, "Growth has been flat since January 2018",
       "Monthly revenue rose almost ninefold in 2017, then stayed between R\$826k and R\$978k", "monthly_revenue")

# 2. Customer concentration --------------------------------------------------------------------
d = pd.read_csv(S / "customer_deciles.csv")
d["share"] = 100 * d.revenue / d.revenue.sum()
fig, ax = plt.subplots(figsize=(8, 4.5))
fig.subplots_adjust(top=0.78, bottom=0.17, left=0.09, right=0.95)
ax.bar(d.decile.astype(str), d.share, color=BLUE, width=0.62)
for x, v in zip(d.decile.astype(str), d.share):
    ax.text(x, v + 0.8, f"{v:.1f}%", ha="center", fontsize=9, color=INK)
ax.set_ylim(0, 48)
ax.set_ylabel("Share of revenue (%)")
ax.set_xlabel("Customer decile by total spend (1 = top 10% of customers)")
finish(fig, ax, "The top 10% of customers bring 41% of revenue",
       "Only 3.0% of customers ever placed a second order, so most revenue comes from one-time buyers", "customer_deciles")

# 3. Delivery and reviews ----------------------------------------------------------------------
v = pd.read_csv(S / "delivery_impact.csv")
v["label"] = v.delivery.str[2:].str.replace("Late 7+ days", "7+ days late").str.replace("Late 1-6 days", "1-6 days late")
v["label"] = v.label.str.replace("On time", "On time")
fig, ax = plt.subplots(figsize=(8, 4.5))
fig.subplots_adjust(top=0.78, bottom=0.17, left=0.09, right=0.95)
ax.bar(v.label, v.avg_review, color=BLUE, width=0.5)
for x, r, lo in zip(v.label, v.avg_review, v.pct_low_review):
    ax.text(x, r + 0.1, f"{r:.2f}", ha="center", fontsize=11, fontweight="bold", color=INK)
    ax.text(x, r - 0.35, f"{lo:.0f}% rated 1-2 stars", ha="center", fontsize=9, color=SURFACE)
ax.set_ylim(0, 5)
ax.set_ylabel("Average review score (1 to 5)")
finish(fig, ax, "Late delivery wrecks review scores, mainly from 7 days late",
       "Repeat purchase after a late first order was not significantly lower (2.0% vs 2.3% within 90 days)",
       "delivery_vs_reviews")

# 4. State penetration vs income ---------------------------------------------------------------
s = pd.read_csv(S / "state_opportunity.csv")
fig, ax = plt.subplots(figsize=(8, 4.5))
fig.subplots_adjust(top=0.78, bottom=0.17, left=0.09, right=0.95)
colors = [ORANGE if c == "PR" else BLUE for c in s.state_code]
ax.scatter(s.income_pc, s.rev_per_1000, s=46, c=colors, edgecolors=SURFACE, linewidths=1.2, zorder=3)
offsets = {"SP": (6, 3), "RJ": (6, 3), "DF": (-22, 5), "MG": (6, -9), "PR": (6, -11), "RS": (6, 2), "SC": (6, 3),
           "BA": (6, 2), "AM": (6, 3), "MA": (6, 3), "PE": (6, 4), "CE": (-4, 7), "ES": (-18, 5), "RO": (6, 3)}
for _, r in s.iterrows():
    if r.state_code in offsets:
        dx, dy = offsets[r.state_code]
        ax.annotate(r.state_code, (r.income_pc, r.rev_per_1000), xytext=(dx, dy), textcoords="offset points",
                    fontsize=9, color=INK, fontweight="bold" if r.state_code == "PR" else "normal")
ax.set_xlabel("Household income per capita, 2018 (R\$ per month)")
ax.set_ylabel("Revenue per 1,000 residents (R\$)")
ax.set_ylim(0, 125)
ax.annotate("Parana (orange): income above the national level,\nrevenue per resident 42% below Rio de Janeiro",
            (1607, 58.5), xytext=(700, 98), fontsize=9, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
finish(fig, ax, "States with higher income buy far more per resident",
       "Income explains 62% of the variation in sales per resident (SP excluded)",
       "state_penetration", "Source: Olist public dataset; IBGE population (1 Jul 2018) and PNAD Continua income (2018)")
