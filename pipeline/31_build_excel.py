"""Build excel/olist_revenue_leak_summary.xlsx for teams that work in Excel.

Totals, shares, growth rates and per-resident figures are live Excel formulas, so the numbers can be
checked and reused. Run:  python pipeline/31_build_excel.py  (after pipeline/30_export_for_bi.py)
"""
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "dashboard" / "summary"
OUT = ROOT / "excel" / "olist_revenue_leak_summary.xlsx"

HEAD = PatternFill("solid", fgColor="1F3A5F")
WHITE = Font(bold=True, color="FFFFFF")
BRL, PCT, INT = '"R$" #,##0', "0.0%", "#,##0"

wb = Workbook()


def sheet(name, headers, widths=None, title=None, note=None):
    ws = wb.create_sheet(name)
    r = 1
    if title:
        ws.cell(1, 1, title).font = Font(bold=True, size=13)
        r = 2
        if note:
            ws.cell(2, 1, note).font = Font(italic=True, color="555555")
            r = 3
        r += 1
    for j, h in enumerate(headers, 1):
        c = ws.cell(r, j, h)
        c.fill, c.font = HEAD, WHITE
        c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[r].height = 32
    for j in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(j)].width = (widths or {}).get(j, 16)
    ws.freeze_panes = ws.cell(r + 1, 1)
    return ws, r + 1


def fmt(ws, col, first, last, number_format):
    for row in range(first, last + 1):
        ws.cell(row, col).number_format = number_format


# ---------------------------------------------------------------- Monthly
m = pd.read_csv(S / "monthly_kpis.csv")
ws, r0 = sheet("Monthly", ["Month", "Revenue (R$)", "Orders", "Active customers", "Avg order value (R$)",
                           "Revenue MoM %", "Freight (R$)"], {1: 11, 2: 15, 3: 10, 4: 14, 5: 14, 6: 12, 7: 14},
               "Monthly KPIs", "Delivered orders, 2017-01 to 2018-08. Revenue = item price, freight excluded.")
for i, row in enumerate(m.itertuples(index=False)):
    r = r0 + i
    ws.cell(r, 1, row.year_month)
    ws.cell(r, 2, row.revenue)
    ws.cell(r, 3, row.orders)
    ws.cell(r, 4, row.active_customers)
    ws.cell(r, 5, f"=B{r}/C{r}")
    ws.cell(r, 6, None if i == 0 else f"=B{r}/B{r-1}-1")
    ws.cell(r, 7, row.freight)
last = r0 + len(m) - 1
tot = last + 1
ws.cell(tot, 1, "Total").font = Font(bold=True)
for col in (2, 3, 7):
    L = get_column_letter(col)
    ws.cell(tot, col, f"=SUM({L}{r0}:{L}{last})").font = Font(bold=True)
ws.cell(tot, 5, f"=B{tot}/C{tot}").font = Font(bold=True)
fmt(ws, 2, r0, tot, BRL)
fmt(ws, 3, r0, tot, INT)
fmt(ws, 4, r0, last, INT)
fmt(ws, 5, r0, tot, '"R$" #,##0.00')
fmt(ws, 6, r0, last, PCT)
fmt(ws, 7, r0, tot, BRL)
ch = LineChart()
ch.title = "Monthly revenue (R$)"
ch.height, ch.width = 8, 18
ch.add_data(Reference(ws, min_col=2, min_row=r0 - 1, max_row=last), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=r0, max_row=last))
ch.legend = None
ws.add_chart(ch, "I3")
monthly_total_cell = f"Monthly!B{tot}"
monthly_orders_cell = f"Monthly!C{tot}"

# ---------------------------------------------------------------- Categories
c = pd.read_csv(S / "category_summary.csv")
ws, r0 = sheet("Categories", ["Category", "Revenue (R$)", "Orders", "Share of revenue", "Cumulative share"],
               {1: 30, 2: 15, 3: 10, 4: 14, 5: 16}, "Revenue by product category",
               "Sorted by revenue. Cumulative share shows how few categories carry most of the revenue.")
for i, row in enumerate(c.itertuples(index=False)):
    r = r0 + i
    ws.cell(r, 1, row.category)
    ws.cell(r, 2, row.revenue)
    ws.cell(r, 3, row.orders)
last = r0 + len(c) - 1
for r in range(r0, last + 1):
    ws.cell(r, 4, f"=B{r}/SUM($B${r0}:$B${last})")
    ws.cell(r, 5, f"=SUM($B${r0}:B{r})/SUM($B${r0}:$B${last})")
fmt(ws, 2, r0, last, BRL)
fmt(ws, 3, r0, last, INT)
fmt(ws, 4, r0, last, PCT)
fmt(ws, 5, r0, last, PCT)
bc = BarChart()
bc.type = "bar"
bc.title = "Top 10 categories by revenue (R$)"
bc.height, bc.width = 9, 18
bc.add_data(Reference(ws, min_col=2, min_row=r0 - 1, max_row=r0 + 9), titles_from_data=True)
bc.set_categories(Reference(ws, min_col=1, min_row=r0, max_row=r0 + 9))
bc.legend = None
bc.x_axis.scaling.orientation = "maxMin"
ws.add_chart(bc, "G3")

# ---------------------------------------------------------------- States
s = pd.read_csv(S / "state_opportunity.csv").sort_values("rev_per_1000", ascending=False)
ws, r0 = sheet("States", ["State", "Region", "Population (1 Jul 2018)", "Income per capita (R$)", "Revenue (R$)",
                          "Revenue per 1,000 residents (R$)", "Expected per 1,000 (from income)",
                          "Penetration vs expected", "Freight % of price", "Late %", "Avg delivery days"],
               {1: 8, 2: 13, 3: 16, 4: 15, 5: 14, 6: 17, 7: 17, 8: 15, 9: 12, 10: 9, 11: 12},
               "State penetration vs income",
               "Population: IBGE estimate (1 July 2018). Income: IBGE PNAD Continua 2018. "
               "Expected = fitted on income across 26 states (SP excluded).")
for i, row in enumerate(s.itertuples(index=False)):
    r = r0 + i
    ws.cell(r, 1, row.state_code)
    ws.cell(r, 2, row.region)
    ws.cell(r, 3, row.population)
    ws.cell(r, 4, row.income_pc)
    ws.cell(r, 5, round(row.revenue, 2))
    ws.cell(r, 6, f"=E{r}/C{r}*1000")
    ws.cell(r, 7, round(row.expected_rev_per_1000, 2))
    ws.cell(r, 8, f"=F{r}/G{r}")
    ws.cell(r, 9, None if pd.isna(row.avg_freight_ratio) else round(row.avg_freight_ratio / 100, 4))
    ws.cell(r, 10, None if pd.isna(row.late_pct) else round(row.late_pct / 100, 4))
    ws.cell(r, 11, None if pd.isna(row.avg_delivery_days) else round(row.avg_delivery_days, 1))
last = r0 + len(s) - 1
fmt(ws, 3, r0, last, INT)
fmt(ws, 4, r0, last, BRL)
fmt(ws, 5, r0, last, BRL)
fmt(ws, 6, r0, last, "0.0")
fmt(ws, 7, r0, last, "0.0")
fmt(ws, 8, r0, last, "0%")
fmt(ws, 9, r0, last, PCT)
fmt(ws, 10, r0, last, PCT)

# ---------------------------------------------------------------- Segments
g = pd.read_csv(S / "rfm_segment_summary.csv")
ws, r0 = sheet("Segments", ["Segment", "Customers", "Revenue (R$)", "Avg spend (R$)",
                            "Median days since last order", "% of customers", "% of revenue"],
               {1: 32, 2: 12, 3: 14, 4: 14, 5: 16, 6: 13, 7: 12}, "Customer segments",
               "One-time buyers split at the 80th percentile of spend (R$175.99). "
               "Recent = ordered in the 180 days before 1 Sep 2018.")
for i, row in enumerate(g.itertuples(index=False)):
    r = r0 + i
    ws.cell(r, 1, row.segment)
    ws.cell(r, 2, row.customers)
    ws.cell(r, 3, row.revenue)
    ws.cell(r, 4, f"=C{r}/B{r}")
    ws.cell(r, 5, row.median_recency_days)
last = r0 + len(g) - 1
for r in range(r0, last + 1):
    ws.cell(r, 6, f"=B{r}/SUM($B${r0}:$B${last})")
    ws.cell(r, 7, f"=C{r}/SUM($C${r0}:$C${last})")
fmt(ws, 2, r0, last, INT)
fmt(ws, 3, r0, last, BRL)
fmt(ws, 4, r0, last, '"R$" #,##0.00')
fmt(ws, 6, r0, last, PCT)
fmt(ws, 7, r0, last, PCT)

# ---------------------------------------------------------------- Delivery
d = pd.read_csv(S / "delivery_impact.csv")
ws, r0 = sheet("Delivery", ["Delivery", "Orders", "Revenue (R$)", "Avg review score",
                            "% low reviews (1-2 stars)", "% of orders", "% of revenue"],
               {1: 20, 2: 10, 3: 15, 4: 14, 5: 20, 6: 11, 7: 12},
               "Delivery against the estimated date and its effect on reviews",
               "Late orders: 54% low reviews against 9% on time. "
               "Repeat purchase showed no significant difference (see report).")
for i, row in enumerate(d.itertuples(index=False)):
    r = r0 + i
    ws.cell(r, 1, row.delivery[2:])
    ws.cell(r, 2, row.orders)
    ws.cell(r, 3, row.revenue)
    ws.cell(r, 4, row.avg_review)
    ws.cell(r, 5, row.pct_low_review / 100)
last = r0 + len(d) - 1
for r in range(r0, last + 1):
    ws.cell(r, 6, f"=B{r}/SUM($B${r0}:$B${last})")
    ws.cell(r, 7, f"=C{r}/SUM($C${r0}:$C${last})")
fmt(ws, 2, r0, last, INT)
fmt(ws, 3, r0, last, BRL)
fmt(ws, 4, r0, last, "0.00")
fmt(ws, 5, r0, last, PCT)
fmt(ws, 6, r0, last, PCT)
fmt(ws, 7, r0, last, PCT)

# ---------------------------------------------------------------- Seller watch-list
w = pd.read_csv(S / "seller_late_performance.csv")
w = w[(w.orders >= 50) & (w.z > 2)].sort_values("excess_late", ascending=False)
ws, r0 = sheet("Seller watch-list", ["Seller id", "State", "Orders", "Late orders", "Late %", "Expected late %",
                                     "Excess late orders", "Revenue (R$)"],
               {1: 36, 2: 8, 3: 9, 4: 11, 5: 9, 6: 14, 7: 14, 8: 14},
               "Sellers with more late orders than their routes explain",
               "Sellers with 50+ orders whose late rate is significantly above expectation (z > 2) "
               "after allowing for distance and state.")
for i, row in enumerate(w.itertuples(index=False)):
    r = r0 + i
    ws.cell(r, 1, row.seller_id)
    ws.cell(r, 2, row.seller_state)
    ws.cell(r, 3, row.orders)
    ws.cell(r, 4, row.late)
    ws.cell(r, 5, f"=D{r}/C{r}")
    ws.cell(r, 6, round(row.expected_pct / 100, 4))
    ws.cell(r, 7, round(row.excess_late, 1))
    ws.cell(r, 8, round(row.revenue, 2))
last = r0 + len(w) - 1
fmt(ws, 5, r0, last, PCT)
fmt(ws, 6, r0, last, PCT)
fmt(ws, 8, r0, last, BRL)
print("watch-list sellers:", len(w))

# ---------------------------------------------------------------- Summary (first sheet)
ws = wb["Sheet"]
ws.title = "Summary"
wb.move_sheet("Summary", offset=-len(wb.sheetnames) + 1)
ws.column_dimensions["A"].width = 44
ws.column_dimensions["B"].width = 20
ws.column_dimensions["C"].width = 70
ws["A1"] = "Olist Revenue Leak Analysis: summary workbook"
ws["A1"].font = Font(bold=True, size=14)
ws["A2"] = "Window: orders purchased 2017-01 to 2018-08, delivered only. Definitions: reports/metrics_definitions.md"
ws["A3"], ws["B3"], ws["C3"] = "Metric", "Value", "Note"
for cell in ("A3", "B3", "C3"):
    ws[cell].fill, ws[cell].font = HEAD, WHITE
rows = [
    ("Revenue (R$)", f"={monthly_total_cell}", BRL, "Item price of delivered orders, freight excluded"),
    ("Delivered orders", f"={monthly_orders_cell}", INT, ""),
    ("Average order value (R$)", "=B4/B5", '"R$" #,##0.00', "Flat between R$124 and R$149 every month"),
    ("Customers", 93096, INT, "Unique persons (customer_unique_id)"),
    ("Repeat customers", 2789, INT, "Two or more delivered orders"),
    ("Repeat rate", "=B8/B7", PCT, "Almost nobody comes back: the main leak"),
    ("Late delivery rate", 0.0813, PCT, "Delivered after the estimated date"),
    ("Low reviews on late orders", 0.541, PCT, "Against 9.2% on on-time orders"),
]
for i, (a, b, f, n) in enumerate(rows):
    r = 4 + i
    ws.cell(r, 1, a)
    ws.cell(r, 2, b).number_format = f
    ws.cell(r, 3, n)
ws["A14"] = "Sheets: Monthly, Categories, States, Segments, Delivery, Seller watch-list."
OUT.parent.mkdir(exist_ok=True)
wb.save(OUT)
print("saved", OUT)
