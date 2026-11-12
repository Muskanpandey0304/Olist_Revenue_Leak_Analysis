# Experiment Design (Stage 8): How do we know a fix would work before rolling it out?

Design only. No result is reported because no experiment has been run. Sizing numbers come from `notebooks/08_experiment_power.py`.

## Recommendations being tested, ranked by money at stake
| # | Recommendation | Money at stake | Evidence |
|---|---|---|---|
| 1 | Lower the cost or time barrier in high-income states that under-sell (first: Paraná) | up to R$1.5M over the window if those states reached RJ's level (ceiling); the realistic part is much smaller | Stage 7 |
| 2 | Win back high-value one-time customers | about R$114,500 per extra percentage point of repeat rate | Stage 3 |
| 3 | Fix delivery in RJ, add a 57-seller watch-list, recalibrate delivery estimates | about R$138,000 of revenue in RJ is attached to excess late orders; late orders get 54% low reviews | Stages 4 and 5 |

Recommendation 3 is an operations change measured by late rate and review score, which is straightforward to track before and after, so the experiment design below covers the other two.

---

## Experiment A: Freight or delivery-promise offer in Paraná

**Hypothesis.** Paraná has income above the national level, the second fastest delivery in the country and the lowest late rate of the large states, yet sells 42% less per resident than RJ. Making the first order cheaper (freight discount) or more attractive (a firm, shorter delivery promise for Paraná) will increase orders.

**Unit of randomisation: the visitor (or session), not the zip area.** A geographic split was tested first and rejected. Paraná has about 60 orders a week across the 37 zip areas with enough volume. Splitting those areas into test and control, the smallest lift that could be detected with 80% power is 72% after 4 weeks, 51% after 8 weeks, 38% after 16 weeks. No freight offer will plausibly raise orders by 40% or more, so a geographic test would show nothing even if the offer worked.

**Design.**
- Randomise Paraná visitors 50/50: control sees current freight and estimate; treatment sees the offer (for example 50% off freight on the first order, or a shorter delivery promise).
- Primary metric: visitor-to-order conversion rate. Secondary: average order value, 90-day repeat rate, late rate and review score of treated orders.
- Guardrails: late rate must not rise (a shorter promise could raise it); contribution per order after the discount must stay positive.
- Duration: at least 2 full weeks to cover weekday patterns, long enough to reach the sample size below, and kept away from Black Friday week.

**Sample size.** The dataset has no visit data, so the baseline conversion rate is **not known** and must be taken from Olist's web analytics before starting. For reference only (the baselines below are illustrative, not measured), visitors needed per arm for 80% power at 5% significance:

| Baseline conversion | Detect +20% relative | Detect +10% relative |
|---|---|---|
| 1% | 42,606 | 163,004 |
| 2% | 21,066 | 80,637 |
| 3% | 13,887 | 53,182 |

**Decision rule.** Roll out only if conversion rises with a 95% confidence interval above zero, late rate and review score are not worse, and contribution per order stays positive. Break-even needs Olist's commission per order, which is not in this dataset. Average Paraná freight is R$24.44 on an average order of R$138.82, so a 50% freight discount costs about R$12 per treated order before any extra orders.

**Risks.** Existing customers see a different price (use randomisation by logged-in or device id and keep it stable); treated orders shift demand from later weeks (watch repeat rate); novelty effects fade (read the second week separately).

---

## Experiment B: Win-back message to high-value one-time customers

**Hypothesis.** A targeted message with an offer raises the 90-day repeat rate of one-time customers who spent R$176 or more.

**Audience.** 7,311 recent (last order within 180 days) plus 10,758 lapsed high-value one-time customers, 18,069 in total (Stage 3). Randomise 50/50 within each of the two groups.

**Sizing.** Baseline 90-day repeat rate is 2.28% (Stage 3). To detect +1 percentage point (2.28% to 3.28%) with 80% power at 5% significance, 4,209 customers are needed per arm (8,417 in total). The recent group alone (7,311) is not enough for +1 point; its smallest detectable lift is +1.08 points (to 3.36%). The combined audience of 18,069 is enough for +1 point; a +2 point lift needs only 2,432 customers.

**Metrics.** Primary: placed a second order within 90 days. Secondary: revenue per customer, discount cost per incremental order. Guardrail: unsubscribe and complaint rate.

**Value of the result.** Each extra percentage point is worth about R$114,500 over the customer base (Stage 3 scenario); here the audience is only 18,069 customers, so a 1-point lift inside it is about 180 orders, about R$22,000 at the Stage 3 average second order of R$123. The test is cheap, but it should be judged on contribution after the offer cost, which needs the commission rate.

**Holdout.** After the test, keep a 5% control group permanently to measure the lasting effect.

---

## What is not claimed
- No effect size for either offer is assumed; the sizing only shows what each test could detect.
- Both designs need business inputs that the public dataset does not contain: visit data, commission per order, offer cost.
