# Power BI Build Guide

## Status: built (2026-11-19)
`dashboard/powerbi/olist_revenue_leak.pbix` is finished (4 pages: Overview, Customers, Delivery, Regions). Screenshots: `page1_overview.png` to `page4_regions.png` in the same folder. Just open the `.pbix`.

**To rebuild or change it (no clicking needed):**
1. `python pipeline/33_export_powerbi.py` (writes the data workbook and `schema.json`).
2. `python pipeline/34_build_powerbi_project.py` (writes `olist_revenue_leak.pbip` with the model, measures and pages). Close Power BI Desktop first.
3. Open `olist_revenue_leak.pbip` in Power BI Desktop. Click **Refresh now** on both yellow banners, then **Apply changes**. File → Save as → `.pbix`.

The data path is stored in one Power Query parameter, `DataPath` (Transform data → Edit parameters). The generator sets it to this machine's path to `olist_powerbi_data.xlsx`; change it if the repo lives somewhere else.

Known limits: number grouping follows the Windows region (Indian grouping shows as R$1,86,272); the RJ bar is not highlighted in orange; the `.pbix` is not published to the Power BI service.

The click-by-click guide below is kept as a fallback and as documentation of the model.

---

# Power BI Build Guide (click by click, manual route)

Takes about 1 to 1.5 hours the first time. Everything you need is in `dashboard/powerbi/`:
- `olist_powerbi_data.xlsx`: all 9 tables, already cleaned (create it with `python pipeline/33_export_powerbi.py`; it is not committed to git because it is 31 MB)
- `olist_theme.json`: the colour theme (blue `#2A78D6`, orange `#EB6834`)

## Fast path for Steps 2 and 3 (TMDL view)
Instead of drawing relationships and typing measures by hand, paste two scripts: **TMDL view** (the last icon on the left, below Report, Table, Model and DAX; if missing, File → Options → Preview features → turn on TMDL view, restart).
1. First delete any lines Power BI auto-created in Model view (right-click a line → Delete).
2. TMDL view → new script → paste the whole of `model_relationships.tmdl` → **Apply**.
3. New script → paste `model_measures.tmdl` → **Apply**.
4. Back in Model view: select `dim_date` → Table tools → **Mark as date table** → column `date`.
5. Do the number check in Step 3 (cards must match). Currency formatting (R$) can be set per measure in Measure tools → Format.
If Apply shows an error, copy the message and send it to me.

## Step 1. Load the data
1. Open Power BI Desktop. Close the start screen.
2. **Home → Get data → Excel workbook** → choose `olist_powerbi_data.xlsx`.
3. In the Navigator, tick **all 9 sheets** (dim_customer, dim_date, dim_product, dim_seller, fact_order_items, fact_orders, rfm_segments, seller_watchlist, states) → **Load**. Wait about a minute.
4. **File → Save as** → `dashboard/powerbi/olist_revenue_leak.pbix`.
5. **View → Themes → Browse for themes** → choose `olist_theme.json`.

Check the types in the **Data view** (table icon on the left): `dim_date[date]` and `fact_orders[purchase_date]` must show a date icon. If not, select the column → **Column tools → Data type → Date**.

## Step 2. Build the model (Model view, the third icon on the left)
Power BI may create some relationships by itself. **Delete any that are not in this table**, then drag to create the missing ones.

| Drag from (many side) | To (one side) | Cardinality | Filter direction |
|---|---|---|---|
| fact_orders[purchase_date] | dim_date[date] | Many to one | Single |
| fact_orders[customer_unique_id] | dim_customer[customer_unique_id] | Many to one | Single |
| fact_order_items[order_id] | fact_orders[order_id] | Many to one | Single |
| fact_order_items[seller_id] | dim_seller[seller_id] | Many to one | Single |
| fact_order_items[product_id] | dim_product[product_id] | Many to one | Single |
| rfm_segments[customer_unique_id] | dim_customer[customer_unique_id] | One to one | Single (dim_customer filters rfm_segments) |

`states` and `seller_watchlist` have no relationships, which is correct. A star shape: dim tables at the top, fact tables in the middle.

Then: select `dim_date` → **Table tools → Mark as date table** → date column = `date` → OK.

## Step 3. Create the measures
Click `fact_orders` in the Data pane → **Home → New measure**. Paste one at a time (delete the default text first).

```dax
Revenue = CALCULATE(SUM(fact_order_items[price]), fact_order_items[is_revenue_item] = 1)

Orders = CALCULATE(DISTINCTCOUNT(fact_orders[order_id]), fact_orders[is_revenue_order] = 1)

Customers = CALCULATE(DISTINCTCOUNT(fact_orders[customer_unique_id]), fact_orders[is_revenue_order] = 1)

AOV = DIVIDE([Revenue], [Orders])

Repeat Customers =
COUNTROWS(
    FILTER(
        VALUES(fact_orders[customer_unique_id]),
        CALCULATE(DISTINCTCOUNT(fact_orders[order_id]), fact_orders[is_revenue_order] = 1) >= 2
    )
)

Repeat Rate = DIVIDE([Repeat Customers], [Customers])

Late Rate = CALCULATE(AVERAGE(fact_orders[is_late]), fact_orders[is_revenue_order] = 1)

Avg Review = CALCULATE(AVERAGE(fact_orders[review_score]), fact_orders[is_revenue_order] = 1)

Low Review % = CALCULATE(AVERAGE(fact_orders[low_review]), fact_orders[is_revenue_order] = 1)

Revenue MoM % =
VAR prev = CALCULATE([Revenue], DATEADD(dim_date[date], -1, MONTH))
RETURN DIVIDE([Revenue] - prev, prev)

Segment Customers = COUNTROWS(rfm_segments)

Segment Revenue = SUM(rfm_segments[monetary])

Segment Revenue % = DIVIDE([Segment Revenue], CALCULATE([Segment Revenue], ALL(rfm_segments)))
```

**Set the formats** (click a measure → **Measure tools** ribbon):
- Revenue, AOV, Segment Revenue: Format **Currency**, then choose **R$ Portuguese (Brazil)**, 0 decimals (AOV: 0 decimals too).
- Repeat Rate, Late Rate, Low Review %, Segment Revenue %, Revenue MoM %: Format **Percentage**, 1 decimal.
- Avg Review: Decimal number, 2 decimals.
- Orders, Customers, Repeat Customers, Segment Customers: Whole number, thousands separator on.

**Check your numbers now.** Create a Card visual for each (no filters applied) and compare:

| Measure | Must show |
|---|---|
| Revenue | R$13,179,778 |
| Orders | 96,203 |
| Customers | 93,096 |
| AOV | R$137 |
| Repeat Rate | 3.0% |
| Late Rate | 8.1% |

If any differ, a relationship is wrong (most often a missing one, or direction set to Both). Fix it before building pages. Delete these test cards afterwards or reuse them on page 1.

## Step 4. Page 1: Overview
Rename the page tab (bottom) to **Overview**.
1. **Cards** (6): Revenue, Orders, Customers, AOV, Repeat Rate, Late Rate across the top. Turn on **Category label** so each shows its name.
2. **Line chart**: X-axis `dim_date[year_month]`, Y-axis `[Revenue]`. Title: *Growth has been flat since January 2018*. Under Format → Visual → Markers, turn markers on.
3. **Bar chart** (clustered): Y-axis `dim_product[category]`, X-axis `[Revenue]`. In the Filters pane for this visual, set `category` → Filter type **Top N** → Top **10** by value `[Revenue]` → Apply. Title: *18 of 74 categories bring 80% of revenue*. Sort descending by Revenue (top-right "…" → Sort axis).
4. **Slicers** (2): `dim_customer[state]` (style: Dropdown) and `dim_date[year]` (style: Tile/Buttons). Put them on the left or top.

## Step 5. Page 2: Customers
Right-click the page tab → **Duplicate page** is not needed; use the **+** at the bottom. Name it **Customers**.
1. **Text box** (Insert → Text box): *Only 3.0% of customers ever placed a second order.* Make it bold and colour it orange.
2. **Cards**: Repeat Rate, Repeat Customers.
3. **Column chart**: X-axis `rfm_segments[decile]`, Y-axis `[Segment Revenue %]`. Turn on **Data labels**. Title: *The top 10% of customers bring 41% of revenue*. (X-axis type: Categorical, so deciles show 1 to 10.)
4. **Bar chart**: Y-axis `rfm_segments[segment]`, X-axis `[Segment Revenue]`. Turn on data labels. Title: *Most revenue sits with one-time buyers*. To highlight the win-back segment: Format → Visual → Bars → Colors → *Show all* → pick orange for `One-time high value - recent`.
5. **Table**: columns `rfm_segments[segment]`, `[Segment Customers]`, `[Segment Revenue]`, `[Segment Revenue %]`.

## Step 6. Page 3: Delivery
Name it **Delivery**.
1. **Column chart**: X-axis `fact_orders[delivery_bucket]`, Y-axis `[Avg Review]`. Filters pane → `delivery_bucket` → **is not blank**. Data labels on. Title: *Reviews collapse from 7 days late*. Expect 4.29, 3.26 and 1.73.
2. **Column chart**: X-axis `fact_orders[distance_band]`, Y-axis `[Late Rate]`. Filters pane → `distance_band` → **is not blank**. Data labels on. Title: *Further away means later*. (This shows all orders; the report used single-seller orders, so values may differ by a fraction of a point.)
3. **Bar chart**: Y-axis `dim_customer[state]`, X-axis `[Late Rate]`. Filters pane: add `[Orders]` → **is greater than or equal to** 500; then `state` → Top N 10 by `[Late Rate]`. Colour RJ orange (as in step 5.4). Title: *Rio de Janeiro is the outlier*.
4. **Table**: all columns of `seller_watchlist`. Title: *Sellers worse than their routes explain*. Sort by `excess_late` descending.
5. **Text box**: *Late delivery hurts reviews, not repeat purchase (2.03% vs 2.31%, p = 0.15).*

## Step 7. Page 4: Regions
Name it **Regions**.
1. **Scatter chart**: X-axis `states[income_pc]`, Y-axis `states[rev_per_1000]`, Values (details) `states[state_code]`. Click the dropdown on X and Y and pick **Don't summarize**. Turn on Data labels (shows the state code). Title: *States with higher income buy far more per resident*.
2. **Table**: `states[state_code]`, `income_pc`, `revenue`, `rev_per_1000`, `penetration_vs_expected`, `late_pct`, `avg_delivery_days`. Sort by `rev_per_1000` descending.
3. **Text box**: *Paraná is the proposed first test: income above the national level, revenue per resident 42% below Rio de Janeiro.*

## Step 8. Finish
- **Titles and alt text** on every visual (Format → General → Title; Alt text under General → Alt text).
- **View → Page view → Fit to page** on every page; make sure nothing overlaps.
- **Save** the file (Ctrl+S).
- **Screenshots**: show a page, press **Win + Shift + S**, drag over the report, paste into Paint and save as `dashboard/powerbi/page1_overview.png` and so on (four images).
- **Record the video** (the 2-minute walkthrough): Windows **Win + G** → Capture, or the free OBS Studio.

## Step 9. Put it on GitHub
```
git add dashboard/powerbi/olist_revenue_leak.pbix dashboard/powerbi/*.png
git commit -m "Add Power BI dashboard and screenshots"
git push
```
Then add the four screenshots to the README. Publishing a public Power BI link (**Home → Publish**, then **File → Embed report → Publish to web**) needs a work or school Microsoft account; with a personal account you may not see the option. In that case rely on the screenshots, the video and the web dashboard link.
