"""Stage 6: early-warning model for late deliveries (explainable, deliberately small).

Predicts, at the moment of purchase, whether an order will arrive late (any) or 7+ days late (severe).
Only information known at purchase is used. Time-based split: train on orders purchased before
2018-04-01, test on April to August 2018 (the model never sees the future).

Run:  python notebooks/06_late_risk_model.py
"""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "olist.db")

df = pd.read_sql("""
SELECT f.order_id, f.purchase_date, f.customer_state, f.is_late, f.delivery_days, f.estimated_days,
       f.holidays_in_window, f.avg_distance_km AS dist, f.items_price, f.freight_total, f.n_items,
       i.seller_id, s.state AS seller_state,
       p.weight_g, p.volume_cm3
FROM fact_orders f
JOIN (SELECT order_id, MIN(seller_id) AS seller_id, MIN(product_id) AS product_id
      FROM fact_order_items GROUP BY order_id) i USING (order_id)
JOIN dim_seller s ON s.seller_id = i.seller_id
JOIN dim_product p ON p.product_id = i.product_id
WHERE f.is_revenue_order = 1 AND f.n_sellers = 1""", con, parse_dates=["purchase_date"])
df["late"] = df.is_late.astype(int)
df["severe"] = ((df.delivery_days - df.estimated_days) >= 7).astype(int)
df["same_state"] = (df.customer_state == df.seller_state).astype(int)
df["purchase_month"] = df.purchase_date.dt.month
df["purchase_dow"] = df.purchase_date.dt.dayofweek
df["freight_ratio"] = df.freight_total / df.items_price.clip(lower=1)
df["dist"] = df.dist.fillna(df.dist.median())
for c in ["weight_g", "volume_cm3"]:
    df[c] = df[c].fillna(df[c].median())

train = df[df.purchase_date < "2018-04-01"].copy()
test = df[df.purchase_date >= "2018-04-01"].copy()
print(f"train {len(train):,} (late {100 * train.late.mean():.1f}%, severe {100 * train.severe.mean():.1f}%) | "
      f"test {len(test):,} (late {100 * test.late.mean():.1f}%, severe {100 * test.severe.mean():.1f}%)")

# Seller history, smoothed toward the overall rate. Training rows use leave-one-out so a row never
# sees its own outcome; test rows use the training-period history only.
K = 20
g = train.late.mean()
agg = train.groupby("seller_id").late.agg(["sum", "count"])
train = train.join(agg, on="seller_id")
train["seller_late_hist"] = (train["sum"] - train.late + K * g) / (train["count"] - 1 + K)
test = test.join(agg, on="seller_id")
test["seller_late_hist"] = ((test["sum"].fillna(0) + K * g) / (test["count"].fillna(0) + K))

num = ["dist", "same_state", "estimated_days", "holidays_in_window", "items_price", "freight_total",
       "freight_ratio", "weight_g", "volume_cm3", "n_items", "seller_late_hist", "purchase_month", "purchase_dow"]
cat = ["customer_state", "seller_state"]
prep = ColumnTransformer([("num", StandardScaler(), num),
                          ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=100), cat)])


def evaluate(name, model, target, show_top=False):
    pipe = Pipeline([("prep", prep), ("model", model)]).fit(train[num + cat], train[target])
    p = pipe.predict_proba(test[num + cat])[:, 1]
    y = test[target].values
    order = np.argsort(-p)
    top = order[: int(0.1 * len(p))]
    print(f"  {name:<20} ROC AUC {roc_auc_score(y, p):.3f} | PR AUC {average_precision_score(y, p):.3f} "
          f"(baseline {y.mean():.3f}) | top 10% riskiest orders catch {100 * y[top].sum() / y.sum():.1f}% of cases "
          f"(precision {100 * y[top].mean():.1f}%)")
    return pipe, p


results = {}
for target in ["late", "severe"]:
    print(f"\nTarget: {target}")
    lr, p_lr = evaluate("logistic regression", LogisticRegression(max_iter=2000, C=0.5), target)
    rf, p_rf = evaluate("random forest", RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=50,
                                                              n_jobs=-1, random_state=42), target)
    results[target] = (lr, rf)

# Explainability on the chosen model: logistic regression coefficients (standardised features)
lr, rf = results["late"]
names = lr.named_steps["prep"].get_feature_names_out()
coef = pd.Series(lr.named_steps["model"].coef_[0], index=names).sort_values(key=abs, ascending=False)
print("\nLogistic regression (target: late): largest standardised coefficients (positive = more late risk)")
print(coef.head(12).round(3).to_string())

pi = permutation_importance(rf, test[num + cat].sample(8000, random_state=1),
                            test.loc[test[num + cat].sample(8000, random_state=1).index, "late"],
                            scoring="roc_auc", n_repeats=5, random_state=1, n_jobs=-1)
imp = pd.Series(pi.importances_mean, index=num + cat).sort_values(ascending=False)
print("\nRandom forest permutation importance (drop in ROC AUC when the feature is shuffled)")
print(imp.head(8).round(4).to_string())

# Calibration of the logistic model by risk decile on the test set
test["risk"] = lr.predict_proba(test[num + cat])[:, 1]
test["decile"] = pd.qcut(test.risk.rank(method="first"), 10, labels=range(1, 11))
cal = test.groupby("decile", observed=True).agg(orders=("late", "size"), predicted=("risk", "mean"), actual=("late", "mean")).round(3)
print("\nCalibration by risk decile (test set)\n", cal.to_string())
test[["order_id", "customer_state", "seller_id", "risk"]].round(4).to_csv(ROOT / "reports" / "late_risk_scores_test.csv", index=False)
