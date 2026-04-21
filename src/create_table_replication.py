"""Table generation functions for PRWP 2025 analysis.

All table functions expect a preprocessed DataFrame to be passed in.
External scripts should load and prepare data once, then pass to these functions.
"""

import pandas as pd
import numpy as np

# Constants

INNOVATION_TYPES = {
    'operational_institutional_tag': 'Operational/Institutional',
    'technological_tag': 'Technological',
    'collaborative_tag': 'Collaborative',
    'financial_tag': 'Financial'
}

INNOVATION_MODELS = {
    'digital_government_tag': 'Digital government platform/portal/services',
    'ppp_tag': 'Public-private partnership (PPP)',
    'e_procurement_tag': 'Electronic procurement (e-procurement)',
    'cdd_tag': 'Community-driven development (CDD)',
    'e_learning_tag': 'Electronic learning (e-learning)',
    'remote_sensing_tag': 'Remote sensing',
    'mobile_banking_tag': 'Mobile banking',
    'biometric_id_tag': 'Biometric ID',
    'cct_tag': 'Conditional cash transfers (CCT)'
}

PILOT_CATEGORIES = ["Pilot + Scaled", "Pilot Only", "No Pilot"]

HM_LABELS = {1: "High + Moderate Innovative Projects", 0: "Low Innovation"}

GP_THRESHOLD = 0.003  # Minimum share of projects for a GP to be included
PCM_GP_THRESHOLD = 0.11   # Minimum PCM share for a GP to appear in Table 3.16

# Helper functions
def _add_percentage_columns(pivot_df: pd.DataFrame, suffix_from='(Number)', suffix_to='(%)', format_str='{:.1f}%') -> pd.DataFrame:
    """Add percentage columns next to count columns in pivot table.

    Args:
        pivot_df: Pivot table with count columns
        suffix_from: Suffix to identify count columns
        suffix_to: Suffix for percentage columns
        format_str: Format string for percentage display

    Returns:
        DataFrame with percentage columns added
    """
    result = pivot_df.copy().assign(total=lambda x: x.sum(axis=1))
    for col in pivot_df.columns:
        if suffix_from in str(col):
            pct_col = str(col).replace(suffix_from, suffix_to)
            result[pct_col] = pivot_df[col].div(result["total"]).round(3)

    result = result.drop(columns=['total'])
    # Reorder columns
    ordered_cols = []
    num_cols = sorted([c for c in pivot_df.columns if suffix_from in str(c)])
    for col in num_cols:
        ordered_cols.extend([col, str(col).replace(suffix_from, suffix_to)])

    return result[ordered_cols]

def _create_decade_summary(df: pd.DataFrame, labels: dict) -> pd.DataFrame:
    """Create summary table by decade for multiple innovation dimensions.

    Args:
        df: Input DataFrame
        labels: Dict mapping column names to display labels

    Returns:
        Concatenated DataFrame with decade summaries
    """
    return (
        df
        .filter(['decade', *labels.keys()])
        .groupby(['decade'])
        .agg({key: 'sum' for key in labels.keys()})
        .rename(columns=labels)
        .T
        .assign(Total = lambda x: x.sum(axis=1))
        .rename_axis(None, axis=1)
        .reset_index(names=['Innovation Type'])
    )


def _create_decade_pivot(df: pd.DataFrame, innovation_model: str, col_names: list) -> pd.DataFrame:
    """Create decade pivot for a specific innovation model.

    Used by tables E3-E10.

    Args:
        df: Input DataFrame
        innovation_model: Column name for innovation model
        col_names: List of column names for output

    Returns:
        Pivot table by decade
    """
    return (
        df[df[innovation_model] == 1]
        .groupby('decade')
        .agg({
            'project_id': 'nunique',
            'high_innovation': ['sum', 'mean']
        })
        .round(3)
        .reset_index()
        .set_axis(['Evaluation decade'] + col_names[1:], axis=1)
    )


def _create_decade_fcs_pivot(df: pd.DataFrame, innovation_model: str, col_names: list) -> pd.DataFrame:
    """Create decade pivot split by FCS status for a specific innovation model.

    Used by tables F2-F5.

    Args:
        df: Input DataFrame
        innovation_model: Column name for innovation model
        col_names: List of column names for output [decade_col, fcs_col, non_fcs_col]

    Returns:
        Pivot table by decade and FCS status
    """
    return (
        df.groupby(['decade', 'fcs_status'])[innovation_model]
        .sum()
        .unstack('fcs_status')
        .assign(**{'Total': lambda x: x.sum(axis=1)})
        .reset_index()
        .rename(columns={'decade': col_names[0], 'FCS': col_names[1], 'Non-FCS': col_names[2]})
        .pipe(lambda x: x[[col_names[0], col_names[1], col_names[2], 'Total']])
        .rename_axis(None, axis=1)
    )


def _add_totals_row(df: pd.DataFrame, position: str = 'bottom') -> pd.DataFrame:
    """Append or prepend a totals row (column-wise sum) to a DataFrame."""
    total = df.sum().to_frame().T.astype(df.dtypes)
    frames = [df, total] if position == 'bottom' else [total, df]
    return pd.concat(frames)


# Table generation functions
# All functions take df as a parameter and return a DataFrame

def create_table_3_1(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.1: Project distribution by cohort and innovation tier."""
    return (
        df.assign(innovation=lambda x: x.high_innovation.map(HM_LABELS))
        .groupby(['cohort', 'innovation'])['project_id'].nunique()
        .unstack('innovation')
        .rename_axis(None, axis=1)
        .pipe(lambda x: x.rename(columns={col: f'{col} (Number)' for col in x.columns}))
        .pipe(_add_percentage_columns)
        .reset_index(drop=False)
        .rename(columns= {'cohort':'Cohort',
                          'High + Moderate Innovative Projects (%)':'High + Moderate Innovation (%)', 
                          'Low Innovation (Number)':'Low Innovative Projects (Number)'})
    )


def create_table_3_2(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.2: Mean high innovation by cohort."""
    return (
        df.groupby('cohort')['high_innovation']
        .mean()
        .round(3)
        .to_frame()
        .reset_index()
        .rename(columns= {'cohort':'Cohort',
                          'high_innovation':'Share of High + Moderate Innovative Projects (%)'})
    )


def create_table_3_3(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.3: Pilot and scale analysis by cohort."""
    return (
        df
        .assign(has_pilot_and_scale=lambda x: x.pilot_category == "Pilot + Scaled")
        .groupby("cohort")
        .agg(**{
            "Total projects": ("project_id", "nunique"),
            "With pilot": ("pilot_tag", "sum"),
            "With pilot and scale in same lessons": ("has_pilot_and_scale", "sum")
        })
        .assign(
            **{'% of all projects with pilot': lambda x: round(x['With pilot'] / x['Total projects'], 3)},
            **{'% of pilots that do not mention scaling': lambda x: round(
                1 - x['With pilot and scale in same lessons'] / x['With pilot'], 3
            )}
        )
        .reset_index()
        .rename(columns={'cohort': 'Cohort'})
    )


def create_table_3_5(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.5: Innovation types in high + moderate innovative projects."""
    results = []
    filter_dummy = 'high_innovation'

    for dummy, label in INNOVATION_TYPES.items():
        innovative = df[(df[dummy] == 1) & (df[filter_dummy] == 1)]['project_id'].nunique()
        pct = round(innovative / df[filter_dummy].sum(), 2)

        results.append({
            'Innovation Type': label,
            'High + Moderate Innovative Projects': innovative,
            'High + Moderate Innovative Projects (%)': pct
        })

    return pd.DataFrame(results)


def create_table_3_6(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.6: Innovation types by decade for high innovation projects."""
    return _create_decade_summary(
        df=df.query('high_innovation == 1'),
        labels=INNOVATION_TYPES
    )


def create_table_3_7(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.7: Regional portfolio analysis."""
    return (
        df
        .groupby(['wb_region'])
        .agg(
            total = ('project_id', pd.Series.nunique),
            hm_count = ('high_innovation', 'sum'),
        )
        .assign(hm_share = lambda x: (x.hm_count / x.total).round(3))
        .reset_index()
        .sort_values('hm_share', ascending=False)
        .pipe(lambda x: pd.concat([
            x[x['wb_region'] != 'Other/Regional-Global'], 
            x[x['wb_region'] == 'Other/Regional-Global']
        ], ignore_index=True))
        .rename(columns={
            'wb_region': 'World Bank Region',
            'total': 'All Projects',
            'hm_count': 'High + Moderate Innovative Projects',
            'hm_share': '% of Region Portfolio'
        })
        .reset_index(drop=True)
    )


def create_table_3_8(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.8: FCS portfolio analysis."""
    return (
        df
        .groupby(['fcs_status'])
        .agg(
            hm_count = ('high_innovation', 'sum'),
            total = ('project_id', pd.Series.nunique)
        )
        .assign(
            hm_share = lambda x: (x.hm_count / x.total).round(3)
        )
        .reset_index()
        .rename(columns={
            'fcs_status': 'Portfolio Slice',
            'hm_count': 'High + Moderate Innovative Projects',
            'total': 'Total Projects',
            'hm_share': 'Share High + Moderate Innovative Projects (%)'
        })
    )


def _get_top_gps(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df
        .groupby('global_practice')['project_id'].nunique()
        .div(df['project_id'].nunique())
        .to_frame()
        .reset_index()
        .sort_values("project_id")
        .pipe(lambda x: x.loc[x["project_id"] > GP_THRESHOLD]["global_practice"])
        .sort_values()
        .to_list()
    )


def create_table_3_9(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.9: Global practice portfolio analysis."""
    rep_gps = _get_top_gps(df)
    
    return (
        df
        .groupby('global_practice')
        .agg(
            total = ('project_id', pd.Series.nunique),
            hm_count = ('high_innovation', 'sum'),
        )
        .assign(hm_share = lambda x: (x.hm_count / x.total).round(3))
        .reset_index()
        .sort_values('hm_share', ascending=False)
        .rename(columns={
            'global_practice': 'GP',
            'total': 'All Projects',
            'hm_count': 'High + Moderate Innovative Projects',
            'hm_share': '% of Sectoral Portfolio'
        })
        .query('GP != "Other"')
        .reset_index(drop=True)
        .pipe(lambda x: x.loc[x["GP"].isin(rep_gps)].reset_index(drop=True))
    )


def create_table_3_11(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.11: Technology premium by innovation tier."""
    return (
        df.assign(innovation=lambda x: x.high_innovation.map(HM_LABELS))
        .groupby(['innovation', 'technological_tag'])['ieg_outcome_ratings_num'].mean()
        .unstack('technological_tag')
        .round(2)
        .assign(**{"Technology Premium": lambda x: x[1] - x[0]})
        .rename(columns={1: "Mean Outcome (Technology)", 0: "Mean Outcome (No Technology)"})
        .reset_index()
        .rename(columns={'innovation': 'Innovation Tier'}
                )
        .rename_axis(None, axis=1)

    )


def create_table_3_12(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.12: Technology premium by global practice for high innovation projects."""
    rep_gps = create_table_3_9(df)['GP'].tolist()

    return (
        df.assign(innovation=lambda x: x.high_innovation.map(HM_LABELS))
        .loc[lambda x: (x["innovation"] == "High + Moderate Innovative Projects") & (x["global_practice"].isin(rep_gps))]
        .groupby(['global_practice', 'technological_tag'])['ieg_outcome_ratings_num'].mean()
        .unstack('technological_tag')
        .assign(**{"Raw Technology Premium": lambda x: x[1] - x[0]})
        .reindex(rep_gps)
        .reset_index()
        .rename_axis(None, axis=1)
        .round(2)
        .rename(columns={'global_practice': 'GP',1: "Mean Outcome (Technology)", 0: "Mean Outcome (No Technology)"})
        .assign(
            GP=lambda x: x["GP"].replace({'Macroeconomics, Trade and Investment': 'Macroeconomics, Trade and Investment (MTI)',
                  'Finance, Competitiveness and Innovation': 'Finance, Competitiveness and Innovation (FCI)'
        }))
        .sort_values(by ='Raw Technology Premium', ascending= True, na_position='first')
        .reset_index(drop=True)
    )


def create_table_3_13(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.13: Innovation by IFC mention"""
    return (
        df
        .groupby(['ifc_tag'])
        .agg(
            hm_count = ('high_innovation', 'sum'),
            low_count = ('high_innovation', lambda x: (x == 0).sum()),
            total=('project_id', 'count'),
        )
        .reset_index()
        .pipe(_add_totals_row)
        .assign(
            ifc_tag = ['No IFC Mention', 'With IFC Mention', 'Total']
        )
        .rename(columns={
            'ifc_tag': 'IFC Mention in Lessons',
            'hm_count': 'High + Moderate Innovation Projects',
            'low_count': 'Low Innovation Projects',
            'total': 'Total'
        })
        .reset_index(drop=True)
    )


def create_table_3_15(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3.15: PCM project mentions across portfolio slices."""
    grouped = (
        df
        .assign(hm_group=lambda x: x.high_innovation.map({1: 'HM', 0: 'L'}))
        .groupby(['hm_group'])
        .agg(
            total=('project_id', 'count'),
            pcm_count=('pcm_tag', 'sum')
        )
        .reset_index()
    )

    all_row = pd.DataFrame({
        'hm_group': ['All Projects'],
        'total': [grouped['total'].sum()],
        'pcm_count': [grouped['pcm_count'].sum()],
    })
    hm_row = (
        grouped
        .query("hm_group == 'HM'")
        .assign(hm_group='High + Moderate Innovative Projects')
    )

    return (
        pd.concat([all_row, hm_row], ignore_index=True)
        .assign(share=lambda x: (x.pcm_count / x.total).astype(float).round(3))
        .drop(columns=['total'])
        .rename(columns={
            'hm_group': 'Portfolio slice',
            'pcm_count': 'Projects mentioning PCM',
            'share': 'Share of portfolio slice'
        })
    )


def create_table_3_16(df: pd.DataFrame) -> pd.DataFrame:
    rep_gps = _get_top_gps(df)

    return (
        df
        .query("global_practice in @rep_gps")
        .groupby(['global_practice'])
        .agg(
            total=('project_id', 'count'),
            pcm_count = ('pcm_tag', 'sum')
        )
        .reset_index()
        .assign(
            share = lambda x: (x.pcm_count / x.total).astype(float).round(3),
        )
        .sort_values('share', ascending=False)
        .reset_index(drop=True)
        .query("share > @PCM_GP_THRESHOLD")
        .rename(columns={
            'global_practice': 'GP',
            'total': 'Total Projects',
            'pcm_count': 'PCM Projects',
            'share': '% with PCM'
        })
    )

def create_table_4_1(df: pd.DataFrame) -> pd.DataFrame:
    """Table 4.1: Pilot categories in high innovation projects."""
    df_high = df.query('high_innovation == 1')
    total_high_innovation = df_high['high_innovation'].sum()
    results = []

    for label in PILOT_CATEGORIES:
        total = df_high[df_high['pilot_category'] == label]['project_id'].nunique()
        pct = round(total / total_high_innovation, 2)

        results.append({
            'High + Moderate \nInnovation Projects': label,
            'Projects': total,
            'Portfolio Share': pct,
        })

    return pd.DataFrame(results)

def create_table_D_1(df: pd.DataFrame) -> pd.DataFrame:
    """Table D.1: Project counts by innovation tier."""
    return (
        df['innovation_tier']
        .value_counts()
        .to_frame()
        .reset_index()
        .assign(pct=lambda x: round(x['count'] / x['count'].sum(), 3))
        .rename(columns={'count': 'Total Projects', 'innovation_tier': 'Innovation tier', 'pct': 'Share of total projects (%)'})
    )


def _create_rating_table(df: pd.DataFrame, rating_col: str, shorten_hm_label: bool = False) -> pd.DataFrame:
    """Build the 'all projects + split by innovation tier' rating table used by D.2a–d.

    Args:
        df: Processed DataFrame.
        rating_col: Column with numeric IEG rating values.
        shorten_hm_label: If True, renames 'High + Moderate Innovative Projects'
            to 'High + Moderate Innovative' in the Projects column (used by D.2c/d).
    """
    overall_mean = df[rating_col].mean().round(2)
    all_row = pd.DataFrame({
        'Projects': ['All'],
        'Average Rating': overall_mean,
        'Difference from Overall': ['-'],
        '% Difference': ['-'],
    })
    split = (
        df.assign(innovation=lambda x: x.high_innovation.map(HM_LABELS))
        .groupby('innovation')[rating_col]
        .mean()
        .round(2)
        .to_frame()
        .reset_index()
        .rename(columns={'innovation': 'Projects', rating_col: 'Average Rating'})
    )
    if shorten_hm_label:
        split['Projects'] = split['Projects'].replace(
            {'High + Moderate Innovative Projects': 'High + Moderate Innovative'}
        )
    split = split.assign(
        **{'Difference from Overall': lambda x: (x['Average Rating'] - overall_mean).round(2)},
        **{'% Difference': lambda x: round(x['Difference from Overall'] / overall_mean, 3)},
    )
    return pd.concat([all_row, split], ignore_index=True, sort=False)


def create_table_D_2a(df: pd.DataFrame) -> pd.DataFrame:
    """Table D.2a: IEG outcome ratings by innovation tier."""
    return _create_rating_table(df, 'ieg_outcome_ratings_num')


def create_table_D_2b(df: pd.DataFrame) -> pd.DataFrame:
    """Table D.2b: Bank performance ratings by innovation tier."""
    return _create_rating_table(df, 'ieg_bank_performance_ratings_num')


def create_table_D_2c(df: pd.DataFrame) -> pd.DataFrame:
    """Table D.2c: Quality of supervision ratings by innovation tier."""
    return _create_rating_table(df, 'ieg_quality_of_supervision_ratings_num', shorten_hm_label=True)


def create_table_D_2d(df: pd.DataFrame) -> pd.DataFrame:
    """Table D.2d: Quality at entry ratings by innovation tier."""
    return _create_rating_table(df, 'ieg_quality_at_entry_ratings_num', shorten_hm_label=True)

def create_table_E_1(df: pd.DataFrame) -> pd.DataFrame:
    """Table E.1: Total mentions of innovation models."""
    model_cols = [
        'remote_sensing_tag', 'ppp_tag', 'e_learning_tag',
        'biometric_id_tag', 'e_procurement_tag', 'cdd_tag', 'cct_tag',
        'digital_government_tag', 'mobile_banking_tag'
    ]

    return (
        df[model_cols]
        .sum()
        .sort_values(ascending=False)
        .to_frame()
        .reset_index()
        .rename(columns={'index': 'Innovation Model', 0: 'Total Mentions'})
        .assign(
            **{'Innovation Model': lambda x: x['Innovation Model'].replace(INNOVATION_MODELS)}
        )
    )


def create_table_E_2(df: pd.DataFrame) -> pd.DataFrame:
    """Table E.2: Innovation models by decade."""
    # Use subset of innovation models for E2
    models_subset = {
       'ppp_tag': 'Public-private partnership (PPP)',
        'cdd_tag': 'Community-driven development (CDD)',
        'cct_tag':'Conditional cash transfers (CCT)',
        'e_procurement_tag': 'Electronic procurement (e-procurement)',
    }

    return (
        _create_decade_summary(
            df=df,
            labels=models_subset
        )
        .drop(columns='Total')
        .rename(columns={'Innovation Type': 'Innovation Model'})
    )


def create_table_E_5(df: pd.DataFrame) -> pd.DataFrame:
    """Table E.5: PPP model by decade."""
    return _create_decade_pivot(
        df=df,
        innovation_model='ppp_tag',
        col_names=[
            'Evaluation decade',
            'PPP model in All Projects',
            'PPP model in High + Moderate Innovative Projects',
            'Share framed as innovation (%)'
        ]
    )


def create_table_E_10(df: pd.DataFrame) -> pd.DataFrame:
    """Table E.10: CDD model by decade."""
    return _create_decade_pivot(
        df=df,
        innovation_model='cdd_tag',
        col_names=[
            'Evaluation decade',
            'CDD model in All Projects',
            'CDD model in High + Moderate Innovative Projects',
            'Share framed as innovation'
        ]
    )


def create_table_F_1(df: pd.DataFrame) -> pd.DataFrame:
    """Table F.1: Innovation models by FCS status."""
    # Use subset of top 4 innovation models for F1
    models_subset = {
        'ppp_tag': 'Public-private partnership (PPP)',
        'cdd_tag': 'Community-driven development (CDD)',
        'cct_tag':'Conditional cash transfers (CCT)',
        'e_procurement_tag': 'Electronic procurement (e-procurement)',
    }

    results = []

    for dummy, label in models_subset.items():
        table = (
            df[df[dummy] == 1]
            .groupby([dummy, 'fcs_status'])['project_id'].nunique()
            .unstack('fcs_status')
            .assign(**{'Total Mentions': lambda x: x.sum(axis=1)})
            .reset_index()
            .assign(**{dummy: lambda x: x[dummy].replace(1, label)})
            .rename(columns={dummy: 'Innovation Model',
                             'FCS': 'FCS Mentions',
                             'Non-FCS': 'Non-FCS Mentions'})
            .rename_axis(None, axis=1)

        )
        results.append(table)

    return pd.concat(results, ignore_index=True)


def create_table_F_2(df: pd.DataFrame) -> pd.DataFrame:
    """Table F.2: Conditional cash transfers by decade and FCS status."""
    return _create_decade_fcs_pivot(
        df=df,
        innovation_model='cct_tag',
        col_names=['Decade', 'FCS Mentions', 'Non-FCS Mentions']
    )


def create_table_F_3(df: pd.DataFrame) -> pd.DataFrame:
    """Table F.3: PPP model by decade and FCS status."""
    return _create_decade_fcs_pivot(
        df=df,
        innovation_model='ppp_tag',
        col_names=['Decade', 'FCS Mentions', 'Non-FCS Mentions']
    )


def create_table_F_4(df: pd.DataFrame) -> pd.DataFrame:
    """Table F.4: E-procurement model by decade and FCS status."""
    return _create_decade_fcs_pivot(
        df=df,
        innovation_model='e_procurement_tag',
        col_names=['Decade', 'FCS Mentions', 'Non-FCS Mentions']
    )


def create_table_F_5(df: pd.DataFrame) -> pd.DataFrame:
    """Table F.5: CDD model by decade and FCS status."""
    return _create_decade_fcs_pivot(
        df=df,
        innovation_model='cdd_tag',
        col_names=['Decade', 'FCS Mentions', 'Non-FCS Mentions']
    )

