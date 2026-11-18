"""Generate a Power BI Project (PBIP) with the Olist model, measures and four report pages.

Output: dashboard/powerbi/olist_revenue_leak.pbip  (+ .SemanticModel and .Report folders)
Open the .pbip in Power BI Desktop, click Refresh once, then File -> Save as .pbix.

Run:  python pipeline/34_build_powerbi_project.py   (after pipeline/33_export_powerbi.py)
"""
from pathlib import Path
import json
import os
import shutil
import stat

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "dashboard" / "powerbi"
XLSX = PBI / "olist_powerbi_data.xlsx"
SCHEMA = json.loads((PBI / "schema.json").read_text(encoding="utf-8"))
NAME = "olist_revenue_leak"
SM = PBI / f"{NAME}.SemanticModel"
RP = PBI / f"{NAME}.Report"

BLUE, ORANGE, GREEN = "#2A78D6", "#EB6834", "#1BAF7A"
SCHEMA_URL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"


def rmtree(path: Path):
    """Delete a folder; Power BI Desktop leaves read-only flags on some folders, which blocks shutil.rmtree."""
    def clear_and_retry(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onexc=clear_and_retry)


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def wjson(path: Path, obj):
    write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- semantic model
BRL = r"\R\$#,##0"
MEASURES = {
    "fact_orders": [
        ("Revenue", "CALCULATE(SUM(fact_order_items[price]), fact_order_items[is_revenue_item] = 1)", BRL),
        ("Orders", "CALCULATE(DISTINCTCOUNT(fact_orders[order_id]), fact_orders[is_revenue_order] = 1)", "#,##0"),
        ("Customers", "CALCULATE(DISTINCTCOUNT(fact_orders[customer_unique_id]), fact_orders[is_revenue_order] = 1)", "#,##0"),
        ("AOV", "DIVIDE([Revenue], [Orders])", BRL),
        ("Repeat Customers", "COUNTROWS(FILTER(VALUES(fact_orders[customer_unique_id]), CALCULATE(DISTINCTCOUNT(fact_orders[order_id]), fact_orders[is_revenue_order] = 1) >= 2))", "#,##0"),
        ("Repeat Rate", "DIVIDE([Repeat Customers], [Customers])", "0.0%"),
        ("Late Rate", "CALCULATE(AVERAGE(fact_orders[is_late]), fact_orders[is_revenue_order] = 1)", "0.0%"),
        ("Avg Review", "CALCULATE(AVERAGE(fact_orders[review_score]), fact_orders[is_revenue_order] = 1)", "0.00"),
        ("Low Review %", "CALCULATE(AVERAGE(fact_orders[low_review]), fact_orders[is_revenue_order] = 1)", "0.0%"),
        ("Revenue MoM %", "VAR prev = CALCULATE([Revenue], DATEADD(dim_date[date], -1, MONTH)) RETURN DIVIDE([Revenue] - prev, prev)", "0.0%"),
        # helpers so the charts need no visual-level filters
        ("Revenue Top 10 Category", "VAR r = RANKX(ALLSELECTED(dim_product[category]), [Revenue], , DESC, DENSE) RETURN IF(r <= 10, [Revenue])", BRL),
        ("Late Rate Known Distance", "CALCULATE([Late Rate], NOT ISBLANK(fact_orders[avg_distance_km]))", "0.0%"),
        ("Late Rate Top 10 States (500+ orders)", "VAR r = RANKX(FILTER(ALLSELECTED(dim_customer[state]), [Orders] >= 500), [Late Rate], , DESC, DENSE) RETURN IF([Orders] >= 500 && r <= 10, [Late Rate])", "0.0%"),
    ],
    "rfm_segments": [
        ("Segment Customers", "COUNTROWS(rfm_segments)", "#,##0"),
        ("Segment Revenue", "SUM(rfm_segments[monetary])", BRL),
        ("Segment Revenue %", "DIVIDE([Segment Revenue], CALCULATE([Segment Revenue], ALL(rfm_segments)))", "0.0%"),
    ],
}
COL_FORMAT = {  # per-column display formats
    ("states", "revenue"): BRL, ("states", "population"): "#,##0", ("states", "income_pc"): BRL,
    ("states", "rev_per_1000"): r"\R\$#,##0.0", ("states", "expected_rev_per_1000"): r"\R\$#,##0.0",
    ("states", "penetration_vs_expected"): "0.00", ("states", "avg_freight_ratio"): "0.0",
    ("states", "late_pct"): "0.0", ("states", "avg_delivery_days"): "0.0",
    ("seller_watchlist", "revenue"): BRL, ("seller_watchlist", "late_pct"): "0.0",
    ("seller_watchlist", "expected_pct"): "0.0", ("seller_watchlist", "excess_late"): "0.0",
    ("rfm_segments", "monetary"): BRL,
    ("dim_date", "date"): "yyyy-mm-dd", ("fact_orders", "purchase_date"): "yyyy-mm-dd",
}
M_TYPE = {"string": "type text", "int64": "Int64.Type", "double": "type number", "dateTime": "type date"}


def tmdl_dtype(pandas_dtype: str) -> str:
    if pandas_dtype.startswith("datetime"):
        return "dateTime"
    if pandas_dtype.startswith("int"):
        return "int64"
    if pandas_dtype.startswith("float"):
        return "double"
    return "string"


def q(name: str) -> str:
    return f"'{name}'" if not name.replace("_", "").isalnum() else name


def table_tmdl(table: str, cols: dict) -> str:
    lines = [f"table {table}"]
    if table == "dim_date":
        lines.append("\tdataCategory: Time")
    lines.append("")
    for col, dt in cols.items():
        t = tmdl_dtype(dt)
        lines.append(f"\tcolumn {q(col)}")
        lines.append(f"\t\tdataType: {t}")
        if (table, col) in COL_FORMAT:
            lines.append(f"\t\tformatString: {COL_FORMAT[(table, col)]}")
        if table == "dim_date" and col == "date":
            lines.append("\t\tisKey")
        lines.append(f"\t\tsourceColumn: {col}")
        lines.append("\t\tsummarizeBy: none")
        lines.append("")
    for mname, dax, fmt in MEASURES.get(table, []):
        lines.append(f"\tmeasure {q(mname)} = {dax}")
        lines.append(f"\t\tformatString: {fmt}")
        lines.append("")
    types = ", ".join(f'{{"{c}", {M_TYPE[tmdl_dtype(d)]}}}' for c, d in cols.items())
    lines += [
        f"\tpartition {table} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\t\tlet",
        "\t\t\t\t    Source = Excel.Workbook(File.Contents(DataPath), true, true),",
        f'\t\t\t\t    Sheet = Source{{[Item="{table}", Kind="Sheet"]}}[Data],',
        f"\t\t\t\t    Typed = Table.TransformColumnTypes(Sheet, {{{types}}})",
        "\t\t\t\tin",
        "\t\t\t\t    Typed",
        "",
    ]
    return "\n".join(lines)


RELATIONSHIPS = """\
relationship rel_orders_date
	fromColumn: fact_orders.purchase_date
	toColumn: dim_date.date

relationship rel_orders_customer
	fromColumn: fact_orders.customer_unique_id
	toColumn: dim_customer.customer_unique_id

relationship rel_items_orders
	fromColumn: fact_order_items.order_id
	toColumn: fact_orders.order_id

relationship rel_items_seller
	fromColumn: fact_order_items.seller_id
	toColumn: dim_seller.seller_id

relationship rel_items_product
	fromColumn: fact_order_items.product_id
	toColumn: dim_product.product_id

relationship rel_rfm_customer
	fromCardinality: one
	crossFilteringBehavior: bothDirections
	fromColumn: rfm_segments.customer_unique_id
	toColumn: dim_customer.customer_unique_id
"""


def build_model():
    if SM.exists():
        rmtree(SM)
    wjson(SM / "definition.pbism", {"version": "4.0", "settings": {}})
    d = SM / "definition"
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")
    order = ["DataPath"] + list(SCHEMA)
    model = [
        "model Model",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures",
        "",
        "\tannotation __PBI_TimeIntelligenceEnabled = 0",
        f"\tannotation PBI_QueryOrder = {json.dumps(order)}",
        "",
    ]
    model += [f"ref table {t}" for t in SCHEMA] + ["ref expression DataPath", ""]
    write(d / "model.tmdl", "\n".join(model))
    write(d / "expressions.tmdl",
          'expression DataPath = "' + str(XLSX) +
          '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n')
    write(d / "relationships.tmdl", RELATIONSHIPS)
    for table, cols in SCHEMA.items():
        write(d / "tables" / f"{table}.tmdl", table_tmdl(table, cols))


# --------------------------------------------------------------------------- report
def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def s(text):  # string literal
    return lit("'" + text.replace("'", "''") + "'")


def col(table, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": prop}}


def meas(table, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": prop}}


def proj(field, table, prop, active=None):
    p = {"field": field, "queryRef": f"{table}.{prop}", "nativeQueryRef": prop}
    if active:
        p["active"] = True
    return p


def C(table, prop, active=None):
    return proj(col(table, prop), table, prop, active)


def M(table, prop):
    return proj(meas(table, prop), table, prop)


def S(table, prop, display):  # explicit Sum (one row per state, so Sum = the value)
    return {"field": {"Aggregation": {"Expression": col(table, prop), "Function": 0}},
            "queryRef": f"Sum({table}.{prop})", "nativeQueryRef": f"Sum of {prop}", "displayName": display}


def sort(field, direction):
    return {"sortDefinition": {"sort": [{"field": field, "direction": direction}], "isDefaultSort": False}}


class Page:
    def __init__(self, key, title):
        self.key, self.title, self.visuals = key, title, []

    def add(self, vtype, name, x, y, w, h, roles, title=None, alt=None, objects=None, srt=None):
        v = {
            "$schema": f"{SCHEMA_URL}/visualContainer/2.0.0/schema.json",
            "name": f"{self.key}_{name}",
            "position": {"x": x, "y": y, "z": len(self.visuals) * 10, "height": h, "width": w,
                         "tabOrder": len(self.visuals) * 10},
            "visual": {"visualType": vtype, "drillFilterOtherVisuals": True},
        }
        vis = v["visual"]
        if roles:
            query = {"queryState": {r: {"projections": p} for r, p in roles.items()}}
            if srt:
                query.update(srt)
            vis["query"] = query
        if objects:
            vis["objects"] = objects
        vco = {}
        if title:
            vco["title"] = [{"properties": {"show": lit("true"), "text": s(title), "fontSize": lit("12D"),
                                            "bold": lit("true")}}]
        if alt:
            vco["general"] = [{"properties": {"altText": s(alt)}}]
        if vco:
            vis["visualContainerObjects"] = vco
        self.visuals.append(v)

    def text(self, name, x, y, w, h, text, size="12pt", bold=False, color="#0B0B0B"):
        run = {"value": text, "textStyle": {"fontSize": size, "color": color}}
        if bold:
            run["textStyle"]["fontWeight"] = "bold"
        self.add("textbox", name, x, y, w, h, None,
                 objects={"general": [{"properties": {"paragraphs": [{"textRuns": [run]}]}}]})


def fill(hex_):
    return {"dataPoint": [{"properties": {"fill": {"solidColor": {"color": lit(f"'{hex_}'")}}}}]}


def labels_on(hex_=None):
    props = {"show": lit("true")}
    return {"labels": [{"properties": props}]}


def card(page, name, x, table, prop, alt, y=70, millions=False):
    units = {"labelDisplayUnits": lit("1000000D"), "labelPrecision": lit("1L")} if millions else {"labelDisplayUnits": lit("1D")}
    page.add("card", name, x, y, 195, 90, {"Values": [M(table, prop)]}, alt=alt,
             objects={"categoryLabels": [{"properties": {"show": lit("true")}}],
                      "labels": [{"properties": units}]})


def heading(page, subtitle):
    page.text("heading", 20, 12, 900, 44, f"Olist Revenue Leak Analysis  |  {subtitle}", size="18pt", bold=True)


def build_report():
    pages = []

    # ---- Page 1: Overview
    p = Page("ov", "Overview")
    heading(p, "Overview")
    p.add("slicer", "state", 930, 10, 160, 50, {"Values": [C("dim_customer", "state", True)]},
          alt="Filter by customer state", objects={"data": [{"properties": {"mode": s("Dropdown")}}]})
    p.add("slicer", "year", 1100, 10, 160, 50, {"Values": [C("dim_date", "year", True)]},
          alt="Filter by year", objects={"data": [{"properties": {"mode": s("Dropdown")}}]})
    for i, (t, m, a) in enumerate([("fact_orders", "Revenue", "Total revenue"), ("fact_orders", "Orders", "Orders"),
                                   ("fact_orders", "Customers", "Customers"), ("fact_orders", "AOV", "Average order value"),
                                   ("fact_orders", "Repeat Rate", "Repeat rate"), ("fact_orders", "Late Rate", "Late delivery rate")]):
        card(p, f"card{i}", 20 + i * 205, t, m, a, millions=(m == "Revenue"))
    p.add("lineChart", "trend", 20, 175, 620, 530,
          {"Category": [C("dim_date", "year_month", True)], "Y": [M("fact_orders", "Revenue")]},
          title="Growth has been flat since January 2018", alt="Monthly revenue line chart",
          objects=fill(BLUE) | {"labels": [{"properties": {"show": lit("false")}}]})
    p.add("clusteredBarChart", "categories", 660, 175, 600, 530,
          {"Category": [C("dim_product", "category", True)], "Y": [M("fact_orders", "Revenue Top 10 Category")]},
          title="18 of 74 categories bring 80% of revenue (top 10 shown)", alt="Top 10 product categories by revenue",
          objects=fill(BLUE) | labels_on(),
          srt=sort(meas("fact_orders", "Revenue Top 10 Category"), "Descending"))
    pages.append(p)

    # ---- Page 2: Customers
    p = Page("cu", "Customers")
    heading(p, "Customers")
    p.text("callout", 440, 80, 820, 70, "Only 3.0% of customers ever placed a second order.", size="20pt", bold=True, color=ORANGE)
    card(p, "c_rate", 20, "fact_orders", "Repeat Rate", "Repeat rate", y=70)
    card(p, "c_rep", 225, "fact_orders", "Repeat Customers", "Repeat customers", y=70)
    p.add("clusteredColumnChart", "deciles", 20, 170, 620, 290,
          {"Category": [C("rfm_segments", "decile", True)], "Y": [M("rfm_segments", "Segment Revenue %")]},
          title="The top 10% of customers bring 41% of revenue (decile 1 = highest spenders)",
          alt="Revenue share by customer spend decile",
          objects=fill(BLUE) | labels_on() | {"categoryAxis": [{"properties": {"axisType": s("Categorical")}}]},
          srt=sort(col("rfm_segments", "decile"), "Ascending"))
    p.add("clusteredBarChart", "segments", 660, 170, 600, 290,
          {"Category": [C("rfm_segments", "segment", True)], "Y": [M("rfm_segments", "Segment Revenue")]},
          title="Most revenue sits with one-time buyers", alt="Revenue by customer segment",
          objects=fill(BLUE) | labels_on(), srt=sort(meas("rfm_segments", "Segment Revenue"), "Descending"))
    p.add("tableEx", "table", 20, 475, 1240, 230,
          {"Values": [C("rfm_segments", "segment"), M("rfm_segments", "Segment Customers"),
                      M("rfm_segments", "Segment Revenue"), M("rfm_segments", "Segment Revenue %")]},
          title="Customer segments", alt="Table of customer segments with size and revenue share",
          srt=sort(meas("rfm_segments", "Segment Revenue"), "Descending"))
    pages.append(p)

    # ---- Page 3: Delivery
    p = Page("de", "Delivery")
    heading(p, "Delivery")
    p.text("callout", 20, 60, 1240, 44,
           "Late delivery hurts reviews, not repeat purchase (2.03% vs 2.31%, p = 0.15).",
           size="16pt", bold=True, color=ORANGE)
    p.add("clusteredColumnChart", "buckets", 20, 115, 400, 300,
          {"Category": [C("fact_orders", "delivery_bucket", True)], "Y": [M("fact_orders", "Avg Review")]},
          title="Reviews collapse from 7 days late", alt="Average review score by delivery outcome",
          objects=fill(ORANGE) | labels_on(), srt=sort(col("fact_orders", "delivery_bucket"), "Ascending"))
    p.add("clusteredColumnChart", "distance", 440, 115, 400, 300,
          {"Category": [C("fact_orders", "distance_band", True)], "Y": [M("fact_orders", "Late Rate Known Distance")]},
          title="Further away means later", alt="Late rate by seller to customer distance",
          objects=fill(BLUE) | labels_on(), srt=sort(col("fact_orders", "distance_band"), "Ascending"))
    p.add("clusteredBarChart", "states", 860, 115, 400, 300,
          {"Category": [C("dim_customer", "state", True)], "Y": [M("fact_orders", "Late Rate Top 10 States (500+ orders)")]},
          title="RJ is late despite being close", alt="Top 10 states by late rate (states with 500 or more orders). Rio de Janeiro is 13.5% late at about 394 km, far more than SP, MG or PR.",
          objects=fill(BLUE) | labels_on(),
          srt=sort(meas("fact_orders", "Late Rate Top 10 States (500+ orders)"), "Descending"))
    p.add("tableEx", "sellers", 20, 430, 1240, 275,
          {"Values": [C("seller_watchlist", c) for c in
              ["seller_id", "seller_state", "orders", "late_orders", "late_pct", "expected_pct", "excess_late", "revenue"]]},
          title="Sellers worse than their routes explain", alt="Seller watch-list table",
          srt=sort(col("seller_watchlist", "excess_late"), "Descending"))
    pages.append(p)

    # ---- Page 4: Regions
    p = Page("re", "Regions")
    heading(p, "Regions")
    p.add("scatterChart", "scatter", 20, 70, 620, 635,
          {"Category": [C("states", "state_code", True)], "X": [S("states", "income_pc", "Income per capita (R$/month)")], "Y": [S("states", "rev_per_1000", "Revenue per 1,000 residents (R$)")]},
          title="States with higher income buy far more per resident",
          alt="Scatter of household income per capita against revenue per 1,000 residents by state",
          objects={"categoryLabels": [{"properties": {"show": lit("true")}}], **fill(BLUE)})
    p.add("tableEx", "table", 660, 70, 600, 450,
          {"Values": [C("states", c) for c in
              ["state_code", "income_pc", "revenue", "rev_per_1000", "penetration_vs_expected", "late_pct", "avg_delivery_days"]]},
          title="State opportunity", alt="Table of states with income, revenue per resident and delivery",
          srt=sort(col("states", "rev_per_1000"), "Descending"))
    p.text("parana", 660, 540, 600, 165,
           "Parana is the proposed first test: income above the national level, revenue per resident 42% below Rio de Janeiro.",
           size="14pt", bold=True, color=ORANGE)
    pages.append(p)

    # ---- write
    if RP.exists():
        rmtree(RP)
    wjson(RP / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    d = RP / "definition"
    wjson(d / "version.json", {"$schema": f"{SCHEMA_URL}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    wjson(d / "report.json", {
        "$schema": f"{SCHEMA_URL}/report/2.0.0/schema.json",
        "themeCollection": {"customTheme": {"name": "olist_theme.json", "reportVersionAtImport": "5.70",
                                            "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "olist_theme.json", "path": "olist_theme.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True}})
    res = RP / "StaticResources" / "RegisteredResources"
    res.mkdir(parents=True, exist_ok=True)
    shutil.copy(PBI / "olist_theme.json", res / "olist_theme.json")
    wjson(d / "pages" / "pages.json", {"$schema": f"{SCHEMA_URL}/pagesMetadata/1.0.0/schema.json",
                                        "pageOrder": [pg.key for pg in pages], "activePageName": pages[0].key})
    for pg in pages:
        wjson(d / "pages" / pg.key / "page.json", {
            "$schema": f"{SCHEMA_URL}/page/2.0.0/schema.json", "name": pg.key, "displayName": pg.title,
            "displayOption": "FitToPage", "height": 720, "width": 1280})
        for v in pg.visuals:
            wjson(d / "pages" / pg.key / "visuals" / v["name"] / "visual.json", v)


def main():
    PBI.mkdir(parents=True, exist_ok=True)
    build_model()
    build_report()
    wjson(PBI / f"{NAME}.pbip", {
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}})
    write(PBI / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    print("wrote", PBI / f"{NAME}.pbip")


if __name__ == "__main__":
    main()
