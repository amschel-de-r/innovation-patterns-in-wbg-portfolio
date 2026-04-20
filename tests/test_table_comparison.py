import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.table_comparison import reconcile_for_comparison


# --- use_first_col=True ---

def test_use_first_col_no_differences():
    """When both tables have the same first-column values, no rows are added."""
    table = pd.DataFrame({"label": ["A", "B"], "val": [1, 2]})
    paper = pd.DataFrame({"label": ["A", "B"], "val": [1, 2]})
    t, p = reconcile_for_comparison(table, paper, use_first_col=True)
    assert set(t["label"]) == {"A", "B"}
    assert set(p["label"]) == {"A", "B"}
    assert len(t) == 2
    assert len(p) == 2


def test_use_first_col_row_only_in_table():
    """A row present only in table should be added as an empty row to paper_table."""
    table = pd.DataFrame({"label": ["A", "B", "C"], "val": [1, 2, 3]})
    paper = pd.DataFrame({"label": ["A", "B"], "val": [10, 20]})
    t, p = reconcile_for_comparison(table, paper, use_first_col=True)
    assert "C" in p["label"].values
    assert p.loc[p["label"] == "C", "val"].iloc[0] == ""


def test_use_first_col_row_only_in_paper():
    """A row present only in paper_table should be added as an empty row to table."""
    table = pd.DataFrame({"label": ["A", "B"], "val": [1, 2]})
    paper = pd.DataFrame({"label": ["A", "B", "C"], "val": [10, 20, 30]})
    t, p = reconcile_for_comparison(table, paper, use_first_col=True)
    assert "C" in t["label"].values
    assert t.loc[t["label"] == "C", "val"].iloc[0] == ""


def test_use_first_col_rows_aligned_by_label():
    """After reconciliation both DataFrames should have matching row order."""
    table = pd.DataFrame({"label": ["B", "A"], "val": [2, 1]})
    paper = pd.DataFrame({"label": ["A", "B"], "val": [10, 20]})
    t, p = reconcile_for_comparison(table, paper, use_first_col=True)
    assert list(t["label"]) == list(p["label"])


def test_use_first_col_sort_order_follows_table():
    """Sort order should follow the table's original row order."""
    table = pd.DataFrame({"label": ["C", "A", "B"], "val": [3, 1, 2]})
    paper = pd.DataFrame({"label": ["A", "B", "C"], "val": [10, 20, 30]})
    t, p = reconcile_for_comparison(table, paper, use_first_col=True)
    assert list(t["label"]) == ["C", "A", "B"]
    assert list(p["label"]) == ["C", "A", "B"]


def test_use_first_col_missing_column_raises():
    """ValueError if first column of table is not present in paper_table."""
    table = pd.DataFrame({"label": ["A"], "val": [1]})
    paper = pd.DataFrame({"other_col": ["A"], "val": [10]})
    with pytest.raises(ValueError, match="label"):
        reconcile_for_comparison(table, paper, use_first_col=True)


# --- use_first_col=False ---

def test_no_first_col_equal_lengths():
    """Equal-length DataFrames should be returned unchanged."""
    table = pd.DataFrame({"val": [1, 2]})
    paper = pd.DataFrame({"val": [10, 20]})
    t, p = reconcile_for_comparison(table, paper, use_first_col=False)
    assert len(t) == 2
    assert len(p) == 2


def test_no_first_col_table_shorter():
    """When table has fewer rows, empty rows are appended to table."""
    table = pd.DataFrame({"val": [1]})
    paper = pd.DataFrame({"val": [10, 20, 30]})
    t, p = reconcile_for_comparison(table, paper, use_first_col=False)
    assert len(t) == 3
    assert len(p) == 3


def test_no_first_col_paper_shorter():
    """When paper_table has fewer rows, empty rows are appended to paper_table."""
    table = pd.DataFrame({"val": [1, 2, 3]})
    paper = pd.DataFrame({"val": [10]})
    t, p = reconcile_for_comparison(table, paper, use_first_col=False)
    assert len(t) == 3
    assert len(p) == 3


def test_no_first_col_original_data_preserved():
    """Padding should not overwrite existing rows."""
    table = pd.DataFrame({"val": [1, 2, 3]})
    paper = pd.DataFrame({"val": [10]})
    t, p = reconcile_for_comparison(table, paper, use_first_col=False)
    assert list(t["val"]) == [1, 2, 3]
    assert p["val"].iloc[0] == 10
