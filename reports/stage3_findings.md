# Stage 3 Findings: Who are our customers, and why do so few come back?

Source: `sql/40_cohort_retention.sql`, `sql/41_customer_concentration.sql`, `notebooks/03_rfm_segments.py`, `reports/rfm_segment_summary.csv`.
Window and definitions as in `metrics_definitions.md`. Customers are identified by `customer_unique_id`.

## Findings
1. **Retention is close to zero in every cohort.** In every monthly cohort, no more than about 0.7% of customers order again in any single later month (month 1 ranges from 0.18% to 0.72%). Cohort sizes are large (700 to 7,000 customers), so this is a stable pattern and not noise from small groups, apart from the early small cohorts.
2. **The 3% repeat rate is not just a timing artefact.** Counting only customers whose first order is at least 90 days before the end of the data, so that everyone had the same chance to return: 75,446 customers, of whom 2.28% ordered again within 90 days and 3.45% ordered again at any time.
3. **Repeat customers are worth about twice as much, but there are very few of them.** Repeat customers (2,789) spend R$260 on average against R$138 for one-time customers. They are 3.0% of customers and 5.5% of revenue. One-time customers are 94.5% of revenue.
4. **Customer value is concentrated.** The top 10% of customers (average spend R$582) bring 41.1% of revenue and the top 20% bring 56.6%. The bottom half bring 16.7%.
5. **Segments** (one-time buyers split at R$175.99, the 80th percentile of one-time spend; "recent" means the last order was within 180 days of 1 September 2018):

| Segment | Customers | % customers | Revenue | % revenue | Avg spend |
|---|---|---|---|---|---|
| One-time high value, lapsed | 10,758 | 11.6 | R$4.14M | 31.4 | R$385 |
| One-time standard, lapsed | 43,206 | 46.4 | R$3.21M | 24.3 | R$74 |
| One-time high value, recent | 7,311 | 7.9 | R$2.90M | 22.0 | R$397 |
| One-time standard, recent | 29,032 | 31.2 | R$2.20M | 16.7 | R$76 |
| Repeat, lapsed | 1,579 | 1.7 | R$0.40M | 3.0 | R$252 |
| Repeat, active | 1,210 | 1.3 | R$0.33M | 2.5 | R$270 |

   Why rule-based segments and not standard RFM quintiles: 97% of customers have frequency 1, so frequency scores would collapse into a single bucket. The segments use frequency (one-time vs repeat), recency and spend directly.

## What this means in money (scenario, not a forecast)
- Average value of a second order is R$123.02.
- Each additional 1 percentage point of customers who place one more order is about 931 customers, worth about **R$114,500, or 0.9% of window revenue**.
- Raising the repeat rate from 3% to 10% would be worth roughly R$0.8M (about 6% of window revenue). This assumes one extra order of average second-order value per newly retained customer and no change in acquisition.
- So retention alone is a modest lever per point; it matters because the business has no other source of growth now that new-customer growth has flattened (Stage 1).

## Where to act first
- **Win-back target: 7,311 recent high-value one-time customers.** They have spent R$2.9M in total (median R$397 each), last ordered a median of 98 days ago, and are still recent enough to respond. These are the first customers to contact. Past spend is not a promise of future spend.
- The lapsed high-value group (10,758 customers, R$4.1M past spend, median 318 days since last order) is a lower-probability second wave.

## Limits of this analysis
- Customers are identified only by `customer_unique_id`; a person using two accounts counts twice.
- Olist is a marketplace where many purchases (furniture, appliances) are rarely repeated, so some of the low retention may be the nature of the products. Stage 4 tests whether delivery experience makes it worse.
- The data stops in August 2018, so customers acquired in the last months have had little time to return; the 90-day measure above is built to avoid that bias, the cohort table is not.

## Passed to later stages
- Does a bad delivery or review reduce the chance that a customer comes back? (Stage 4)
- Which categories have the best chance of a second purchase? (Stage 6 and the dashboard)
