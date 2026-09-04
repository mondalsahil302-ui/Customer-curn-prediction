# ============================================================
# LTV MODEL TRAINING
# ============================================================

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from xgboost import XGBRegressor


# ============================================================
# 1. LOAD DATA
# ============================================================

df = pd.read_csv(
    "PreProcessed_IBM_Telco_Customer_Churn_Cleaned.csv"
)

print("Original shape:", df.shape)


# ============================================================
# 2. LOAD YOUR EXISTING PREPROCESSING PACKAGE
# ============================================================

package = joblib.load(
    "preprocessing_package.pkl"
)

print(
    "Preprocessing package loaded successfully."
)

print(
    "Expected feature count:",
    len(package["feature_order"])
)


# ============================================================
# 3. IMPORT YOUR EXISTING PREPROCESSING MODULE
# ============================================================

import preprocessing


# ============================================================
# 4. CREATE THE 25 INPUT FEATURES
# ============================================================

X = preprocessing.transform(
    df,
    package
)

print(
    "\nProcessed feature shape:",
    X.shape
)


# ============================================================
# 5. CREATE LTV TARGET
# ============================================================

# Keep original values for target construction
target_df = df.copy()

# Convert charge columns to numeric
target_df["MonthlyCharges"] = pd.to_numeric(
    target_df["MonthlyCharges"],
    errors="coerce"
).fillna(0)

target_df["TotalCharges"] = pd.to_numeric(
    target_df["TotalCharges"],
    errors="coerce"
).fillna(0)

# Convert churn to 0/1
churn = target_df["Churn"].map({
    "Yes": 1,
    "No": 0
})


# ============================================================
# 6. DEFINE PROJECTED LTV
# ============================================================

PROJECTED_MONTHS = 12

future_value = (
    target_df["MonthlyCharges"]
    * PROJECTED_MONTHS
)

retention_adjusted_future_value = (
    future_value
    * (1 - churn)
)

projected_ltv = (
    target_df["TotalCharges"]
    + retention_adjusted_future_value
)

y = projected_ltv.rename(
    "Projected_LTV"
)

print("\nLTV target statistics:")
print(y.describe())


# ============================================================
# 7. CHECK ALIGNMENT
# ============================================================

if len(X) != len(y):
    raise ValueError(
        "X and LTV target have different numbers of rows."
    )

print(
    "\nX rows:",
    len(X)
)

print(
    "LTV rows:",
    len(y)
)


# ============================================================
# 8. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print(
    "\nTraining rows:",
    len(X_train)
)

print(
    "Testing rows:",
    len(X_test)
)


# ============================================================
# 9. CREATE XGBOOST REGRESSOR
# ============================================================

ltv_model = XGBRegressor(
    objective="reg:squarederror",

    n_estimators=500,

    max_depth=5,

    learning_rate=0.03,

    subsample=0.8,

    colsample_bytree=0.8,

    min_child_weight=3,

    reg_alpha=0.01,

    reg_lambda=1.0,

    random_state=42,

    eval_metric="rmse"
)


# ============================================================
# 10. TRAIN LTV MODEL
# ============================================================

ltv_model.fit(
    X_train,
    y_train,
    eval_set=[
        (X_test, y_test)
    ],
    verbose=False
)

print(
    "\nLTV model training completed."
)


# ============================================================
# 11. PREDICT LTV
# ============================================================

y_pred = ltv_model.predict(
    X_test
)


# ============================================================
# 12. EVALUATE MODEL
# ============================================================

mae = mean_absolute_error(
    y_test,
    y_pred
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        y_pred
    )
)

r2 = r2_score(
    y_test,
    y_pred
)

print("\n======================================")
print("LTV MODEL EVALUATION")
print("======================================")

print(
    "MAE :",
    round(mae, 2)
)

print(
    "RMSE:",
    round(rmse, 2)
)

print(
    "R²  :",
    round(r2, 4)
)


# ============================================================
# 13. SHOW SAMPLE PREDICTIONS
# ============================================================

comparison = pd.DataFrame({
    "Actual_LTV": y_test.values,
    "Predicted_LTV": y_pred
})

comparison["Absolute_Error"] = (
    abs(
        comparison["Actual_LTV"]
        -
        comparison["Predicted_LTV"]
    )
)

print("\nSample predictions:")
print(
    comparison.head(20).to_string(
        index=False
    )
)


# ============================================================
# 14. SAVE LTV MODEL
# ============================================================

LTV_MODEL_PATH = "ltv_model.json"

ltv_model.save_model(
    LTV_MODEL_PATH
)

print(
    f"\nLTV model saved successfully: {LTV_MODEL_PATH}"
)


# ============================================================
# 15. VERIFY SAVED MODEL
# ============================================================

loaded_ltv_model = XGBRegressor()

loaded_ltv_model.load_model(
    LTV_MODEL_PATH
)

verified_predictions = loaded_ltv_model.predict(
    X_test
)

verified_mae = mean_absolute_error(
    y_test,
    verified_predictions
)

print(
    "\nSaved-model verification MAE:",
    round(verified_mae, 2)
)

print(
    "LTV model loaded successfully."
)