import pandas as pd
import numpy as np
from pathlib import Path
from ._paths import DATA_ROOT
from keyword_matcher import KeywordMatcher


def match_innovation_keywords(df: pd.DataFrame, keywords_dir: Path = None) -> pd.DataFrame:
    """Match innovation keywords in project lessons

    Args:
        df: DataFrame with a 'lessons' column
        keywords_dir: Path to the keywords directory. Defaults to the canonical
            data/reference/keywords path under the analysis root.

    Returns:
        DataFrame with 'keywords' (set of matched concepts) and 'distinct_hits' (count) columns
    """
    if keywords_dir is None:
        keywords_dir = DATA_ROOT / "reference" / "keywords"
    KEYWORDS_FILEPATH = keywords_dir / "innovation_keywords.json"
    df = (
        KeywordMatcher(
            df=df,
            text_column="lessons",
            copy=True
        )
        .add_dictionary(keywords_dir / "top_models_keywords.json", dict_name="top_models", flatten=False, output_format='binary', match_mode='substring')
        .add_dictionary(keywords_dir / "taxonomy_keywords.json", dict_name="taxonomy", flatten=False, output_format='binary', match_mode='substring')
        .add_dictionary(keywords_dir / "pcm_keywords.json", dict_name="pcm", flatten=False, output_format='binary', match_mode='substring')
        .add_dictionary(keywords_dir / "ifc_keywords.json", dict_name="ifc", flatten=False, output_format='binary', match_mode='substring', case_sensitive=True)
        .add_dictionary(keywords_dir / "pilot_scale_keywords.json", dict_name="pilot_scale", flatten=False, output_format="binary", match_mode="substring")
        .process()
    )

    df = (
        KeywordMatcher(
            df=df,
            text_column="lessons",
            copy=True
        )
        .add_dictionary(KEYWORDS_FILEPATH, dict_name="innovation", flatten=True, output_format='set', match_mode='word_boundary', replace_hyphens=True)
        .process()
        .assign(
            innovation_tier = lambda x: x.innovation_distinct_hits.case_when([
                (x.innovation_distinct_hits <= 1, "Low"),
                (x.innovation_distinct_hits <= 3, "Moderate"),
                (x.innovation_distinct_hits >= 4, "High"),
            ]),
            high_innovation = lambda x:  np.where(x.innovation_tier.isin(["High","Moderate"]),1, 0),
            has_no_category = lambda x: (x.operational_institutional_tag + x.technological_tag + x.financial_tag + x.collaborative_tag) == 0,
            operational_institutional_tag = lambda x: x.operational_institutional_tag.mask(x.has_no_category, 1),
            pilot_category=lambda x: np.where(
                (x.pilot_tag == 1) & (x.scale_tag == 1), "Pilot + Scaled",
                np.where(
                    (x.pilot_tag == 1) & (x.scale_tag == 0), "Pilot Only",
                    "No Pilot"
                )
            )
        )
    )

    return df