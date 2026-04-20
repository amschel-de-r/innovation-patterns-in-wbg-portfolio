"""KeywordMatcher: A framework for applying keyword dictionaries to text data.

This package provides flexible keyword matching with multiple output formats
and support for nested dictionary structures.
"""

from .core import KeywordMatcher, DictConfig
from .compare import compare_runs, extract_snippets, RunComparison

__version__ = "1.0.0"
__all__ = ["KeywordMatcher", "DictConfig", "compare_runs", "extract_snippets", "RunComparison"]
