"""Tests for compare_runs and extract_snippets."""

import pytest
import pandas as pd
from keyword_matcher.compare import compare_runs, extract_snippets


# ============================================================================
# compare_runs
# ============================================================================

def _make_df(data: dict, join_key: str = "id") -> pd.DataFrame:
    return pd.DataFrame(data)


def test_compare_runs_detects_increases():
    before = pd.DataFrame({"id": [1, 2], "score_distinct_hits": [0, 1]})
    after  = pd.DataFrame({"id": [1, 2], "score_distinct_hits": [1, 1]})

    result = compare_runs(before, after, join_key="id")

    row = result.summary[result.summary["column"] == "score_distinct_hits"].iloc[0]
    assert row["n_increased"] == 1
    assert row["n_decreased"] == 0
    assert row["n_changed"] == 1


def test_compare_runs_detects_decreases():
    before = pd.DataFrame({"id": [1, 2], "score_distinct_hits": [3, 2]})
    after  = pd.DataFrame({"id": [1, 2], "score_distinct_hits": [1, 2]})

    result = compare_runs(before, after, join_key="id")

    row = result.summary[result.summary["column"] == "score_distinct_hits"].iloc[0]
    assert row["n_decreased"] == 1
    assert row["n_increased"] == 0


def test_compare_runs_no_changes():
    df = pd.DataFrame({"id": [1, 2], "score_distinct_hits": [2, 0]})

    result = compare_runs(df, df.copy(), join_key="id")

    row = result.summary[result.summary["column"] == "score_distinct_hits"].iloc[0]
    assert row["n_changed"] == 0
    assert row["n_unchanged"] == 2
    assert result.changes.empty


def test_compare_runs_added_removed_keys():
    before = pd.DataFrame({"id": [1, 2], "score_distinct_hits": [1, 1]})
    after  = pd.DataFrame({"id": [2, 3], "score_distinct_hits": [1, 1]})

    result = compare_runs(before, after, join_key="id")

    assert 3 in result.added
    assert 1 in result.removed
    assert 2 not in result.added
    assert 2 not in result.removed


def test_compare_runs_auto_detects_columns():
    before = pd.DataFrame({
        "id": [1],
        "a_tag": [0],
        "b_distinct_hits": [2],
        "unrelated": ["x"],
    })
    after = pd.DataFrame({
        "id": [1],
        "a_tag": [1],
        "b_distinct_hits": [2],
        "unrelated": ["y"],
    })

    result = compare_runs(before, after, join_key="id")

    compared_cols = result.summary["column"].tolist()
    assert "a_tag" in compared_cols
    assert "b_distinct_hits" in compared_cols
    assert "unrelated" not in compared_cols


def test_compare_runs_explicit_columns():
    before = pd.DataFrame({"id": [1], "a_tag": [0], "b_tag": [1]})
    after  = pd.DataFrame({"id": [1], "a_tag": [1], "b_tag": [1]})

    result = compare_runs(before, after, join_key="id", columns=["a_tag"])

    assert result.summary["column"].tolist() == ["a_tag"]


def test_compare_runs_raises_when_no_comparable_columns():
    before = pd.DataFrame({"id": [1], "notes": ["x"]})
    after  = pd.DataFrame({"id": [1], "notes": ["y"]})

    with pytest.raises(ValueError, match="No comparable columns found"):
        compare_runs(before, after, join_key="id")


def test_compare_runs_changes_multiindex():
    before = pd.DataFrame({"id": [1, 2], "score_distinct_hits": [0, 5]})
    after  = pd.DataFrame({"id": [1, 2], "score_distinct_hits": [3, 5]})

    result = compare_runs(before, after, join_key="id")

    assert not result.changes.empty
    assert ("score_distinct_hits", "after") in result.changes.columns
    assert ("score_distinct_hits", "before") in result.changes.columns
    assert result.changes.loc[1, ("score_distinct_hits", "after")] == 3.0
    assert result.changes.loc[1, ("score_distinct_hits", "before")] == 0.0


# ============================================================================
# extract_snippets
# ============================================================================

def test_extract_snippets_basic():
    text = "The project focused on digital innovation and climate resilience."
    snippets = extract_snippets(text, ["digital innovation"])

    assert len(snippets) == 1
    assert snippets[0]["keyword"] == "digital innovation"
    assert "digital innovation" in snippets[0]["snippet"]


def test_extract_snippets_case_insensitive():
    text = "We applied DIGITAL tools throughout."
    snippets = extract_snippets(text, ["digital"], case_sensitive=False)

    assert len(snippets) == 1


def test_extract_snippets_case_sensitive_no_match():
    text = "We applied DIGITAL tools throughout."
    snippets = extract_snippets(text, ["digital"], case_sensitive=True)

    assert len(snippets) == 0


def test_extract_snippets_multiple_occurrences():
    # Occurrences must be more than 2*context chars apart to produce separate snippets.
    # With context=60, pad the gap to ~130 chars so the two matches don't merge.
    padding = "x" * 130
    text = f"First innovation here. {padding} Second innovation there."
    snippets = extract_snippets(text, ["innovation"], case_sensitive=False)

    assert len(snippets) == 2


def test_extract_snippets_multiple_keywords():
    text = "The project used digital tools and promoted innovation."
    snippets = extract_snippets(text, ["digital", "innovation"])

    keywords_found = {s["keyword"] for s in snippets}
    assert "digital" in keywords_found
    assert "innovation" in keywords_found


def test_extract_snippets_context_window():
    text = "a" * 100 + " keyword " + "b" * 100
    snippets = extract_snippets(text, ["keyword"], context=10)

    assert len(snippets) == 1
    # Snippet should be much shorter than the full text
    assert len(snippets[0]["snippet"]) < len(text)


def test_extract_snippets_highlight():
    text = "The project demonstrated innovation in design."
    snippets = extract_snippets(text, ["innovation"], highlight=True)

    assert "**innovation**" in snippets[0]["snippet"]


def test_extract_snippets_no_match_returns_empty():
    text = "Nothing relevant here."
    snippets = extract_snippets(text, ["innovation"])

    assert snippets == []


def test_extract_snippets_empty_text():
    snippets = extract_snippets("", ["innovation"])

    assert snippets == []
