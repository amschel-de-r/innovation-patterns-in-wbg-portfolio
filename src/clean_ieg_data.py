"""
Module for cleaning IEG ICRR-PPAR Lessons data.
"""
import json
from pathlib import Path
from typing import Optional
import janitor
import ftfy
import numpy as np
import pandas as pd

from src._paths import DATA_ROOT

# Rating scale mapping from text to numeric values
RATING_SCALE = {
    'Highly Unsatisfactory': 1,
    'Unsatisfactory': 2,
    'Moderately Unsatisfactory': 3,
    'Moderately Satisfactory': 4,
    'Satisfactory': 5,
    'Highly Satisfactory': 6
}

# Data quality constants
DEFAULT_MIN_EVALUATION_YEAR = 1998  # IEG data collection started systematically
DEFAULT_MAX_EVALUATION_YEAR = 2025  # Current data cutoff

# Three rows in the source file have NaN lessons because Excel misparses cell
# values that start with "-" as formula errors. Corrections are stored in
# data/raw/IEG_ICRR-PPAR_Lessons_2025-03-12_patches.csv and applied during
# clean_data() so the original downloaded file remains the sole data input.
_PATCHES_PATH = DATA_ROOT / "raw" / "IEG_ICRR-PPAR_Lessons_2025-03-12_patches.csv"

# FCS reference data constants
_FCS_DIR = DATA_ROOT / "reference" / "FCS"
_FCS_COUNTRIES_PATH = _FCS_DIR / "fcs_list.json"
FCS_DATA_MIN_YEAR = 2015  # Earliest year available in FCS.xlsx
FCS_DATA_MAX_YEAR = 2025  # Latest year available in FCS.xlsx


def load_fcs_countries(start_fy: int | None = None, end_fy: int = FCS_DATA_MAX_YEAR) -> list[str]:
    """Return countries that appeared on the FCS list at any point during [start_fy, end_fy].

    Args:
        start_fy: First fiscal year to include (inclusive). If None, no lower bound.
                  Must be >= FCS_DATA_MIN_YEAR (2015) when provided.
        end_fy:   Last fiscal year to include (inclusive). Defaults to FCS_DATA_MAX_YEAR (2025).
                  Must be <= FCS_DATA_MAX_YEAR.

    Raises:
        ValueError: If parameters fall outside the available data range or are inconsistent.
    """
    if end_fy > FCS_DATA_MAX_YEAR:
        raise ValueError(f"end_fy ({end_fy}) exceeds available data (max: {FCS_DATA_MAX_YEAR})")
    if start_fy is not None:
        if start_fy < FCS_DATA_MIN_YEAR:
            raise ValueError(f"start_fy ({start_fy}) is before available data (min: {FCS_DATA_MIN_YEAR})")
        if start_fy > end_fy:
            raise ValueError(f"start_fy ({start_fy}) must be <= end_fy ({end_fy})")

    with open(_FCS_COUNTRIES_PATH, "r", encoding="utf-8") as f:
        fcs_countries_map = json.load(f)

    fcs = (
        pd.read_excel(_FCS_DIR / "FCS.xlsx")
        .assign(country=lambda x: x.country.str.strip())
        .assign(country_corr=lambda x: x.country.replace(fcs_countries_map))
    )

    mask = fcs["year"] <= end_fy
    if start_fy is not None:
        mask &= fcs["year"] >= start_fy

    return fcs.loc[mask, "country_corr"].unique().tolist()

def strip_excel_prefixes(df: pd.DataFrame) -> pd.DataFrame:
    """Remove Excel's leading quote prefix from string columns."""
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.lstrip("'")
    return df

def clean_data(df: pd.DataFrame,
               drop_na_lessons: bool = True,
               prefer_ppar_over_icrr: bool = True,
               recalculate_fcs_status: bool = False,
               fcs_countries_list: list | None = None,
               min_evaluation_year: int = DEFAULT_MIN_EVALUATION_YEAR,
               max_evaluation_year: int = DEFAULT_MAX_EVALUATION_YEAR) -> pd.DataFrame:
    """Clean IEG ICRR-PPAR data and return one row per project.

    Args:
        df: Raw DataFrame as loaded from the IEG Excel file.
        drop_na_lessons: If True (default), drop rows where the Lessons field
            is null, "None", or "Not Available".
        prefer_ppar_over_icrr: If True (default), keep the PPAR evaluation for
            projects that have both a PPAR and an ICRR; otherwise keep the ICRR.
            Where only one type exists it is always kept.
        recalculate_fcs_status: If True, overwrite the FCS status column using
            ``fcs_countries_list``. If False (default), the source value is
            preserved.
        fcs_countries_list: List of country names considered FCS. Only used
            when ``recalculate_fcs_status=True``.
        min_evaluation_year: Drop evaluations before this fiscal year
            (default: 1998, when IEG systematic data collection began).
        max_evaluation_year: Drop evaluations after this fiscal year
            (default: 2025).

    Returns:
        Cleaned DataFrame with one row per project.
    """

    cleaned_df = (
        df
        .pipe(janitor.clean_names) 
        .pipe(strip_excel_prefixes) 
        # Filter to systematic data collection period
        .query(f"evaluation_fy >= {min_evaluation_year} and evaluation_fy <= {max_evaluation_year}")
        .sort_values(['project_id', 'evaluation_fy'], ascending=[True, False])
        .assign(
            lessons = lambda x: x.lessons.apply(lambda x: ftfy.fix_text(x) if pd.notnull(x) else x),
            # Convert rating text to numeric values (1=worst, 6=best)
            ieg_outcome_ratings_num=lambda x: x.ieg_outcome_ratings.map(RATING_SCALE),
            ieg_bank_performance_ratings_num=lambda x: x.ieg_bank_performance_ratings.map(RATING_SCALE),
            ieg_quality_at_entry_ratings_num=lambda x: x.ieg_quality_at_entry_ratings.map(RATING_SCALE),
            ieg_quality_of_supervision_ratings_num=lambda x: x.ieg_quality_of_supervision_ratings.map(RATING_SCALE),
            # Create cohort and decade groups
            cohort=lambda x: pd.cut(
                x.evaluation_fy, 
                [1998, 2003, 2008, 2013, 2018, 2023, 2026], 
                include_lowest=True, 
                right=False,
                labels=["1998-2002", "2003-2007", "2008-2012", "2013-2017", "2018-2022", "2023-2025"]
            ).astype(object),
            decade=lambda x: pd.cut(
                x.evaluation_fy,
                [1998, 2008, 2018, 2026],
                include_lowest=True,
                right=False,
                labels=["1998-2007", "2008-2017", "2018-2025"]
            ).astype(object),
            # Relabel GP
            global_practice=lambda x: x.global_practice.replace({
                'Environment, Natural Resources & the Blue Economy': 'Environment',
                'Health, Nutrition & Population': 'Health, Nutrition and Population',
                'Energy & Extractives': 'Energy and Extractives',
                'Social Protection & Jobs': 'Social Protection and Jobs',
            }),
            # Normalize region name variant
            wb_region=lambda x: x.wb_region.replace({
                'Latin America and Caribbean': 'Latin America and the Caribbean'
            })
        )
        # .dropna(subset=['lessons'])
        .reset_index(drop=True)
    )

    # Apply patches for rows where Excel misparses leading "-" as formula errors
    patches = pd.read_csv(_PATCHES_PATH)
    for _, row in patches.iterrows():
        mask = cleaned_df["project_id"] == row["project_id"]
        cleaned_df.loc[mask, row["field"]] = row["patched_value"]

    if drop_na_lessons:
        cleaned_df = (cleaned_df
            # Drop observation where lessons is None
            .query('(lessons not in ["None","Not Available"] and lessons.notnull())')
            .reset_index(drop=True)
        )

    preferred_eval_type = "PPAR" if prefer_ppar_over_icrr else "ICRR"
    cleaned_df = (
        cleaned_df
        .assign(
            # Flag projects that have preferred_type evaluations
            has_preferred_eval_type=lambda x: x.groupby('project_id')['evaluation_type']
                                .transform(lambda grp: (grp == preferred_eval_type).any()),
            # Rank evaluations within each project (1=most recent)
            rank=lambda x: x.groupby('project_id').cumcount() + 1
        )
        # Select one evaluation per project: preferred_type if available, otherwise most recent ICRR
        .query(f'(has_preferred_eval_type and evaluation_type == "{preferred_eval_type}") or (~has_preferred_eval_type and rank == 1)')
        .drop(columns=['has_preferred_eval_type', 'rank'])
        .reset_index(drop=True)
    )

    if recalculate_fcs_status:
        cleaned_df = (
            cleaned_df
            .assign(
                fcs_status = lambda x: np.where(x.country.isin(fcs_countries_list),'FCS', 'Non-FCS')
            )
        )
        
    return cleaned_df
