# ============================================================
# test_data_generator.py
#
# PURPOSE
# ------------------------------------------------------------
# Generate controlled test activity for the project:
#
#   1. Update 150 existing customers
#   2. Insert 50 new customers
#
# This file DOES NOT:
#   - Run the ML models
#   - Run preprocessing
#   - Run scheduler.py
#   - Generate churn predictions
#   - Generate LTV predictions
#
# It only creates database changes.
# ============================================================

import random

import pandas as pd

from sqlalchemy import text

import database as db


# ============================================================
# CONFIGURATION
# ============================================================

NUMBER_OF_UPDATES = 150

NUMBER_OF_INSERTS = 50

GENERATED_ID_PREFIX = "TEST-GEN-"


# ============================================================
# POSSIBLE VALUES
# ============================================================

GENDERS = [
    "Male",
    "Female"
]

YES_NO = [
    "Yes",
    "No"
]

INTERNET_SERVICES = [
    "DSL",
    "Fiber optic",
    "No"
]

SERVICE_VALUES = [
    "Yes",
    "No"
]

CONTRACTS = [
    "Month-to-month",
    "One year",
    "Two year"
]

PAYMENT_METHODS = [
    "Electronic check",
    "Mailed check",
    "Bank transfer (automatic)",
    "Credit card (automatic)"
]


# ============================================================
# TENURE GROUP
# ============================================================

def get_tenure_group(tenure):

    if tenure <= 12:
        return "0-1 Year"

    if tenure <= 24:
        return "1-2 Years"

    if tenure <= 48:
        return "2-4 Years"

    return "4-6 Years"


# ============================================================
# RANDOM CUSTOMER VALUES
# ============================================================

def generate_customer_values():

    tenure = random.randint(
        1,
        72
    )

    monthly_charges = round(
        random.uniform(
            30.00,
            120.00
        ),
        2
    )

    total_charges = round(
        monthly_charges * tenure,
        2
    )

    total_services = random.randint(
        1,
        7
    )

    return {

        "gender":
            random.choice(
                GENDERS
            ),

        "seniorcitizen":
            random.randint(
                0,
                1
            ),

        "partner":
            random.choice(
                YES_NO
            ),

        "dependents":
            random.choice(
                YES_NO
            ),

        "tenure":
            tenure,

        "phoneservice":
            random.choice(
                YES_NO
            ),

        "multiplelines":
            random.choice(
                YES_NO
            ),

        "internetservice":
            random.choice(
                INTERNET_SERVICES
            ),

        "onlinesecurity":
            random.choice(
                SERVICE_VALUES
            ),

        "onlinebackup":
            random.choice(
                SERVICE_VALUES
            ),

        "deviceprotection":
            random.choice(
                SERVICE_VALUES
            ),

        "techsupport":
            random.choice(
                SERVICE_VALUES
            ),

        "streamingtv":
            random.choice(
                SERVICE_VALUES
            ),

        "streamingmovies":
            random.choice(
                SERVICE_VALUES
            ),

        "contract":
            random.choice(
                CONTRACTS
            ),

        "paperlessbilling":
            random.choice(
                YES_NO
            ),

        "paymentmethod":
            random.choice(
                PAYMENT_METHODS
            ),

        "monthlycharges":
            monthly_charges,

        "totalcharges":
            total_charges,

        "tenuregroup":
            get_tenure_group(
                tenure
            ),

        "totalservices":
            total_services

    }


# ============================================================
# GENERATE CUSTOMER ID
# ============================================================

def generate_customer_id(number):

    return (
        f"{GENERATED_ID_PREFIX}"
        f"{number:04d}"
    )


# ============================================================
# FETCH EXISTING CUSTOMER IDS
# ============================================================

def fetch_existing_customer_ids(
    engine
):

    query = text(
        """
        SELECT customerid
        FROM public.customers
        """
    )

    result = pd.read_sql(
        query,
        engine
    )

    return (
        result[
            "customerid"
        ]
        .astype(str)
        .tolist()
    )


# ============================================================
# UPDATE EXISTING CUSTOMERS
# ============================================================

def update_existing_customers(
    engine,
    number_of_updates
):

    existing_ids = (
        fetch_existing_customer_ids(
            engine
        )
    )

    if len(existing_ids) < number_of_updates:

        raise ValueError(
            f"Only {len(existing_ids)} existing customers "
            f"are available, but {number_of_updates} "
            f"updates were requested."
        )

    selected_ids = random.sample(
        existing_ids,
        number_of_updates
    )


    # --------------------------------------------------------
    # IMPORTANT
    #
    # updated_at is explicitly set here.
    #
    # This guarantees that the changed rows are visible to
    # change_tracker.py during the next processing window.
    # --------------------------------------------------------

    update_sql = text(
        """
        UPDATE public.customers

        SET
            gender = :gender,
            seniorcitizen = :seniorcitizen,
            partner = :partner,
            dependents = :dependents,
            tenure = :tenure,
            phoneservice = :phoneservice,
            multiplelines = :multiplelines,
            internetservice = :internetservice,
            onlinesecurity = :onlinesecurity,
            onlinebackup = :onlinebackup,
            deviceprotection = :deviceprotection,
            techsupport = :techsupport,
            streamingtv = :streamingtv,
            streamingmovies = :streamingmovies,
            contract = :contract,
            paperlessbilling = :paperlessbilling,
            paymentmethod = :paymentmethod,
            monthlycharges = :monthlycharges,
            totalcharges = :totalcharges,
            tenuregroup = :tenuregroup,
            totalservices = :totalservices,

            updated_at = CURRENT_TIMESTAMP

        WHERE customerid = :customerid
        """
    )


    records = []


    for customer_id in selected_ids:

        values = (
            generate_customer_values()
        )

        values[
            "customerid"
        ] = customer_id

        records.append(
            values
        )


    with engine.begin() as connection:

        connection.execute(
            update_sql,
            records
        )


    print(
        f"Updated {len(records)} existing customers."
    )


    return selected_ids


# ============================================================
# INSERT NEW CUSTOMERS
# ============================================================

def insert_new_customers(
    engine,
    number_of_inserts,
    existing_ids
):

    insert_sql = text(
        """
        INSERT INTO public.customers (

            customerid,
            gender,
            seniorcitizen,
            partner,
            dependents,
            tenure,
            phoneservice,
            multiplelines,
            internetservice,
            onlinesecurity,
            onlinebackup,
            deviceprotection,
            techsupport,
            streamingtv,
            streamingmovies,
            contract,
            paperlessbilling,
            paymentmethod,
            monthlycharges,
            totalcharges,
            tenuregroup,
            totalservices

        )

        VALUES (

            :customerid,
            :gender,
            :seniorcitizen,
            :partner,
            :dependents,
            :tenure,
            :phoneservice,
            :multiplelines,
            :internetservice,
            :onlinesecurity,
            :onlinebackup,
            :deviceprotection,
            :techsupport,
            :streamingtv,
            :streamingmovies,
            :contract,
            :paperlessbilling,
            :paymentmethod,
            :monthlycharges,
            :totalcharges,
            :tenuregroup,
            :totalservices

        )
        """
    )


    records = []

    next_number = 1


    while len(records) < number_of_inserts:

        customer_id = (
            generate_customer_id(
                next_number
            )
        )

        next_number += 1


        if customer_id in existing_ids:

            continue


        values = (
            generate_customer_values()
        )

        values[
            "customerid"
        ] = customer_id

        records.append(
            values
        )

        existing_ids.append(
            customer_id
        )


    with engine.begin() as connection:

        connection.execute(
            insert_sql,
            records
        )


    print(
        f"Inserted {len(records)} new customers."
    )


    return [
        record[
            "customerid"
        ]
        for record in records
    ]


# ============================================================
# GENERATE TEST DATA
# ============================================================

def generate_test_data():

    print()
    print("=" * 70)
    print("TEST DATA GENERATOR")
    print("=" * 70)


    # --------------------------------------------------------
    # Connect to Neon
    # --------------------------------------------------------

    print()
    print(
        "Connecting to Neon PostgreSQL..."
    )

    engine = db.get_engine()

    db.test_connection(
        engine
    )


    # --------------------------------------------------------
    # Existing customers
    # --------------------------------------------------------

    existing_ids = (
        fetch_existing_customer_ids(
            engine
        )
    )


    print(
        f"Existing customers available: "
        f"{len(existing_ids)}"
    )


    # --------------------------------------------------------
    # Update 150 existing customers
    # --------------------------------------------------------

    print()
    print(
        "Updating existing customers..."
    )

    updated_ids = (
        update_existing_customers(
            engine,
            NUMBER_OF_UPDATES
        )
    )


    # --------------------------------------------------------
    # Insert 50 new customers
    # --------------------------------------------------------

    print()
    print(
        "Inserting new customers..."
    )

    inserted_ids = (
        insert_new_customers(
            engine,
            NUMBER_OF_INSERTS,
            existing_ids
        )
    )


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total = (
        len(updated_ids)
        + len(inserted_ids)
    )


    print()
    print("=" * 70)
    print("TEST DATA GENERATION COMPLETED")
    print("=" * 70)

    print(
        f"Existing customers updated : "
        f"{len(updated_ids)}"
    )

    print(
        f"New customers inserted     : "
        f"{len(inserted_ids)}"
    )

    print(
        f"Total affected customers   : "
        f"{total}"
    )

    print()
    print(
        "Ready for scheduler processing."
    )

    return {
        "updated": updated_ids,
        "inserted": inserted_ids
    }


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    generate_test_data()