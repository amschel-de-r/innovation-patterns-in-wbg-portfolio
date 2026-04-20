"""Shared fixtures and utilities for replication tests."""
import sys
from pathlib import Path

# Add analysis root to path so we can import from src
_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ANALYSIS_ROOT))

# Import paths from single source of truth (also sets up matcher path)
from src._paths import DATA_ROOT
from src.clean_ieg_data import clean_data
from src.create_kw_index import match_innovation_keywords
from scripts.run_analysis import (
    DROP_NA_LESSONS, PREFER_PPAR_OVER_ICRR, RECALCULATE_FCS_STATUS,
    FCS_COUNTRIES_LIST, RAW_FILE, load_data
)

import pandas as pd
import janitor
import pytest
import re


@pytest.fixture(scope="session")
def expected_keywords_processed_df():
    """Load expected results from original innovation keyword analysis.

    This fixture loads the baseline results that the refactored code should match.
    """
    return pd.read_excel(
        DATA_ROOT / "processed" / "processed_dataset.xlsx"
    ).pipe(janitor.clean_names)


@pytest.fixture(scope="session")
def actual_cleaned_df():
    raw_df = load_data(RAW_FILE)
    return clean_data(
        raw_df,
        drop_na_lessons=DROP_NA_LESSONS,
        prefer_ppar_over_icrr=PREFER_PPAR_OVER_ICRR,
        recalculate_fcs_status=RECALCULATE_FCS_STATUS,
        fcs_countries_list=FCS_COUNTRIES_LIST
    )


@pytest.fixture(scope="session")
def actual_keywords_processed_df(actual_cleaned_df):
    return match_innovation_keywords(actual_cleaned_df)


def show_keyword_context(lessons_text, keyword, context_chars=40):
    """Display keyword with surrounding context from lessons text.

    Args:
        lessons_text: The full text to search in
        keyword: The keyword to find
        context_chars: Number of characters of context to show on each side

    Returns:
        String showing the keyword in context, or "No match found"
    """
    match = re.search(
        rf"(\b.{{20,{context_chars}}}{re.escape(keyword)}.{{20,{context_chars}}}\b)",
        lessons_text.lower()
    )
    return match.group(0) if match else "No match found"


def print_mismatch_diagnostics(mismatched_df):
    """Print detailed diagnostics for mismatched keyword counts.

    Args:
        mismatched_df: DataFrame containing rows with mismatches, must have columns:
            - project_id
            - keywords
            - distinct_hits_actual
            - distinct_hits_expected
            - lessons (optional, for context)
    """
    for _, row in mismatched_df.iterrows():
        print(f"\n--- Project: {row['project_id']} ---")
        print(f"Keywords found: {row['keywords']}")
        print(f"Count: {row['distinct_hits_actual']} (actual) vs {row['distinct_hits_expected']} (expected)")

        if 'lessons' in row:
            for kw in row['keywords']:
                print(f"  '{kw}': {show_keyword_context(row['lessons'], kw)}")
        print("-----")


@pytest.fixture(scope="session")
def expected_cleaned_df():
    return (
        pd.read_excel(DATA_ROOT / "intermediate" / "cleaned_dataset.xlsx")
        .pipe(janitor.clean_names)
        .reset_index(drop=True)
    )
