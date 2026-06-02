"""
Controlled vocabularies, constants, and configuration for the oncology pipeline.
"""

# ─── Status vocabulary ──────────────────────────────────────────────────────
STATUS_MAP = {
    # Terminal positive
    "COMPLETED": "completed",
    "ACTIVE_NOT_RECRUITING": "active_not_recruiting",
    # Terminal negative
    "WITHDRAWN": "withdrawn",
    "TERMINATED": "terminated",
    # Ongoing / not yet started
    "RECRUITING": "recruiting",
    "NOT_YET_RECRUITING": "not_yet_recruiting",
    "ENROLLING_BY_INVITATION": "enrolling_by_invitation",
    # Ambiguous
    "SUSPENDED": "suspended",
    "UNKNOWN": "unknown",
}

STATUS_SUCCESS_TIER = {
    "completed": 2,             # Trial ran to completion — highest proxy for success
    "active_not_recruiting": 1, # Ongoing, promising
    "recruiting": 1,            # Ongoing
    "enrolling_by_invitation": 1,
    "not_yet_recruiting": 0,    # Not started — neutral
    "suspended": -1,            # Negative signal
    "terminated": -2,           # Stopped early — strongest failure proxy
    "withdrawn": -2,            # Cancelled before starting
    "unknown": None,            # Censored — exclude from rate analysis
}

# Binary success: completed=1, terminated/withdrawn=0, rest=None (censored)
BINARY_SUCCESS_MAP = {
    "completed": 1,
    "active_not_recruiting": None,  # right-censored
    "recruiting": None,
    "enrolling_by_invitation": None,
    "not_yet_recruiting": None,
    "suspended": None,
    "terminated": 0,
    "withdrawn": 0,
    "unknown": None,
}

# ─── Phase vocabulary ────────────────────────────────────────────────────────
PHASE_NORMALIZER = {
    "PHASE1": [1],
    "PHASE2": [2],
    "PHASE3": [3],
    "PHASE4": [4],
    "EARLY_PHASE1": [1],
    "PHASE1/PHASE2": [1, 2],
    "PHASE2/PHASE3": [2, 3],
    "PHASE3/PHASE4": [3, 4],
}

PHASE_LABEL_MAP = {1: "Phase I", 2: "Phase II", 3: "Phase III", 4: "Phase IV"}

# ─── Technology taxonomy ─────────────────────────────────────────────────────
TECH_BROAD_GROUPS = {
    "Antibody": "Biologic – Antibody",
    "Monoclonal Antibody": "Biologic – Antibody",
    "Bispecific Antibody": "Biologic – Antibody",
    "Bispecific T-Cell Engager": "Biologic – Antibody",
    "Antibody Drug Conjugate (ADC)": "Biologic – ADC",
    "Small Molecule": "Small Molecule",
    "Chimeric Antigen Receptor T-Cell Therapy (CAR-T)": "Cell Therapy – CAR-T",
    "Chimeric Antigen Receptor NK-Cell Therapy (CAR-NK)": "Cell Therapy – CAR-NK",
    "Cancer Vaccine": "Biologic – Vaccine",
    "mRNA Vaccine": "Biologic – Vaccine",
    "Radiopharmaceutical": "Radiopharmaceutical",
    "Radiopharmaceutical Imaging": "Imaging – Radiopharmaceutical",
    "Gene Therapy": "Gene/Cell Therapy",
    "Small Interfering RNA (siRNA)": "Nucleic Acid Therapy",
    "Antisense Oligonucleotide (ASO)": "Nucleic Acid Therapy",
}

# ─── Columns ─────────────────────────────────────────────────────────────────
RAW_COLUMNS = [
    "ID-datalake", "nct_id", "brief_title", "official_title",
    "phase", "recruitment_status", "start_date", "completion_date",
    "primary_completion_date", "enrollment", "enrollment_type",
    "indications", "interventions_drugs", "drugs_datalake",
    "main_technologies", "specific_technologies",
    "target_names", "target_abbreviations",
]

DATE_COLS = ["start_date", "completion_date", "primary_completion_date"]
LIST_COLS = ["indications", "interventions_drugs", "drugs_datalake"]
NESTED_LIST_COLS = ["main_technologies", "specific_technologies",
                    "target_names", "target_abbreviations"]