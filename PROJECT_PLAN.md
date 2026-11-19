# Olist Revenue Leak Analysis

**Full title:** Olist Revenue Leak Analysis: Finding Where a Marketplace Loses Money in Customers, Delivery and Regions
**Repository name:** `olist-revenue-leak-analysis`

Living document. It holds the full plan, the reasoning behind every part, and the progress log. Any change to scope, tools, data or findings is recorded here (see the Change Log at the bottom).

---

## 0. Project Rules

1. Every feature in this project must exist because a business question needs it. If a tool or dataset does not answer a question, it does not go in.
2. This file is updated whenever the plan, scope, tools, data or results change.

---

## 1. One Project, Built Like Real Work

**One connected project**, not several small ones. A real analyst job is one continuous chain: someone asks a question, you find and combine the data, clean it, model it, query it, test the answer, put a money value on it, and hand over something each team can use.

Two things make this project different from the common Olist notebooks:

1. **It is built like a company data pipeline**, with raw, staging and modeled layers, a star schema and automated data quality tests, instead of one long notebook.
2. **It combines Olist with official Brazilian public data**, so it can answer questions that the dataset alone cannot. No two versions of this project will look the same.

Every finding is expressed in money where possible, because that is how decisions get made.

---

## 2. Project Setting

**Company:** Olist, a Brazilian online marketplace connecting small sellers to large sales channels.
**Role framing:** Data analyst supporting leadership, operations and marketing.

**Central brief from leadership:**
> Growth has levelled off. We do not know which customers matter, why most customers buy only once, whether delivery problems are costing us, or whether we are under-selling in the regions with the most spending power. Tell us where the money is, where we are losing it, and what to do first.

---

## 3. Data Sources

All sources are free and public. Each one is included only because a specific question needs it, and each joins cleanly on a key that already exists in Olist.

### 3.1 Core dataset: Olist Brazilian E-commerce (Kaggle)
- About 100,000 orders, 2016 to 2018, 9 related tables: orders, order items, payments, reviews, customers, sellers, products, geolocation, category name translation.
- **Why this dataset:** multi-table (real joins), real and messy (real cleaning), right size for a laptop, and covers revenue, customers, delivery, reviews, sellers and geography in one connected model.

### 3.2 IBGE state population and income (external)
- Source: IBGE, Brazil's official statistics institute. State-level (27 states) population estimates and household income per capita for 2017 and 2018, matching the Olist period.
- **Joins on:** state code (`customer_state`, `seller_state`), for example SP, RJ, MG.
- **Built:** `data/raw/external/ibge_states_2018.csv`. Population is the IBGE estimate for 1 July 2018; income is PNAD Contínua 2018 nominal monthly household income per capita. Only 2018 is used, not 2017 and 2018 as first planned, because Olist volume is concentrated in 2017 to 2018 and one reference year keeps the join simple. Totals were checked against IBGE's Brazil and regional totals.
- **Question it answers:** "Are we under-selling in states where people can afford to buy more?" Without it, the analysis only shows that big states sell more, which mostly reflects population.
- **Enables:** revenue per 1,000 residents, penetration vs income, an "untapped market" ranking of states.
- **Fit:** 27 rows, one small CSV built from published tables. Very easy.

### 3.3 Brazilian public holidays (external)
- Source: the Python `holidays` library (national holidays for Brazil, with state holidays where available) for 2016 to 2018. Cross-checked against the official calendar.
- **Joins on:** date (purchase date, estimated and actual delivery dates).
- **Question it answers:** "Do holidays delay deliveries or shift demand?" Also a feature in the late-delivery risk model (number of holidays inside the delivery window).
- **Fit:** generated in a few lines of code, becomes a flag in the date dimension. Very easy.

### 3.4 Seller-to-customer distance (derived from Olist data)
- Not an external download. Calculated from the Olist geolocation table: average latitude and longitude per zip-code prefix, then the straight-line (haversine) distance between seller and customer.
- **Question it answers:** "Is a late delivery a distance problem or a seller problem?" These need different fixes (logistics partners vs seller management).
- **Fit:** one calculation step in the staging layer. Easy.

### 3.5 Deliberately not included
- Weather, fuel prices, exchange rates, social media data. Each would add download and matching effort without a clear question that the sources above do not already cover. Can be reconsidered later only if a finding demands it.

---

## 4. Data Architecture

### 4.1 Layers
```
raw        → original files, never edited
staging    → cleaned, typed, deduplicated tables (one per source table)
marts      → star schema used by analysis, model and dashboard
```

### 4.2 Star schema (marts layer)
- **fact_order_items**: one row per item sold (price, freight, order id, product, seller, customer, dates)
- **fact_orders**: one row per order (totals, payment, delivery days, late flag, review score, distance)
- **dim_customer**: customer, city, state, plus IBGE population and income of that state
- **dim_seller**: seller, city, state, location
- **dim_product**: product, category (English), size and weight
- **dim_date**: calendar, month, quarter, weekday, holiday flag

### 4.3 Automated data quality tests
Run every time the pipeline runs. The pipeline stops if any test fails.
- No duplicate order ids in `fact_orders`
- Revenue in marts reconciles with raw payment totals (within a stated tolerance, with the gap explained)
- No negative delivery durations
- Every fact row links to an existing dimension row
- Every Olist state matches an IBGE state

**Why this is needed:** a wrong number shown confidently is worse than no number. Tests prove the numbers can be trusted and that the work is reproducible.

### 4.4 Metrics definitions
A one-page document in `reports/metrics_definitions.md` defining exactly how each KPI is calculated: revenue (and whether freight is included), order, active customer, repeat customer, repeat rate, average order value, late delivery, delivery days. Real teams disagree on these, so they are fixed before any analysis.

---

## 5. Question-Driven Build (why each skill is needed)

### Stage 1: "Are we actually growing, and where does revenue come from?"
- **Need:** data is spread across 9 tables; no single table answers this.
- **Skill:** SQL on the marts (joins, CTEs, aggregations, LAG for month-over-month growth, RANK for top categories).
- **Output:** KPI trend table using the agreed metric definitions.
- **Why required:** orders with multiple items or payments double-count revenue if joined carelessly. Getting this right is the first real test of an analyst.

### Stage 2: "Can we trust this data?"
- **Need:** missing delivery dates, duplicate geolocation rows, inconsistent category names, canceled orders mixed in, and external data that must match Olist's state codes.
- **Skill:** Python (pandas) for cleaning and building the staging and marts layers, plus the automated tests in section 4.3.
- **Output:** clean star schema and a data quality log listing every issue and the decision made.

### Stage 3: "Who are our customers, and why do so few come back?"
- **Need:** treating all customers the same hides that a small group produces much of the revenue.
- **Skill:** RFM segmentation, cohort retention analysis, Pareto (80/20) analysis.
- **Output:** segments with size and revenue share; retention by first-purchase month.
- **Money view:** revenue at risk in the "At Risk" segment.

### Stage 4: "Is late delivery hurting us, or is that just a guess?"
- **Need:** operations believes delivery speed matters; leadership wants proof before spending.
- **Skill:** hypothesis test (t-test or Mann-Whitney, chosen after checking distributions) on review scores of late vs on-time orders, with effect size and confidence interval. Also compare repeat-purchase rates.
- **Money view:** estimated repeat revenue lost each year due to late deliveries.

### Stage 5: "Is late delivery a distance problem, a seller problem, or a holiday problem?"
- **Need:** each cause has a different fix.
- **Skill:** analysis using seller-to-customer distance and the holiday flag; compare sellers at similar distances.
- **Output:** split of lateness into distance-driven and seller-driven, with the worst seller groups and routes.

### Stage 6: "Which orders will likely be late, so operations can act early?"
- **Need:** knowing lateness hurts is only useful if the team can prevent it.
- **Skill:** one explainable model (logistic regression, compared with a random forest), proper train/test split, metrics suited to imbalanced data, feature importance in plain language. Features include distance, holidays in the delivery window, product weight, freight value and seller history.
- **Output:** risk score and the top risk factors.
- **Why kept small:** an analyst must be able to explain the model to operations, not just score it.

### Stage 7: "Where are we under-selling?"
- **Need:** big states always sell the most; the useful question is where sales are low relative to population and income.
- **Skill:** combine Olist revenue with IBGE data; revenue per 1,000 residents vs income per capita; ranking and geographic analysis.
- **Output:** "untapped states" list and the categories and sellers with the most impact.
- **Money view:** potential revenue if the weakest high-income states reached the average penetration rate.

### Stage 8: "How do we know a fix would work before rolling it out?"
- **Need:** recommendations should be tested, not assumed.
- **Skill:** experiment design for the top recommendation: success metric, sample size and power calculation, duration, risks.
- **Output:** one-page experiment plan. Design only; no result is invented.

### Stage 9: "How do different teams get the answer?"
- **Need:** each audience uses a different format.
- **Outputs:**
  - **Power BI dashboard** (published to the web): executive KPIs, customer segments and retention, delivery performance and causes, regional opportunity map, with drill-through from state to seller.
  - **Excel workbook** with pivot summaries for teams that work in Excel.
  - **Stakeholder memo** (1 page) to the Head of Operations: 3 recommendations ranked by money impact, cost, and how success will be measured.
  - **Full insights report** (about 2 to 3 pages).
  - ~~2-minute walkthrough video~~ dropped (2026-11-19): the live dashboard and the README already show the findings, and a video is optional.

---

## 6. Tools and the Reason for Each

| Tool | Used for | Needed because |
|---|---|---|
| SQL (SQLite; PostgreSQL optional) | Marts queries, KPIs, cohorts, rankings | Data is spread across many tables |
| Python (pandas, numpy) | Cleaning, staging, marts, distance calculation | Scripted, repeatable data preparation |
| Python (`holidays`) | Holiday calendar | Tests holiday effect on delivery and demand |
| Python (scipy, statsmodels) | Hypothesis tests, power analysis | Claims need statistical evidence |
| Python (scikit-learn) | Late-delivery risk model | Operations needs an early warning |
| Python test scripts (pytest or plain asserts) | Data quality tests | Proves numbers are trustworthy |
| Matplotlib / seaborn | Exploration charts | Spot patterns before the dashboard |
| Power BI | Interactive dashboard | Self-service views for leadership and ops |
| Excel | Pivot summary | Many business teams work in Excel |
| Git and GitHub | Version control, portfolio | Reproducible work visible to recruiters |

---

## 7. Repository Structure

```
olist-revenue-leak-analysis/
├── PROJECT_PLAN.md            (this plan)
├── README.md                  (written later, after results exist)
├── data/
│   ├── raw/
│   │   ├── olist/             (9 original CSVs, never edited)
│   │   └── external/          (IBGE state data)
│   ├── staging/
│   └── marts/                 (star schema tables / SQLite database)
├── pipeline/                  (scripts: load → staging → marts, run in order)
├── tests/                     (data quality tests)
├── sql/                       (numbered query files, one per question)
├── notebooks/                 (EDA, statistical tests, model)
├── dashboard/                 (Power BI file and screenshots)
├── excel/                     (pivot workbook)
└── reports/
    ├── metrics_definitions.md
    ├── data_quality_log.md
    ├── insights_report.md      (export to PDF when final)
    ├── stakeholder_memo.md     (export to PDF when final)
    └── experiment_design.md
```

The full pipeline must run from raw files to marts with one command, and all tests must pass.

---

## 8. Timeline (about 4 weeks)

| Week | Focus | Done when |
|---|---|---|
| 1 | Download data, build IBGE CSV, metric definitions, pipeline to staging and marts, data quality tests (Stage 2) | One command builds the star schema and all tests pass |
| 2 | SQL KPIs, segmentation, retention, late-delivery test, cause analysis (Stages 1, 3, 4, 5) | Each question has a written answer with numbers and money impact |
| 3 | Risk model, regional opportunity, experiment design (Stages 6, 7, 8) | Model is evaluated and explained; untapped states ranked |
| 4 | Dashboard, Excel, memo, report, repo polish (Stage 9) | Dashboard link works, memo is clear, repo runs from scratch |

---

## 9. What a Recruiter Should See in 30 Seconds

1. A live dashboard link at the top of the repository.
2. The problem and the top three findings, each with a money figure.
3. A visible pipeline, star schema and passing tests, showing the work is reliable.
4. SQL, Python, statistics, a model, Power BI and Excel, each tied to a question.

Resume line (finalised after results): one bullet naming data size, combined sources, tools, and the main finding with a money figure.

---

## 10. Progress Tracker

- [x] Download Olist data and build IBGE state CSV
- [x] Metrics definitions written (first version; revisit after staging)
- [x] Pipeline: raw → staging (`pipeline/10_build_staging.py`)
- [x] Pipeline: staging → marts (`pipeline/20_build_marts.py`, `sql/10_build_marts.sql`)
- [x] Data quality tests passing (20 tests, `tests/test_marts.py`; whole pipeline runs with `python pipeline/run_pipeline.py`)
- [x] Stage 1: SQL KPIs (`sql/30` to `33`, findings in `reports/stage1_findings.md`)
- [x] Stage 2: Data quality log (first full version; update as new issues appear)
- [x] Stage 3: Segmentation and retention (`sql/40`, `41`, `notebooks/03_rfm_segments.py`, `reports/stage3_findings.md`)
- [x] Stage 4: Late delivery vs reviews test (`notebooks/04_late_delivery_tests.py`, `reports/stage4_findings.md`)
- [x] Stage 5: Causes of late delivery (`notebooks/05_late_delivery_causes.py`, `reports/stage5_findings.md`)
- [x] Stage 6: Late-delivery risk model (`notebooks/06_late_risk_model.py`, `reports/stage6_findings.md`)
- [x] Stage 7: Regional opportunity (`notebooks/07_regional_opportunity.py`, `reports/stage7_findings.md`)
- [x] Stage 8: Experiment design (`notebooks/08_experiment_power.py`, `reports/experiment_design.md`)
- [x] Stage 9a: exports for BI, Excel workbook, stakeholder memo, insights report, Power BI build guide
- [x] Stage 9b-web: interactive web dashboard built (`pipeline/32_build_web_dashboard.py`, `docs/index.html`, 4 pages, light and dark mode); turn on GitHub Pages to publish
- [x] Stage 9b-powerbi: Power BI file built and checked in Desktop (`dashboard/powerbi/olist_revenue_leak.pbix`, 4 pages, generated by `pipeline/34_build_powerbi_project.py`; page screenshots `page1_overview.png` to `page4_regions.png`). Not yet published to the Power BI service
- [x] Stage 9c: walkthrough video dropped by decision (not needed; see Decisions Log)
- [x] README written and updated with Power BI section, screenshots and run steps
- [x] README figures (`notebooks/09_readme_figures.py`, `reports/figures/`)
- [x] Memo and report exported to PDF (`pipeline/35_export_pdfs.py`, `reports/stakeholder_memo.pdf` 1 page, `reports/insights_report.pdf` 3 pages)
- [ ] Final repository polish: add resume line, pin the repo and fill in the About box

---

## 11. Decisions Log

| Date | Decision | Reason |
|---|---|---|
| 2026-11-12 | One connected project instead of several small ones | Shows the full analyst workflow |
| 2026-11-12 | Olist as core dataset | Multi-table, real and messy, right size, many connected business angles, free and public |
| 2026-11-12 | ML limited to one small explainable model | Entry-level analyst role; interpretability matters more than complexity |
| 2026-11-12 | Build as a layered pipeline with star schema and data quality tests | Separates the project from common notebook-only versions; shows reliability |
| 2026-11-12 | Add IBGE state population and income | Enables per-capita and income-adjusted regional analysis; joins on state; 27 rows |
| 2026-11-12 | Add Brazilian public holidays | Tests holiday effect on delivery and demand; model feature; generated in code |
| 2026-11-12 | Derive seller-to-customer distance | Separates distance-driven from seller-driven lateness; no extra download |
| 2026-11-12 | IBGE reference year: 2018 only; holidays: national only | Single year keeps the state join simple; state holiday data is not available in one reliable source |
| 2026-11-12 | Analysis window 2017-01 to 2018-08; revenue from delivered orders, item price only | Months outside the window are nearly empty; freight is not seller revenue |
| 2026-11-12 | Exclude weather, fuel, exchange rate, social data | Extra effort without a question not already covered |
| 2026-11-12 | Express findings in money where possible | Decisions are made on money impact |
| 2026-11-12 | Project named "Olist Revenue Leak Analysis" | Says what the project finds (lost money), not just what data it uses; easy to remember |
| 2026-11-19 | Decision: no walkthrough video | The live dashboard, README and PDFs already show the work; a README placeholder for a missing video looks unfinished |

---

## 12. Change Log

| Date | Change |
|---|---|
| 2026-11-12 | Initial plan created |
| 2026-11-12 | Added pipeline layers, star schema, data quality tests, metrics definitions; added IBGE, holidays and distance data; added cause analysis and regional opportunity stages; added stakeholder memo and video; timeline extended to 4 weeks |
| 2026-11-12 | Project named "Olist Revenue Leak Analysis"; repository folder renamed to `olist-revenue-leak-analysis` |
| 2026-11-12 | Plan file renamed to `PROJECT_PLAN.md` and moved into the repository folder; folder structure, Python virtual environment (`.venv`), `requirements.txt` and `.gitignore` created; project work started |
| 2026-11-12 | Olist and external data loaded; raw profile and key checks run; IBGE state table and holiday calendar built and validated; first versions of `reports/data_quality_log.md` and `reports/metrics_definitions.md` written; IBGE reference year narrowed to 2018 |
| 2026-11-12 | Staging layer built (`pipeline/10_build_staging.py`): 8 cleaned Olist tables plus IBGE and holiday tables written to one SQLite database, `data/olist.db`, with indexes. Data quality issues 4, 6 and 7 resolved and logged. Added `pipeline/run_sql.py` to run a `.sql` file against the database |
| 2026-11-12 | Staging and marts now live in one SQLite file (`data/olist.db`, tables prefixed `stg_` and later `fact_` and `dim_`) instead of separate folders | One file keeps SQL joins simple and the project easy to run |
| 2026-11-12 | Star schema built (dim_date, dim_customer, dim_seller, dim_product, fact_order_items, fact_orders) with revenue flags, haversine distance and holidays-in-window. 20 data quality tests added, including reconciliation of revenue and late rate against the raw CSV files. One command, `python pipeline/run_pipeline.py`, now runs raw to tested marts |
| 2026-11-12 | Two defects found by the tests or checks and fixed: purchase_date carried a time part so it did not join to dim_date (also hid holidays on the purchase day); 42 geolocation rows were outside Brazil and produced distances up to 8,678 km, now dropped (max 3,579 km) |
| 2026-11-12 | Stage 1 done: KPI, monthly trend (LAG), category Pareto (RANK, cumulative share) and state and payment queries written; findings recorded in `reports/stage1_findings.md`. Headline: revenue R$13.18M, growth flat since Jan 2018, repeat rate 3.0% |
| 2026-11-12 | Stage 3 done: cohort retention, censoring-safe 90-day repeat rate, customer concentration and rule-based RFM segments (quintile scoring dropped because 97% of customers have frequency 1). `rfm_segments` table added to the database. Headline: monthly retention at most 0.7%, 90-day repeat 2.28%, 7,311 recent high-value one-time customers as first win-back target; +1 point of repeat rate is worth about R$114,500 (scenario) |
| 2026-11-12 | Stage 4 done. Late delivery lowers review scores by 1.73 stars (late 2.57 vs on-time 4.29; Mann-Whitney, Cliff's delta -0.55) and the damage is concentrated at 7+ days late (78% low reviews). It does NOT significantly reduce 90-day repeat purchase (2.03% vs 2.31%, p = 0.148, CI -0.64 to +0.08 pts). The planned claim that late delivery causes lost repeat revenue is dropped; delivery is framed as a review and reputation problem. Money view: R$1.16M (8.8%) of revenue is tied to late deliveries |
| 2026-11-12 | Decision: Stage 6 model targets orders 7+ days late (the cases that destroy reviews), in addition to any-late | Stage 4 showed the damage is concentrated there |
| 2026-11-12 | Stage 5 done. About 93% of the extra time in late orders is carrier transit, not seller dispatch. Late rate rises with distance (6.5% under 300 km to 13.2% beyond 1,500 km). RJ is the outlier (13.5% late at about 394 km vs 5.0% to 5.9% in SP, MG and PR). Holidays do not explain lateness. 57 of 410 sellers (50+ orders) are significantly worse than expected and hold 25.3% of late orders. Delivery estimates are padded by about two weeks for on-time orders. Seller watch-list saved to `reports/seller_late_performance.csv` |
| 2026-11-12 | Stage 6 done. Time-based split (train before 2018-04-01, test Apr to Aug 2018). Logistic regression (ROC AUC 0.718 late, 0.722 for 7+ days late) beat random forest (0.650, 0.668) and is the chosen model. Top 10% riskiest orders catch 25.0% of late and 32.0% of 7+ day late orders. Estimated delivery days is the strongest driver. Limits recorded: moderate accuracy and base-rate shift between train (9.3% late) and test (6.1%) |
| 2026-11-12 | Stage 7 done. Revenue per 1,000 residents is explained 62% by state income (SP excluded) and correlates at -0.93 with average delivery days and -0.82 with freight share; the effects cannot be separated across 27 states. Scenarios: R$51k (5 weakest states to 80% of expected), R$213k (all states to income-predicted), R$1.51M ceiling (high-income states reach RJ's level). Paraná chosen as the Stage 8 test state. State table saved to `reports/state_opportunity.csv` |
| 2026-11-12 | Stage 8 done. A geographic test in Paraná was sized and rejected: about 60 orders a week split across 37 zip areas can only detect lifts of 38% to 72% depending on length. Experiment A is therefore randomised at visitor level (baseline conversion must come from Olist's web data; illustrative sample sizes given). Experiment B (win-back) uses all 18,069 high-value one-time customers; +1 point repeat lift needs 8,417 customers in total. Design only, no result claimed |
| 2026-11-12 | Decision: experiment designs avoid inventing any baseline or effect size not in the data | Honest sizing; business inputs listed as needed |
| 2026-11-12 | Stage 9 built except the parts that need Power BI Desktop and a screen recording. Added `pipeline/30_export_for_bi.py` (star schema and summaries as CSV), `pipeline/31_build_excel.py` (workbook `excel/olist_revenue_leak_summary.xlsx` with live formulas and charts, 7 sheets), `reports/stakeholder_memo.md`, `reports/insights_report.md` and `dashboard/POWER_BI_BUILD_GUIDE.md` (model, DAX measures, four pages). Memo and report are Markdown for now; PDF export left until the numbers are final |
| 2026-11-12 | Decision: Power BI file and video are left to be made by hand | They need Power BI Desktop and a screen recording, which cannot be produced from the command line |
| 2026-11-13 | README written with findings, figures, data sources, skills table and run instructions. Added four static figures for it (`notebooks/09_readme_figures.py`, palette checked with the colour validator). Aligned the 1 to 6 days late figures in `stage4_findings.md` and `insights_report.md` with the metric definition (3.26 average review, 33.8% low reviews) |
| 2026-11-13 | Power BI Desktop cannot be run from the command line, so an interactive web dashboard with the same four pages was built instead (Overview, Customers, Delivery, Regions) as a single file, `docs/index.html`, to be published free with GitHub Pages. Built from the same summary tables as the Excel workbook; figures match the reports. Palette checked with the colour validator, dark mode follows the system setting, every chart has a table or tooltip equivalent. The Power BI guide stays as the route for a native Power BI version |
| 2026-11-13 | Power BI Desktop installed by the author. Added `pipeline/33_export_powerbi.py` (one workbook with 9 tidy tables plus helper columns, and a colour theme file) and rewrote `dashboard/POWER_BI_BUILD_GUIDE.md` as a click-by-click guide: load, relationships, 13 DAX measures, four pages, reconciliation values to check against, screenshots, GitHub upload. The workbook is not committed (31 MB, regenerable) |
| 2026-11-19 | Power BI dashboard built by script instead of by hand. `pipeline/34_build_powerbi_project.py` writes a Power BI Project (`olist_revenue_leak.pbip`: TMDL model with 9 tables, 6 relationships, 16 measures; report with 4 pages and 28 visuals; report JSON checked against Microsoft's published schemas). Opened in Power BI Desktop, refreshed from `olist_powerbi_data.xlsx`, and saved as `olist_revenue_leak.pbix` (17.7 MB). Desktop caught two real defects, both fixed: a one-to-one relationship needs filtering in both directions, and `Excel.Workbook` needs the headers argument set to true. Cards match the reconciliation values (96,203 orders, 93,096 customers, AOV R$137, repeat 3.0%, late 8.1%, revenue R$13.2M); the 4.29 / 3.26 / 1.73 review scores, 41.1% top-decile share and RJ 13.5% late match the reports. One chart title from the old guide was corrected: the state late-rate chart is now "RJ is late despite being close" (MA, CE and BA are higher, so "RJ is the outlier" was misleading) |
| 2026-11-19 | Memo and insights report exported to PDF with `pipeline/35_export_pdfs.py` (Markdown to HTML, printed by headless Edge or Chrome, so no extra software). Memo is 1 page, report is 3 pages. README links both PDFs. Added `markdown` to `requirements.txt` |
| 2026-11-19 | Walkthrough video dropped from the plan and the README; plan, tracker and guide updated to match |
| 2026-11-19 | Added MIT `LICENSE` and a three-line "result in 30 seconds" summary above the images in the README, as the plan's recruiter-in-30-seconds goal asks |
