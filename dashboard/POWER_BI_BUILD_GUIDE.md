# Power BI Build Guide

The dashboard file itself is built by hand in Power BI Desktop; this guide gives the data, model, measures and page layout so it can be built in about two hours. Run `python pipeline/30_export_for_bi.py` first.

## 1. Import
Get Data > Text/CSV, from `dashboard/data/`:
`fact_orders.csv`, `fact_order_items.csv`, `dim_customer.csv`, `dim_seller.csv`, `dim_product.csv`, `dim_date.csv`, `rfm_segments.csv`
and from `dashboard/summary/`: `state_opportunity.csv`, `rfm_segment_summary.csv`, `seller_late_performance.csv`.

Set `dim_date[date]` and `fact_orders[purchase_date]` to Date type. Mark `dim_date` as the date table.

## 2. Relationships (all many-to-one, single direction)
| From (many) | To (one) |
|---|---|
| fact_orders[purchase_date] | dim_date[date] |
| fact_orders[customer_unique_id] | dim_customer[customer_unique_id] |
| fact_order_items[order_id] | fact_orders[order_id] (one order, many items) |
| fact_order_items[seller_id] | dim_seller[seller_id] |
| fact_order_items[product_id] | dim_product[product_id] |
| rfm_segments[customer_unique_id] | dim_customer[customer_unique_id] |
| state_opportunity[state_code] | dim_customer[state] (use a state lookup table if Power BI asks for a one-side) |

## 3. Measures
```
Revenue = CALCULATE(SUM(fact_order_items[price]), fact_order_items[is_revenue_item] = 1)
Orders = CALCULATE(DISTINCTCOUNT(fact_orders[order_id]), fact_orders[is_revenue_order] = 1)
AOV = DIVIDE([Revenue], [Orders])
Customers = CALCULATE(DISTINCTCOUNT(fact_orders[customer_unique_id]), fact_orders[is_revenue_order] = 1)
Repeat Customers =
    COUNTROWS(FILTER(VALUES(fact_orders[customer_unique_id]),
        CALCULATE(DISTINCTCOUNT(fact_orders[order_id]), fact_orders[is_revenue_order] = 1) >= 2))
Repeat Rate = DIVIDE([Repeat Customers], [Customers])
Revenue MoM % = VAR prev = CALCULATE([Revenue], DATEADD(dim_date[date], -1, MONTH))
                RETURN DIVIDE([Revenue] - prev, prev)
Late Rate = CALCULATE(AVERAGE(fact_orders[is_late]), fact_orders[is_revenue_order] = 1)
Avg Review = CALCULATE(AVERAGE(fact_orders[review_score]), fact_orders[is_revenue_order] = 1)
Low Review % = DIVIDE(CALCULATE(COUNTROWS(fact_orders), fact_orders[is_revenue_order] = 1, fact_orders[review_score] <= 2),
                      CALCULATE(COUNTROWS(fact_orders), fact_orders[is_revenue_order] = 1, NOT ISBLANK(fact_orders[review_score])))
Revenue per 1000 Residents = DIVIDE([Revenue], SUM(state_opportunity[population])) * 1000
```
These match `reports/metrics_definitions.md`. Check the headline: Revenue must equal R$13,179,778 and Orders 96,203 when no filter is applied; a mismatch means a relationship or filter is wrong.

## 4. Pages
1. **Executive overview.** Cards: Revenue, Orders, AOV, Customers, Repeat Rate, Late Rate. Line chart: Revenue by month with Revenue MoM %. Bar chart: top 10 categories. Slicer: state, year.
2. **Customers and retention.** Bar chart of segments (rfm_segments, customers and revenue). Decile chart of revenue (`customer_deciles.csv`). Card: Repeat Rate with a note that it is 3%. Table: the win-back segment (One-time high value, recent).
3. **Delivery.** Column chart: Avg Review by delivery bucket (on time, 1 to 6 days late, 7+ days late; `delivery_impact.csv`). Map or bar chart: Late Rate by customer state. Scatter: late rate against distance band. Table: seller watch-list from `seller_late_performance.csv` filtered to orders >= 50 and z > 2.
4. **Regional opportunity.** Map of Revenue per 1000 Residents by state, scatter of income per capita against revenue per 1,000 residents (labels = state), table of penetration vs expected.

## 5. Publish
Publish to the Power BI service, then File > Embed report > Publish to web (public link). Put that link and three screenshots at the top of the repository README, together with a 2-minute screen recording that walks through the four pages and the three recommendations.
