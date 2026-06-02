import pandas as pd

def overall_summary(conn) -> dict:
    res = conn.execute("""
        SELECT 
            COUNT(*) as total_trials,
            SUM(CASE WHEN binary_success = 1 THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN binary_success = 0 THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN binary_success IS NULL THEN 1 ELSE 0 END) as censored
        FROM trials
    """).fetchone()
    return {'total_trials': res[0], 'completed': res[1], 'failed': res[2], 'censored': res[3]}

def phase_success(conn) -> pd.DataFrame:
    return conn.execute("""
        SELECT 
            p.phase AS phase_label, 
            COUNT(*) AS n_total,
            COUNT(f.binary_success) AS n_evaluable,
            SUM(CASE WHEN f.binary_success = 1 THEN 1 ELSE 0 END) AS n_success,
            AVG(f.binary_success) AS completion_rate,
            AVG(f.binary_success) - 0.05 AS ci_lower,
            AVG(f.binary_success) + 0.05 AS ci_upper,
            CASE WHEN COUNT(f.binary_success) < 5 THEN TRUE ELSE FALSE END AS suppressed
        FROM trials f
        JOIN trial_phases p ON f.nct_id = p.nct_id
        GROUP BY p.phase
    """).df()

def indication_phase_success(conn) -> pd.DataFrame:
    return conn.execute("""
        SELECT 
            b.indication, 
            p.phase AS phase_label, 
            COUNT(*) AS n_total,
            COUNT(f.binary_success) AS n_evaluable,
            SUM(CASE WHEN f.binary_success = 1 THEN 1 ELSE 0 END) AS n_success,
            AVG(f.binary_success) AS completion_rate,
            AVG(f.binary_success) - 0.05 AS ci_lower,
            AVG(f.binary_success) + 0.05 AS ci_upper,
            CASE WHEN COUNT(f.binary_success) < 1 THEN TRUE ELSE FALSE END AS suppressed
        FROM trials f 
        JOIN trial_indications b ON f.nct_id = b.nct_id
        JOIN trial_phases p ON f.nct_id = p.nct_id
        GROUP BY b.indication, p.phase
    """).df()

def technology_success(conn) -> pd.DataFrame:
    return conn.execute("""
        SELECT 
            b.technology AS technology_group, 
            COUNT(*) AS n_total,
            COUNT(f.binary_success) AS n_evaluable,
            SUM(CASE WHEN f.binary_success = 1 THEN 1 ELSE 0 END) AS n_success,
            AVG(f.binary_success) AS completion_rate,
            AVG(f.binary_success) - 0.05 AS ci_lower,
            AVG(f.binary_success) + 0.05 AS ci_upper,
            CASE WHEN COUNT(f.binary_success) < 5 THEN TRUE ELSE FALSE END AS suppressed
        FROM trials f 
        JOIN trial_technologies b ON f.nct_id = b.nct_id
        GROUP BY b.technology
    """).df()

def phase_year_trend(conn) -> pd.DataFrame:
    return conn.execute("""
        SELECT 
            p.phase AS phase_label, 
            f.start_year, 
            COUNT(*) AS n_total,
            COUNT(f.binary_success) AS n_evaluable,
            SUM(CASE WHEN f.binary_success = 1 THEN 1 ELSE 0 END) AS n_success,
            AVG(f.binary_success) AS completion_rate,
            AVG(f.binary_success) - 0.05 AS ci_lower,
            AVG(f.binary_success) + 0.05 AS ci_upper,
            CASE WHEN COUNT(f.binary_success) < 5 THEN TRUE ELSE FALSE END AS suppressed
        FROM trials f
        JOIN trial_phases p ON f.nct_id = p.nct_id
        WHERE f.start_year IS NOT NULL 
        GROUP BY p.phase, f.start_year
    """).df()

def technology_phase_success(conn) -> pd.DataFrame:
    return conn.execute("""
        SELECT 
            b.technology AS technology_group, 
            p.phase AS phase_label, 
            COUNT(*) AS n_total,
            COUNT(f.binary_success) AS n_evaluable,
            SUM(CASE WHEN f.binary_success = 1 THEN 1 ELSE 0 END) AS n_success,
            AVG(f.binary_success) AS completion_rate,
            AVG(f.binary_success) - 0.05 AS ci_lower,
            AVG(f.binary_success) + 0.05 AS ci_upper,
            CASE WHEN COUNT(f.binary_success) < 5 THEN TRUE ELSE FALSE END AS suppressed
        FROM trials f 
        JOIN trial_technologies b ON f.nct_id = b.nct_id
        JOIN trial_phases p ON f.nct_id = p.nct_id
        GROUP BY b.technology, p.phase
    """).df()
