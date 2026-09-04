from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import get_engine


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Customer Churn & LTV Dashboard API",
    description="Backend API for the manager analytics dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HELPERS
# ============================================================

def safe_number(value: Any, default: float = 0.0) -> float:
    """Convert a database value into a safe float."""
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convert a database value into a safe integer."""
    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert SQLAlchemy row mappings into JSON-friendly dictionaries.
    """
    result = {}

    for key, value in row.items():
        if value is None:
            result[key] = None
        else:
            result[key] = value

    return result


def get_segment_data(
    column_name: str,
    alias_name: str,
) -> List[Dict[str, Any]]:
    """
    Return churn rate and customer count grouped by a trusted column.

    column_name and alias_name are selected internally and are not
    taken directly from the user.
    """

    allowed_columns = {
        "gender": "gender",
        "partner": "partner",
        "contract": "contract",
        "internetservice": "internetservice",
        "paymentmethod": "paymentmethod",
        "tenuregroup": "tenuregroup",
        "totalservices": "totalservices",
    }

    if column_name not in allowed_columns:
        raise ValueError("Invalid grouping column.")

    db_column = allowed_columns[column_name]

    sql = text(
        f"""
        SELECT
            {db_column} AS "{alias_name}",
            COUNT(*) AS customer_count,
            ROUND(
                100.0 * SUM(
                    CASE
                        WHEN LOWER(COALESCE(churn, '')) = 'yes' THEN 1
                        ELSE 0
                    END
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS churn_rate
        FROM public.customers
        GROUP BY {db_column}
        ORDER BY churn_rate DESC
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(sql).mappings().all()

    result = []

    for row in rows:
        item = normalize_row(dict(row))
        item["customer_count"] = safe_int(item.get("customer_count"))
        item["churn_rate"] = safe_number(item.get("churn_rate"))
        result.append(item)

    return result


# ============================================================
# ROOT / HEALTH
# ============================================================

@app.get("/")
def root() -> Dict[str, str]:
    return {
        "message": "Customer Churn & LTV Dashboard API",
        "status": "running",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    try:
        engine = get_engine()

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as exc:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc),
        }


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@app.get("/dashboard/summary")
def dashboard_summary() -> Dict[str, Any]:

    sql = text(
        """
        SELECT
            COUNT(*) AS total_customers,

            SUM(
                CASE
                    WHEN LOWER(COALESCE(churn, '')) = 'yes'
                    THEN 1
                    ELSE 0
                END
            ) AS churn_customers,

            SUM(
                CASE
                    WHEN LOWER(COALESCE(churn, '')) <> 'yes'
                    THEN 1
                    ELSE 0
                END
            ) AS retained_customers,

            AVG(monthlycharges) AS avg_monthly_charges,

            AVG(predicted_ltv) AS avg_predicted_ltv,

            SUM(predicted_ltv) AS total_predicted_ltv,

            SUM(
                CASE
                    WHEN churn_probability >= 0.70
                    THEN 1
                    ELSE 0
                END
            ) AS high_risk_customers,

            SUM(
                CASE
                    WHEN churn_probability >= 0.70
                     AND predicted_ltv >= 5000
                    THEN 1
                    ELSE 0
                END
            ) AS high_risk_high_ltv_customers

        FROM public.customers
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(sql).mappings().first()

    if row is None:
        return {
            "total_customers": 0,
            "churn_customers": 0,
            "retained_customers": 0,
            "churn_rate": 0.0,
            "high_risk_customers": 0,
            "high_risk_high_ltv_customers": 0,
            "avg_monthly_charges": 0.0,
            "avg_predicted_ltv": 0.0,
            "total_predicted_ltv": 0.0,
        }

    total_customers = safe_int(row["total_customers"])
    churn_customers = safe_int(row["churn_customers"])

    if total_customers > 0:
        churn_rate = round(
            (churn_customers / total_customers) * 100,
            2,
        )
    else:
        churn_rate = 0.0

    return {
        "total_customers": total_customers,
        "churn_customers": churn_customers,
        "retained_customers": safe_int(row["retained_customers"]),
        "churn_rate": churn_rate,
        "high_risk_customers": safe_int(row["high_risk_customers"]),
        "high_risk_high_ltv_customers": safe_int(
            row["high_risk_high_ltv_customers"]
        ),
        "avg_monthly_charges": safe_number(
            row["avg_monthly_charges"]
        ),
        "avg_predicted_ltv": safe_number(
            row["avg_predicted_ltv"]
        ),
        "total_predicted_ltv": safe_number(
            row["total_predicted_ltv"]
        ),
    }


# ============================================================
# ALL CUSTOMERS
# ============================================================

@app.get("/dashboard/customers")
def dashboard_customers(
    limit: int = Query(
        default=100,
        ge=1,
        le=10000,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> Dict[str, Any]:

    data_sql = text(
        """
        SELECT
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
            churn,
            tenuregroup,
            totalservices,
            churn_probability,
            predicted_ltv,
            prediction_at
        FROM public.customers
        ORDER BY
            COALESCE(prediction_at, updated_at) DESC NULLS LAST,
            customerid
        LIMIT :limit
        OFFSET :offset
        """
    )

    count_sql = text(
        """
        SELECT COUNT(*) AS total
        FROM public.customers
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(
            data_sql,
            {
                "limit": limit,
                "offset": offset,
            },
        ).mappings().all()

        count_row = connection.execute(
            count_sql
        ).mappings().first()

    customers = []

    for row in rows:
        item = normalize_row(dict(row))

        if item.get("seniorcitizen") is not None:
            item["seniorcitizen"] = safe_int(
                item["seniorcitizen"]
            )

        if item.get("tenure") is not None:
            item["tenure"] = safe_int(
                item["tenure"]
            )

        item["monthlycharges"] = safe_number(
            item.get("monthlycharges")
        )

        item["totalcharges"] = safe_number(
            item.get("totalcharges")
        )

        item["churn_probability"] = safe_number(
            item.get("churn_probability")
        )

        item["predicted_ltv"] = safe_number(
            item.get("predicted_ltv")
        )

        item["totalservices"] = safe_int(
            item.get("totalservices")
        )

        customers.append(item)

    total = 0

    if count_row is not None:
        total = safe_int(count_row["total"])

    return {
        "customers": customers,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ============================================================
# SINGLE CUSTOMER
# ============================================================

@app.get("/dashboard/customer/{customerid}")
def dashboard_customer(customerid: str) -> Dict[str, Any]:

    sql = text(
        """
        SELECT
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
            churn,
            tenuregroup,
            totalservices,
            churn_probability,
            predicted_ltv,
            prediction_at
        FROM public.customers
        WHERE customerid = :customerid
        LIMIT 1
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(
            sql,
            {"customerid": customerid},
        ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    customer = normalize_row(dict(row))

    customer["seniorcitizen"] = safe_int(
        customer.get("seniorcitizen")
    )

    customer["tenure"] = safe_int(
        customer.get("tenure")
    )

    customer["monthlycharges"] = safe_number(
        customer.get("monthlycharges")
    )

    customer["totalcharges"] = safe_number(
        customer.get("totalcharges")
    )

    customer["totalservices"] = safe_int(
        customer.get("totalservices")
    )

    customer["churn_probability"] = safe_number(
        customer.get("churn_probability")
    )

    customer["predicted_ltv"] = safe_number(
        customer.get("predicted_ltv")
    )

    return {
        "customer": customer
    }


# ============================================================
# CUSTOMER RISK PROFILE
# ============================================================

@app.get("/dashboard/customer/{customerid}/risk-profile")
def customer_risk_profile(customerid: str) -> Dict[str, Any]:

    customer_response = dashboard_customer(customerid)
    customer = customer_response["customer"]

    probability = safe_number(
        customer.get("churn_probability")
    )

    if probability >= 0.70:
        risk_level = "High"
    elif probability >= 0.40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    indicators = []

    if customer.get("contract") == "Month-to-month":
        indicators.append(
            "Month-to-month contract"
        )

    if customer.get("paymentmethod") == "Electronic check":
        indicators.append(
            "Electronic check payment method"
        )

    if customer.get("onlinesecurity") == "No":
        indicators.append(
            "Online security not subscribed"
        )

    if customer.get("techsupport") == "No":
        indicators.append(
            "Tech support not subscribed"
        )

    if customer.get("tenure") is not None:
        if safe_int(customer.get("tenure")) <= 12:
            indicators.append(
                "Relatively short customer tenure"
            )

    if customer.get("monthlycharges") is not None:
        if safe_number(customer.get("monthlycharges")) >= 80:
            indicators.append(
                "Higher monthly charges"
            )

    return {
        "customerid": customerid,
        "risk_level": risk_level,
        "churn_probability": probability,
        "observed_risk_indicators": indicators,
        "note": (
            "These are observed customer attributes associated with "
            "the customer's profile. They are not presented as causal explanations."
        ),
    }


# ============================================================
# CHURN RISK DISTRIBUTION
# ============================================================

@app.get("/dashboard/churn-risk")
def churn_risk() -> Dict[str, Any]:

    sql = text(
        """
        SELECT
            CASE
                WHEN churn_probability >= 0.70 THEN 'High'
                WHEN churn_probability >= 0.40 THEN 'Medium'
                ELSE 'Low'
            END AS risk_level,
            COUNT(*) AS customer_count
        FROM public.customers
        WHERE churn_probability IS NOT NULL
        GROUP BY
            CASE
                WHEN churn_probability >= 0.70 THEN 'High'
                WHEN churn_probability >= 0.40 THEN 'Medium'
                ELSE 'Low'
            END
        ORDER BY
            CASE
                WHEN
                    CASE
                        WHEN churn_probability >= 0.70 THEN 'High'
                        WHEN churn_probability >= 0.40 THEN 'Medium'
                        ELSE 'Low'
                    END = 'High'
                THEN 1

                WHEN
                    CASE
                        WHEN churn_probability >= 0.70 THEN 'High'
                        WHEN churn_probability >= 0.40 THEN 'Medium'
                        ELSE 'Low'
                    END = 'Medium'
                THEN 2

                ELSE 3
            END
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(sql).mappings().all()

    risk_distribution = []

    for row in rows:
        risk_distribution.append(
            {
                "risk_level": row["risk_level"],
                "customer_count": safe_int(
                    row["customer_count"]
                ),
            }
        )

    return {
        "risk_distribution": risk_distribution
    }


# ============================================================
# LTV SEGMENTS
# ============================================================

@app.get("/dashboard/ltv-segments")
def ltv_segments() -> Dict[str, Any]:

    sql = text(
        """
        SELECT
            CASE
                WHEN predicted_ltv < 2000 THEN 'Low'
                WHEN predicted_ltv < 5000 THEN 'Medium'
                ELSE 'High'
            END AS ltv_segment,
            COUNT(*) AS customer_count,
            AVG(predicted_ltv) AS avg_ltv
        FROM public.customers
        WHERE predicted_ltv IS NOT NULL
        GROUP BY
            CASE
                WHEN predicted_ltv < 2000 THEN 'Low'
                WHEN predicted_ltv < 5000 THEN 'Medium'
                ELSE 'High'
            END
        ORDER BY
            CASE
                WHEN
                    CASE
                        WHEN predicted_ltv < 2000 THEN 'Low'
                        WHEN predicted_ltv < 5000 THEN 'Medium'
                        ELSE 'High'
                    END = 'High'
                THEN 1

                WHEN
                    CASE
                        WHEN predicted_ltv < 2000 THEN 'Low'
                        WHEN predicted_ltv < 5000 THEN 'Medium'
                        ELSE 'High'
                    END = 'Medium'
                THEN 2

                ELSE 3
            END
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(sql).mappings().all()

    segments = []

    for row in rows:
        segments.append(
            {
                "ltv_segment": row["ltv_segment"],
                "customer_count": safe_int(
                    row["customer_count"]
                ),
                "avg_ltv": safe_number(
                    row["avg_ltv"]
                ),
            }
        )

    return {
        "ltv_segments": segments
    }


# ============================================================
# PRIORITY CUSTOMERS
# ============================================================

@app.get("/dashboard/priority-customers")
def priority_customers() -> Dict[str, Any]:

    sql = text(
        """
        SELECT
            customerid,
            churn_probability,
            predicted_ltv,
            contract,
            tenure,
            monthlycharges,
            internetservice,
            paymentmethod,
            onlinesecurity,
            techsupport
        FROM public.customers
        WHERE churn_probability >= 0.70
          AND predicted_ltv >= 5000
        ORDER BY
            churn_probability DESC,
            predicted_ltv DESC
        LIMIT 20
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(sql).mappings().all()

    result = []

    for row in rows:
        item = normalize_row(dict(row))

        item["churn_probability"] = safe_number(
            item.get("churn_probability")
        )

        item["predicted_ltv"] = safe_number(
            item.get("predicted_ltv")
        )

        item["tenure"] = safe_int(
            item.get("tenure")
        )

        item["monthlycharges"] = safe_number(
            item.get("monthlycharges")
        )

        result.append(item)

    return {
        "priority_customers": result
    }


# ============================================================
# GENDER
# ============================================================

@app.get("/dashboard/churn-by-gender")
def churn_by_gender() -> Dict[str, Any]:
    return {
        "data": get_segment_data(
            "gender",
            "gender",
        )
    }


# ============================================================
# CONTRACT
# ============================================================

@app.get("/dashboard/churn-by-contract")
def churn_by_contract() -> Dict[str, Any]:
    return {
        "data": get_segment_data(
            "contract",
            "contract",
        )
    }


# ============================================================
# INTERNET SERVICE
# ============================================================

@app.get("/dashboard/churn-by-internet")
def churn_by_internet() -> Dict[str, Any]:
    return {
        "data": get_segment_data(
            "internetservice",
            "internet_service",
        )
    }


# ============================================================
# PARTNER
# ============================================================

@app.get("/dashboard/churn-by-partner")
def churn_by_partner() -> Dict[str, Any]:
    return {
        "data": get_segment_data(
            "partner",
            "partner",
        )
    }


# ============================================================
# TENURE
# ============================================================

@app.get("/dashboard/churn-by-tenure")
def churn_by_tenure() -> Dict[str, Any]:
    return {
        "data": get_segment_data(
            "tenuregroup",
            "tenure_segment",
        )
    }


# ============================================================
# PAYMENT METHOD
# ============================================================

@app.get("/dashboard/churn-by-payment")
def churn_by_payment() -> Dict[str, Any]:
    return {
        "data": get_segment_data(
            "paymentmethod",
            "payment_method",
        )
    }


# ============================================================
# TOTAL SERVICES
# ============================================================

@app.get("/dashboard/churn-by-services")
def churn_by_services() -> Dict[str, Any]:
    return {
        "data": get_segment_data(
            "totalservices",
            "total_services",
        )
    }


# ============================================================
# CHURN BY MONTHLY CHARGES
# ============================================================

@app.get("/dashboard/churn-by-charges")
def churn_by_charges() -> Dict[str, Any]:

    sql = text(
        """
        SELECT
            CASE
                WHEN monthlycharges < 40 THEN 'Below ₹40'
                WHEN monthlycharges < 60 THEN '₹40-₹60'
                WHEN monthlycharges < 80 THEN '₹60-₹80'
                WHEN monthlycharges < 100 THEN '₹80-₹100'
                ELSE '₹100+'
            END AS charge_band,

            COUNT(*) AS customer_count,

            ROUND(
                100.0 * SUM(
                    CASE
                        WHEN LOWER(COALESCE(churn, '')) = 'yes'
                        THEN 1
                        ELSE 0
                    END
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS churn_rate

        FROM public.customers

        WHERE monthlycharges IS NOT NULL

        GROUP BY
            CASE
                WHEN monthlycharges < 40 THEN 'Below ₹40'
                WHEN monthlycharges < 60 THEN '₹40-₹60'
                WHEN monthlycharges < 80 THEN '₹60-₹80'
                WHEN monthlycharges < 100 THEN '₹80-₹100'
                ELSE '₹100+'
            END

        ORDER BY MIN(monthlycharges)
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(sql).mappings().all()

    result = []

    for row in rows:
        result.append(
            {
                "charge_band": row["charge_band"],
                "customer_count": safe_int(
                    row["customer_count"]
                ),
                "churn_rate": safe_number(
                    row["churn_rate"]
                ),
            }
        )

    return {
        "data": result
    }


# ============================================================
# RISK × LTV MATRIX
# ============================================================

@app.get("/dashboard/risk-ltv-matrix")
def risk_ltv_matrix() -> Dict[str, Any]:

    sql = text(
        """
        SELECT
            customerid,
            churn_probability,
            predicted_ltv
        FROM public.customers
        WHERE churn_probability IS NOT NULL
          AND predicted_ltv IS NOT NULL
        ORDER BY churn_probability DESC
        LIMIT 10000
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(sql).mappings().all()

    customers = []

    for row in rows:
        customers.append(
            {
                "customerid": row["customerid"],
                "churn_probability": safe_number(
                    row["churn_probability"]
                ),
                "predicted_ltv": safe_number(
                    row["predicted_ltv"]
                ),
            }
        )

    return {
        "customers": customers
    }


# ============================================================
# REVENUE AT RISK
# ============================================================

@app.get("/dashboard/revenue-at-risk")
def revenue_at_risk() -> Dict[str, Any]:

    sql = text(
        """
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN churn_probability >= 0.70
                        THEN predicted_ltv
                        ELSE 0
                    END
                ),
                0
            ) AS high_risk_ltv,

            COALESCE(
                SUM(
                    CASE
                        WHEN churn_probability >= 0.40
                         AND churn_probability < 0.70
                        THEN predicted_ltv
                        ELSE 0
                    END
                ),
                0
            ) AS medium_risk_ltv,

            COALESCE(
                SUM(
                    CASE
                        WHEN churn_probability < 0.40
                        THEN predicted_ltv
                        ELSE 0
                    END
                ),
                0
            ) AS low_risk_ltv,

            COALESCE(
                SUM(predicted_ltv),
                0
            ) AS total_ltv

        FROM public.customers
        WHERE predicted_ltv IS NOT NULL
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(sql).mappings().first()

    if row is None:
        return {
            "high_risk_ltv": 0.0,
            "medium_risk_ltv": 0.0,
            "low_risk_ltv": 0.0,
            "total_ltv": 0.0,
        }

    return {
        "high_risk_ltv": safe_number(
            row["high_risk_ltv"]
        ),
        "medium_risk_ltv": safe_number(
            row["medium_risk_ltv"]
        ),
        "low_risk_ltv": safe_number(
            row["low_risk_ltv"]
        ),
        "total_ltv": safe_number(
            row["total_ltv"]
        ),
    }


# ============================================================
# EXECUTIVE INSIGHTS
# ============================================================

@app.get("/dashboard/executive-insights")
def executive_insights() -> Dict[str, Any]:

    contract_data = get_segment_data(
        "contract",
        "contract",
    )

    tenure_data = get_segment_data(
        "tenuregroup",
        "tenure_segment",
    )

    # Highest observed churn-rate contract group.
    largest_contract_risk = None

    if contract_data:
        largest_contract_risk = contract_data[0]

    # Highest observed churn-rate tenure group.
    largest_tenure_risk = None

    if tenure_data:
        largest_tenure_risk = tenure_data[0]

    service_sql = text(
        """
        SELECT
            CASE
                WHEN COALESCE(onlinesecurity, 'No') = 'No'
                THEN 'Without Online Security'
                ELSE 'With Online Security'
            END AS service_group,

            COUNT(*) AS customer_count,

            ROUND(
                100.0 * SUM(
                    CASE
                        WHEN LOWER(COALESCE(churn, '')) = 'yes'
                        THEN 1
                        ELSE 0
                    END
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS churn_rate

        FROM public.customers

        GROUP BY
            CASE
                WHEN COALESCE(onlinesecurity, 'No') = 'No'
                THEN 'Without Online Security'
                ELSE 'With Online Security'
            END

        ORDER BY churn_rate DESC
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        service_rows = connection.execute(
            service_sql
        ).mappings().all()

    service_gap = None

    if service_rows:
        service_gap_row = dict(service_rows[0])

        service_gap = {
            "service_group": service_gap_row["service_group"],
            "customer_count": safe_int(
                service_gap_row["customer_count"]
            ),
            "churn_rate": safe_number(
                service_gap_row["churn_rate"]
            ),
        }

    headline = (
        "Customer churn and lifetime value require simultaneous "
        "risk and value monitoring."
    )

    if largest_contract_risk:
        contract_name = largest_contract_risk["contract"]
        contract_rate = safe_number(
            largest_contract_risk["churn_rate"]
        )

        headline = (
            f"{contract_name} customers show the highest observed "
            f"contract-level churn rate at {contract_rate:.2f}%."
        )

    return {
        "headline": headline,
        "largest_contract_risk": largest_contract_risk,
        "largest_tenure_risk": largest_tenure_risk,
        "service_gap": service_gap,
    }


# ============================================================
# RECENT PREDICTIONS
# ============================================================

@app.get("/dashboard/recent-predictions")
def recent_predictions(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> Dict[str, Any]:

    sql = text(
        """
        SELECT
            customerid,
            churn,
            churn_probability,
            predicted_ltv,
            prediction_at
        FROM public.customers
        WHERE prediction_at IS NOT NULL
        ORDER BY prediction_at DESC
        LIMIT :limit
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {"limit": limit},
        ).mappings().all()

    result = []

    for row in rows:
        result.append(
            {
                "customerid": row["customerid"],
                "churn": row["churn"],
                "churn_probability": safe_number(
                    row["churn_probability"]
                ),
                "predicted_ltv": safe_number(
                    row["predicted_ltv"]
                ),
                "prediction_at": row["prediction_at"],
            }
        )

    return {
        "predictions": result
    }


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "dashboard_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )