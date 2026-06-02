"""
Success metric computation with statistical confidence.

Design principles
-----------------
1. Binary proxy:   completed=1, terminated/withdrawn=0, all others=censored (None)
2. Confidence:     Wilson score interval (handles small n correctly)
3. Suppression:    strata with n_evaluable < MIN_N are flagged, not silently reported
4. Transparency:   every aggregation carries n_total, n_evaluable, n_completed, n_failed

Why Wilson, not normal approximation?
   - Normal CI (p ± 1.96√(p(1-p)/n)) breaks at p=0 or p=1 (zero-width interval)
   - Wilson CI is asymmetric and correct for small samples
"""

import warnings
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

MIN_N = 10  # Minimum evaluable trials to report a rate


# ─── Wilson confidence interval ───────────────────────────────────────────────

def wilson_ci(n_success: int, n_total: int,
              alpha: float = 0.05) -> tuple[float, float, float]:
    """
    Wilson score confidence interval for a proportion.
    Returns (point_estimate, lower_bound, upper_bound).
    """
    if n_total == 0:
        return (np.nan, np.nan, np.nan)

    z = stats.norm.ppf(1 - alpha / 2)
    p_hat = n_success / n_total
    denominator = 1 + z**2 / n_total
    centre = (p_hat + z**2 / (2 * n_total)) / denominator
    margin = z * np.sqrt(p_hat * (1 - p_hat) / n_total + z**2 / (4 * n_total**2)) / denominator

    return (
        round(p_hat, 4),
        round(max(0, centre - margin), 4),
        round(min(1, centre + margin), 4),
    )


# ─── Group-level success rate ─────────────────────────────────────────────────

def compute_success_rate(group: pd.Series) -> dict:
    """
    Given a Series of binary_success values (1, 0, or None/NaN),
    return a dict with counts and Wilson CI.
    None = censored → excluded from denominator.
    """
    evaluable = group.dropna()
    n_total = len(group)
    n_evaluable = len(evaluable)
    n_completed = int((evaluable == 1).sum())
    n_failed = int((evaluable == 0).sum())

    point, lo, hi = wilson_ci(n_completed, n_evaluable)

    return {
        "n_total": n_total,
        "n_evaluable": n_evaluable,          # total - censored
        "n_completed": n_completed,
        "n_failed": n_failed,
        "n_censored": n_total - n_evaluable,
        "completion_rate": point,
        "ci_lower": lo,
        "ci_upper": hi,
        "suppressed": n_evaluable < MIN_N,   # flag small strata
    }


# ─── Stratified analysis ──────────────────────────────────────────────────────

def stratified_success(df: pd.DataFrame,
                        group_cols: list[str],
                        min_n: int = MIN_N) -> pd.DataFrame:
    """
    Compute success rates stratified by group_cols.
    Always uses binary_success as outcome.
    """
    records = []
    for keys, group in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        result = compute_success_rate(group["binary_success"])
        row = dict(zip(group_cols, keys))
        row.update(result)
        records.append(row)

    out = pd.DataFrame(records)
    out = out.sort_values("n_evaluable", ascending=False)
    return out