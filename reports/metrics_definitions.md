# Metrics Definitions

Every number in the dashboard, report and memo uses these definitions. If a definition changes, this file and the change log in PROJECT_PLAN.md are updated first.

| Metric | Definition |
|---|---|
| Analysis window | Orders purchased from 2017-01-01 to 2018-08-31 (see data quality log, issue 2) |
| Order | One row in `orders` |
| Delivered order | Order with status `delivered` and a delivered-to-customer date |
| Revenue | Sum of item `price` for delivered orders. Freight is not included |
| Freight revenue | Sum of `freight_value` for delivered orders, reported separately |
| Average order value (AOV) | Revenue divided by number of delivered orders |
| Customer | A person, identified by `customer_unique_id` |
| Active customer (month) | Customer with at least one delivered order in that month |
| Repeat customer | Customer with two or more delivered orders in the analysis window |
| Repeat rate | Repeat customers divided by all customers with at least one delivered order |
| Delivery days | Date delivered to customer minus purchase date, in whole days |
| Late delivery | Delivered date is later than the estimated delivery date |
| Late rate | Late delivered orders divided by delivered orders with a delivery date |
| Review score | One review per order (latest), 1 to 5 |
| Low review | Review score of 1 or 2 |
| Seller-customer distance | Straight-line (haversine) distance in km between the seller and customer zip-prefix centres |
| Revenue per 1,000 residents | State revenue divided by IBGE state population (1 July 2018), times 1,000 |
| Revenue lost (repeat) | Defined when the retention analysis is complete; the method will be written here before any figure is quoted |

## Open questions
- Whether canceled orders after payment should count as lost revenue (decided after issue 3 and 4 in the data quality log are checked).
