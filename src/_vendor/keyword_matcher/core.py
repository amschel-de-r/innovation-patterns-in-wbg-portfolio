"""Apply keyword dictionaries to text data with flexible output formats."""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Optional, Literal, Union, Self
from dataclasses import dataclass
from sklearn.feature_extraction.text import CountVectorizer
import ahocorasick

logger = logging.getLogger(__name__)


@dataclass
class DictConfig:
    """Configuration for a single dictionary to apply."""
    keywords: dict
    base_name: str
    output_format: Literal['binary', 'count', 'set']
    match_mode: Literal['word_boundary', 'substring'] = 'word_boundary'
    case_sensitive: bool = False
    replace_hyphens: bool = False
    enforce_word_boundaries: bool = False
    column_suffix: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration on creation."""
        if not self.keywords:
            raise ValueError(f"DictConfig '{self.base_name}' has empty keywords")
        if not self.base_name:
            raise ValueError("DictConfig must have non-empty base_name")
        
        # Validate output_format
        valid_formats = {'binary', 'count', 'set'}
        if self.output_format not in valid_formats:
            raise ValueError(
                f"Invalid output_format '{self.output_format}' for '{self.base_name}'. "
                f"Must be one of: {', '.join(sorted(valid_formats))}"
            )
        
        # Validate match_mode
        valid_modes = {'word_boundary', 'substring'}
        if self.match_mode not in valid_modes:
            raise ValueError(
                f"Invalid match_mode '{self.match_mode}' for '{self.base_name}'. "
                f"Must be one of: {', '.join(sorted(valid_modes))}"
            )


class KeywordMatcher:
    """Apply keyword dictionaries to text data with optimized single-pass tokenization.
    
    Key optimization: Tokenizes text once for all dictionaries by building a combined
    vocabulary and splitting results afterward.
    
    Supports:
    - Multiple output formats (binary, count, set)
    - Nested dictionary structures (flatten or separate columns)
    - Batch processing from folder
    - Method chaining for pandas workflows
    
    Usage:
        # Register dictionaries, then process in one pass
        result = (
            KeywordMatcher(df, 'text_column')
            .add_dictionary('dict1.json', output_format='count')
            .add_dictionary('dict2.json', output_format='binary')
            .process()
        )
    """
    
    # Class constants
    DEFAULT_SUFFIXES = {
        'binary': 'tag',
        'count': 'distinct_hits',
        'set': 'matched_keywords'
    }
    
    def __init__(self, df: pd.DataFrame, text_column: str, copy: bool = True, verbose: bool = False):
        """
        Initialize matcher with DataFrame.
        
        Args:
            df: DataFrame containing text to match against
            text_column: Name of column containing text
            copy: If True, copies DataFrame; if False, modifies in place
            verbose: If True, logs detailed processing information including longest keywords
        
        Raises:
            ValueError: If text_column not in DataFrame
        """
        if text_column not in df.columns:
            available = ', '.join(list(df.columns)[:5])
            suffix = '...' if len(df.columns) > 5 else ''
            raise ValueError(
                f"Column '{text_column}' not found in DataFrame. "
                f"Available columns: {available}{suffix}"
            )
        
        self.df = df.copy() if copy else df
        self.text_column = text_column
        self.verbose = verbose
        self._dict_configs: list[DictConfig] = []
        self._processed = False
        
    def add_dictionary(
        self,
        dictionary: Union[str, Path, dict],
        dict_name: Optional[str] = None,
        flatten: bool = True,
        output_format: Literal['binary', 'count', 'set'] = 'count',
        match_mode: Literal['word_boundary', 'substring'] = 'word_boundary',
        case_sensitive: bool = False,
        replace_hyphens: bool = False,
        enforce_word_boundaries: bool = False,
        column_suffix: Optional[str] = None
    ) -> Self:
        """
        Register a dictionary for processing (doesn't process immediately).
        
        Call process() after adding all dictionaries to perform optimized single-pass matching.
        
        Args:
            dictionary: Either a path to JSON file (str/Path) or a dictionary object
            dict_name: Name for output columns (defaults to filename stem if path, or 'dictionary' if dict)
            flatten: If nested dict, combine all subcategories (True) 
                     or create separate columns per subcategory (False)
            output_format: 
                - 'binary': Single True/False column for any match
                - 'count': Count of unique concepts matched
                - 'set': Set of matched concepts (creates 2 columns: keywords + distinct_hits)
            match_mode:
                - 'word_boundary': Match complete words only (default, e.g., 'pilot' won't match 'piloting')
                - 'substring': Match keywords anywhere in text (e.g., 'pilot' matches 'piloting')
                               Requires pyahocorasick: pip install pyahocorasick
            case_sensitive: If True, matching is case-sensitive. If False (default), matching is case-insensitive
            replace_hyphens: If False (default), preserves hyphens in text and keywords during matching.
                           Set to True to replace hyphens with spaces (e.g., to match 'e-learning' as 'e learning')
            enforce_word_boundaries: If True, only match when keyword is at word boundaries.
                                   Only applies to 'substring' match_mode. Allows matching 'scale' in 'small-scale'
                                   but not in 'escalate'. Has no effect on 'word_boundary' mode.
            column_suffix: Override default suffix
                           (defaults: 'tag' for binary, 'distinct_hits' for count, 'matched_keywords' for set)
        
        Returns:
            self (for method chaining)
            
        Raises:
            FileNotFoundError: If dictionary is a path and doesn't exist
            ValueError: If JSON is invalid or dictionary is empty
            TypeError: If dictionary is neither a path nor a dict
        """
        # Handle dictionary input - can be path or dict object
        if isinstance(dictionary, dict):
            keywords_dict = dictionary
            # Use provided name or default
            if dict_name is None:
                dict_name = 'dictionary'
        elif isinstance(dictionary, (str, Path)):
            dict_path = Path(dictionary)
            
            if not dict_path.exists():
                raise FileNotFoundError(f"Dictionary file not found: {dict_path}")
            
            # Load dictionary from file
            try:
                with open(dict_path, 'r') as f:
                    keywords_dict = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {dict_path}: {e}")
            
            # Determine dictionary name from filename if not provided
            if dict_name is None:
                dict_name = dict_path.stem
        else:
            raise TypeError(
                f"dictionary must be a path (str/Path) or dict, got {type(dictionary).__name__}"
            )
        
        if not keywords_dict:
            raise ValueError(f"Empty dictionary provided")
        
        # Auto-detect nested structure
        is_nested = self._is_nested_dict(keywords_dict)
        
        # Validate keyword uniqueness within this dictionary
        if is_nested and flatten:
            self._validate_keyword_uniqueness(keywords_dict, dict_name, replace_hyphens)
        elif not is_nested:
            self._validate_keyword_uniqueness({'all': keywords_dict}, dict_name, replace_hyphens)
        
        if is_nested and not flatten:
            # Create separate configs for each subcategory
            for subcategory, concepts in keywords_dict.items():
                subcategory_name = self._sanitize_column_name(subcategory)
                col_name = subcategory_name
                self._dict_configs.append(
                    DictConfig(
                        keywords=concepts,
                        base_name=col_name,
                        output_format=output_format,
                        match_mode=match_mode,
                        case_sensitive=case_sensitive,
                        replace_hyphens=replace_hyphens,
                        enforce_word_boundaries=enforce_word_boundaries,
                        column_suffix=column_suffix
                    )
                )
        else:
            # Flatten nested dict or use as-is if already flat
            if is_nested:
                keywords_dict = self._flatten_dict(keywords_dict)
            self._dict_configs.append(
                DictConfig(
                    keywords=keywords_dict,
                    base_name=dict_name,
                    output_format=output_format,
                    match_mode=match_mode,
                    case_sensitive=case_sensitive,
                    replace_hyphens=replace_hyphens,
                    enforce_word_boundaries=enforce_word_boundaries,
                    column_suffix=column_suffix
                )
            )
        
        return self
    
    def add_folder(
        self,
        folder_path: str | Path,
        default_format: Literal['binary', 'count', 'set'] = 'count',
        flatten: bool = True,
        match_mode: Literal['word_boundary', 'substring'] = 'word_boundary',
        case_sensitive: bool = False,
        replace_hyphens: bool = False,
        enforce_word_boundaries: bool = False,
        custom_configs: Optional[dict] = None
    ) -> Self:
        """
        Register all JSON files in a folder for processing.

        Args:
            folder_path: Path to folder containing JSON files
            default_format: Default output format for all dicts
            flatten: Default flatten behavior for nested dicts
            match_mode: Default match mode ('word_boundary' or 'substring')
            case_sensitive: Default case sensitivity
            replace_hyphens: Default hyphen replacement behavior
            enforce_word_boundaries: Default word boundary enforcement (substring mode only)
            custom_configs: Override settings per dict, e.g.:
                {
                    'taxonomy': {'flatten': False, 'output_format': 'binary'},
                    'innovation': {'match_mode': 'substring', 'output_format': 'count'}
                }

        Returns:
            self (for method chaining)
        """
        folder_path = Path(folder_path)
        custom_configs = custom_configs or {}

        # Find all JSON files
        json_files = sorted(folder_path.glob('*.json'))

        for json_file in json_files:
            dict_name = json_file.stem

            # Get custom config for this dictionary
            config = custom_configs.get(dict_name, {})

            self.add_dictionary(
                dictionary=json_file,
                dict_name=dict_name,
                flatten=config.get('flatten', flatten),
                output_format=config.get('output_format', default_format),
                match_mode=config.get('match_mode', match_mode),
                case_sensitive=config.get('case_sensitive', case_sensitive),
                replace_hyphens=config.get('replace_hyphens', replace_hyphens),
                enforce_word_boundaries=config.get('enforce_word_boundaries', enforce_word_boundaries),
                column_suffix=config.get('column_suffix')
            )

        return self
    
    def process(self) -> pd.DataFrame:
        """
        Process all registered dictionaries in optimized passes.
        
        Groups dictionaries by match_mode and case_sensitive, then processes each group efficiently:
        - word_boundary: Single CountVectorizer pass per case-sensitivity setting
        - substring: Single Aho-Corasick pass per case-sensitivity setting
        
        Returns:
            DataFrame with all keyword match columns added
        """
        if self._processed:
            logger.warning("Already processed. Returning current DataFrame.")
            return self.df
        
        if not self._dict_configs:
            logger.warning(
                "No dictionaries registered. Use .add_dictionary() "
                "before calling .process(). Returning DataFrame unchanged."
            )
            return self.df
        
        # Group dictionaries by match_mode, case_sensitive, replace_hyphens, and enforce_word_boundaries
        for match_mode in ['word_boundary', 'substring']:
            for case_sensitive in [False, True]:
                for replace_hyphens in [False, True]:
                    for enforce_word_boundaries in [False, True]:
                        configs = [
                            cfg for cfg in self._dict_configs 
                            if cfg.match_mode == match_mode 
                            and cfg.case_sensitive == case_sensitive
                            and cfg.replace_hyphens == replace_hyphens
                            and cfg.enforce_word_boundaries == enforce_word_boundaries
                        ]
                        
                        if not configs:
                            continue
                        
                        if match_mode == 'word_boundary':
                            self._process_word_boundary(configs, case_sensitive, replace_hyphens)
                        else:
                            self._process_substring(configs, case_sensitive, replace_hyphens, enforce_word_boundaries)
        
        self._processed = True
        return self.df
    
    def _process_word_boundary(self, configs: list[DictConfig], case_sensitive: bool, replace_hyphens: bool):
        """Process dictionaries using word boundary matching (CountVectorizer).
        
        Args:
            configs: List of dictionary configurations to process
            case_sensitive: Whether to perform case-sensitive matching
            replace_hyphens: Whether to replace hyphens with spaces
        """
        # Build combined keyword-to-dict mapping
        keyword_to_dict_and_concept = {}
        for idx, config in enumerate(configs):
            for concept, kw_list in config.keywords.items():
                for kw in kw_list:
                    # Normalize based on case sensitivity and hyphen replacement
                    if replace_hyphens:
                        kw = kw.replace("-", " ")
                    if not case_sensitive:
                        kw = kw.lower()
                    # Store dict index and concept for this keyword
                    if kw not in keyword_to_dict_and_concept:
                        keyword_to_dict_and_concept[kw] = []
                    keyword_to_dict_and_concept[kw].append((idx, concept))
        
        # Create single vectorizer with ALL keywords
        all_keywords = list(keyword_to_dict_and_concept.keys())
        
        if not all_keywords:
            logger.warning("No keywords found in registered dictionaries.")
            return
        
        max_n_words = max(len(kw.split()) for kw in all_keywords)
        
        if self.verbose:
            longest_keyword = max(all_keywords, key=lambda kw: len(kw.split()))
            logger.info(f"Longest keyword: '{longest_keyword}' with {max_n_words} words")
        
        logger.info(f"Processing {len(configs)} dictionaries with {len(all_keywords)} unique keywords (case_sensitive={case_sensitive}, replace_hyphens={replace_hyphens})")
        
        vectorizer = CountVectorizer(
            vocabulary=all_keywords,
            lowercase=not case_sensitive,  # Only lowercase if case-insensitive
            token_pattern=r"\b[\w-]+\b" if not replace_hyphens else r"\b\w+\b",
            ngram_range=(1, max_n_words)  # To include multi-word keywords
        )
        
        # Tokenize ONCE for all dictionaries
        # Normalize text: fillna, convert to string, optionally replace hyphens with spaces
        text_series = (
            self.df[self.text_column]
            .fillna('')
            .astype(str)
        )
        
        if replace_hyphens:
            text_series = text_series.str.replace("-", " ", regex=False)
        
        # Apply lowercase only if case-insensitive
        if not case_sensitive:
            text_series = text_series.str.lower()
        
        keyword_match_matrix = vectorizer.fit_transform(text_series)
        matched_features = vectorizer.get_feature_names_out()
        
        # Split results by dictionary and add columns
        for dict_idx, config in enumerate(configs):
            # Find which keywords belong to this dictionary
            relevant_kw_indices = {
                i for i, kw in enumerate(matched_features)
                if any(idx == dict_idx for idx, _ in keyword_to_dict_and_concept[kw])
            }
            
            # Extract matches for this dictionary only
            matched_keywords_col = []
            for row_idx in range(len(self.df)):
                matched_kw_indices = keyword_match_matrix[row_idx].nonzero()[1]
                
                # Filter to keywords from this dict and get their concepts
                concepts = set()
                for kw_idx in matched_kw_indices:
                    if kw_idx in relevant_kw_indices:
                        kw = matched_features[kw_idx]
                        # Get concepts for this keyword from this specific dict
                        for idx, concept in keyword_to_dict_and_concept[kw]:
                            if idx == dict_idx:
                                concepts.add(concept)
                
                matched_keywords_col.append(concepts)
            
            distinct_hits = [len(kws) for kws in matched_keywords_col]
            
            # Add columns based on output format
            self._add_result_columns(config, matched_keywords_col, distinct_hits)
    
    def _process_substring(self, configs: list[DictConfig], case_sensitive: bool, replace_hyphens: bool, enforce_word_boundaries: bool = False):
        """Process dictionaries using substring matching (Aho-Corasick).
        
        Args:
            configs: List of dictionary configurations to process
            case_sensitive: Whether to perform case-sensitive matching
            replace_hyphens: Whether to replace hyphens with spaces
            enforce_word_boundaries: Whether to enforce word boundaries for matches
        """
        
        # Build Aho-Corasick automaton with all keywords from substring configs
        automaton = ahocorasick.Automaton()
        
        # Map keywords to (config_idx, concept) tuples
        keyword_to_dict_and_concept = {}
        for idx, config in enumerate(configs):
            for concept, kw_list in config.keywords.items():
                for kw in kw_list:
                    # Normalize based on case sensitivity and hyphen replacement
                    if replace_hyphens:
                        kw = kw.replace("-", " ")
                    if not case_sensitive:
                        kw = kw.lower()
                    if kw not in keyword_to_dict_and_concept:
                        keyword_to_dict_and_concept[kw] = []
                        # Add to automaton only once per unique keyword
                        automaton.add_word(kw, kw)
                    keyword_to_dict_and_concept[kw].append((idx, concept))
        
        automaton.make_automaton()
        
        total_keywords = len(keyword_to_dict_and_concept)
        if self.verbose:
            longest_keyword = max(keyword_to_dict_and_concept.keys(), key=len)
            logger.info(f"[substring] Longest keyword: '{longest_keyword}' ({len(longest_keyword)} chars)")
        
        logger.info(f"Processing {len(configs)} dictionaries (substring mode) with {total_keywords} unique keywords (case_sensitive={case_sensitive}, replace_hyphens={replace_hyphens}, enforce_word_boundaries={enforce_word_boundaries})")
        
        # Normalize text once
        text_series = (
            self.df[self.text_column]
            .fillna('')
            .astype(str)
        )
        
        # Optionally replace hyphens
        if replace_hyphens:
            text_series = text_series.str.replace("-", " ", regex=False)
        
        # Apply lowercase only if case-insensitive
        if not case_sensitive:
            text_series = text_series.str.lower()
        
        # Process each dictionary
        for dict_idx, config in enumerate(configs):
            matched_keywords_col = []
            
            for text in text_series:
                concepts = set()
                # Find all keyword matches in this text
                for end_index, found_kw in automaton.iter(text):
                    # Check word boundaries if enforced
                    if enforce_word_boundaries:
                        start_index = end_index - len(found_kw) + 1
                        
                        # Check character before match (if not at start)
                        if start_index > 0:
                            char_before = text[start_index - 1]
                            if char_before.isalnum() or char_before == '_':
                                continue  # Not at word boundary
                        
                        # Check character after match (if not at end)
                        if end_index < len(text) - 1:
                            char_after = text[end_index + 1]
                            if char_after.isalnum() or char_after == '_':
                                continue  # Not at word boundary
                    
                    # Get concepts for this keyword from this specific dict
                    for idx, concept in keyword_to_dict_and_concept[found_kw]:
                        if idx == dict_idx:
                            concepts.add(concept)
                
                matched_keywords_col.append(concepts)
            
            distinct_hits = [len(kws) for kws in matched_keywords_col]
            
            # Add columns based on output format
            self._add_result_columns(config, matched_keywords_col, distinct_hits)
    
    def _add_result_columns(
        self,
        config: DictConfig,
        matched_keywords: list[set],
        distinct_hits: list[int]
    ):
        """Add result columns to DataFrame based on configuration."""
        column_suffix = config.column_suffix or self.DEFAULT_SUFFIXES[config.output_format]
        if config.output_format == 'binary':
            self.df[f"{config.base_name}_{column_suffix}"] = [int(hits > 0) for hits in distinct_hits]
        elif config.output_format == 'count':
            self.df[f"{config.base_name}_{column_suffix}"] = distinct_hits
        elif config.output_format == 'set':
            self.df[f"{config.base_name}_{column_suffix}"] = matched_keywords
            self.df[f"{config.base_name}_distinct_hits"] = distinct_hits
    
    # Convenience class methods for pandas .pipe() integration
    
    @classmethod
    def apply_folder_pipe(
        cls,
        df: pd.DataFrame,
        text_column: str,
        folder_path: str | Path,
        default_format: Literal['binary', 'count', 'set'] = 'count',
        flatten: bool = True,
        match_mode: Literal['word_boundary', 'substring'] = 'word_boundary',
        case_sensitive: bool = False,
        replace_hyphens: bool = False,
        enforce_word_boundaries: bool = False,
        custom_configs: Optional[dict] = None,
        verbose: bool = False
    ) -> pd.DataFrame:
        """
        Convenience method for .pipe() usage in pandas chains.

        Usage:
            df.pipe(
                KeywordMatcher.apply_folder_pipe,
                text_column='lessons',
                folder_path='data/reference/keywords/',
                default_format='count',
                custom_configs={'taxonomy': {'flatten': False}},
                verbose=True
            )

        Args:
            df: Input DataFrame
            text_column: Column containing text to match
            folder_path: Path to folder with JSON keyword files
            default_format: Default output format
            flatten: Default flatten behavior
            match_mode: Default match mode ('word_boundary' or 'substring')
            case_sensitive: Default case sensitivity
            replace_hyphens: Default hyphen replacement behavior
            enforce_word_boundaries: Default word boundary enforcement (substring mode only)
            custom_configs: Per-dictionary custom settings
            verbose: If True, logs detailed processing information

        Returns:
            DataFrame with keyword match columns added
        """
        return (
            cls(df, text_column, verbose=verbose)
            .add_folder(
                folder_path=folder_path,
                default_format=default_format,
                flatten=flatten,
                match_mode=match_mode,
                case_sensitive=case_sensitive,
                replace_hyphens=replace_hyphens,
                enforce_word_boundaries=enforce_word_boundaries,
                custom_configs=custom_configs
            )
            .process()
        )
    
    @classmethod
    def apply_dictionary_pipe(
        cls,
        df: pd.DataFrame,
        text_column: str,
        dictionary: Union[str, Path, dict],
        dict_name: Optional[str] = None,
        flatten: bool = True,
        output_format: Literal['binary', 'count', 'set'] = 'count',
        match_mode: Literal['word_boundary', 'substring'] = 'word_boundary',
        case_sensitive: bool = False,
        replace_hyphens: bool = False,
        enforce_word_boundaries: bool = False,
        column_suffix: Optional[str] = None,
        verbose: bool = False
    ) -> pd.DataFrame:
        """
        Convenience method for applying a single dictionary in .pipe().
        
        Usage:
            df.pipe(
                KeywordMatcher.apply_dictionary_pipe,
                text_column='lessons',
                dictionary='innovation_keywords.json',  # or pass a dict directly
                output_format='count',
                match_mode='substring',
                verbose=True
            )
        
        Args:
            df: Input DataFrame
            text_column: Column containing text
            dictionary: Path to JSON keyword file (str/Path) or dictionary object
            dict_name: Optional name for columns
            flatten: Whether to flatten nested dicts
            output_format: Output format type
            match_mode: 'word_boundary' (default) or 'substring'
            case_sensitive: If True, matching is case-sensitive
            replace_hyphens: If False (default), preserves hyphens. Set to True to replace with spaces
            enforce_word_boundaries: If True, only match at word boundaries (substring mode only)
            column_suffix: Optional column suffix override
            verbose: If True, logs detailed processing information
            
        Returns:
            DataFrame with keyword match columns added
        """
        return (
            cls(df, text_column, verbose=verbose)
            .add_dictionary(
                dictionary=dictionary,
                dict_name=dict_name,
                flatten=flatten,
                output_format=output_format,
                match_mode=match_mode,
                case_sensitive=case_sensitive,
                replace_hyphens=replace_hyphens,
                enforce_word_boundaries=enforce_word_boundaries,
                column_suffix=column_suffix
            )
            .process()
        )
    
    # Private helper methods
    
    def _is_nested_dict(self, d: dict) -> bool:
        """Check if dictionary has nested structure (categories with concepts)."""
        if not d:
            return False
        first_value = next(iter(d.values()))
        return isinstance(first_value, dict)
    
    def _flatten_dict(self, nested_dict: dict) -> dict:
        """Flatten nested dictionary: {category: {concept: [kws]}} -> {concept: [kws]}."""
        flattened = {}
        for category, concepts in nested_dict.items():
            for concept in concepts:
                if concept in flattened:
                    logger.warning(
                        f"Duplicate concept key '{concept}' in category '{category}' "
                        f"overwrites an earlier definition during flattening."
                    )
            flattened.update(concepts)
        return flattened
    
    def _sanitize_column_name(self, name: str) -> str:
        """Convert category name to valid column name."""
        return name.lower().replace(' ', '_').replace('/', '_').replace('-', '_')
    
    def _validate_keyword_uniqueness(self, keywords_dict: dict, dict_name: str, replace_hyphens: bool = False):
        """Warn if same keyword appears in multiple concepts within one dictionary.

        This helps identify potential issues where a keyword might match multiple
        concepts, leading to double-counting in the results.

        Args:
            keywords_dict: Dictionary structure (potentially nested)
            dict_name: Name of dictionary for logging
            replace_hyphens: Whether hyphens will be normalized to spaces during matching
        """
        seen_keywords = {}

        # Handle nested dictionaries
        if self._is_nested_dict(keywords_dict):
            # Flatten for validation
            flat_dict = {}
            for category, concepts in keywords_dict.items():
                for concept, kw_list in concepts.items():
                    full_concept_name = f"{category}/{concept}"
                    flat_dict[full_concept_name] = kw_list
            keywords_dict = flat_dict

        # Check for duplicate keywords
        for concept, kw_list in keywords_dict.items():
            for kw in kw_list:
                normalized = kw.lower()
                if replace_hyphens:
                    normalized = normalized.replace("-", " ")
                if normalized in seen_keywords:
                    logger.warning(
                        f"Dictionary '{dict_name}': keyword '{kw}' appears in both "
                        f"'{seen_keywords[normalized]}' and '{concept}'. "
                        f"Matches will count toward both concepts."
                    )
                else:
                    seen_keywords[normalized] = concept