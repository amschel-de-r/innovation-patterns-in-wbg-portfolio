"""Path setup for notebooks.

This module provides path constants and sets up Python path
for importing from the analysis source code and vendored matcher.

Usage:
    import paths  # Adds repo root to sys.path
    from src.create_kw_index import match_innovation_keywords
    from keyword_matcher import KeywordMatcher
"""
import sys
from pathlib import Path

# Add repo root to path so we can import src.* modules (notebooks/ → repo root)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src._paths import ANALYSIS_ROOT, DATA_ROOT, TABLES_DIR, OUTPUT_DIR

__all__ = ["ANALYSIS_ROOT", "DATA_ROOT", "TABLES_DIR", "OUTPUT_DIR"]