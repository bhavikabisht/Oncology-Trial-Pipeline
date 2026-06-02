import pandas as pd
import duckdb
import logging
import os

def compute_success_proxy(status):
    if pd.isna(status): return None
    s = str(status).upper()
    if 'COMPLETED' in s: return 1
    if s in ['WITHDRAWN', 'SUSPENDED', 'TERMINATED']: return 0
    return None

def build_all_tables(df_raw: pd.DataFrame) -> dict:
    logging.info("Building Dimensional Model (Star Schema)...")
    df = df_raw.copy()
    
    df['binary_success'] = df['recruitment_status'].apply(compute_success_proxy)
    
    if 'start_date' in df.columns:
        df['start_year'] = pd.to_datetime(df['start_date'], errors='coerce').dt.year
    else:
        df['start_year'] = None
        
    fact_cols = ['nct_id', 'start_date', 'start_year', 'completion_date', 'duration_days', 
                 'study_type', 'recruitment_status', 'binary_success']
    trials = df[[c for c in fact_cols if c in df.columns]].copy()
    
    trial_indications = df[['nct_id', 'indications']].explode('indications').dropna()
    trial_indications = trial_indications.rename(columns={'indications': 'indication'})
    
    trial_drugs = df[['nct_id', 'interventions_drugs']].explode('interventions_drugs').dropna()
    trial_drugs = trial_drugs.rename(columns={'interventions_drugs': 'drug'})
    
    trial_technologies = df[['nct_id', 'main_technologies']].explode('main_technologies').dropna()
    trial_technologies = trial_technologies.rename(columns={'main_technologies': 'technology'})
    
    if 'target_names' in df.columns:
        trial_targets_flat = df[['nct_id', 'target_names']].explode('target_names').dropna()
        trial_targets_flat = trial_targets_flat.rename(columns={'target_names': 'target'})
    else:
        trial_targets_flat = pd.DataFrame(columns=['nct_id', 'target'])
    
    if 'phase' in df.columns:
        df['phase_list'] = df['phase'].astype(str).str.split('/')
        trial_phases = df[['nct_id', 'phase_list']].explode('phase_list').dropna()
        trial_phases = trial_phases.rename(columns={'phase_list': 'phase'})
        trial_phases['phase'] = trial_phases['phase'].str.strip()
        trial_phases.loc[trial_phases['phase'] == 'NAN', 'phase'] = 'UNKNOWN'
    else:
        trial_phases = pd.DataFrame(columns=['nct_id', 'phase'])
    
    return {
        'trials': trials,
        'trial_indications': trial_indications,
        'trial_drugs': trial_drugs,
        'trial_technologies': trial_technologies,
        'trial_targets_flat': trial_targets_flat,
        'trial_phases': trial_phases
    }

def save_to_duckdb(tables: dict, db_path: str):
    logging.info(f"Loading tables into DuckDB at {db_path}...")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = duckdb.connect(db_path)
    for table_name, df_table in tables.items():
        conn.register('temp_df', df_table)
        conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM temp_df")
    return conn
