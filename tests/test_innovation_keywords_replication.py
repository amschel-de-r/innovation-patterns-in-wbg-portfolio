import pytest
import numpy as np
import pandas as pd
from tests.conftest import print_mismatch_diagnostics

def test_innovation_keywords_replication(
    expected_keywords_processed_df,
    actual_keywords_processed_df
):
    """Validate innovation keyword matching produces expected results.

    Tests that the pipeline reproduces the canonical processed_dataset.xlsx:
    same row count and matching innovation_distinct_hits for every project.
    """
    expected_results = expected_keywords_processed_df
    actual_results = actual_keywords_processed_df

    assert len(actual_results) == len(expected_results), (
        f"Row count mismatch: actual={len(actual_results)}, expected={len(expected_results)}"
    )

    comparison_df = (
        actual_results[['project_id', 'evaluation_type', 'lessons', 'innovation_matched_keywords', 'innovation_distinct_hits']]
        .rename(columns={'innovation_matched_keywords': 'keywords'})
        .merge(
            expected_results[['project_id', 'evaluation_type', 'innovation_distinct_hits']],
            on=['project_id', 'evaluation_type'],
            how='inner',
            suffixes=('_actual', '_expected')
        )
    )
    print(f"Matched rows: {len(comparison_df)} / {len(actual_results)}")

    mismatched_rows = comparison_df.query("innovation_distinct_hits_actual != innovation_distinct_hits_expected")
    print(f"Keyword count matches: {len(comparison_df) - len(mismatched_rows)} / {len(comparison_df)}")

    if not mismatched_rows.empty:
        print_mismatch_diagnostics(mismatched_rows)

    assert mismatched_rows.empty, (
        f"Found {len(mismatched_rows)} rows with mismatched keyword counts:\n"
        f"{mismatched_rows[['project_id', 'innovation_distinct_hits_actual', 'innovation_distinct_hits_expected']].to_string()}"
    )


def test_innovation_tier_categorization(
    expected_keywords_processed_df,
    actual_keywords_processed_df
):
    """Test that innovation_tier column correctly categorizes projects.
    
    Validates that projects are categorized into:
    - Low (0-1 distinct hits)
    - Moderate (2-3 distinct hits)
    - High (4+ distinct hits)
    
    Args:
        expected_innovation_keywords_df: Fixture with expected results
        actual_innovation_keywords_df: Fixture with actual results (cached)
    """
    expected_results = expected_keywords_processed_df
    actual_results = actual_keywords_processed_df
    
    # Verify innovation_tier column exists
    assert 'innovation_tier' in actual_results.columns, (
        "innovation_tier column not found in results"
    )
    
    # Verify all tiers match expected based on distinct_hits
    hits = actual_results['innovation_distinct_hits']
    expected_tiers = np.select([hits <= 1, hits <= 3], ['Low', 'Moderate'], default='High')
    mismatch_mask = actual_results['innovation_tier'] != expected_tiers
    tier_mismatches = actual_results[mismatch_mask][['project_id', 'innovation_distinct_hits', 'innovation_tier']].copy()
    tier_mismatches['expected_tier'] = expected_tiers[mismatch_mask]

    if not tier_mismatches.empty:
        print(f"\nInnovation tier mismatches: {len(tier_mismatches)}")
        print(tier_mismatches.to_string(index=False))

    assert tier_mismatches.empty, (
        f"Found {len(tier_mismatches)} projects with incorrect innovation_tier assignment"
    )
    
    # Verify tier distribution
    tier_counts = actual_results['innovation_tier'].value_counts()
    print("\nInnovation tier distribution:")
    print(tier_counts.to_string())
    
    # Test against expected results if available
    if 'innovation_tier' in expected_results.columns:
        comparison_df = (
            actual_results[['project_id', 'evaluation_type', 'evaluation_fy', 'innovation_tier']]
            .merge(
                expected_results[['project_id', 'evaluation_type', 'evaluation_fy', 'innovation_tier']],
                on=['project_id', 'evaluation_type', 'evaluation_fy'],
                how='inner',
                suffixes=('_actual', '_expected')
            )
        )
        
        tier_comparison_mismatches = comparison_df.query('innovation_tier_actual != innovation_tier_expected')
        
        if tier_comparison_mismatches.shape[0] > 0:
            print(f"\nTier comparison with expected: {tier_comparison_mismatches.shape[0]} mismatches")
            print(tier_comparison_mismatches[[
                'project_id', 
                'innovation_tier_actual', 
                'innovation_tier_expected'
            ]].head(20).to_string())
        
        assert tier_comparison_mismatches.shape[0] == 0, (
            f"Found {tier_comparison_mismatches.shape[0]} projects where innovation_tier "
            f"doesn't match expected results"
        )
