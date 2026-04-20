"""Test replication of feature keyword tagging.

Tests that the refactored KeywordMatcher produces the same binary tags
for feature categories (digital technology, IFC, private capital mobilization,
pilot/scale) as the original analysis.

Each feature category is tested separately for clear failure reporting 
and independent test execution.
"""
import pytest


def _assert_tag_replication(expected_df, actual_df, column_name):
    """Helper function to compare a tag column between expected and actual results.
    
    Args:
        expected_df: DataFrame with expected results
        actual_df: DataFrame with actual results
        column_name: Name of the column to compare
    """
    # Column should exist in both datasets
    assert column_name in actual_df.columns, \
        f"{column_name} column not found in actual results ({actual_df.columns.tolist()})"
    assert column_name in expected_df.columns, \
        f"{column_name} column not found in expected results ({expected_df.columns.tolist()})"
    
    # Merge on project_id to compare
    comparison = expected_df[['project_id', column_name]].merge(
        actual_df[['project_id', column_name]],
        on='project_id',
        suffixes=('_expected', '_actual')
    )
    
    # Find mismatches
    mismatches = comparison[
        comparison[f'{column_name}_expected'] != comparison[f'{column_name}_actual']
    ]
    
    assert len(mismatches) == 0, \
        f"Found {len(mismatches)} mismatches in {column_name}.\n" \
        f"First 5 mismatches:\n{mismatches.head()}\n" \
        f"{mismatches.project_id.to_list()}"
    
    


# Map feature tags to their descriptions
FEATURE_TAG_MAPPING = [
    ("ifc_tag", "IFC-related keywords from ifc_keywords.json (case-sensitive)"),
    ("pcm_tag", "private capital mobilization keywords from pcm_keywords.json"),
    ("pilot_tag", "pilot-related keywords from pilot_scale_keywords.json"),
    ("scale_tag", "scale-related keywords from pilot_scale_keywords.json"),
    ("pilot_category", "derived categorical tag (Pilot + Scaled / Pilot Only / No Pilot)"),
]


@pytest.mark.parametrize("column_name,description", FEATURE_TAG_MAPPING)
def test_feature_tag_replication(
    expected_keywords_processed_df,
    actual_keywords_processed_df,
    column_name,
    description
):
    """Test that a specific feature tag matches expected results.
    
    Args:
        expected_innovation_keywords_df: Fixture with expected results
        actual_innovation_keywords_df: Fixture with actual results (cached)
        column_name: Name of the column to test
        description: Description of what the tag represents
    """
    _assert_tag_replication(
        expected_keywords_processed_df,
        actual_keywords_processed_df,
        column_name
    )


def test_pilot_scale_consistency(actual_keywords_processed_df):
    """Test that pilot_category values are consistent with pilot_tag and scale_tag.

    Validates: "Pilot + Scaled" ↔ pilot_tag=1 AND scale_tag=1
               "Pilot Only"     ↔ pilot_tag=1 AND scale_tag=0
               "No Pilot"       ↔ pilot_tag=0
    """
    df = actual_keywords_processed_df

    pilot_and_scale = df[df['pilot_category'] == "Pilot + Scaled"]
    assert pilot_and_scale['pilot_tag'].all(), \
        "Found 'Pilot + Scaled' rows with pilot_tag=False"
    assert pilot_and_scale['scale_tag'].all(), \
        "Found 'Pilot + Scaled' rows with scale_tag=False"

    pilot_only = df[df['pilot_category'] == "Pilot Only"]
    assert pilot_only['pilot_tag'].all(), \
        "Found 'Pilot Only' rows with pilot_tag=False"
    assert (pilot_only['scale_tag'] == 0).all(), \
        "Found 'Pilot Only' rows with scale_tag=True"

    no_pilot = df[df['pilot_category'] == "No Pilot"]
    assert (no_pilot['pilot_tag'] == 0).all(), \
        "Found 'No Pilot' rows with pilot_tag=True"

    both = df[(df['pilot_tag'] == 1) & (df['scale_tag'] == 1)]
    assert (both['pilot_category'] == "Pilot + Scaled").all(), \
        "Found pilot_tag=1 AND scale_tag=1 rows not categorised as 'Pilot + Scaled'"


def test_feature_tags_are_binary(actual_keywords_processed_df):
    """Test that all feature tag columns contain only binary (0/1 or True/False) values."""
    df = actual_keywords_processed_df

    binary_columns = [
        'ifc_tag',
        'pilot_tag', 'scale_tag',
    ]

    for col in binary_columns:
        if col in df.columns:
            unique_values = set(df[col].dropna().unique())
            assert unique_values.issubset({0, 1, True, False}), \
                f"Column {col} contains non-binary values: {unique_values}"
