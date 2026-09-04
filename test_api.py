# ============================================================
# test_api.py
#
# PURPOSE
# ------------------------------------------------------------
# FastAPI backend for the test-data generator.
#
# Frontend:
#     test_console.html
#
# Endpoint:
#     POST /generate-test-data
#
# This API ONLY starts the test-data generator.
# It does NOT run the ML models.
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import test_data_generator


# ============================================================
# CREATE FASTAPI APP
# ============================================================

app = FastAPI(
    title="Churn LTV Test Data API",
    description="API for generating test customer activity.",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():

    return {
        "status": "running",
        "service": "Churn + LTV Test Data API"
    }


# ============================================================
# GENERATE TEST DATA
# ============================================================

@app.post("/generate-test-data")
def generate_test_data():

    result = (
        test_data_generator
        .generate_test_data()
    )

    return {
        "success": True,

        "updated":
            len(
                result["updated"]
            ),

        "inserted":
            len(
                result["inserted"]
            ),

        "total":
            (
                len(result["updated"])
                +
                len(result["inserted"])
            )
    }