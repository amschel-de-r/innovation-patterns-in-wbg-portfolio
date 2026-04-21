"""Path setup for scripts.

Re-exports from src._paths for backward compatibility.
All path definitions live in src/_paths.py.
"""
import sys
from pathlib import Path

# Add repo root to path so we can import from src._paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src._paths import ANALYSIS_ROOT, DATA_ROOT, TABLES_DIR, OUTPUT_DIR

__all__ = ["ANALYSIS_ROOT", "DATA_ROOT", "TABLES_DIR", "OUTPUT_DIR"]