# Stage 5 Findings: Is late delivery a distance problem, a seller problem, or a holiday problem?

Source: `notebooks/05_late_delivery_causes.py`, `reports/seller_late_performance.csv`. Delivered, single-seller orders in the window (94,931; late rate 8.22%). Multi-seller orders are left out because one order would have several distances and sellers.

## Findings
1. **Lateness is mostly carrier transit, not seller dispatch.** Late orders spend a median 3.4 days between purchase and handover to the carrier, against 2.1 days for on-time orders (1.3 days more). The carrier leg takes a median 23.9 days against 6.9 days (17.0 days more). Of the extra time in late orders, about 93% is in transit.
2. **Distance matters, as expected.** Late rate rises with seller-to-customer distance: 6.5% under 300 km, 7.9% at 300 to 600 km, 8.6% at 600 to 1,000 km, 10.2% at 1,000 to 1,500 km, 13.2% beyond 1,500 km. In the regression each extra 100 km raises the odds of being late by 2.8%, and an order where seller and customer share a state has 23% lower odds.
3. **Rio de Janeiro is the outlier that distance does not explain.** RJ has a 13.5% late rate at a median distance of about 394 km, against 5.9% in SP, 5.6% in MG and 5.0% in PR at similar or longer distances (MG 490 km, PR 426 km). That points to a last-mile or carrier problem in RJ, not a distance problem. RJ is 12,310 orders; matching the MG rate would remove roughly 970 late orders, and those orders carry about R$138,000 in revenue (average RJ order R$142). This is revenue attached to bad deliveries in that state, not a measured loss (Stage 4).
4. **Far-away northern and north-eastern states are late because of distance.** Highest late rates among states with 500+ orders: MA 19.8%, CE 15.5%, BA 14.2% (medians of 1,400 to 2,300 km from the seller).
5. **Holidays do not explain it.** Late rate with no holiday in the promised delivery window: 8.3%; one holiday: 8.4%; two or more: 7.4%. The regression gives a lower, not higher, late risk with two or more holidays, probably because Olist's estimates already allow for them. The holiday hypothesis is not supported; the variable stays in the model only as a control.
6. **A minority of sellers are worse than their routes explain.** After accounting for distance, same-state delivery and customer state, 57 of 410 sellers with 50 or more orders have a late rate significantly above expectation (z > 2). They handle 15.4% of orders but 25.3% of late orders, and about 770 late orders more than expected. The 10 worst sellers account for about 320 of those. These sellers are listed in `reports/seller_late_performance.csv`.
7. **Delivery estimates are very padded.** On-time orders arrive at a median of 9 days against a median estimate of 23 days, about two weeks early. Late orders have a median estimate of 22 days and arrive at 29. So estimates are not shorter for the orders that end up late; they do not separate fast routes from slow ones well. Better estimates by state and distance would reduce late flags without changing a single parcel.

## What this means
- Fixing seller dispatch alone would not move late delivery much (seller handling is a small part of the delay). The levers are carrier performance (RJ above all, then the far north-east) and the estimate itself.
- A seller watch-list of about 57 sellers is a smaller, cheaper action with a visible effect (about 10% of late orders are excess caused by them).

## Limits
- This is observational and uses a straight-line distance from zip-prefix centres, not the real route.
- Carrier is not in the data, so the RJ explanation (carrier or last-mile) is an inference from where the delay sits (transit time), not a direct measurement.
- Seller flags use a normal approximation; sellers near the z = 2 line should be treated as uncertain.
