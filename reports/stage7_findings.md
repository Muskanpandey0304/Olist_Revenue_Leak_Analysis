# Stage 7 Findings: Where are we under-selling?

Source: `notebooks/07_regional_opportunity.py`, `reports/state_opportunity.csv`. Olist revenue (window, delivered orders) per state divided by IBGE population (1 July 2018), compared with IBGE household income per capita (2018). 27 states.

## Findings
1. **Sales per resident follow income closely.** Across 26 states (SP excluded, see below), income explains 62% of the variation in revenue per 1,000 residents (log-log regression, elasticity 1.6, p < 0.001). Richer states buy far more than proportionally more.
2. **The home market sets the ceiling.** São Paulo state sells R$111 per 1,000 residents over the window, Rio de Janeiro R$102, the Federal District R$99. Most other states are at R$12 to R$74. SP is left out of the income fit because most sellers are there, so its penetration is not a demand signal.
3. **Delivery time and freight cost track sales even more than income does.** Across states, revenue per resident has a rank correlation of -0.93 with average delivery days and -0.82 with freight as a share of price (SP: 8.3 days and 13.9% freight; AM: 26 days and 24.5%). Income, delivery time and freight are strongly tied to each other (income vs delivery days: -0.82), so their separate effects cannot be told apart with 27 states. What can be said is that the low-selling states are also the slow and expensive ones.
4. **Late rate is not what holds sales back.** RJ has the second highest revenue per resident (R$102) with a 13.5% late rate; RO has a 2.9% late rate and low sales. Speed (days) and freight cost line up with sales; lateness against the estimate does not.
5. **Under-selling relative to income.** Five states sell below 80% of what their income predicts: AM (29% of expected), RR (33%), RO (80%), AC (78%), AP (75%). The largest gap in absolute terms is AM, with a population of 4.1 million and revenue of only R$22,000 (R$5 per 1,000 residents). Among states at or above the national income level, DF (85% of expected), MS (85%) and MT (95%) have the largest gaps.

## What it could be worth (scenarios, not forecasts)
| Scenario | Extra revenue over the window | Share of window revenue |
|---|---|---|
| The 5 states below 80% of expectation reach 80% | R$51,000 | 0.4% |
| Every state below its income-predicted level reaches it (SP excluded) | R$213,000 | 1.6% |
| Ceiling: states with income at or above R$1,373 (DF, SC, RS, PR, MS, MT) reach RJ's revenue per resident of R$102 | R$1.51M | 11.5% |

- The first two are small because income already explains most of the gap, and the poorer states are small markets.
- The ceiling scenario is the one with real size: **PR (R$494k) and RS (R$430k), SC (R$217k), MT (R$199k) and MS (R$165k)** together. It assumes those states can buy like RJ, which has a sellers' hub and short delivery times; it is an upper bound, not a target. Test it first on one state (Stage 8).

## Limits
- 27 states is a small sample for a regression, and income, delivery time and freight move together, so causes cannot be separated.
- State income is an average; it hides large differences inside each state.
- Seller location (mostly SP) drives delivery time, so "far from sellers" and "slow and expensive" are the same effect.
- The window covers a period of fast growth for Olist, so penetration may still be catching up in some states.

## Recommendation for Stage 8
The most promising state to test is **Paraná**: income R$1,607 (above the national level), the shortest delivery time after SP (11.5 days) and the lowest late rate (5.0%) of the large states, yet revenue per resident (R$58.5) is 42% below RJ's. Barriers there look like awareness and assortment, not logistics.
