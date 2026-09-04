# ============================================================
# XGBOOST TRAINING NOTEBOOK
# ============================================================

import pandas as pd
import numpy as np
import warnings
import xgboost as xgb
import matplotlib.pyplot as plt
import shap
import joblib

warnings.filterwarnings("ignore")

from xgboost import XGBClassifier
from sklearn.model_selection import (
    train_test_split,
    RandomizedSearchCV,
    StratifiedKFold
)
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    RocCurveDisplay,
    PrecisionRecallDisplay
)


# ============================================================
# 1. LOAD DATA
# ============================================================

df = pd.read_csv(
    "PreProcessed_IBM_Telco_Customer_Churn_Cleaned.csv"
)

# Remove customerID
df = df.drop(
    columns=["customerID"]
)

print("Initial shape:", df.shape)

print("\nChurn distribution:")
print(
    df["Churn"].value_counts(
        normalize=True
    )
)


# ============================================================
# 2. PREPROCESSING
#    EXACTLY AS YOUR ORIGINAL XGBOOST NOTEBOOK
# ============================================================

# Target
df["Churn"] = df["Churn"].map({
    "Yes": 1,
    "No": 0
})

# Gender
df["gender"] = df["gender"].map({
    "Male": 1,
    "Female": 0
})

# Binary columns
for c in [
    "Partner",
    "Dependents",
    "PhoneService",
    "PaperlessBilling"
]:
    df[c] = df[c].map({
        "Yes": 1,
        "No": 0
    })


# Service columns
collapse_cols = [
    "MultipleLines",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies"
]

for c in collapse_cols:

    df[c] = df[c].replace({
        "No internet service": "No",
        "No phone service": "No"
    })

    df[c] = df[c].map({
        "Yes": 1,
        "No": 0
    })


# TenureGroup
df["TenureGroup"] = df["TenureGroup"].map({
    "0-1 Year": 0,
    "1-2 Years": 1,
    "2-4 Years": 2,
    "4-6 Years": 3
})


# One-hot encoding
df = pd.get_dummies(
    df,
    columns=[
        "InternetService",
        "Contract",
        "PaymentMethod"
    ],
    drop_first=True
)


# Boolean → integer
bool_cols = df.select_dtypes(
    include="bool"
).columns

df[bool_cols] = df[bool_cols].astype(int)


# ============================================================
# 3. X AND Y
# ============================================================

X = df.drop(
    columns=["Churn"]
)

y = df["Churn"]

print("\nProcessed shape:", df.shape)
print("X shape:", X.shape)
print("y shape:", y.shape)


# ============================================================
# 4. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42
)

print("\nTrain shape:", X_train.shape)
print("Test shape :", X_test.shape)


# ============================================================
# 5. CLASS WEIGHT
# ============================================================

neg = (y_train == 0).sum()
pos = (y_train == 1).sum()

spw = neg / pos

print(
    f"\nscale_pos_weight = {neg}/{pos} = {spw:.4f}"
)


# ============================================================
# 6. BASELINE XGBOOST
# ============================================================

results = {}

baseline_model = XGBClassifier(
    random_state=42,
    eval_metric="logloss"
)

baseline_model.fit(
    X_train,
    y_train
)

pred = baseline_model.predict(
    X_test
)

proba = baseline_model.predict_proba(
    X_test
)[:, 1]

results["Baseline"] = {
    "Accuracy": accuracy_score(
        y_test,
        pred
    ),

    "Precision": precision_score(
        y_test,
        pred
    ),

    "Recall": recall_score(
        y_test,
        pred
    ),

    "F1": f1_score(
        y_test,
        pred
    ),

    "ROC-AUC": roc_auc_score(
        y_test,
        proba
    )
}

print("\nBaseline results:")
print(results["Baseline"])

print("\nBaseline confusion matrix:")
print(
    confusion_matrix(
        y_test,
        pred
    )
)


# ============================================================
# 7. RESIDUAL + TREE TRACE
#    THREE DEMONSTRATION BOOSTING ROUNDS
# ============================================================

churn_idx = y_test[
    y_test == 1
].index[:3]

no_churn_idx = y_test[
    y_test == 0
].index[:3]

sample_idx = churn_idx.append(
    no_churn_idx
)

X_sample = X_test.loc[
    sample_idx
]

y_sample = y_test.loc[
    sample_idx
].values

dsample = xgb.DMatrix(
    X_sample
)

dtrain = xgb.DMatrix(
    X_train,
    label=y_train
)

trace_params = {
    "max_depth": 3,
    "eta": 0.3,
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "scale_pos_weight": spw
}

booster = None

for round_num in range(1, 4):

    # Initial probability
    if booster is None:
        prob_before = np.full(
            len(sample_idx),
            y_train.mean()
        )
    else:
        prob_before = booster.predict(
            dsample
        )

    # Intuitive residual
    residual = (
        y_sample
        - prob_before
    )

    # Add one tree
    booster = xgb.train(
        trace_params,
        dtrain,
        num_boost_round=1,
        xgb_model=booster
    )

    # Probability after tree
    prob_after = booster.predict(
        dsample
    )

    tbl = pd.DataFrame({
        "CustomerID": sample_idx,
        "ActualChurn": y_sample,
        "Prob_Before": prob_before.round(4),
        "Residual": residual.round(4),
        "Prob_After": prob_after.round(4)
    })

    print(
        f"\n--- Round {round_num} ---"
    )

    print(
        tbl.to_string(
            index=False
        )
    )

    print(
        "\nTree added this round:"
    )

    print(
        booster.get_dump()[-1]
    )

    print(
        "=" * 70
    )


# ============================================================
# 8. CLASS-WEIGHTED MODEL
# ============================================================

weighted_model = XGBClassifier(
    random_state=42,
    eval_metric="logloss",
    scale_pos_weight=spw
)

weighted_model.fit(
    X_train,
    y_train
)

pred = weighted_model.predict(
    X_test
)

proba = weighted_model.predict_proba(
    X_test
)[:, 1]

results["Class-Weighted"] = {
    "Accuracy": accuracy_score(
        y_test,
        pred
    ),

    "Precision": precision_score(
        y_test,
        pred
    ),

    "Recall": recall_score(
        y_test,
        pred
    ),

    "F1": f1_score(
        y_test,
        pred
    ),

    "ROC-AUC": roc_auc_score(
        y_test,
        proba
    )
}

print(
    "\nClass-weighted results:"
)

print(
    results["Class-Weighted"]
)


# ============================================================
# 9. RANDOMIZED HYPERPARAMETER SEARCH
# ============================================================

param_dist = {

    "n_estimators": [
        100,
        200,
        300,
        400,
        500
    ],

    "max_depth": [
        3,
        4,
        5,
        6,
        7,
        8
    ],

    "learning_rate": [
        0.01,
        0.02,
        0.05,
        0.08,
        0.1,
        0.15
    ],

    "subsample": [
        0.6,
        0.7,
        0.8,
        0.9,
        1.0
    ],

    "colsample_bytree": [
        0.6,
        0.7,
        0.8,
        0.9,
        1.0
    ],

    "min_child_weight": [
        1,
        3,
        5,
        7
    ],

    "gamma": [
        0,
        0.1,
        0.2,
        0.3,
        0.5
    ],

    "reg_alpha": [
        0,
        0.01,
        0.1,
        1
    ],

    "reg_lambda": [
        0.5,
        1,
        1.5,
        2,
        3
    ]
}


base = XGBClassifier(
    random_state=42,
    eval_metric="logloss",
    scale_pos_weight=spw
)

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

search = RandomizedSearchCV(
    base,
    param_distributions=param_dist,
    n_iter=40,
    scoring="roc_auc",
    cv=cv,
    random_state=42,
    n_jobs=-1
)

search.fit(
    X_train,
    y_train
)

print(
    "\nBest CV ROC-AUC:",
    search.best_score_
)

print(
    "\nBest parameters:"
)

print(
    search.best_params_
)


# ============================================================
# 10. FINAL TUNED MODEL WITH EARLY STOPPING
# ============================================================

X_tr2, X_val, y_tr2, y_val = train_test_split(
    X_train,
    y_train,
    test_size=0.15,
    stratify=y_train,
    random_state=42
)

params = dict(
    search.best_params_
)

params["n_estimators"] = 2000

final_model = XGBClassifier(
    random_state=42,
    eval_metric="auc",
    scale_pos_weight=spw,
    early_stopping_rounds=30,
    **params
)

final_model.fit(
    X_tr2,
    y_tr2,
    eval_set=[
        (X_val, y_val)
    ],
    verbose=False
)


# ============================================================
# 11. FINAL MODEL EVALUATION
# ============================================================

print(
    "\nTrees actually used:",
    final_model.best_iteration
)

pred = final_model.predict(
    X_test
)

proba = final_model.predict_proba(
    X_test
)[:, 1]

results["Tuned (Final)"] = {

    "Accuracy": accuracy_score(
        y_test,
        pred
    ),

    "Precision": precision_score(
        y_test,
        pred
    ),

    "Recall": recall_score(
        y_test,
        pred
    ),

    "F1": f1_score(
        y_test,
        pred
    ),

    "ROC-AUC": roc_auc_score(
        y_test,
        proba
    )
}

print(
    "\nFinal model results:"
)

print(
    results["Tuned (Final)"]
)

print(
    "\nConfusion matrix:"
)

print(
    confusion_matrix(
        y_test,
        pred
    )
)

print(
    "\nClassification report:"
)

print(
    classification_report(
        y_test,
        pred,
        target_names=[
            "No Churn",
            "Churn"
        ]
    )
)


# ============================================================
# 12. ROC CURVE
# ============================================================

RocCurveDisplay.from_predictions(
    y_test,
    proba
)

plt.title(
    "XGBoost ROC Curve"
)

plt.grid(
    True
)

plt.show()


# ============================================================
# 13. PRECISION-RECALL CURVE
# ============================================================

PrecisionRecallDisplay.from_predictions(
    y_test,
    proba
)

plt.title(
    "XGBoost Precision-Recall Curve"
)

plt.grid(
    True
)

plt.show()


# ============================================================
# 14. FINAL MODEL FEATURE IMPORTANCE
# ============================================================

importance = pd.Series(
    final_model.feature_importances_,
    index=X.columns
).sort_values(
    ascending=False
)

print(
    "\nTop 20 feature importances:"
)

print(
    importance.head(20)
)

plt.figure(
    figsize=(10, 7)
)

importance.head(20).sort_values().plot(
    kind="barh"
)

plt.title(
    "Top 20 XGBoost Feature Importances"
)

plt.xlabel(
    "Importance"
)

plt.tight_layout()

plt.show()


# ============================================================
# 15. SAVE FINAL TRAINED XGBOOST MODEL
# ============================================================

MODEL_PATH = "xgboost_model.json"

final_model.save_model(
    MODEL_PATH
)

print(
    f"\nXGBoost model saved successfully: {MODEL_PATH}"
)


# ============================================================
# 16. VERIFY SAVED MODEL
# ============================================================

loaded_model = XGBClassifier()

loaded_model.load_model(
    MODEL_PATH
)

loaded_proba = loaded_model.predict_proba(
    X_test
)[:, 1]

loaded_pred = (
    loaded_proba >= 0.5
).astype(int)

print(
    "\nSaved model verification:"
)

print(
    "ROC-AUC:",
    roc_auc_score(
        y_test,
        loaded_proba
    )
)

print(
    "Accuracy:",
    accuracy_score(
        y_test,
        loaded_pred
    )
)

print(
    "Model file:",
    MODEL_PATH
)

print(
    "Model loaded and verified successfully."
)