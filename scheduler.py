# ============================================================
# scheduler.py
#
# PURPOSE
# ------------------------------------------------------------
# Runs the Churn + LTV prediction pipeline every 5 minutes.
#
# IMPORTANT:
# ------------------------------------------------------------
# The scheduler now WAITs 5 minutes BEFORE the first run.
#
# Therefore:
#
#   Start scheduler
#          ↓
#       WAIT 5 MIN
#          ↓
#      Run pipeline
#          ↓
#       WAIT 5 MIN
#          ↓
#      Run pipeline
#          ↓
#          ...
#
# ============================================================


import time
import traceback

from datetime import datetime

from main import run_pipeline


# ============================================================
# CONFIGURATION
# ============================================================

INTERVAL_SECONDS = 5 * 60


# ============================================================
# RUN ONE PIPELINE
# ============================================================

def run_scheduled_pipeline():

    start_time = datetime.now()


    print()
    print("=" * 70)
    print("SCHEDULED RUN")
    print("=" * 70)


    print(
        "Started:",
        start_time
    )


    try:

        run_pipeline()


        print()
        print(
            "Pipeline run finished successfully."
        )


    except Exception as error:

        print()
        print(
            "PIPELINE FAILED"
        )


        print(
            "Error:",
            error
        )


        traceback.print_exc()


# ============================================================
# START SCHEDULER
# ============================================================

def start_scheduler():

    print()
    print("=" * 70)
    print("CHURN + LTV SCHEDULER STARTED")
    print("=" * 70)


    print(
        "Interval: 5 minutes"
    )


    print(
        "The first pipeline run will start "
        "after 5 minutes."
    )


    print(
        "Press CTRL+C to stop the scheduler."
    )


    # ========================================================
    # WAIT BEFORE FIRST RUN
    # ========================================================

    try:

        while True:

            print()
            print(
                "-" * 70
            )

            print(
                "Waiting 5 minutes "
                "before next pipeline run..."
            )

            print(
                "Next run:",
                datetime.now()
            )

            print(
                "-" * 70
            )


            # ------------------------------------------------
            # WAIT 5 MINUTES
            # ------------------------------------------------

            time.sleep(
                INTERVAL_SECONDS
            )


            # ------------------------------------------------
            # RUN PIPELINE
            # ------------------------------------------------

            run_scheduled_pipeline()


    except KeyboardInterrupt:

        print()
        print(
            "Scheduler stopped by user."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        start_scheduler()


    except Exception:

        print()
        print(
            "SCHEDULER FAILED TO START"
        )

        traceback.print_exc()