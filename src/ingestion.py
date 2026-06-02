import ast
import re
import warnings
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from dateutil import parser as date_parser
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ─── List field parsing ───────────────────────────────────────────────────────
def safe_parse_list(raw: Any) -> list:
    """Parse a list-literal string. Returns an empty list for null values."""
    if pd.isna(raw) or raw in ("", "[]", "[[]]"):
        return []
    raw = str(raw).strip()
    try:
        result = ast.literal_eval(raw)
        if isinstance(result, list):
            return result
        return [result]
    except (ValueError, SyntaxError):
        cleaned = re.sub(r"[\[\]']", "", raw)
        return [x.strip() for x in cleaned.split(",") if x.strip()]

def flatten_nested_list(raw: Any) -> list[str]:
    """Flatten nested list literals into a flat list of unique strings."""
    parsed = safe_parse_list(raw)
    flat: list[str] = []
    for item in parsed:
        if isinstance(item, list):
            flat.extend([str(x) for x in item if x])
        elif item:
            flat.append(str(item))
    return list(dict.fromkeys(flat)) 

# ─── Date parsing ─────────────────────────────────────────────────────────────
def parse_date(raw: Any):
    """Parse dates in mixed formats safely."""
    if pd.isna(raw) or raw in ("", "0"):
        return None
    raw_str = str(raw).strip()
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return pd.to_datetime(raw_str, format=fmt)
        except ValueError:
            continue
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return pd.Timestamp(date_parser.parse(raw_str, dayfirst=True))
    except Exception:
        return None

# ─── String cleaning ──────────────────────────────────────────────────────────
def clean_nct_id(raw: Any) -> str:
    if pd.isna(raw):
        return ""
    return re.sub(r"\s+", "", str(raw)).upper()

def clean_phase(raw: Any) -> str:
    if pd.isna(raw):
        return "UNKNOWN"
    s = str(raw).strip().upper()
    s = re.sub(r"\s+", "", s) 
    s = s.replace("EARYPHASE1", "EARLY_PHASE1")
    return s if s else "UNKNOWN"

# ─── Main loader ─────────────────────────────────────────────────────────────
def load_and_clean(filepath: str | Path) -> pd.DataFrame:
    logging.info(f"Loading raw data from {filepath}...")
    df = pd.read_csv(filepath, dtype=str, low_memory=False)

    # 1. Standardise column names
    df.columns = [c.strip().lower().replace("-", "_").replace(" ", "_") for c in df.columns]

    if "id_datalake" in df.columns:
        df = df.rename(columns={"id_datalake": "datalake_id"})

    # 2. NCT ID cleaning
    df["nct_id"] = df["nct_id"].apply(clean_nct_id)

    # 3. Phase & Status cleaning
    if "phase" in df.columns:
        df["phase"] = df["phase"].apply(clean_phase)

    if "recruitment_status" in df.columns:
        df["recruitment_status"] = df["recruitment_status"].str.strip().str.upper().str.replace(r"\s+", "_", regex=True).fillna("UNKNOWN")

    # 4. Date parsing
    for col in ["start_date", "completion_date", "primary_completion_date"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_date)

    # 5. Enrollment
    if "enrollment" in df.columns:
        df["enrollment"] = pd.to_numeric(df["enrollment"], errors="coerce")

    # 6. Parse list fields
    for col in ["indications", "interventions_drugs", "drugs_datalake"]:
        if col in df.columns:
            df[col] = df[col].apply(safe_parse_list)

    for col in ["main_technologies", "specific_technologies", "target_names", "target_abbreviations"]:
        if col in df.columns:
            df[col] = df[col].apply(flatten_nested_list)

    # 7. Deduplicate & Calculate Duration
    df = df.drop_duplicates(subset=["nct_id"], keep="first").reset_index(drop=True)

    if "start_date" in df.columns and "completion_date" in df.columns:
        df["duration_days"] = (df["completion_date"] - df["start_date"]).dt.days

    return df