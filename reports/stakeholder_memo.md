# Memo

**To:** Head of Operations
**From:** Data Analytics
**Date:** 12 November 2026
**Subject:** Late deliveries: where they come from and what to fix first

## Summary
8.1% of delivered orders (7,822 of 96,203, January 2017 to August 2018) arrived after the promised date. These orders got a 2.6 average review score against 4.3 for on-time orders, and 54% of them were rated 1 or 2 stars (9% for on-time orders). The damage is concentrated in orders that are 7 or more days late: 78% low reviews. Three actions below, ranked by the revenue attached to the problem.

**What the data does not show:** late delivery did not measurably reduce repeat purchase (2.03% repeat within 90 days after a late first order, 2.31% after an on-time one; the difference is not statistically significant). The cost of late delivery is reputation and review quality, so the figures below are revenue attached to bad deliveries, not revenue lost.

## Recommendations
| # | Action | Revenue attached to the problem | Cost | How we will know it worked |
|---|---|---|---|---|
| 1 | **Investigate carrier performance in Rio de Janeiro.** RJ has a 13.5% late rate at a median distance of about 394 km, against 5.0% to 5.9% in SP, MG and PR at similar or longer distances. Of the extra time in late orders, 93% is carrier transit. | about R$138,000 (about 970 excess late orders in RJ at R$142 each) | Carrier review and possibly a second carrier; not estimated, needs carrier contracts | RJ late rate falls toward 6% within 3 months; share of 1 and 2 star reviews in RJ falls |
| 2 | **Put 57 sellers on a watch-list.** After allowing for distance and state, these sellers have significantly more late orders than expected. They handle 15% of orders and 25% of all late orders. | about R$114,000 (about 770 excess late orders at R$148) | Account management time; the list is in the attached workbook | Their late rate returns to the expected level; no increase in cancellations |
| 3 | **Recalibrate the delivery estimate and flag risky orders at purchase.** On-time orders arrive a median of 14 days before the estimate, yet the orders that end up late are not given longer estimates. A simple model catches 25% of late orders in the riskiest 10% of orders (32% of orders that are 7+ days late). | Reduces the 54% low-review rate on late orders by warning customers earlier; not priced | Low: estimates and a daily risk list from existing data | Late rate against the new estimate; review score of flagged orders after proactive contact |

## Notes on the evidence
- The model is a ranking tool (ROC AUC 0.72). It will flag many orders that arrive on time and needs recalibration on recent data.
- The carrier is not in the dataset, so the RJ explanation (carrier or last mile) is an inference from where the delay sits, not a measurement.
- Holidays do not explain lateness (late rate 8.3% with no holiday in the window, 7.4% with two or more).

## Outside the scope of operations
The larger revenue question is that only 3.0% of customers ever buy a second time. That, and where to focus regional growth, is covered in the full report for the commercial team.
