# Oncology Trial Success Rate Pipeline

> **i3 Digital Health — Data Engineering Assignment**  
> End-to-end pipeline: raw flat-file → normalised DuckDB schema → stratified success rate analysis

---

## Quick Start

```bash
git clone https://github.com/bhavikabisht/oncology-trial-pipeline
cd oncology-trial-pipeline
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py --input data/raw/oncology_trials.csv
```

## Architecture
Raw CSV (flat, imperfect)
│
src/ingestion.py       ← encoding fixes, list-literal parsing, date normalisation
│
src/profiling.py       ← completeness, cardinality, dirty values, structural anomalies
│
src/schema.py          ← normalised relational tables in DuckDB, derived fields
│
src/analysis.py        ← stratified success rates with small-strata suppression
│
src/visualization.py   ← interactive Plotly dashboards (including Sankey attrition)
│
tests/                 ← pytest suite for ingestion edge-cases and logic validation

## Schema Design

| Table | Description |
|---|---|
| `trials` | Core fact table: scalar fields + derived (`duration_days`, `start_year`, `binary_success`) |
| `trial_phases` | Bridge table: exploded phase lookup |
| `trial_indications` | Bridge table: one row per (trial, indication) |
| `trial_technologies` | Bridge table: one row per (trial, technology) |
| `trial_targets_flat` | Bridge table: one row per (trial, target) |
| `trial_drugs` | Bridge table: one row per (trial, drug) |

## Success Metric

Binary proxy: **COMPLETED = 1, TERMINATED/WITHDRAWN = 0, all others = censored**

| Status | Binary | Rationale |
|---|---|---|
| COMPLETED | 1 | Trial ran to completion |
| TERMINATED | 0 | Stopped early — safety, futility, or sponsor decision |
| WITHDRAWN | 0 | Cancelled before enrollment |
| RECRUITING / ACTIVE_NOT_RECRUITING | None | Right-censored: ongoing ≠ failed |
| UNKNOWN / SUSPENDED | None | Ambiguous — excluded to avoid bias |

**Key caveat**: This proxy measures *process completion*, NOT therapeutic efficacy. 
A completed Phase 3 still requires FDA approval. Our metric sits at the left-most 
end of the translational success spectrum.

## Engineering Rigour

To ensure this pipeline meets production standards, I implemented:
* **Unit Testing:** Core data-cleaning functions (like parsing malformed stringified arrays) and proxy-logic are validated via `pytest`.
* **Right-Censoring Treatment:** Explicitly excluding ongoing/recruiting trials from denominators to prevent artificially lowering success rates in recent cohorts.
* **Small-Strata Suppression:** Strata with fewer than 5 evaluable trials are flagged and hidden from visualizations to prevent statistical noise.
* **Phase Attrition Tracking:** Generated a Plotly Sankey diagram to visualize trial flow and drop-offs across Phase 1 → Phase 2 → Phase 3.

## Key Findings

[Auto-populated from analysis — see `reports/`]

## Caveats

1. **Right-censoring bias**: Ongoing trials look like "no data" not "failure"
2. **Small-strata suppression**: Rates with n_evaluable < 5 are flagged `suppressed=True` 
3. **Registration bias**: ClinicalTrials.gov skews toward industry-sponsored, later-phase trials
4. **Proxy validity**: COMPLETED ≠ statistically significant result
