# ============================================================
# change_tracker.py
#
# PURPOSE
# ------------------------------------------------------------
# Keeps track of the Python-side pipeline checkpoint.
#
# The checkpoint is stored locally in:
#
#     pipeline_state.json
#
# The database does NOT maintain the pipeline checkpoint.
#
# TIME STANDARD
# ------------------------------------------------------------
# All timestamps used by this file are UTC.
#
# We store UTC as a timezone-aware ISO timestamp so that
# local machine time and Neon PostgreSQL time cannot become
# mixed accidentally.
# ============================================================

import json

from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

STATE_FILE = Path(
    "pipeline_state.json"
)


# ============================================================
# GET CURRENT UTC TIME
# ============================================================

def get_current_utc_time():
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(
        timezone.utc
    )


# ============================================================
# LOAD LAST SUCCESSFUL RUN
# ============================================================

def load_last_successful_run():
    """
    Read the previous successful pipeline timestamp.

    Returns:
        datetime | None
    """

    if not STATE_FILE.exists():

        return None


    try:

        with STATE_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            state = json.load(
                file
            )


        saved_time = state.get(
            "last_successful_run"
        )


        if not saved_time:

            return None


        parsed_time = datetime.fromisoformat(
            saved_time
        )


        # ----------------------------------------------------
        # Make old naive timestamps UTC-aware.
        # ----------------------------------------------------

        if parsed_time.tzinfo is None:

            parsed_time = (
                parsed_time.replace(
                    tzinfo=timezone.utc
                )
            )


        return parsed_time.astimezone(
            timezone.utc
        )


    except Exception as error:

        raise RuntimeError(
            "Could not read pipeline_state.json."
        ) from error


# ============================================================
# SAVE LAST SUCCESSFUL RUN
# ============================================================

def save_last_successful_run(
    run_time
):
    """
    Save the successful pipeline completion time.
    """

    if run_time.tzinfo is None:

        run_time = run_time.replace(
            tzinfo=timezone.utc
        )

    run_time = run_time.astimezone(
        timezone.utc
    )


    state = {

        "last_successful_run":
            run_time.isoformat()

    }


    temporary_file = (
        STATE_FILE.with_suffix(
            ".tmp"
        )
    )


    try:

        with temporary_file.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                state,
                file,
                indent=4
            )


        temporary_file.replace(
            STATE_FILE
        )


    except Exception as error:

        raise RuntimeError(
            "Could not save pipeline_state.json."
        ) from error


# ============================================================
# CREATE PROCESSING WINDOW
# ============================================================

def create_processing_window():
    """
    Create the processing window:

        previous successful run
                    ↓
              current UTC time

    First run:
        1970-01-01 → current UTC time
    """

    window_end = (
        get_current_utc_time()
    )


    window_start = (
        load_last_successful_run()
    )


    # --------------------------------------------------------
    # FIRST RUN
    # --------------------------------------------------------

    if window_start is None:

        window_start = datetime(
            1970,
            1,
            1,
            tzinfo=timezone.utc
        )


    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if window_end <= window_start:

        print()
        print("=" * 70)

        print(
            "WARNING: INVALID PIPELINE CHECKPOINT"
        )

        print(
            "Previous checkpoint:",
            window_start
        )

        print(
            "Current UTC time    :",
            window_end
        )

        print("=" * 70)

        raise ValueError(
            "Pipeline checkpoint is in the future. "
            "Delete pipeline_state.json and run again."
        )


    return (
        window_start,
        window_end
    )


# ============================================================
# DISPLAY PROCESSING WINDOW
# ============================================================

def print_processing_window(
    window_start,
    window_end
):
    """
    Print the current processing window.
    """

    print()
    print(
        "-" * 70
    )

    print(
        "CHANGE DETECTION WINDOW"
    )

    print(
        "-" * 70
    )

    print(
        "Window start:",
        window_start
    )

    print(
        "Window end  :",
        window_end
    )

    print(
        "-" * 70
    )