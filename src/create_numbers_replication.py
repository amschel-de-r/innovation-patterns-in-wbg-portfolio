import pandas as pd
import janitor

def create_numbers_summary(raw:pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """
    Create summary statistics for the replication of numbers in the paper.
    """
    ifc_outcome = df.groupby('ifc_tag')['ieg_outcome_ratings_num'].mean()

    hm_mask = df['innovation_tier'].isin(['High', 'Moderate'])
    low_mask = df['innovation_tier'] == 'Low'

    portfolio_mean = df['ieg_outcome_ratings_num'].mean()
    hm_mean = df.loc[hm_mask, 'ieg_outcome_ratings_num'].mean()
    low_mean = df.loc[low_mask, 'ieg_outcome_ratings_num'].mean()

    return pd.DataFrame([
        # Corpus counts (para 91)
        {'Label': 'Total Projects',              'Value': df['project_id'].nunique(),             'Para': 91},
        {'Label': 'Reviews',                     'Value': len(raw),                               'Para': 91},
        {'Label': 'ICRR (post-dedup)',           'Value': (df['evaluation_type'] == 'ICRR').sum(),'Para': 91},
        {'Label': 'PPAR (post-dedup)',           'Value': (df['evaluation_type'] == 'PPAR').sum(),'Para': 91},
        {'Label': 'Both PPAR & ICRR',            'Value': raw.pipe(janitor.clean_names).groupby('project_id')['evaluation_type'].nunique().eq(2).sum(), 'Para': 91},
        # Innovation tiers (para 286)
        {'Label': 'Number of HM projects',       'Value': df['high_innovation'].sum(),            'Para': 286},
        # IFC collaboration stats (para 276)
        {'Label': 'IFC-tagged projects (total)', 'Value': int(df['ifc_tag'].sum()),               'Para': 276},
        {'Label': 'IFC-tagged HM projects',      'Value': int(df.loc[hm_mask, 'ifc_tag'].sum()), 'Para': 276},
        {'Label': 'IFC-tagged Low projects',     'Value': int(df.loc[low_mask, 'ifc_tag'].sum()),'Para': 276},
        {'Label': '% HM with IFC',               'Value': round(df.loc[hm_mask, 'ifc_tag'].mean() * 100, 1), 'Para': 276},
        {'Label': '% Low with IFC',              'Value': round(df.loc[low_mask, 'ifc_tag'].mean() * 100, 1), 'Para': 276},
        # PCM stats (para 286)
        {'Label': '% full portfolio with PCM',   'Value': round(df['pcm_tag'].mean() * 100, 1),  'Para': 286},
        {'Label': '% HM with PCM',               'Value': round(df.loc[hm_mask, 'pcm_tag'].mean() * 100, 1), 'Para': 286},
        # Outcome premium (para 303)
        {'Label': 'Portfolio mean outcome',      'Value': round(portfolio_mean, 4),               'Para': 303},
        {'Label': 'HM/Moderate mean outcome',    'Value': round(hm_mean, 4),                      'Para': 303},
        {'Label': 'HM/Moderate outcome diff',    'Value': round(hm_mean - portfolio_mean, 4),     'Para': 303},
        {'Label': 'HM/Moderate outcome diff %',  'Value': round((hm_mean - portfolio_mean) / portfolio_mean * 100, 1), 'Para': 303},
        {'Label': 'Low mean outcome',            'Value': round(low_mean, 4),                     'Para': 303},
        {'Label': 'Low outcome diff',            'Value': round(low_mean - portfolio_mean, 4),    'Para': 303},
        {'Label': 'Low outcome diff %',          'Value': round((low_mean - portfolio_mean) / portfolio_mean * 100, 1), 'Para': 303},
        # IFC outcome comparison
        {'Label': 'Avg outcome non-IFC',         'Value': ifc_outcome.iloc[0],                   'Para': None},
        {'Label': 'Avg outcome IFC',             'Value': ifc_outcome.iloc[1],                   'Para': None},
    ])

def create_ifc_gp_table(df: pd.DataFrame) -> pd.DataFrame:
        return (df.loc[(df['ifc_tag'] == 1)]['global_practice'].value_counts())

def create_ifc_country_table(df: pd.DataFrame) -> pd.DataFrame:
        return (df.loc[(df['ifc_tag'] == 1)]['country'].value_counts())