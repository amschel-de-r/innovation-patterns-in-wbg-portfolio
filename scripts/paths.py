"""Path setup for scripts.

Re-exports from src._paths for backward compatibility.
All path definitions live in src/_paths.py.
"""
import sys
from pathlib import Path

# Add src to path so we can import from _paths
_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ANALYSIS_ROOT))

# Re-export everything from the single source of truth
from src._paths import REPO_ROOT, ANALYSIS_ROOT, DATA_ROOT, TABLES_DIR, OUTPUT_DIR

# Backward compatibility alias
ROOT = REPO_ROOT

__all__ = ["ROOT", "REPO_ROOT", "ANALYSIS_ROOT", "DATA_ROOT", "TABLES_DIR", "OUTPUT_DIR"]