"""Utilities for reconciling and comparing generated tables against paper tables."""

import pandas as pd


def reconcile_for_comparison(
    table: pd.DataFrame,
    paper_table: pd.DataFrame,
    use_first_col: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Align two DataFrames so they can be compared with DataFrame.compare().

    When use_first_col is True, rows are matched on the first column's values:
    rows present in one but not the other are added as empty rows, then both
    DataFrames are sorted by that column so rows align correctly.

    When use_first_col is False, the DataFrames are padded to equal row counts
    with empty rows.

    Args:
        table: The generated (proposed) table.
        paper_table: The reference table extracted from the paper.
        use_first_col: If True, align on first-column values. If False, pad to
            equal length.

    Returns:
        Tuple of (table, paper_table) ready for DataFrame.compare().

    Raises:
        ValueError: If use_first_col is True but the first column of table is
            not present in paper_table.
    """
    if use_first_col:
        first_col = table.columns[0]
        if first_col not in paper_table.columns:
            raise ValueError(f"Column '{first_col}' not found in paper_table")

        values_table = set(table[first_col].dropna().unique())
        values_paper_table = set(paper_table[first_col].dropna().unique())
        only_in_table = values_table - values_paper_table
        only_in_paper_table = values_paper_table - values_table

        if only_in_table:
            missing_rows = pd.DataFrame(
                {col: [""] * len(only_in_table) for col in paper_table.columns}
                | {first_col: list(only_in_table)}
            )
            paper_table = pd.concat([paper_table, missing_rows], ignore_index=True)

        if only_in_paper_table:
            missing_rows = pd.DataFrame(
                {col: [""] * len(only_in_paper_table) for col in table.columns}
            )
            missing_rows[first_col] = list(only_in_paper_table)
            table = pd.concat([table, missing_rows], ignore_index=True)

        table_value_order = table[first_col].dropna().unique()
        all_values = list(table_value_order) + [
            v for v in paper_table[first_col].dropna().unique()
            if v not in table_value_order
        ]
        cat_type = pd.CategoricalDtype(categories=all_values, ordered=True)
        table[first_col] = table[first_col].astype(cat_type)
        paper_table[first_col] = paper_table[first_col].astype(cat_type)
        table = table.sort_values(first_col).reset_index(drop=True)
        paper_table = paper_table.sort_values(first_col).reset_index(drop=True)
    else:
        row_diff = paper_table.shape[0] - table.shape[0]
        empty = pd.DataFrame(columns=table.columns, index=range(abs(row_diff)))
        if row_diff > 0:
            table = pd.concat([table, empty], ignore_index=True)
        elif row_diff < 0:
            paper_table = pd.concat([paper_table, empty], ignore_index=True)

    return table, paper_table
