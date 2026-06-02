# Assignment Reflection: Future Roadmap

This document outlines the strategic evolution of the Oncology Trial Pipeline, addressing potential enhancements to the success metric and schema architecture.

What additional data would improve the success metric?

The current proxy — did this trial complete? — sits at the furthest left of the translational success spectrum. To move rightward, I'd need:

1. Primary endpoint outcomes. Whether the trial met its pre-specified primary endpoint (e.g., HR < 0.80 for OS, ORR ≥ 30%). This is the single most important upgrade. With it, I can separate "completed and succeeded" from "completed and failed."

2. Regulatory milestones. NDA/BLA submission dates, FDA approval decisions, and accelerated designation grants (Breakthrough Therapy, Fast Track). These link trial completion to actual market impact.

3. Follow-on trial registration. If a Phase II completes and no Phase III is registered within 3 years, that's a strong negative signal. This "progression rate" is a meaningful intermediate outcome I can compute from the registry itself.

4. Sponsor type and funding source. Industry-sponsored trials complete at higher rates than NIH-funded trials for structural reasons. Controlling for this removes confounding.

5. Protocol amendments and SAEs. Mid-trial safety amendments correlate with later termination. Early warning signals from the amendments log would improve predictive modelling.


How would the schema evolve?

The current schema is flat-to-relational. With richer data, I'd evolve it in three directions:

(i) Add outcome tables: trial_endpoints (primary/secondary endpoint definitions), trial_results (reported outcomes, p-values, hazard ratios), regulatory_decisions (approval/rejection with dates). The trials table becomes a spine; outcomes attach as satellite tables.

(ii) Add temporal event tables: A trial_events table capturing protocol amendments, status changes, and safety holds as time-series rows. This enables survival analysis — modelling time to completion rather than just did it complete.

(iii) Add entity resolution: Indications, drugs, and targets currently arrive as free text. With a drug-ontology layer (DrugBank IDs, ChEMBL IDs) and a disease ontology (ICD-10, MeSH, SNOMED), I can compute meaningful hierarchy-level success rates — e.g., "all VEGF-targeting agents in solid tumours" as a single analytical unit regardless of free-text variation.

The DuckDB schema I built is deliberately designed for this evolution — the bridge tables already support many-to-many relationships, and DuckDB's SQL dialect handles recursive CTEs and window functions needed for time-series analysis. 


