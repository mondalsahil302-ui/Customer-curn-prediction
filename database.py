# ============================================================
# database.py
#
# PURPOSE:
#   Database connection and database read/write operations.
#
# IMPORTANT:
#   - No ML logic here.
#   - No preprocessing here.
#   - No five-minute scheduling here.
#   - Credentials come from .env.
# ============================================================

import os

import pandas as pd

from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_engine():
    """
    Create and return the SQLAlchemy engine for Neon PostgreSQL.
    """

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")

    # --------------------------------------------------------
    # Validate credentials
    # --------------------------------------------------------

    if not all(
        [
            db_user,
            db_password,
            db_host,
            db_name
        ]
    ):
        raise ValueError(
            "Database credentials are missing. "
            "Check your .env file."
        )

    # --------------------------------------------------------
    # Neon PostgreSQL connection
    # --------------------------------------------------------

    engine = create_engine(
        (
            "postgresql+psycopg2://"
            f"{db_user}:{db_password}@"
            f"{db_host}:{db_port}/{db_name}"
            "?sslmode=require"
        ),
        pool_pre_ping=True,
        pool_recycle=300
    )

    return engine


# ============================================================
# TEST CONNECTION
# ============================================================

def test_connection(engine=None):
    """
    Test the PostgreSQL connection.
    """

    if engine is None:
        engine = get_engine()

    with engine.connect():
        print(
            "PostgreSQL connected successfully!"
        )

    return True


# ============================================================
# FETCH CUSTOMERS CHANGED DURING A WINDOW
# ============================================================

def fetch_customers_in_window(
    window_start,
    window_end,
    engine=None
):
    """
    Fetch customers whose updated_at falls inside
    the supplied processing window.

    New rows and updated rows are handled the same way:
    they are expected to have churn = NULL until prediction
    is completed.
    """

    if engine is None:
        engine = get_engine()

    query = text(
        """
        SELECT *
        FROM public.customers
        WHERE updated_at > :window_start
          AND updated_at <= :window_end
          AND churn IS NULL
        ORDER BY updated_at, customerid
        """
    )

    df = pd.read_sql(
        query,
        engine,
        params={
            "window_start": window_start,
            "window_end": window_end
        }
    )

    print(
        f"Fetched {len(df)} customers "
        f"from the current processing window."
    )

    return df


# ============================================================
# WRITE PREDICTIONS
# ============================================================

def write_predictions(
    result,
    engine=None
):
    """
    Write churn and LTV predictions back to customers.
    """

    if engine is None:
        engine = get_engine()

    if result.empty:

        print(
            "No predictions to update."
        )

        return

    sql = text(
        """
        UPDATE public.customers

        SET
            churn = :churn,
            churn_probability = :churn_probability,
            predicted_ltv = :predicted_ltv,
            prediction_at = CURRENT_TIMESTAMP

        WHERE customerid = :customerid
        """
    )

    records = (
        result[
            [
                "customerid",
                "churn",
                "churn_probability",
                "predicted_ltv"
            ]
        ]
        .to_dict(
            orient="records"
        )
    )

    with engine.begin() as connection:

        connection.execute(
            sql,
            records
        )

    print(
        f"Updated {len(records)} customers "
        f"with predictions."
    )