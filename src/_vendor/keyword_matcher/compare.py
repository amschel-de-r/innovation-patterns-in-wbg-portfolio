"""Compare results from two keyword matching runs and extract keyword context snippets."""

import re
import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class RunComparison:
    """Results of comparing two keyword matching runs.

    Attributes:
        summary: Per-column counts of projects that increased, decreased, or were unchanged.
        changes: Rows that changed, with before/after values per column (MultiIndex columns).
        added: join_key values present in df_after but not df_before.
        removed: join_key values present in df_before but not df_after.
    """
    summary: pd.DataFrame
    changes: pd.DataFrame
    added: pd.Index
    removed: pd.Index


def compare_runs(
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
    join_key: str,
    columns: Optional[list[str]] = None,
) -> RunComparison:
    """Compare keyword matching results between two DataFrame runs.

    Args:
        df_before: DataFrame from the baseline/earlier run.
        df_after: DataFrame from the current run.
        join_key: Column to align rows on (e.g., 'project_id').
        columns: Columns to compare. If None, auto-detects columns ending in
                 '_tag' or '_distinct_hits' that exist in both DataFrames.

    Returns:
        RunComparison with summary stats, per-row changes, and added/removed keys.

    Raises:
        ValueError: If no comparable columns are found.
    """
    before_indexed = df_before.set_index(join_key)
    after_indexed = df_after.set_index(join_key)

    added = after_indexed.index.difference(before_indexed.index)
    removed = before_indexed.index.difference(after_indexed.index)
    common = before_indexed.index.intersection(after_indexed.index)

    before_common = before_indexed.loc[common]
    after_common = after_indexed.loc[common]

    if columns is None:
        columns = [
            c for c in after_common.columns
            if c.endswith(('_tag', '_distinct_hits'))
            and c in before_common.columns
        ]
    else:
        columns = [c for c in columns if c in before_common.columns and c in after_common.columns]

    if not columns:
        raise ValueError(
            "No comparable columns found. Specify columns= explicitly, or ensure both "
            "DataFrames share columns ending in '_tag' or '_distinct_hits'."
        )

    # Cast to float64 so pandas .compare() handles int/bool/float dtype mismatches
    before_sel = before_common[columns].sort_index().astype(float)
    after_sel = after_common[columns].sort_index().astype(float)

    diff = after_sel.compare(before_sel, result_names=("after", "before"), keep_shape=False)

    summary_rows = []
    changed_cols = diff.columns.get_level_values(0).unique()
    for col in columns:
        if col not in changed_cols:
            summary_rows.append({
                "column": col,
                "n_changed": 0,
                "n_increased": 0,
                "n_decreased": 0,
                "n_unchanged": len(common),
            })
        else:
            col_diff = diff[col]
            delta = col_diff["after"] - col_diff["before"]
            n_changed = int(delta.notna().sum())
            summary_rows.append({
                "column": col,
                "n_changed": n_changed,
                "n_increased": int((delta > 0).sum()),
                "n_decreased": int((delta < 0).sum()),
                "n_unchanged": len(common) - n_changed,
            })

    return RunComparison(
        summary=pd.DataFrame(summary_rows),
        changes=diff,
        added=added,
        removed=removed,
    )


def extract_snippets(
    text: str,
    keywords: list[str],
    context: int = 60,
    case_sensitive: bool = False,
    highlight: bool = False,
) -> list[dict]:
    """Extract keyword-in-context snippets from a text string.

    For each keyword, finds all occurrences in the text and returns a
    surrounding context window. Useful for manually evaluating why a
    project gained or lost a keyword match between runs.

    Args:
        text: The source text to search (e.g., a project's lessons field).
        keywords: List of keywords to search for.
        context: Number of characters of context to include on each side of the match.
        case_sensitive: If False (default), matching is case-insensitive.
        highlight: If True, wraps each matched keyword in **...** (markdown bold).

    Returns:
        List of dicts with keys: 'keyword', 'snippet'.
        Multiple occurrences of the same keyword produce separate entries.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    results = []
    for kw in keywords:
        pattern = rf".{{0,{context}}}{re.escape(kw)}.{{0,{context}}}"
        for m in re.finditer(pattern, text, flags):
            snippet = m.group(0).strip()
            if highlight:
                snippet = re.sub(re.escape(kw), lambda hit: f"**{hit.group(0)}**", snippet, flags=flags)
            results.append({"keyword": kw, "snippet": snippet})
    return results
