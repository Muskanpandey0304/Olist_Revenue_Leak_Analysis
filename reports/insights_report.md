# Olist Revenue Leak Analysis: Findings and Recommendations

Data: Olist public marketplace dataset (about 100,000 orders, 2016 to 2018) combined with IBGE state population and income and the Brazilian holiday calendar. Analysis window: orders purchased from January 2017 to August 2018, delivered orders only. Revenue is item price, freight excluded. Every figure can be reproduced with `python pipeline/run_pipeline.py` and the scripts named in each section.

## Executive summary
- Revenue in the window was **R$13.18M** from 96,203 orders and 93,096 customers. Growth has been flat since January 2018 (monthly revenue between R$826k and R$978k after a peak of R$988k in November 2017).
- **The main leak is that customers do not come back.** Only 3.0% of customers placed a second order; within 90 days of a first order the rate is 2.3%. Growth has depended on finding new customers every month.
- **Late delivery is a review problem, not a retention problem.** Late orders (8.1%) score 2.6 against 4.3, but customers whose first order was late came back at about the same rate (2.0% against 2.3%, not significant).
- **Where sales are low, delivery is slow and expensive.** Revenue per resident follows state income and tracks delivery days (rank correlation -0.93) and freight cost (-0.82). The largest realistic opportunity is in high-income states outside the south-east, with Paraná, Rio Grande do Sul, Santa Catarina, Mato Grosso and Mato Grosso do Sul far below the level of Rio de Janeiro.
- Lateness comes mainly from carrier transit (93% of the extra time), is worst in RJ and far north-eastern states, and about a quarter of late orders come from 57 sellers who are worse than their routes explain.

## 1. Are we growing, and where does revenue come from? (Stage 1)
Monthly revenue rose from R$112k (January 2017) to R$988k (November 2017). From January to August 2018 it stayed flat and August 2018 was 9.3% below January. Year over year it is still up (August 2018 is 51% above August 2017) but the gap is closing. Average order value is stable (R$124 to R$149 every month, R$137 overall), so growth came from order volume. Eighteen of 74 categories bring 80% of revenue; the top five are health_beauty, watches_gifts, bed_bath_table, sports_leisure and computers_accessories. São Paulo state is 38.4% of revenue; SP, RJ and MG together are 63.4%.

## 2. Who are our customers, and why do so few come back? (Stage 3)
- In every monthly cohort, no more than about 0.7% of customers order again in any single later month.
- Counting customers who had at least 90 days to return: 2.28% ordered again within 90 days, 3.45% ever.
- Repeat customers spend R$260 on average against R$138 for one-time customers, but they are 3.0% of customers and 5.5% of revenue.
- The top 10% of customers bring 41.1% of revenue; the top 20% bring 56.6%.
- **First win-back target:** 7,311 recent high-value one-time customers (spent R$176 or more, last order within 180 days, R$2.9M past spend). A further 10,758 lapsed high-value customers are a second wave.
- Scenario: each extra percentage point of customers who place one more order is worth about R$114,500 (0.9% of window revenue); raising the repeat rate from 3% to 10% would be worth about R$0.8M if each placed one average second order.

## 3. Is late delivery hurting us? (Stage 4)
Late orders: mean review 2.57, 54.1% low reviews; on-time orders: 4.29, 9.2% (difference -1.73 stars, 95% confidence interval -1.77 to -1.69; Mann-Whitney test, effect size -0.55). Up to 6 days late: 3.15 and 36.8% low reviews; 7 or more days late: about 1.7 and 78% low reviews. Repeat purchase within 90 days: 2.03% after a late first order and 2.31% after an on-time one (difference -0.28 points, confidence interval -0.64 to +0.08, p = 0.148). The effect on repeat purchase, if any, is small. R$1.16M (8.8%) of window revenue sits on late orders.

## 4. Why are deliveries late? (Stage 5)
- Carrier transit accounts for about 93% of the extra time of late orders (17.0 of 18.3 extra median days); seller dispatch accounts for 1.3 days.
- Late rate rises with distance: 6.5% under 300 km to 13.2% beyond 1,500 km.
- RJ is the outlier: 13.5% late at a median of about 394 km against 5.0% to 5.9% in SP, MG and PR.
- Holidays do not explain lateness.
- 57 of 410 sellers with 50 or more orders are significantly worse than their routes explain; they handle 15.4% of orders and 25.3% of late orders.
- On-time orders arrive a median of 14 days before the estimate, so estimates are padded.

## 5. Can we predict late orders at purchase? (Stage 6)
Logistic regression trained on orders before April 2018 and tested on April to August 2018. ROC AUC 0.72 for late orders and 0.72 for orders 7 or more days late. The riskiest 10% of orders contain 25% of late orders and 32% of 7+ day late orders (2.5 and 3.2 times random). The strongest driver is the estimated delivery time, then distance, customer state (RJ and AL raise risk) and the seller's past record. It is a prioritisation tool, not an exact predictor; the late rate fell from 9.3% in training to 6.1% in testing, so scores need recalibration.

## 6. Where are we under-selling? (Stage 7)
State income explains 62% of the variation in revenue per 1,000 residents (SP excluded). Five states sell below 80% of what their income predicts (AM, RR, RO, AC, AP), but they are small, worth R$51k in total at 80%. The larger prize is high-income states: if DF, SC, RS, PR, MS and MT reached the revenue per resident of RJ, revenue would be R$1.51M (11.5%) higher over the window. This is a ceiling, since RJ is next to the seller hub. Paraná (income R$1,607, 11.5 days average delivery, 5.0% late rate, revenue per resident 42% below RJ) is the proposed first test.

## 7. Recommendations, ranked by money at stake
| # | Recommendation | Owner | Money at stake | Evidence |
|---|---|---|---|---|
| 1 | Test a freight or delivery-promise offer in Paraná, then in RS and SC | Commercial | up to R$1.5M ceiling for six states; realistic share much smaller | Stage 7 |
| 2 | Win back 18,069 high-value one-time customers with a randomised message | Marketing | about R$114,500 per extra point of repeat rate | Stage 3 |
| 3 | Investigate the RJ carrier; watch-list 57 sellers; recalibrate estimates; flag top 10% risk orders | Operations | about R$138k (RJ) and R$114k (sellers) of revenue attached to excess late orders | Stages 4 to 6 |

Test designs and sample sizes are in `reports/experiment_design.md`.

## 8. Limits
- Observational data; no causal claim is made. Late and on-time orders, and states, differ in ways the data cannot fully control.
- The carrier, visit data, margins and commissions are not in the dataset, so costs and break-even points are not estimated.
- Seller-customer distance is a straight line between zip-prefix centres.
- 27 states is a small sample for the regional regression, and income, delivery time and freight move together.
- Customers are identified by `customer_unique_id`; a person with two accounts counts twice.
- The data ends in August 2018; customers acquired late had less time to return.

## 9. Method and reproducibility
Raw files go through a staging layer and a star schema (two fact tables and four dimensions) built by scripts, and 20 automated tests must pass: revenue and the late rate reconcile with the raw files, there are no duplicate or lost rows, every record links to its dimension, every state matches the IBGE table and the population totals match the published total of IBGE. Data issues and decisions are in `reports/data_quality_log.md`; metric definitions are in `reports/metrics_definitions.md`.
