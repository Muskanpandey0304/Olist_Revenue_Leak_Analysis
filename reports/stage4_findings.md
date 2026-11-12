# Stage 4 Findings: Is late delivery hurting us, or is that just a guess?

Source: `notebooks/04_late_delivery_tests.py`, `sql/50_late_revenue_exposure.sql`. Delivered orders in the analysis window (96,203); 7,822 (8.13%) were late.

## Result in one line
Late delivery strongly damages review scores, but there is **no evidence that it reduces repeat purchase**. The retention problem from Stage 3 is not caused by delivery.

## 1. Review scores (clear, large effect)
| | Late | On time |
|---|---|---|
| Reviewed orders | 7,658 | 87,902 |
| Mean review score | 2.57 | 4.29 |
| Low reviews (1 to 2 stars) | 54.1% | 9.2% |

- Mean difference: **-1.73 stars**, 95% bootstrap confidence interval [-1.77, -1.69].
- Test: Mann-Whitney U, chosen because review scores are strongly skewed (59% are 5 stars). p-value below 1e-300 (reported as 0 by the software); effect size Cliff's delta = -0.55 (a large effect).
- **How late matters.** Orders up to 6 days late score 3.15 on average (36.8% low reviews). From 7 days late the score collapses to about 1.7 (78% low reviews). Orders on or before the estimated date score 4.1 to 4.3. The estimated date is a promise; breaking it by a week is the cliff.

## 2. Repeat purchase (no detectable effect)
Customers whose first order was in time to be observed for 90 days (75,306 customers):

| First order | Customers | Repeated within 90 days |
|---|---|---|
| On time | 68,701 | 2.31% |
| Late | 6,605 | 2.03% |

- Difference -0.28 points, 95% confidence interval [-0.64, +0.08], two-proportion z-test p = 0.148. Not statistically significant.
- Customers whose first order got a low review repeated at 2.29%, against 2.28% for the others. A bad experience did not change the repeat rate either.
- The confidence interval is informative: with 6,605 late customers the data rule out an effect larger than about 0.64 points. If lateness has any effect on repeat, it is small.
- Caution: this is observational. Late and on-time orders are not randomly assigned (late orders may differ in region or product), so even this small gap would not be proof of cause.

## 3. Money
- **Revenue tied to late deliveries:** R$1.16M, 8.8% of window revenue (4,234 orders 1 to 6 days late, R$0.60M; 3,588 orders 7+ days late, R$0.56M).
- **Repeat revenue lost because of lateness:** best estimate is close to zero. Using the observed gap of 0.28 points as an upper bound (it is not statistically significant) gives about R$2,600 over 20 months. Not worth a headline.
- So the cost of late delivery is mainly satisfaction and reputation (54% low reviews on late orders; 4 in 5 on orders 7+ days late), not measured repeat revenue. That reputational cost cannot be priced from this dataset.

## What this changes in the plan
- The story "late delivery causes the revenue leak" is not supported and will not be claimed. The leak is the near-absence of repeat buying (Stage 3), which happens whatever the delivery experience.
- Delivery stays in the project because it drives reviews (visible to new buyers) and it is the one thing operations can act on directly. Stage 5 finds what drives late deliveries; Stage 6 predicts the 7+ day cases, which are the ones that wreck reviews.
