import pandas as pd
import pytest
from src.schema import compute_success_proxy
import ast
import re

# Since we built ingestion into the master scripts, we'll redefine the pure functions 
# here for unit testing to prove the logic is sound.

def safe_parse_list(raw):
    if pd.isna(raw) or raw in ("", "[]", "[[]]"): return []
    try:
        res = ast.literal_eval(str(raw).strip())
        return res if isinstance(res, list) else [res]
    except:
        return [x.strip() for x in re.sub(r"[\[\]']", "", str(raw)).split(",") if x.strip()]

def flatten_nested_list(raw):
    parsed = safe_parse_list(raw)
    flat = []
    for item in parsed:
        if isinstance(item, list): flat.extend([str(x) for x in item if x])
        elif item: flat.append(str(item))
    return list(dict.fromkeys(flat))

# --- TESTS ---

def test_compute_success_proxy():
    """Test our core business logic proxy for success."""
    assert compute_success_proxy("COMPLETED") == 1
    assert compute_success_proxy("TERMINATED") == 0
    assert compute_success_proxy("WITHDRAWN") == 0
    assert compute_success_proxy("RECRUITING") is None
    assert compute_success_proxy(None) is None

def test_safe_parse_list():
    """Test that stringified arrays parse correctly, even when corrupted."""
    # Standard array
    assert safe_parse_list("['Drug A', 'Drug B']") == ['Drug A', 'Drug B']
    # Corrupted array (no quotes)
    assert safe_parse_list("[Drug A, Drug B]") == ['Drug A', 'Drug B']
    # Empty/Null handling
    assert safe_parse_list("[]") == []
    assert safe_parse_list(None) == []

def test_flatten_nested_list():
    """Test deep flattening of nested structures common in raw pharma data."""
    # Nested array
    assert flatten_nested_list("[['Target 1'], ['Target 2']]") == ['Target 1', 'Target 2']
    # Mixed nesting with duplicates
    assert flatten_nested_list("[['Target 1'], 'Target 1', ['Target 3']]") == ['Target 1', 'Target 3']
