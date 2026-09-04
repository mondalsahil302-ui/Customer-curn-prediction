# ============================================================
# main.py
#
# CUSTOMER CHURN + LTV PREDICTION PIPELINE
#
# FLOW
# ------------------------------------------------------------
# 1. Connect to Neon PostgreSQL
# 2. Create Python-side processing window
# 3. Fetch customers changed in that window
# 4. Load preprocessing package
# 5. Preprocess incoming rows
# 6. Validate processed features
# 7. Load churn model
# 8. Predict churn
# 9. Load LTV model
# 10. Predict LTV
# 11. Create final prediction result
# 12. Write predictions to PostgreSQL
# 13. Save successful Python checkpoint
# ============================================================


import pandas as pd
import numpy as np
import joblib
import xgboost as xgb


import database as db
import preprocessing
import change_tracker


# ============================================================
# FILE PATHS
# ============================================================

PREPROCESSING_PACKAGE_PATH = (
    "preprocessing_package.pkl"
)

CHURN_MODEL_PATH = (
    "xgboost_model.json"
)

LTV_MODEL_PATH = (
    "ltv_model.json"
)


# ============================================================
# ONE PIPELINE RUN
# ============================================================

def run_pipeline():

    print()
    print("=" * 70)
    print("STARTING CHURN + LTV PIPELINE")
    print("=" * 70)


    # ========================================================
    # 1. CONNECT TO NEON POSTGRESQL
    # ========================================================

    print()
    print(
        "Connecting to Neon PostgreSQL..."
    )

    engine = db.get_engine()

    db.test_connection(
        engine
    )


    # ========================================================
    # 2. CREATE PROCESSING WINDOW
    # ========================================================
    #
    # change_tracker.py now controls the timestamp window.
    #
    # IMPORTANT:
    # create_processing_window() takes NO arguments.
    # ========================================================

    (
        window_start,
        window_end
    ) = (
        change_tracker
        .create_processing_window()
    )


    # --------------------------------------------------------
    # The end of this window becomes the checkpoint only
    # after the pipeline finishes successfully.
    # --------------------------------------------------------

    run_time = window_end


    # ========================================================
    # 3. DISPLAY PROCESSING WINDOW
    # ========================================================

    change_tracker.print_processing_window(
        window_start,
        window_end
    )


    # ========================================================
    # 4. FETCH CUSTOMERS CHANGED DURING WINDOW
    # ========================================================

    print()
    print(
        "Checking for new or updated customers..."
    )


    raw_df = (
        db.fetch_customers_in_window(
            window_start,
            window_end,
            engine
        )
    )


    # ========================================================
    # 5. NO ROWS TO PROCESS
    # ========================================================

    if raw_df.empty:

        print()
        print(
            "No new or updated customers "
            "require prediction."
        )


        # ----------------------------------------------------
        # The database was checked successfully.
        # Therefore advance the Python checkpoint.
        # ----------------------------------------------------

        change_tracker.save_last_successful_run(
            run_time
        )


        print(
            "Processing window checkpoint updated:",
            run_time
        )


        return


    # ========================================================
    # 6. SHOW ROW COUNT
    # ========================================================

    print()
    print(
        f"Rows to process: {len(raw_df)}"
    )


    # ========================================================
    # 7. LOAD PREPROCESSING PACKAGE
    # ========================================================

    print()
    print(
        "Loading preprocessing package..."
    )


    package = joblib.load(
        PREPROCESSING_PACKAGE_PATH
    )


    print(
        "Preprocessing package loaded."
    )


    # ========================================================
    # 8. PREPROCESS / TRANSFORM
    # ========================================================

    print()
    print(
        "Preprocessing incoming customer data..."
    )


    features_df = (
        preprocessing.transform(
            raw_df,
            package
        )
    )


    print(
        "Processed shape:",
        features_df.shape
    )


    # ========================================================
    # 9. VALIDATE FEATURE COUNT
    # ========================================================

    expected_features = len(
        package[
            "feature_order"
        ]
    )


    actual_features = (
        features_df.shape[1]
    )


    print(
        "Expected features:",
        expected_features
    )


    print(
        "Actual features:",
        actual_features
    )


    if actual_features != expected_features:

        raise ValueError(
            f"Feature mismatch: "
            f"expected {expected_features}, "
            f"got {actual_features}"
        )


    # ========================================================
    # 10. VALIDATE NaN VALUES
    # ========================================================

    if (
        features_df
        .isnull()
        .sum()
        .sum()
        > 0
    ):

        nan_columns = (
            features_df
            .columns[
                features_df
                .isnull()
                .any()
            ]
            .tolist()
        )


        raise ValueError(
            "NaN detected after preprocessing. "
            f"Columns: {nan_columns}"
        )


    print(
        "NaN validation passed."
    )


    # ========================================================
    # 11. CONVERT TO NUMPY
    # ========================================================

    X_input = (
        features_df
        .to_numpy(
            dtype=np.float32
        )
    )


    print(
        "Feature matrix ready:",
        X_input.shape
    )


    # ========================================================
    # 12. LOAD CHURN MODEL
    # ========================================================

    print()
    print(
        "Loading churn model..."
    )


    churn_model = (
        xgb.XGBClassifier()
    )


    churn_model.load_model(
        CHURN_MODEL_PATH
    )


    print(
        "Churn model loaded."
    )


    # ========================================================
    # 13. CHURN PREDICTION
    # ========================================================

    print()
    print(
        "Running churn prediction..."
    )


    churn_probability = (
        churn_model
        .predict_proba(
            X_input
        )[:, 1]
    )


    # --------------------------------------------------------
    # Churn threshold
    # --------------------------------------------------------

    threshold = 0.50


    churn_prediction = (
        churn_probability
        >= threshold
    ).astype(int)


    # ========================================================
    # 14. LOAD LTV MODEL
    # ========================================================

    print()
    print(
        "Loading LTV model..."
    )


    ltv_model = (
        xgb.XGBRegressor()
    )


    ltv_model.load_model(
        LTV_MODEL_PATH
    )


    print(
        "LTV model loaded."
    )


    # ========================================================
    # 15. LTV PREDICTION
    # ========================================================

    print()
    print(
        "Running LTV prediction..."
    )


    predicted_ltv = (
        ltv_model
        .predict(
            X_input
        )
    )


    # ========================================================
    # 16. FIND CUSTOMER ID COLUMN
    # ========================================================

    customer_id_col = next(
        (
            col
            for col in raw_df.columns
            if col.lower()
            == "customerid"
        ),
        None
    )


    if customer_id_col is None:

        raise ValueError(
            "customerID column not found."
        )


    # ========================================================
    # 17. CREATE FINAL RESULT
    # ========================================================

    result = pd.DataFrame(
        {
            "customerid":
                raw_df[
                    customer_id_col
                ].values,

            "churn":
                np.where(
                    churn_prediction == 1,
                    "Yes",
                    "No"
                ),

            "churn_probability":
                churn_probability,

            "predicted_ltv":
                predicted_ltv
        }
    )


    # ========================================================
    # 18. DISPLAY MODEL OUTPUT
    # ========================================================

    print()
    print("=" * 70)
    print("MODEL OUTPUT")
    print("=" * 70)


    print(
        result.to_string(
            index=False
        )
    )


    # ========================================================
    # 19. WRITE PREDICTIONS TO NEON
    # ========================================================

    print()
    print(
        "Writing predictions to Neon PostgreSQL..."
    )


    db.write_predictions(
        result,
        engine
    )


    # ========================================================
    # 20. SAVE PYTHON CHECKPOINT
    # ========================================================
    #
    # VERY IMPORTANT:
    #
    # We save the checkpoint ONLY after all predictions have
    # been successfully written.
    #
    # If preprocessing fails, model fails, or database update
    # fails, this checkpoint is NOT advanced.
    #
    # The same rows can therefore be retried on the next run.
    # ========================================================

    change_tracker.save_last_successful_run(
        run_time
    )


    print(
        "Processing window checkpoint updated:",
        run_time
    )


    # ========================================================
    # 21. COMPLETE
    # ========================================================

    print()
    print("=" * 70)
    print(
        "PIPELINE COMPLETED SUCCESSFULLY"
    )
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_pipeline()