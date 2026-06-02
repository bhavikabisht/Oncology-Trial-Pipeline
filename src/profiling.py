"""
Data quality report: completeness, cardinality, dirty values, structural anomalies.
Outputs a rich HTML report and a JSON summary.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()


# ─── Completeness ────────────────────────────────────────────────────────────

def field_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-column completeness rate, null count, and unique count."""
    records = []
    for col in df.columns:
        series = df[col]
        # For list columns, count empty lists as null
        if series.dtype == object and series.apply(lambda x: isinstance(x, list)).any():
            null_mask = series.apply(
                lambda x: x is None or (isinstance(x, list) and len(x) == 0)
            )
        else:
            null_mask = series.isna() | (series.astype(str).str.strip() == "")

        n_null = null_mask.sum()
        n_total = len(series)
        n_unique = series.apply(
            lambda x: tuple(x) if isinstance(x, list) else x
        ).nunique()

        records.append({
            "column": col,
            "total": n_total,
            "non_null": n_total - n_null,
            "null_count": n_null,
            "completeness_%": round(100 * (n_total - n_null) / n_total, 1),
            "unique_count": n_unique,
            "cardinality_%": round(100 * n_unique / max(n_total - n_null, 1), 1),
        })
    return pd.DataFrame(records).sort_values("completeness_%")


# ─── Status / Phase value audit ───────────────────────────────────────────────

def audit_controlled_vocab(df: pd.DataFrame, col: str,
                            expected: set[str]) -> dict[str, Any]:
    """Return counts of expected vs. unexpected values in a column."""
    value_counts = df[col].value_counts().to_dict()
    unexpected = {k: v for k, v in value_counts.items() if k not in expected}
    return {
        "column": col,
        "value_counts": value_counts,
        "unexpected_values": unexpected,
        "n_unexpected": sum(unexpected.values()),
    }


# ─── Date anomalies ───────────────────────────────────────────────────────────

def audit_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Check for future start dates, completion before start, etc."""
    issues = []
    today = pd.Timestamp.today()

    for idx, row in df.iterrows():
        start = row.get("start_date")
        end = row.get("completion_date")
        prim = row.get("primary_completion_date")
        nct = row.get("nct_id", idx)

        if pd.notna(start) and pd.notna(end) and end < start:
            issues.append({"nct_id": nct, "issue": "completion_before_start",
                            "start": start, "completion": end})
        if pd.notna(prim) and pd.notna(end) and prim > end:
            issues.append({"nct_id": nct, "issue": "primary_completion_after_completion",
                            "primary": prim, "completion": end})

    return pd.DataFrame(issues)


# ─── Duplicate detection ──────────────────────────────────────────────────────

def detect_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    dup_nct = df[df.duplicated(subset=["nct_id"], keep=False)]
    dup_title = df[df.duplicated(subset=["brief_title"], keep=False)]
    return {
        "duplicate_nct_ids": len(dup_nct),
        "duplicate_titles": len(dup_title),
        "duplicate_nct_examples": dup_nct["nct_id"].head(5).tolist(),
    }


# ─── Full report ──────────────────────────────────────────────────────────────

def generate_quality_report(df: pd.DataFrame,
                             output_path: str = "reports/quality_report.json"
                             ) -> dict[str, Any]:
    """Generate and save a structured data quality report."""
    from src.config import PHASE_NORMALIZER, STATUS_MAP

    report: dict[str, Any] = {}

    # 1. Dimensions
    report["dimensions"] = {"rows": len(df), "columns": len(df.columns)}

    # 2. Completeness
    completeness_df = field_completeness(df)
    report["completeness"] = completeness_df.to_dict(orient="records")

    # 3. Status vocab audit
    expected_statuses = set(STATUS_MAP.keys())
    report["status_audit"] = audit_controlled_vocab(
        df, "recruitment_status", expected_statuses
    )

    # 4. Phase vocab audit
    expected_phases = set(PHASE_NORMALIZER.keys()) | {"UNKNOWN"}
    report["phase_audit"] = audit_controlled_vocab(
        df, "phase", expected_phases
    )

    # 5. Date anomalies
    date_issues = audit_dates(df)
    report["date_anomalies"] = {
        "count": len(date_issues),
        "examples": date_issues.head(10).to_dict(orient="records"),
    }

    # 6. Duplicates
    report["duplicates"] = detect_duplicates(df)

    # 7. Enrollment summary
    enroll = df["enrollment"].describe().to_dict()
    report["enrollment_summary"] = {k: round(v, 1) for k, v in enroll.items()}

    # 8. Missing dates count
    for dcol in ["start_date", "completion_date", "primary_completion_date"]:
        report[f"{dcol}_null_count"] = int(df[dcol].isna().sum())

    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary to console
    _print_summary(report)
    return report


def _print_summary(report: dict) -> None:
    console.rule("[bold cyan]Data Quality Report")
    console.print(f"[green]Rows:[/] {report['dimensions']['rows']}")
    console.print(f"[green]Columns:[/] {report['dimensions']['columns']}")

    t = Table(title="Field Completeness (worst 10)", show_lines=True)
    t.add_column("Column", style="cyan")
    t.add_column("Completeness %", justify="right")
    t.add_column("Null Count", justify="right")
    for row in sorted(report["completeness"], key=lambda x: x["completeness_%"])[:10]:
        t.add_row(row["column"], str(row["completeness_%"]), str(row["null_count"]))
    console.print(t)