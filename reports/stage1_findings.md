# Stage 1 Findings: Are we growing, and where does revenue come from?

Source queries: `sql/30_kpi_overview.sql`, `31_monthly_trend.sql`, `32_category_concentration.sql`, `33_state_and_payment.sql`.
Window: orders purchased 2017-01 to 2018-08, delivered only. Revenue is item price, freight excluded (see `metrics_definitions.md`).

## Headline numbers
| Metric | Value |
|---|---|
| Revenue | R$13,179,778 |
| Delivered orders | 96,203 |
| Customers | 93,096 |
| Average order value | R$137.00 |
| Freight collected (not revenue) | R$2,191,963 |
| Repeat rate | 3.0% (2,789 customers bought more than once) |

## Findings
1. **Growth has stalled since January 2018.** Monthly revenue rose from R$112k (Jan 2017) to R$988k (Nov 2017, the peak month). From January to August 2018 it stayed between R$826k and R$978k, and August 2018 (R$839k) was 9.3% below January 2018 (R$925k). Orders show the same shape: 7,069 in Jan 2018, 6,351 in Aug 2018. Year over year the business is still up (Aug 2018 is 51% above Aug 2017), but that gap is closing because the 2018 level is flat. The November 2017 spike is consistent with Black Friday; this has not been tested.
2. **Almost nobody comes back.** Only 3.0% of customers placed a second delivered order, and repeaters account for just 6.1% of orders. Growth has depended on finding new customers every month. This is the main candidate for the "revenue leak" and is examined properly in Stage 3 with cohorts. Caution: customers acquired late in the window have had less time to return, so the true rate by cohort has to be read together with age.
3. **Order value is flat.** AOV stayed between R$124 and R$149 in every month. Revenue growth came from order volume, not from larger baskets.
4. **Revenue is spread across many categories, but the top ones matter.** 18 of 74 categories produce 80% of revenue. The top five are health_beauty (9.3%), watches_gifts (8.8%), bed_bath_table (7.8%), sports_leisure (7.2%) and computers_accessories (6.7%), together 39.9%.
5. **Sales are concentrated in the south-east.** São Paulo state alone is 38.4% of revenue; SP, RJ and MG together are 63.4%. Stage 7 tests whether the other states are weak because of low demand or because of low coverage.
6. **Credit cards dominate.** 75.5% of orders are paid mainly by credit card, 19.9% by boleto.

## Questions passed to later stages
- Why is the repeat rate so low, and is it tied to delivery experience? (Stages 3 and 4)
- Is the flat 2018 level a market limit or a retention problem? (Stages 3 and 7)
- Do the states outside SP, RJ and MG have low sales for their population and income? (Stage 7)
