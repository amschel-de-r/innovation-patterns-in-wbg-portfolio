"""Shared path configuration for prwp_2025 analysis.

This module is the single source of truth for all paths in this analysis.

Usage:
    from src._paths import DATA_ROOT, ANALYSIS_ROOT, TABLES_DIR
    from keyword_matcher import KeywordMatcher  # Available after import
"""
import sys
from pathlib import Path

# Navigate up to repository root (src/ → repo root)
ANALYSIS_ROOT = Path(__file__).resolve().parents[1]

# Data paths
DATA_ROOT = ANALYSIS_ROOT / "data"

# Output paths
TABLES_DIR = ANALYSIS_ROOT / "output" / "tables"
OUTPUT_DIR = ANALYSIS_ROOT / "output"

# Add vendored matcher to Python path (frozen at v1.0.0 for publication)
sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
