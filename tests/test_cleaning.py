import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal
from src.clean_ieg_data import clean_data

def _minimal_row(project_id, evaluation_type, evaluation_fy=2015):
    return {
        'project_id': project_id,
        'evaluation_type': evaluation_type,
        'evaluation_fy': evaluation_fy,
        'lessons': 'Some lesson text.',
        'ieg_outcome_ratings': 'Satisfactory',
        'ieg_bank_performance_ratings': 'Satisfactory',
        'ieg_quality_at_entry_ratings': 'Satisfactory',
        'ieg_quality_of_supervision_ratings': 'Satisfactory',
        'global_practice': 'Education',
        'wb_region': 'Sub-Saharan Africa',
        'country': 'Kenya',
    }


def test_prefer_ppar_over_icrr_selects_ppar():
    """When prefer_ppar_over_icrr=True, PPAR is selected for projects with both eval types."""
    raw = pd.DataFrame([
        _minimal_row('P001', 'PPAR', 2015),  # P001: has both — PPAR should win
        _minimal_row('P001', 'ICRR', 2014),
        _minimal_row('P002', 'ICRR', 2015),  # P002: ICRR only — kept as-is
        _minimal_row('P003', 'PPAR', 2015),  # P003: PPAR only — kept as-is
    ])
    result = clean_data(raw, prefer_ppar_over_icrr=True, recalculate_fcs_status=False)

    assert len(result) == 3
    assert result.loc[result['project_id'] == 'P001', 'evaluation_type'].iloc[0] == 'PPAR'
    assert result.loc[result['project_id'] == 'P002', 'evaluation_type'].iloc[0] == 'ICRR'
    assert result.loc[result['project_id'] == 'P003', 'evaluation_type'].iloc[0] == 'PPAR'


def test_prefer_icrr_over_ppar_selects_icrr():
    """When prefer_ppar_over_icrr=False, ICRR is selected for projects with both eval types."""
    raw = pd.DataFrame([
        _minimal_row('P001', 'PPAR', 2015),  # P001: has both — ICRR should win
        _minimal_row('P001', 'ICRR', 2014),
        _minimal_row('P002', 'PPAR', 2015),  # P002: PPAR only — kept as-is (no ICRR available)
    ])
    result = clean_data(raw, prefer_ppar_over_icrr=False, recalculate_fcs_status=False)

    assert result.loc[result['project_id'] == 'P001', 'evaluation_type'].iloc[0] == 'ICRR'
    assert result.loc[result['project_id'] == 'P002', 'evaluation_type'].iloc[0] == 'PPAR'


def test_merge_produces_expected_output(actual_cleaned_df, expected_cleaned_df):
    result = actual_cleaned_df
    expected = expected_cleaned_df

    column_comparison = (
        pd.DataFrame(result.dtypes, columns=['actual'])
        .reset_index(names="column_name")
        .merge(
            pd.DataFrame(expected.dtypes, columns=['expected']).reset_index(names="column_name"),
            on="column_name",
            how="outer"
        )
        .query("actual != expected")
    )

    assert expected.shape[0] == result.shape[0], f"Expected {expected.shape[0]} rows but got {result.shape[0]} rows"
    result = result.filter(expected.columns)

    print(column_comparison)
    assert_frame_equal(result, expected, check_dtype=False)
    assert len(result) == result['project_id'].nunique()