# Stage 6 Findings: Which orders will likely be late, so operations can act early?

Source: `notebooks/06_late_risk_model.py`, scores for the test period in `reports/late_risk_scores_test.csv`.

## Set-up
- One row per single-seller delivered order in the window (94,931). Only information known at purchase is used: seller-customer distance, same-state flag, estimated delivery days, holidays in the promised window, price, freight, weight, volume, number of items, customer and seller state, purchase month and weekday, and the seller's past late rate.
- **Time-based split.** Trained on orders purchased before 2018-04-01 (63,333 orders), tested on April to August 2018 (31,598 orders). The model is judged on a period it never saw.
- Two targets: late (any), and severe (7+ days late, the cases that wreck reviews in Stage 4).
- Two models compared: logistic regression (explainable) and random forest.
- The seller's past late rate is computed from the training period only; for training rows it leaves out the row's own outcome so the model cannot see the answer.

## Results (test period)
| Target | Model | ROC AUC | Top 10% riskiest orders catch | Precision in top 10% | Base rate |
|---|---|---|---|---|---|
| Late | **Logistic regression** | **0.718** | **25.0%** of late orders | 15.3% | 6.1% |
| Late | Random forest | 0.650 | 19.9% | 12.2% | 6.1% |
| 7+ days late | **Logistic regression** | **0.722** | **32.0%** of severe cases | 6.1% | 1.9% |
| 7+ days late | Random forest | 0.668 | 26.2% | 5.0% | 1.9% |

- **Chosen model: logistic regression.** It scored better than the random forest on both targets and can be explained line by line, which matters for an operations audience.
- **Value in plain terms:** checking only the riskiest 10% of orders finds 2.5 times more late orders than checking 10% at random (25% of late cases caught), and 3.2 times more for the severe cases (32%). It is a prioritisation tool, not a precise predictor.

## What drives the risk
- **Estimated delivery days** is the strongest signal. Orders promised with longer estimates are less likely to be late (negative coefficient, largest permutation importance). This matches Stage 5: estimates are padded, and the risky orders are those whose estimate is tight for their route.
- **Distance** and **same state** (positive for distance, negative for same state), consistent with Stage 5.
- **Customer state:** AL, RJ raise risk; PR, MG, SP, DF lower it. RJ again stands out.
- **Seller history** raises risk (positive coefficient), so past late performance of a seller is informative.
- Holidays, weight, price and weekday add little.

## Honest limits
- **Moderate accuracy.** ROC AUC about 0.72 is useful for ranking, not for individual promises. Most risky orders still arrive on time (precision 15% in the top decile).
- **Base rate shift.** The late rate was 9.3% in training (it includes the November 2017 to March 2018 peak) and 6.1% in the test months. The model over-predicts in absolute terms (for the riskiest decile it predicts 33% against an actual 15%), although the ranking still holds (actual late rate rises from 0.8% in the safest decile to 15.3% in the riskiest). In real use the scores would need recalibrating on recent data.
- No carrier information and no weather are available; both likely matter.

## How operations could use it
Flag the top 10% of orders by risk at purchase, then contact the customer early, move them to a faster carrier or re-check the delivery estimate. Because the model is a logistic regression, each flag can be explained by its drivers (state, distance, tight estimate, seller history).
