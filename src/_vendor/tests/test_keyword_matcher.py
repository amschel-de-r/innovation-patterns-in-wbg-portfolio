"""Unit tests for KeywordMatcher class.

These tests validate the core functionality of the KeywordMatcher class
using synthetic test data. They focus on:
- Correct initialization and configuration
- Proper dictionary loading and processing
- Accurate keyword matching logic
- Expected output formats
- Edge case handling

These tests are independent of any specific replication or real-world dataset.
"""
import logging
import pytest
import pandas as pd
import json
from keyword_matcher.core import KeywordMatcher, DictConfig

# ============================================================================
# CORE UNIT TESTS
# ============================================================================

# --- Initialization Tests (3 tests) ---

def test_initialization_with_valid_dataframe():
    """Test KeywordMatcher initializes correctly with valid DataFrame and column."""
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'text': ['sample text', 'another text', 'more text']
    })
    
    matcher = KeywordMatcher(df, 'text')
    
    assert matcher.text_column == 'text'
    assert len(matcher.df) == 3
    assert matcher._processed == False
    assert len(matcher._dict_configs) == 0


def test_initialization_raises_on_missing_column():
    """Test ValueError raised when text_column doesn't exist in DataFrame."""
    df = pd.DataFrame({
        'id': [1, 2],
        'text': ['sample', 'text']
    })
    
    with pytest.raises(ValueError, match="Column 'nonexistent' not found in DataFrame"):
        KeywordMatcher(df, 'nonexistent')


def test_initialization_copy_vs_inplace():
    """Test that copy=True creates copy, copy=False modifies original DataFrame."""
    original_df = pd.DataFrame({
        'id': [1, 2],
        'text': ['test', 'sample']
    })
    
    # Test copy=True (default)
    matcher_copy = KeywordMatcher(original_df, 'text', copy=True)
    matcher_copy.df['new_col'] = [10, 20]
    assert 'new_col' not in original_df.columns
    
    # Test copy=False (in-place)
    matcher_inplace = KeywordMatcher(original_df, 'text', copy=False)
    matcher_inplace.df['another_col'] = [30, 40]
    assert 'another_col' in original_df.columns


# --- Dictionary Loading Tests (4 tests) ---

def test_add_dictionary_flat_structure(tmp_path):
    """Test adding a flat dictionary structure {concept: [keywords]}."""
    # Create test dictionary
    test_dict = {
        "innovation": ["innovative", "innovation"],
        "digital": ["digital", "digitalization"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({'text': ['innovative approach', 'digital tools']})
    matcher = KeywordMatcher(df, 'text')
    matcher.add_dictionary(dict_path)
    
    # Should have one config added
    assert len(matcher._dict_configs) == 1
    assert matcher._dict_configs[0].base_name == 'test_dict'
    assert matcher._dict_configs[0].keywords == test_dict


def test_add_dictionary_nested_structure_flattened(tmp_path):
    """Test adding nested dict with flatten=True combines all categories."""
    # Create nested dictionary
    nested_dict = {
        "technology": {
            "innovation": ["innovative", "innovation"],
            "digital": ["digital"]
        },
        "methods": {
            "pilot": ["pilot", "piloting"]
        }
    }
    dict_path = tmp_path / "nested_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(nested_dict, f)
    
    df = pd.DataFrame({'text': ['test']})
    matcher = KeywordMatcher(df, 'text')
    matcher.add_dictionary(dict_path, flatten=True)
    
    # Should have one config with flattened keywords
    assert len(matcher._dict_configs) == 1
    expected_flat = {
        "innovation": ["innovative", "innovation"],
        "digital": ["digital"],
        "pilot": ["pilot", "piloting"]
    }
    assert matcher._dict_configs[0].keywords == expected_flat


def test_add_dictionary_nested_structure_separate(tmp_path):
    """Test adding nested dict with flatten=False creates separate columns per category."""
    nested_dict = {
        "technology": {
            "innovation": ["innovative"],
            "digital": ["digital"]
        },
        "methods": {
            "pilot": ["pilot"]
        }
    }
    dict_path = tmp_path / "nested_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(nested_dict, f)
    
    df = pd.DataFrame({'text': ['test']})
    matcher = KeywordMatcher(df, 'text')
    matcher.add_dictionary(dict_path, flatten=False)
    
    # Should have separate config for each category
    assert len(matcher._dict_configs) == 2
    config_names = {cfg.base_name for cfg in matcher._dict_configs}
    assert config_names == {'technology', 'methods'}


def test_add_dictionary_file_not_found():
    """Test FileNotFoundError raised for non-existent dictionary file."""
    df = pd.DataFrame({'text': ['test']})
    matcher = KeywordMatcher(df, 'text')
    
    with pytest.raises(FileNotFoundError, match="Dictionary file not found"):
        matcher.add_dictionary('/nonexistent/path/to/dict.json')


# --- Output Format Tests ---

@pytest.mark.parametrize("output_format,expected_columns", [
    ("binary", ["dict_name_tag"]),
    ("count", ["dict_name_distinct_hits"]),
    ("set", ["dict_name_matched_keywords", "dict_name_distinct_hits"]),
])
def test_output_formats_create_correct_columns(output_format, expected_columns, tmp_path):
    """Test each output format creates expected column names."""
    test_dict = {
        "concept1": ["keyword1", "keyword2"]
    }
    dict_path = tmp_path / "dict_name.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({'text': ['keyword1 is here', 'no match']})
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, output_format=output_format)
        .process()
    )
    
    for col in expected_columns:
        assert col in result.columns, f"Expected column {col} not found"


def test_custom_column_suffix(tmp_path):
    """Test column_suffix parameter overrides default suffixes."""
    test_dict = {
        "concept1": ["keyword1"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({'text': ['keyword1']})
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, output_format='binary', column_suffix='custom_suffix')
        .process()
    )
    
    assert 'test_dict_custom_suffix' in result.columns
    assert 'test_dict_tag' not in result.columns


# --- Text Matching Tests (3 tests) ---

def test_exact_keyword_match(tmp_path):
    """Test exact keyword matches are found correctly."""
    test_dict = {
        "innovation": ["innovative"],
        "pilot": ["pilot"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({
        'text': [
            'This is innovative work',
            'We ran a pilot program',
            'No matches here'
        ]
    })
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, output_format='count')
        .process()
    )
    
    assert result['test_dict_distinct_hits'].tolist() == [1, 1, 0]


def test_case_insensitive_matching(tmp_path):
    """Test keywords match regardless of case."""
    test_dict = {
        "innovation": ["Innovation", "INNOVATIVE"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({
        'text': [
            'innovation is key',
            'INNOVATION matters',
            'Innovative approach',
            'innovative solutions'
        ]
    })
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, output_format='count')
        .process()
    )
    
    # All should match (case-insensitive)
    assert all(result['test_dict_distinct_hits'] == 1)


def test_hyphen_normalization(tmp_path):
    """Test hyphens in keywords and text are normalized to spaces."""
    test_dict = {
        "tech": ["e-commerce", "co-creation"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({
        'text': [
            'e-commerce platform',      # Hyphen in text
            'e commerce platform',      # Space in text
            'co-creation workshop',     # Hyphen in text
            'co creation workshop'      # Space in text
        ]
    })
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, output_format='count', replace_hyphens=True)
        .process()
    )
    
    # All should match (hyphens normalized to spaces)
    assert result['test_dict_distinct_hits'].tolist() == [1, 1, 1, 1]


def test_replace_hyphens_false_preserves_hyphens():
    r"""Test replace_hyphens=False: hyphens preserved, only exact matches work.
    
    Token pattern: \b[\w-]+\b (treats hyphenated words as single tokens)
    """
    test_dict = {
        "scale": ["scaled-up"],
        "learning": ["e-learning"],
        "multi": ["well-thought-out"]  # Multiple hyphens
    }
    
    df = pd.DataFrame({
        'text': [
            'scaled-up project',           # Match: exact hyphen
            'scaled up project',           # No match: spaces instead of hyphen
            'e-learning platform',         # Match: exact hyphen
            'well-thought-out plan',       # Match: multiple hyphens preserved
            'well thought out plan',       # No match: spaces instead
        ]
    })
    
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(test_dict, output_format='binary', replace_hyphens=False)
        .process()
    )
    
    # Check matches
    assert result.iloc[0]['dictionary_tag'] == 1  # scaled-up matches
    assert result.iloc[1]['dictionary_tag'] == 0  # scaled up doesn't
    assert result.iloc[2]['dictionary_tag'] == 1  # e-learning matches
    assert result.iloc[3]['dictionary_tag'] == 1  # well-thought-out matches
    assert result.iloc[4]['dictionary_tag'] == 0  # well thought out doesn't


def test_replace_hyphens_true_normalizes_to_spaces():
    r"""Test replace_hyphens=True: hyphens → spaces, matches both forms.
    
    Token pattern: \b[\w]+\b (standard word tokenization)
    Both 'scaled-up' and 'scaled up' normalized to 'scaled up' before matching.
    """
    test_dict = {
        "scale": ["scaled-up"],
        "learning": ["e-learning"],
        "multi": ["well-thought-out"]
    }
    
    df = pd.DataFrame({
        'text': [
            'scaled-up project',      # Match: hyphen → space
            'scaled up project',      # Match: already spaces
            'e-learning platform',    # Match: hyphen → space
            'well-thought-out plan',  # Match: hyphens → spaces
            'well thought out plan',  # Match: already spaces
        ]
    })
    
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(test_dict, output_format='binary', replace_hyphens=True)
        .process()
    )
    
    # All should match after normalization
    assert all(result['dictionary_tag'] == 1)


# --- Edge Case Tests (5 tests) ---

def test_empty_text_handling(tmp_path):
    """Test NaN, None, and empty strings handled without errors."""
    test_dict = {
        "innovation": ["innovative"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({
        'text': [
            'innovative',
            None,
            '',
            pd.NA,
            'another innovative'
        ]
    })
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, output_format='count')
        .process()
    )
    
    # Should handle empty values without errors
    assert result['test_dict_distinct_hits'].tolist() == [1, 0, 0, 0, 1]


def test_no_keywords_match(tmp_path):
    """Test rows with no matches return 0 counts and empty sets."""
    test_dict = {
        "innovation": ["innovative"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({
        'text': ['nothing matches here', 'same here']
    })
    
    # Test count format
    result_count = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, output_format='count')
        .process()
    )
    assert all(result_count['test_dict_distinct_hits'] == 0)
    
    # Test set format
    result_set = (
        KeywordMatcher(df, 'text', copy=True)
        .add_dictionary(dict_path, output_format='set')
        .process()
    )
    assert all(result_set['test_dict_matched_keywords'].apply(lambda x: len(x) == 0))


def test_multi_word_keyword_matching(tmp_path):
    """Test multi-word keywords (n-grams) match correctly."""
    test_dict = {
        "innovation": ["innovation ecosystem", "digital transformation"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({
        'text': [
            'The innovation ecosystem is growing',
            'We focus on digital transformation projects',
            'innovation or ecosystem alone'  # Should not match
        ]
    })
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, output_format='count')
        .process()
    )
    
    assert result['test_dict_distinct_hits'].tolist() == [1, 1, 0]


def test_overlapping_keywords_count_correctly(tmp_path):
    """Test when multiple keywords map to same concept, counted once."""
    test_dict = {
        "innovation": ["innovative", "innovation", "innovate"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({
        'text': [
            'innovative innovation innovate',  # All 3 keywords but same concept
            'innovative',
            'innovation'
        ]
    })
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, output_format='count')
        .process()
    )
    
    # All rows match the same single concept "innovation"
    assert result['test_dict_distinct_hits'].tolist() == [1, 1, 1]


def test_multiple_dictionaries_single_pass(tmp_path):
    """Test multiple dictionaries processed in one optimized pass."""
    dict1 = {"innovation": ["innovative"]}
    dict2 = {"digital": ["digital", "digitalization"]}
    
    dict1_path = tmp_path / "dict1.json"
    dict2_path = tmp_path / "dict2.json"
    
    with open(dict1_path, 'w') as f:
        json.dump(dict1, f)
    with open(dict2_path, 'w') as f:
        json.dump(dict2, f)
    
    df = pd.DataFrame({
        'text': [
            'innovative digital tools',
            'innovative only',
            'digitalization only',
            'neither'
        ]
    })
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict1_path, output_format='count')
        .add_dictionary(dict2_path, output_format='count')
        .process()
    )
    
    # Both dictionary columns should exist
    assert 'dict1_distinct_hits' in result.columns
    assert 'dict2_distinct_hits' in result.columns
    
    # Check counts
    assert result['dict1_distinct_hits'].tolist() == [1, 1, 0, 0]
    assert result['dict2_distinct_hits'].tolist() == [1, 0, 1, 0]


# --- Integration Tests (2 tests) ---

def test_apply_dictionary_pipe(tmp_path):
    """Test apply_dictionary_pipe() classmethod works in pandas .pipe() chain."""
    test_dict = {
        "innovation": ["innovative", "innovation"]
    }
    dict_path = tmp_path / "test_dict.json"
    with open(dict_path, 'w') as f:
        json.dump(test_dict, f)
    
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'text': ['innovative approach', 'no match', 'innovation here']
    })
    
    # Use in .pipe() chain
    result = df.pipe(
        KeywordMatcher.apply_dictionary_pipe,
        text_column='text',
        dictionary=dict_path,
        output_format='count'
    )
    
    # Should have original columns plus keyword column
    assert 'id' in result.columns
    assert 'text' in result.columns
    assert 'test_dict_distinct_hits' in result.columns
    assert result['test_dict_distinct_hits'].tolist() == [1, 0, 1]


def test_apply_folder_pipe(tmp_path):
    """Test apply_folder_pipe() classmethod works in pandas .pipe() chain."""
    (tmp_path / "dict_a.json").write_text(json.dumps({"concept1": ["keyword1"]}))
    (tmp_path / "dict_b.json").write_text(json.dumps({"concept2": ["keyword2"]}))
    df = pd.DataFrame({'text': ['keyword1', 'keyword2', 'keyword1 keyword2']})

    result = df.pipe(
        KeywordMatcher.apply_folder_pipe,
        text_column='text',
        folder_path=tmp_path
    )

    assert 'dict_a_distinct_hits' in result.columns
    assert 'dict_b_distinct_hits' in result.columns
    assert result['dict_a_distinct_hits'].tolist() == [1, 0, 1]
    assert result['dict_b_distinct_hits'].tolist() == [0, 1, 1]


# ============================================================================
# Additional Tests
# ============================================================================

def test_add_dictionary_invalid_json(tmp_path):
    """Test ValueError raised for malformed JSON file."""
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ not: valid json }")
    df = pd.DataFrame({'text': ['test']})
    matcher = KeywordMatcher(df, 'text')
    with pytest.raises(ValueError, match="Invalid JSON"):
        matcher.add_dictionary(bad_json)


def test_add_dictionary_empty_dict(tmp_path):
    """Test ValueError raised for empty dictionary."""
    empty_json = tmp_path / "empty.json"
    empty_json.write_text("{}")
    df = pd.DataFrame({'text': ['test']})
    matcher = KeywordMatcher(df, 'text')
    with pytest.raises(ValueError):
        matcher.add_dictionary(empty_json)


def test_add_dictionary_custom_name(tmp_path):
    """Test custom dict_name overrides filename stem."""
    dict_path = tmp_path / "my_dict.json"
    dict_path.write_text(json.dumps({"concept": ["keyword"]}))
    df = pd.DataFrame({'text': ['keyword']})
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_path, dict_name='custom')
        .process()
    )
    assert 'custom_distinct_hits' in result.columns
    assert 'my_dict_distinct_hits' not in result.columns


def test_duplicate_keywords_within_dictionary_warns(tmp_path, caplog):
    """Test warning logged when same keyword appears in multiple concepts."""
    dict_with_dupes = {
        "concept_a": ["shared_keyword"],
        "concept_b": ["shared_keyword"],
    }
    dict_path = tmp_path / "dupes.json"
    dict_path.write_text(json.dumps(dict_with_dupes))
    df = pd.DataFrame({'text': ['test']})
    with caplog.at_level(logging.WARNING, logger='keyword_matcher.core'):
        KeywordMatcher(df, 'text').add_dictionary(dict_path)
    assert any('shared_keyword' in r.message for r in caplog.records)


def test_duplicate_keywords_across_dictionaries_allowed():
    """Same keyword in different dictionaries is allowed (intentional overlap)."""
    dict_a = {"innovation": ["pilot"]}
    dict_b = {"feasibility": ["pilot"]}

    df = pd.DataFrame({'text': ['we ran a pilot program']})
    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(dict_a, dict_name='dict_a', output_format='binary')
        .add_dictionary(dict_b, dict_name='dict_b', output_format='binary')
        .process()
    )

    # Both dictionaries should independently match the shared keyword
    assert result['dict_a_tag'].tolist() == [1]
    assert result['dict_b_tag'].tolist() == [1]


def test_special_characters_in_text():
    """Text with punctuation and special characters doesn't break matching."""
    test_dict = {"term": ["innovation", "digital"]}

    df = pd.DataFrame({'text': [
        'innovation! digital?',           # Punctuation after keywords
        '(innovation) [digital]',         # Brackets around keywords
        'innovation, digital.',           # Comma/period separators
        '"innovation" & "digital"',       # Quotes and ampersand
        'innovation\tdigital',            # Tab separator
    ]})

    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(test_dict, output_format='count')
        .process()
    )

    assert all(result['dictionary_distinct_hits'] == 1)


def test_very_long_keyword_matches():
    """Keywords with many words (>10 words) are handled and matched correctly."""
    long_keyword = "sustainable development through inclusive green growth and climate resilience"
    test_dict = {"sustainability": [long_keyword]}

    df = pd.DataFrame({'text': [
        f"The project achieved {long_keyword} outcomes.",
        "The project achieved sustainable outcomes.",  # Partial — should not match
    ]})

    result = (
        KeywordMatcher(df, 'text')
        .add_dictionary(test_dict, output_format='binary')
        .process()
    )

    assert result['dictionary_tag'].tolist() == [1, 0]


def test_process_called_multiple_times_warns(tmp_path, caplog):
    """Test warning when process() called twice without reset."""
    dict_path = tmp_path / "dict.json"
    dict_path.write_text(json.dumps({"concept": ["keyword"]}))
    df = pd.DataFrame({'text': ['keyword']})
    matcher = KeywordMatcher(df, 'text').add_dictionary(dict_path)
    matcher.process()
    with caplog.at_level(logging.WARNING, logger='keyword_matcher.core'):
        matcher.process()
    assert any('Already processed' in r.message for r in caplog.records)


def test_add_folder_loads_all_json_files(tmp_path):
    """Test add_folder() discovers and loads all .json files."""
    (tmp_path / "dict_a.json").write_text(json.dumps({"c1": ["kw1"]}))
    (tmp_path / "dict_b.json").write_text(json.dumps({"c2": ["kw2"]}))
    df = pd.DataFrame({'text': ['kw1 kw2']})
    result = (
        KeywordMatcher(df, 'text')
        .add_folder(tmp_path)
        .process()
    )
    assert 'dict_a_distinct_hits' in result.columns
    assert 'dict_b_distinct_hits' in result.columns


def test_add_folder_with_custom_configs(tmp_path):
    """Test custom_configs parameter overrides per-dictionary settings."""
    (tmp_path / "dict_a.json").write_text(json.dumps({"c1": ["kw1"]}))
    df = pd.DataFrame({'text': ['kw1']})
    result = (
        KeywordMatcher(df, 'text')
        .add_folder(tmp_path, custom_configs={'dict_a': {'output_format': 'binary'}})
        .process()
    )
    assert 'dict_a_tag' in result.columns
    assert 'dict_a_distinct_hits' not in result.columns


def test_add_folder_empty_directory(tmp_path):
    """Test add_folder() handles directory with no JSON files gracefully."""
    df = pd.DataFrame({'text': ['test']})
    result = (
        KeywordMatcher(df, 'text')
        .add_folder(tmp_path)
        .process()
    )
    assert list(result.columns) == ['text']


# ============================================================================
# Parameter Validation Tests
# ============================================================================

def test_invalid_output_format_raises_error():
    """Test that invalid output_format raises ValueError with helpful message."""
    df = pd.DataFrame({'text': ['test']})
    matcher = KeywordMatcher(df, 'text')
    
    test_dict = {"concept": ["keyword"]}
    
    with pytest.raises(ValueError, match="Invalid output_format 'invalid'"):
        matcher.add_dictionary(test_dict, output_format='invalid')


def test_invalid_match_mode_raises_error():
    """Test that invalid match_mode raises ValueError with helpful message."""
    df = pd.DataFrame({'text': ['test']})
    matcher = KeywordMatcher(df, 'text')
    
    test_dict = {"concept": ["keyword"]}
    
    with pytest.raises(ValueError, match="Invalid match_mode 'invalid'"):
        matcher.add_dictionary(test_dict, match_mode='invalid')


def test_valid_output_formats_accepted():
    """Test that all valid output formats are accepted."""
    df = pd.DataFrame({'text': ['test']})
    test_dict = {"concept": ["keyword"]}
    
    for output_format in ['binary', 'count', 'set']:
        matcher = KeywordMatcher(df, 'text')
        # Should not raise
        matcher.add_dictionary(test_dict, output_format=output_format)


def test_valid_match_modes_accepted():
    """Test that all valid match modes are accepted."""
    df = pd.DataFrame({'text': ['test']})
    test_dict = {"concept": ["keyword"]}
    
    for match_mode in ['word_boundary', 'substring']:
        matcher = KeywordMatcher(df, 'text')
        # Should not raise
        matcher.add_dictionary(test_dict, match_mode=match_mode)


def test_enforce_word_boundaries_in_substring_mode():
    """Test enforce_word_boundaries=True prevents partial matches while allowing hyphen boundaries."""
    test_dict = {"scale": ["scale", "scaled-up"]}
    
    # Format: (text, expected_match)
    df = pd.DataFrame([
        ('small-scale project', 1),   # Match: hyphen boundary
        ('rescale the image', 0),     # No match: embedded
        ('scaled-up version', 1),     # Match: exact hyphenated keyword
        ('scale alone', 1),           # Match: standalone
    ], columns=['text', 'expected'])
    
    result = (
        KeywordMatcher(df[['text']], 'text')
        .add_dictionary(
            test_dict,
            match_mode='substring',
            replace_hyphens=False,
            enforce_word_boundaries=True,
            output_format='binary'
        )
        .process()
    )
    
    assert result['dictionary_tag'].tolist() == df['expected'].tolist()


def test_enforce_word_boundaries_with_punctuation_and_embedded():
    """Test word boundary enforcement with punctuation boundaries vs embedded matches."""
    test_dict = {"term": ["test", "scale"]}
    
    # Format: (text, expected_match)
    df = pd.DataFrame([
        ('test.', 1),           # Match: punctuation boundary
        ('a test, here', 1),    # Match: space/comma boundaries
        ('testing', 0),         # No match: embedded in word
        ('downscale', 0),       # No match: embedded in word
    ], columns=['text', 'expected'])
    
    result = (
        KeywordMatcher(df[['text']], 'text')
        .add_dictionary(
            test_dict,
            match_mode='substring',
            enforce_word_boundaries=True,
            output_format='binary'
        )
        .process()
    )
    
    assert result['dictionary_tag'].tolist() == df['expected'].tolist()


def test_enforce_word_boundaries_false_matches_substrings():
    """Test enforce_word_boundaries=False allows embedded matches (default substring behavior)."""
    test_dict = {"term": ["scale"]}
    
    # Format: (text, expected_match)
    df = pd.DataFrame([
        ('small-scale', 1),    # Match: boundaries not enforced
        ('downscale', 1),      # Match: boundaries not enforced
        ('rescale', 1),        # Match: boundaries not enforced
    ], columns=['text', 'expected'])
    
    result = (
        KeywordMatcher(df[['text']], 'text')
        .add_dictionary(
            test_dict,
            match_mode='substring',
            enforce_word_boundaries=False,
            output_format='binary'
        )
        .process()
    )
    
    assert result['dictionary_tag'].tolist() == df['expected'].tolist()


