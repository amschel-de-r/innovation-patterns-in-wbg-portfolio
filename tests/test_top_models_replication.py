"""Test replication of top models keyword tagging.

Tests that the refactored KeywordMatcher produces the same binary tags
for top models (PPP, CDD, CCT, etc.) as the original analysis.

Each top model is tested separately using parametrized tests for clear
failure reporting and independent test execution.
"""
import pytest
import pandas as pd


# Map from top_models_keywords.json categories to sanitized column names.
# Both actual and expected use the same column name; pandas appends _actual/_expected on merge.
TOP_MODELS_MAPPING = [
    ("digital government", "digital_government_tag"),
    ("PPP", "ppp_tag"),
    ("e-procurement", "e_procurement_tag"),
    ("Remote Sensing", "remote_sensing_tag"),
    ("e-learning", "e_learning_tag"),
    ("mobile banking", "mobile_banking_tag"),
    ("CDD", "cdd_tag"),
    ("biometric ID", "biometric_id_tag"),
    ("CCT", "cct_tag"),
]


@pytest.mark.parametrize("model_name,col", TOP_MODELS_MAPPING)
def test_top_model_tag_replication(
    expected_keywords_processed_df,
    actual_keywords_processed_df,
    model_name,
    col
):
    """Test that a specific top model tag matches expected results."""
    join_keys = ['project_id', 'evaluation_type', 'evaluation_fy']
    comparison_df = (
        actual_keywords_processed_df[join_keys + [col]]
        .merge(
            expected_keywords_processed_df[join_keys + [col]],
            on=join_keys,
            how='inner',
            suffixes=('_actual', '_expected')
        )
    )
    assert len(comparison_df) == len(actual_keywords_processed_df), (
        f"{model_name}: inner merge dropped rows — join key mismatch between actual and expected"
    )

    actual_col, expected_col = f"{col}_actual", f"{col}_expected"
    mismatches = comparison_df.query(f"{actual_col} != {expected_col}")

    if not mismatches.empty:
        false_positives = mismatches.query(f"{actual_col} > {expected_col}").shape[0]
        false_negatives = mismatches.query(f"{actual_col} < {expected_col}").shape[0]
        print(f"\n{model_name} mismatches: {len(mismatches)} / {len(comparison_df)}")
        print(f"  False positives: {false_positives}, False negatives: {false_negatives}")
        print(mismatches[['project_id', 'evaluation_type', actual_col, expected_col]].to_string())

    assert mismatches.empty, (
        f"{model_name} tags don't match: {len(mismatches)} mismatches found"
    )


def test_all_top_models_present(actual_keywords_processed_df):
    """Verify all expected top model columns are generated."""
    actual_results = actual_keywords_processed_df
    
    missing_columns = []
    for model_name, expected_col in TOP_MODELS_MAPPING:
        actual_col = model_name.lower().replace(' ', '_').replace('-', '_') + '_tag'
        if actual_col not in actual_results.columns:
            missing_columns.append(f"{model_name} -> {actual_col}")
    
    assert len(missing_columns) == 0, (
        f"Missing top model columns: {', '.join(missing_columns)}"
    )
