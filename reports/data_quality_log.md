# Data Quality Log

Issues found in the raw data and the decision for each. Findings come from `pipeline/00_profile_raw.py` and `pipeline/01_key_checks.py`. Status "open" means the decision is not final until the staging step confirms it.

## Raw file sizes
| File | Rows |
|---|---|
| orders | 99,441 |
| order_items | 112,650 |
| order_payments | 103,886 |
| order_reviews | 99,224 |
| customers | 99,441 |
| products | 32,951 |
| sellers | 3,095 |
| geolocation | 1,000,163 |
| category translation | 71 |

## Issues
| # | Issue | Evidence | Decision | Status |
|---|---|---|---|---|
| 1 | `customer_id` is created per order, so it cannot identify a returning customer | 99,441 customer_ids but 96,096 `customer_unique_id` | Use `customer_unique_id` for every repeat, retention and RFM calculation | decided |
| 2 | Incomplete months at both ends of the data | 2016-09: 4 orders, 2016-12: 1, 2018-09: 16, 2018-10: 4; no orders in 2016-11 | Main analysis window is 2017-01 to 2018-08. Earlier and later orders stay in staging but are excluded from trends | decided |
| 3 | Orders with no outcome | Status counts: delivered 96,478; shipped 1,107; canceled 625; unavailable 609; invoiced 314; processing 301; created 5; approved 2 | Revenue uses delivered orders only (definition in metrics_definitions.md). Others are kept and analysed separately as lost or unfinished orders | decided |
| 4 | Orders with no items | 775 orders have no row in order_items (`sql/00_open_issue_checks.sql`) | Confirmed: 603 are `unavailable`, 164 `canceled`, 5 `created`, 2 `invoiced`, 1 `shipped`. They never had items, so they carry no revenue. Kept in staging, excluded from revenue | decided |
| 5 | Orders with no review | 768 orders | Keep; review score stays null. Review-based tests use only reviewed orders | decided |
| 6 | Duplicate reviews | 814 duplicate `review_id`; 547 orders have more than one review | Kept one review per order, the latest by `review_answer_timestamp`: 99,224 rows became 98,673 (one per order). Applied in staging | decided |
| 7 | Payments do not equal items plus freight for some orders | Whole file: items+freight R$15,843,553 vs paid R$16,008,872 | Revenue is built from item prices, not payment value. Explained: payments on orders with no items account for about R$162,600 of the gap (those orders have payments but never had items). Among orders that do have items, delivered orders match to R$2,700 on R$15.4M; 256 delivered orders differ, 237 of them paid more (average 6.5 installments, consistent with installment interest) and 19 paid less | decided |
| 8 | Odd payment records | 9 payments with value 0; 3 with type `not_defined`; 1 order with no payment | Excluded from payment analysis; orders themselves kept | decided |
| 9 | Delivered orders missing delivery date | 8 orders with status delivered and no delivered date | Excluded from delivery-time and late-delivery analysis | decided |
| 10 | Missing timestamps | approved_at: 160 null; carrier date: 1,783 null; customer delivery date: 2,965 null | Expected for canceled or unfinished orders; not filled in | decided |
| 11 | Products with no category | 610 products with no category and name/description/photo fields; 2 with no weight or size | Category set to `unknown`; the 2 without size are excluded from the model | decided |
| 12 | Geolocation has many duplicates | 261,831 fully duplicated rows out of 1,000,163; many coordinates per zip prefix | Reduce to one row per zip prefix using the median latitude and longitude | decided |
| 15 | Bad coordinates in geolocation | 42 rows outside Brazil's bounding box; before removal the largest seller-customer distance was 8,678 km | Rows outside lat -34 to 6 and lng -74 to -34 are dropped before taking the median per zip prefix. Largest distance is now 3,579 km | decided |
| 13 | Some customer zip prefixes have no location | 278 customer rows | Distance left empty for these orders; reported in the distance analysis | decided |
| 14 | Late delivery baseline | 8.1% of orders with a delivery date arrive after the estimated date; no negative delivery times | Definition fixed in metrics_definitions.md | decided |

## External data checks
- IBGE state table: 27 states; population sums to IBGE's published Brazil total (208,494,900) and to all five regional totals.
- Every state code in Olist customers and sellers exists in the IBGE table, and no IBGE state is missing from Olist.
- Holiday calendar covers 2016 to 2018: 9 national holidays per year (27 rows). State and city holidays are not included.
