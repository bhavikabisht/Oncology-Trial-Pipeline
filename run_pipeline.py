"""
End-to-end pipeline runner.
Usage: python run_pipeline.py --input data/raw/oncology_trials.csv
"""

import argparse
from pathlib import Path

from src.ingestion import load_and_clean
from src.profiling import generate_quality_report
from src.schema import build_all_tables, save_to_duckdb
from src.analysis import (
    overall_summary,
    phase_success,
    indication_phase_success,
    technology_success,
    phase_year_trend,
    technology_phase_success,
)
from src.visualization import (
    fig_phase_success,
    fig_technology_heatmap,
    fig_indication_bars,
    fig_temporal_trend,
    save_all_figures,
    fig_attrition_sankey
)


def main(input_path: str, db_path: str = "data/processed/oncology.duckdb") -> None:
    print("\n━━━ 1. LOADING & CLEANING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    df_raw = load_and_clean(input_path)
    print(f"  Loaded {len(df_raw):,} trials, {df_raw.shape[1]} columns")

    print("\n━━━ 2. DATA QUALITY REPORT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    generate_quality_report(df_raw)

    print("\n━━━ 3. SCHEMA NORMALISATION → DUCKDB ━━━━━━━━━━━━━━━━━━━━")
    tables = build_all_tables(df_raw)
    conn = save_to_duckdb(tables, db_path)

    print("\n━━━ 4. COHORT ANALYSIS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    summary = overall_summary(conn)
    print(f"  Total trials: {summary['total_trials']:,}")
    print(f"  Completed:    {summary['completed']:,}")
    print(f"  Failed:       {summary['failed']:,}")
    print(f"  Censored:     {summary['censored']:,}")

    phase_df = phase_success(conn)
    ind_df   = indication_phase_success(conn)
    tech_df  = technology_success(conn)
    trend_df = phase_year_trend(conn)
    tph_df   = technology_phase_success(conn)

    # Save CSVs
    Path("data/processed").mkdir(exist_ok=True)
    phase_df.to_csv("data/processed/phase_success.csv", index=False)
    ind_df.to_csv("data/processed/indication_phase_success.csv", index=False)
    tech_df.to_csv("data/processed/technology_success.csv", index=False)
    trend_df.to_csv("data/processed/phase_year_trend.csv", index=False)
    tph_df.to_csv("data/processed/technology_phase_success.csv", index=False)
    print("  ✓ Analysis CSVs saved to data/processed/")

    print("\n━━━ 5. VISUALISATIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    figures = {
        "phase_completion_rate":      fig_phase_success(phase_df),
        "technology_phase_heatmap":   fig_technology_heatmap(tph_df),
        "indication_completion_rate": fig_indication_bars(ind_df.groupby("indication", as_index=False).agg({
            "completion_rate": "mean", "n_evaluable": "sum",
            "ci_lower": "min", "ci_upper": "max", "suppressed": "any"
        })),
        "temporal_trend":             fig_temporal_trend(trend_df),
        "phase_attrition_sankey":     fig_attrition_sankey(phase_df)
    }
    save_all_figures(figures)

    print("\n━━━ DONE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Reports: reports/")
    print("  DB:      data/processed/oncology.duckdb")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/oncology_trials.csv")
    args = parser.parse_args()
    main(args.input)
