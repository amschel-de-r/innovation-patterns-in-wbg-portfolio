"""Path setup for notebooks.

This module provides path constants and sets up Python path
for importing from the analysis source code and shared matcher.

Usage:
    import paths  # Adds src/ and matcher/ to sys.path
    from src.create_kw_index import match_innovation_keywords
    from keyword_matcher import KeywordMatcher
"""
import sys
from pathlib import Path

# Navigate up to repository root
ROOT = Path(__file__).resolve().parents[3]

# Analysis-specific paths
ANALYSIS_ROOT = ROOT / "analyses" / "prwp_2025"

# Shared data location (during development)
DATA_ROOT = ANALYSIS_ROOT / "data"

# Add analysis root to path (so we can import src.* modules)
sys.path.insert(0, str(ANALYSIS_ROOT))

# Add matcher to path (so we can import keyword_matcher)
sys.path.insert(0, str(ROOT / "matcher" / "src"))

# Export paths for use in notebooks
__all__ = ["ROOT", "ANALYSIS_ROOT", "DATA_ROOT"]