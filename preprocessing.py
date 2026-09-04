# ============================================================
# preprocessing.py
#
# Purpose:
#   1. Build preprocessing_package.pkl ONCE
#   2. Transform incoming PostgreSQL rows for prediction
#
# Important:
#   - Original PostgreSQL data is NEVER modified here.
#   - updated_at is only for pipeline tracking.
#   - updated_at is NOT an ML feature.
#   - Output feature order must remain identical to training.
# ============================================================

import numpy as np
import pandas as pd
import joblib


# ============================================================
# 1. EXPECTED CUSTOMER COLUMNS
# ============================================================

CANONICAL_COLUMNS = [
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn",
    "TenureGroup",
    "TotalServices"
]


# ============================================================
# 2. MAPPINGS
# ============================================================

BINARY_COLUMNS = [
    "Partner",
    "Dependents",
    "PhoneService",
    "PaperlessBilling"
]


SERVICE_COLUMNS = [
    "MultipleLines",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies"
]


SERVICE_COLLAPSE_MAPPING = {
    "No internet service": "No",
    "No phone service": "No"
}


# ------------------------------------------------------------
# TenureGroup mapping
#
# Accept both singular and plural spellings so incoming
# PostgreSQL data does not become NaN because of a text mismatch.
# ------------------------------------------------------------

TENURE_MAPPING = {
    "0-1 Year": 0,
    "0-1 Years": 0,

    "1-2 Year": 1,
    "1-2 Years": 1,

    "2-4 Year": 2,
    "2-4 Years": 2,

    "4-6 Year": 3,
    "4-6 Years": 3
}


NUMERIC_MODEL_COLUMNS = [
    "SeniorCitizen",
    "tenure",
    "MonthlyCharges",
    "TotalCharges",
    "TenureGroup",
    "TotalServices"
]


NUMERIC_CHARGE_COLUMNS = [
    "MonthlyCharges",
    "TotalCharges"
]


ONE_HOT_COLUMNS = [
    "InternetService",
    "Contract",
    "PaymentMethod"
]


# ============================================================
# 3. NORMALIZE COLUMN NAMES ONLY
# ============================================================

def normalize_columns(raw_df):
    """
    Makes column-name matching robust.

    This only normalizes column names.
    Customer values are not modified here.
    """

    df = raw_df.copy()

    # --------------------------------------------------------
    # Strip spaces from column names
    # --------------------------------------------------------

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    # --------------------------------------------------------
    # Case-insensitive matching
    # --------------------------------------------------------

    lower_to_actual = {
        col.lower(): col
        for col in df.columns
    }

    rename_map = {}
    missing = []

    for canonical in CANONICAL_COLUMNS:

        key = canonical.lower()

        if key in lower_to_actual:

            actual = lower_to_actual[key]

            if actual != canonical:
                rename_map[actual] = canonical

        else:
            missing.append(canonical)

    if missing:
        raise ValueError(
            "Missing required columns:\n"
            f"{missing}\n\n"
            "Columns received:\n"
            f"{df.columns.tolist()}"
        )

    df = df.rename(
        columns=rename_map
    )

    # --------------------------------------------------------
    # updated_at is pipeline metadata only.
    # Never send it to the ML model.
    # --------------------------------------------------------

    if "updated_at" in df.columns:

        df = df.drop(
            columns=["updated_at"]
        )

    return df


# ============================================================
# 4. BUILD PREPROCESSING PACKAGE
#
# Run this only when creating/rebuilding the package.
# ============================================================

def build_preprocessing_package(
    raw_df,
    save_path="preprocessing_package.pkl"
):

    # Work on a copy
    df = normalize_columns(raw_df)

    # --------------------------------------------------------
    # Remove ID + target
    # --------------------------------------------------------

    data = df.drop(
        columns=[
            "customerID",
            "Churn"
        ]
    ).copy()

    # --------------------------------------------------------
    # Gender
    # --------------------------------------------------------

    data["gender"] = data[
        "gender"
    ].map({
        "Male": 1,
        "Female": 0
    })

    # --------------------------------------------------------
    # Binary columns
    # --------------------------------------------------------

    for col in BINARY_COLUMNS:

        data[col] = data[
            col
        ].map({
            "Yes": 1,
            "No": 0
        })

    # --------------------------------------------------------
    # Service columns
    # --------------------------------------------------------

    for col in SERVICE_COLUMNS:

        data[col] = data[
            col
        ].replace(
            SERVICE_COLLAPSE_MAPPING
        )

        data[col] = data[
            col
        ].map({
            "Yes": 1,
            "No": 0
        })

    # --------------------------------------------------------
    # TenureGroup
    # --------------------------------------------------------

    data["TenureGroup"] = data[
        "TenureGroup"
    ].map(
        TENURE_MAPPING
    )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    for col in NUMERIC_MODEL_COLUMNS:

        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Existing training behavior:
    # invalid/blank charge values become 0
    # --------------------------------------------------------

    data[
        NUMERIC_CHARGE_COLUMNS
    ] = data[
        NUMERIC_CHARGE_COLUMNS
    ].fillna(0)

    # --------------------------------------------------------
    # One-hot encoding
    # --------------------------------------------------------

    data = pd.get_dummies(
        data,
        columns=ONE_HOT_COLUMNS,
        drop_first=True
    )

    # --------------------------------------------------------
    # bool -> int
    # --------------------------------------------------------

    bool_columns = data.select_dtypes(
        include="bool"
    ).columns

    data[
        bool_columns
    ] = data[
        bool_columns
    ].astype(int)

    # --------------------------------------------------------
    # Final numeric conversion
    # --------------------------------------------------------

    for col in data.columns:

        if data[col].dtype == "object":

            data[col] = pd.to_numeric(
                data[col],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if data.isnull().sum().sum() > 0:

        missing = data.isnull().sum()

        missing = missing[
            missing > 0
        ]

        raise ValueError(
            "Preprocessing produced NaN values:\n"
            f"{missing}"
        )

    non_numeric = data.select_dtypes(
        exclude=np.number
    ).columns.tolist()

    if non_numeric:

        raise ValueError(
            "Non-numeric columns remain: "
            f"{non_numeric}"
        )

    if np.isinf(
        data.to_numpy(
            dtype=float
        )
    ).sum() > 0:

        raise ValueError(
            "Infinite values detected."
        )

    # --------------------------------------------------------
    # Save exact feature order
    # --------------------------------------------------------

    feature_order = data.columns.tolist()

    preprocessing_package = {

        "feature_order":
            feature_order,

        "drop_columns": [
            "customerID",
            "Churn"
        ],

        "gender_mapping": {
            "Male": 1,
            "Female": 0
        },

        "binary_columns":
            BINARY_COLUMNS,

        "binary_mapping": {
            "Yes": 1,
            "No": 0
        },

        "service_columns":
            SERVICE_COLUMNS,

        "service_collapse_mapping":
            SERVICE_COLLAPSE_MAPPING,

        "service_mapping": {
            "Yes": 1,
            "No": 0
        },

        "tenure_mapping":
            TENURE_MAPPING,

        "numeric_model_columns":
            NUMERIC_MODEL_COLUMNS,

        "numeric_charge_columns":
            NUMERIC_CHARGE_COLUMNS,

        "numeric_charge_fill_value":
            0,

        "one_hot_columns":
            ONE_HOT_COLUMNS,

        "drop_first":
            True
    }

    joblib.dump(
        preprocessing_package,
        save_path
    )

    print(
        "Preprocessing package created."
    )

    print(
        "Feature count:",
        len(feature_order)
    )

    print(
        "Feature order:"
    )

    for i, feature in enumerate(
        feature_order,
        start=1
    ):
        print(
            f"{i:02d}. {feature}"
        )

    print(
        "Saved to:",
        save_path
    )

    return (
        preprocessing_package,
        data
    )


# ============================================================
# 5. TRANSFORM INCOMING DATA
#    USED BY main.py
# ============================================================

def transform(
    raw_df,
    package
):

    # Always work on a copy
    df = normalize_columns(raw_df)

    # --------------------------------------------------------
    # Remove fields that are not model inputs
    # --------------------------------------------------------

    drop_cols = [
        col
        for col in package[
            "drop_columns"
        ]
        if col in df.columns
    ]

    data = df.drop(
        columns=drop_cols
    ).copy()

    # --------------------------------------------------------
    # Gender
    # --------------------------------------------------------

    data["gender"] = data[
        "gender"
    ].map(
        package[
            "gender_mapping"
        ]
    )

    # --------------------------------------------------------
    # Binary columns
    # --------------------------------------------------------

    for col in package[
        "binary_columns"
    ]:

        data[col] = data[
            col
        ].map(
            package[
                "binary_mapping"
            ]
        )

    # --------------------------------------------------------
    # Service columns
    # --------------------------------------------------------

    for col in package[
        "service_columns"
    ]:

        data[col] = data[
            col
        ].replace(
            package[
                "service_collapse_mapping"
            ]
        )

        data[col] = data[
            col
        ].map(
            package[
                "service_mapping"
            ]
        )

    # --------------------------------------------------------
    # TenureGroup
    # --------------------------------------------------------

    data["TenureGroup"] = data[
        "TenureGroup"
    ].map(
        package[
            "tenure_mapping"
        ]
    )

    # --------------------------------------------------------
    # Numeric model columns
    # --------------------------------------------------------

    for col in package[
        "numeric_model_columns"
    ]:

        if col in data.columns:

            data[col] = pd.to_numeric(
                data[col],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Numeric charge columns
    # --------------------------------------------------------

    for col in package[
        "numeric_charge_columns"
    ]:

        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        )

    data[
        package[
            "numeric_charge_columns"
        ]
    ] = data[
        package[
            "numeric_charge_columns"
        ]
    ].fillna(
        package[
            "numeric_charge_fill_value"
        ]
    )

    # --------------------------------------------------------
    # One-hot encoding
    # --------------------------------------------------------

    data = pd.get_dummies(
        data,
        columns=package[
            "one_hot_columns"
        ],
        drop_first=package[
            "drop_first"
        ]
    )

    # --------------------------------------------------------
    # bool -> int
    # --------------------------------------------------------

    bool_columns = data.select_dtypes(
        include="bool"
    ).columns

    data[
        bool_columns
    ] = data[
        bool_columns
    ].astype(int)

    # --------------------------------------------------------
    # Re-create missing dummy columns
    # AND remove unexpected columns
    # using the saved training feature order.
    # --------------------------------------------------------

    data = data.reindex(
        columns=package[
            "feature_order"
        ],
        fill_value=0
    )

    # --------------------------------------------------------
    # Final numeric type
    # --------------------------------------------------------

    data = data.astype(
        np.float32
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    nan_columns = data.columns[
        data.isnull().any()
    ].tolist()

    if nan_columns:

        print("\n" + "=" * 70)
        print(
            "NaN VALUES DETECTED AFTER TRANSFORMATION"
        )
        print("=" * 70)

        for col in nan_columns:

            print(
                f"\nColumn: {col}"
            )

            print(
                data.loc[
                    data[col].isnull(),
                    [col]
                ]
            )

        raise ValueError(
            "NaN values detected after transformation. "
            f"Columns: {nan_columns}"
        )

    # --------------------------------------------------------
    # Infinite-value validation
    # --------------------------------------------------------

    if np.isinf(
        data.to_numpy(
            dtype=np.float32
        )
    ).sum() > 0:

        raise ValueError(
            "Infinite values detected after transformation."
        )

    return data


# ============================================================
# 6. OPTIONAL PACKAGE CREATION TEST
# ============================================================

if __name__ == "__main__":

    import database as db

    engine = db.get_engine()

    raw_df = db.fetch_all_customers(
        engine
    )

    build_preprocessing_package(
        raw_df,
        "preprocessing_package.pkl"
    )