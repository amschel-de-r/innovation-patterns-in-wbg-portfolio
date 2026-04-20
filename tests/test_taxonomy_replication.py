"""Test replication of taxonomy keyword tagging.

Tests that the refactored KeywordMatcher produces the same binary tags
for innovation taxonomy categories (collaborative, financial, operational/institutional, 
technological) as the original analysis.

Each taxonomy category is tested separately using parametrized tests for clear
failure reporting and independent test execution.
"""
import pytest
import pandas as pd
from src.create_kw_index import match_innovation_keywords


def _sanitize_column_name(category_name: str) -> str:
    """Convert taxonomy category name to column name format."""
    return category_name.lower().replace(' ', '_').replace('/', '_').replace('-', '_') + '_tag'


# Map from taxonomy_keywords.json categories to expected column names
TAXONOMY_MAPPING = [
    ("collaborative", "collaborative_tag"),
    ("financial", "financial_tag"),
    ("operational/institutional", "operational_institutional_tag"),
    ("technological", "technological_tag"),
]


@pytest.mark.parametrize("taxonomy_category,expected_column", TAXONOMY_MAPPING)
def test_taxonomy_tag_replication(
    expected_keywords_processed_df,
    actual_keywords_processed_df,
    taxonomy_category,
    expected_column
):
    """Test that a specific taxonomy category tag matches expected results.
    
    Args:
        expected_innovation_keywords_df: Fixture with expected results
        actual_innovation_keywords_df: Fixture with actual results (cached)
        taxonomy_category: Name of the category in taxonomy_keywords.json
        expected_column: Name of the column in expected results (e.g., 'collaborative_tag')
    """
    expected_results = expected_keywords_processed_df
    actual_results = actual_keywords_processed_df
    
    # Construct actual column name (KeywordMatcher uses sanitized names)
    # e.g., "operational/institutional" -> "operational_institutional_tag"
    actual_column = _sanitize_column_name(taxonomy_category)
    
    # Verify columns exist
    if actual_column not in actual_results.columns:
        pytest.fail(f"Actual column '{actual_column}' not found in results. Available columns: {list(actual_results.columns)}")
    
    if expected_column not in expected_results.columns:
        pytest.fail(f"Expected column '{expected_column}' not found in baseline. Available columns: {list(expected_results.columns)}")
    
    # Merge actual and expected results
    comparison_df = (
        actual_results[['project_id', 'evaluation_type', 'evaluation_fy', actual_column]]
        .merge(
            expected_results[['project_id', 'evaluation_type', 'evaluation_fy', expected_column]],
            on=['project_id', 'evaluation_type', 'evaluation_fy'],
            how='inner',
            suffixes=('_actual', '_expected')
        )
    )
    
    # Handle column naming
    actual_col_name = f"{actual_column}_actual" if actual_column == expected_column else actual_column
    expected_col_name = f"{expected_column}_expected" if actual_column == expected_column else expected_column
    
    # Find mismatches
    mismatches = comparison_df.query(f"{actual_col_name} != {expected_col_name}")
    
    if mismatches.shape[0] > 0:
        print(f"\n{taxonomy_category} ({expected_column}) Mismatches:")
        print(f"Total mismatches: {mismatches.shape[0]} / {comparison_df.shape[0]}")
        print(mismatches[[
            'project_id', 
            'evaluation_type', 
            actual_col_name, 
            expected_col_name
        ]].head(20).to_string())
        
        # Show breakdown
        false_positives = mismatches.query(f"{actual_col_name} > {expected_col_name}").shape[0]
        false_negatives = mismatches.query(f"{actual_col_name} < {expected_col_name}").shape[0]
        print(f"  False positives (tagged but shouldn't be): {false_positives}")
        print(f"  False negatives (should be tagged but aren't): {false_negatives}")
    
    # Assert perfect match
    assert mismatches.shape[0] == 0, (
        f"{taxonomy_category} tags don't match: {mismatches.shape[0]} mismatches found"
    )


def test_all_taxonomy_columns_present(actual_keywords_processed_df):
    """Verify all expected taxonomy columns are generated."""
    actual_results = actual_keywords_processed_df
    
    missing_columns = []
    for taxonomy_category, expected_col in TAXONOMY_MAPPING:
        actual_col = _sanitize_column_name(taxonomy_category)
        if actual_col not in actual_results.columns:
            missing_columns.append(f"{taxonomy_category} -> {actual_col}")
    
    assert len(missing_columns) == 0, (
        f"Missing taxonomy columns: {', '.join(missing_columns)}"
    )


def test_taxonomy_tags_are_binary(actual_keywords_processed_df):
    """Verify all taxonomy tags contain only 0 and 1 values."""
    actual_results = actual_keywords_processed_df
    
    invalid_columns = []
    for taxonomy_category, _ in TAXONOMY_MAPPING:
        actual_col = _sanitize_column_name(taxonomy_category)
        if actual_col in actual_results.columns:
            unique_values = set(actual_results[actual_col].dropna().unique())
            if not unique_values.issubset({0, 1, True, False}):
                invalid_columns.append(f"{actual_col}: {unique_values}")
    
    assert len(invalid_columns) == 0, (
        f"Non-binary values found in: {', '.join(invalid_columns)}"
    )


def test_taxonomy_mutual_exclusivity(actual_keywords_processed_df):
    """Test that taxonomy categories are NOT mutually exclusive.
    
    A project can have multiple taxonomy tags (e.g., both technological 
    and collaborative innovation), so we just verify that we have cases
    with multiple tags to ensure the logic is working as expected.
    """
    actual_results = actual_keywords_processed_df
    
    # Create a dataframe with just the taxonomy tags
    taxonomy_cols = [
        _sanitize_column_name(taxonomy_category)
        for taxonomy_category, _ in TAXONOMY_MAPPING
    ]
    
    available_cols = [col for col in taxonomy_cols if col in actual_results.columns]
    
    if len(available_cols) < 2:
        pytest.skip("Not enough taxonomy columns available for exclusivity test")
    
    taxonomy_df = actual_results[available_cols]
    
    # Count projects with multiple taxonomy tags
    multiple_tags = (taxonomy_df.sum(axis=1) > 1).sum()
    
    # We expect some projects to have multiple taxonomy types
    assert multiple_tags > 0, (
        "No projects found with multiple taxonomy tags. "
        "Expected some overlap between categories."
    )
    
    print(f"\nProjects with multiple taxonomy tags: {multiple_tags} / {len(taxonomy_df)}")
    print(f"Distribution of tag counts:")
    print(taxonomy_df.sum(axis=1).value_counts().sort_index().to_string())
