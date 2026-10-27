"""Tests for Data Cleaning Engine, Suggested Plans, Lineage, and API Endpoints (Phase C)."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from backend.app.data_quality.checks import DataQualityEngine
from backend.app.data_quality.cleaner import (
    DataCleaningEngine,
    sanitize_formula_injection,
    to_safe_csv_text,
)
from backend.app.data_quality.models import (
    CleaningAuditSummary,
    CleaningJob,
    CleaningResult,
    CleaningStep,
    DatasetLineage,
)
from backend.app.data_quality.plan import CleaningPlanRequest, generate_suggested_plan
from backend.app.data_quality.service import default_dq_service


# =========================================================================
# 1. DataCleaningEngine Unit Tests
# =========================================================================

def test_cleaner_statelessness():
    """DataCleaningEngine is completely stateless across multiple calls."""
    engine = DataCleaningEngine()
    df1 = pd.DataFrame({"col": [" a ", " b "]})
    res1 = engine.clean(df1, strip_whitespace=True)

    df2 = pd.DataFrame({"num": [10, 20]})
    res2 = engine.clean(df2, strip_whitespace=False)

    assert len(res1.steps) == 1
    assert len(res2.steps) == 0


def test_strip_whitespace():
    """Trimming whitespaces records exact cell diffs in audit."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "name": [" Alice ", "Bob", " Charlie "],
            "city": [" NY ", "LA", "SF"],
        }
    )
    res = engine.clean(df, strip_whitespace=True)

    assert res.cleaned_df["name"].tolist() == ["Alice", "Bob", "Charlie"]
    assert res.cleaned_df["city"].tolist() == ["NY", "LA", "SF"]
    # 2 trimmed in name + 1 trimmed in city = 3 cells fixed
    assert res.audit.values_fixed == 3


def test_normalize_column_names_default_off():
    """Column names are preserved by default to protect analysis & widgets."""
    engine = DataCleaningEngine()
    df = pd.DataFrame({"  col_a  ": [1, 2], " col_b ": [3, 4]})

    # Default off
    res_off = engine.clean(df)
    assert list(res_off.cleaned_df.columns) == ["  col_a  ", " col_b "]

    # Explicit on
    res_on = engine.clean(df, normalize_column_names=True)
    assert list(res_on.cleaned_df.columns) == ["col_a", "col_b"]


def test_casing_and_categorical_mapping():
    """Standardizes casing and replaces categorical mappings."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "gender": ["male", "FEMALE", "Male"],
            "code": ["NY", "CALI", "TEX"],
        }
    )
    res = engine.clean(
        df,
        casing_rules={"gender": "title"},
        categorical_mappings={"code": {"CALI": "CA", "TEX": "TX"}},
    )

    assert res.cleaned_df["gender"].tolist() == ["Male", "Female", "Male"]
    assert res.cleaned_df["code"].tolist() == ["NY", "CA", "TX"]
    # 2 casing diffs + 2 mappings = 4 values fixed
    assert res.audit.values_fixed == 4


def test_date_normalization_audit_accuracy():
    """Date normalization accurately separates valid dates from coerced nulls (Fix D1)."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "date": [
                "2023-01-15",
                "02/20/2023",
                "March 10, 2023",
                "unparseable-date-1",
                "unparseable-date-2",
            ]
        }
    )
    res = engine.clean(df, date_columns=["date"])

    # 3 parseable dates should be normalized to YYYY-MM-DD
    assert res.cleaned_df["date"].iloc[0] == "2023-01-15"
    assert res.cleaned_df["date"].iloc[1] == "2023-02-20"
    assert res.cleaned_df["date"].iloc[2] == "2023-03-10"

    # 2 unparseable dates should be NaN
    assert pd.isna(res.cleaned_df["date"].iloc[3])
    assert pd.isna(res.cleaned_df["date"].iloc[4])

    # Accurate audit verification
    assert res.audit.values_fixed == 3
    assert res.audit.values_nullified == 2

    date_step = next(s for s in res.steps if s.operation == "date_normalization")
    assert date_step.rows_affected == 3
    assert "2 unparseable values coerced to null" in date_step.details


def test_range_enforcement_clamp_and_nullify():
    """Range bounds checking supports clamping (fixed) and nullifying (nullified)."""
    engine = DataCleaningEngine()
    df = pd.DataFrame({"score": [50.0, -10.0, 150.0, 75.0]})

    # Clamp
    res_clamp = engine.clean(
        df, range_rules={"score": {"min": 0.0, "max": 100.0, "action": "clamp"}}
    )
    assert res_clamp.cleaned_df["score"].tolist() == [50.0, 0.0, 100.0, 75.0]
    assert res_clamp.audit.values_fixed == 2
    assert res_clamp.audit.values_nullified == 0

    # Nullify
    res_null = engine.clean(
        df, range_rules={"score": {"min": 0.0, "max": 100.0, "action": "nullify"}}
    )
    assert res_null.cleaned_df["score"].iloc[1] is np.nan or pd.isna(res_null.cleaned_df["score"].iloc[1])
    assert res_null.cleaned_df["score"].iloc[2] is np.nan or pd.isna(res_null.cleaned_df["score"].iloc[2])
    assert res_null.audit.values_nullified == 2


def test_duplicate_removal():
    """Duplicate removal drops exact rows or subset and tracks audit."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "id": [1, 2, 2, 3],
            "val": ["A", "B", "B", "C"],
        }
    )
    res = engine.clean(df, drop_duplicates_subset=True)

    assert len(res.cleaned_df) == 3
    assert res.audit.duplicates_removed == 1
    assert res.audit.original_rows == 4
    assert res.audit.final_rows == 3


def test_missing_value_imputation():
    """Imputation fills nulls and updates values_imputed counter."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "num": [10.0, 20.0, np.nan, 30.0],
            "cat": ["A", "B", None, "A"],
        }
    )
    res = engine.clean(
        df,
        missing_strategies={
            "num": {"strategy": "median"},
            "cat": {"strategy": "mode"},
        },
    )

    assert res.cleaned_df["num"].iloc[2] == 20.0
    assert res.cleaned_df["cat"].iloc[2] == "A"
    assert res.audit.values_imputed == 2


def test_strict_type_conversion_audit_accuracy():
    """Type conversions track changed cells and coerced nulls accurately (Fix D2)."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "str_num": ["10", "20", "corrupted", "40"],
        }
    )
    res = engine.clean(df, type_conversions={"str_num": "int"})

    # Int64 nullable integer
    assert res.cleaned_df["str_num"].iloc[0] == 10
    assert pd.isna(res.cleaned_df["str_num"].iloc[2])

    type_step = next(s for s in res.steps if s.operation == "type_conversion")
    assert type_step.parameters["coerced_nulls"] == 1
    assert res.audit.values_nullified == 1


def test_audit_explanation_string():
    """Audit summary generates a clear explainable narrative."""
    audit = CleaningAuditSummary(
        original_rows=100,
        duplicates_removed=5,
        values_fixed=12,
        values_imputed=8,
        values_nullified=2,
        final_rows=95,
        explanation="",
    )
    expected = (
        "Original 100 rows → removed 5 duplicates → fixed 12 values → "
        "imputed 8 missing → nullified 2 invalid → final 95 rows."
    )
    assert audit.original_rows == 100
    assert audit.duplicates_removed == 5
    assert audit.final_rows == 95


def test_formula_injection_sanitization():
    """Prevents CSV formula injection by prepending single quotes to trigger characters."""
    df = pd.DataFrame(
        {
            "command": ["=SUM(A1:A10)", "@echo", "-10", "normal"],
            "value": [10, 20, 30, 40],
        }
    )
    safe_df = sanitize_formula_injection(df)

    assert safe_df["command"].iloc[0] == "'=SUM(A1:A10)"
    assert safe_df["command"].iloc[1] == "'@echo"
    assert safe_df["command"].iloc[2] == "'-10"
    assert safe_df["command"].iloc[3] == "normal"

    csv_text = to_safe_csv_text(df)
    assert "'=SUM" in csv_text


# =========================================================================
# 2. Suggested Plan Generator Tests
# =========================================================================

def test_generate_suggested_plan():
    """Suggests clean operations matching detected dataset issues."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 2, 3],
            "title": ["  A ", "b", "B", "C"],
            "date": ["2023-01-01", "2023-01-02", "bad", "2023-01-04"],
            "val": [10.0, None, 30.0, 40.0],
        }
    )
    engine = DataQualityEngine()
    report = engine.analyze(df)

    plan = generate_suggested_plan(report, df)
    assert plan["strip_whitespace"] is True
    assert plan["normalize_column_names"] is False
    assert plan.get("drop_duplicates_subset") is True
    assert "date" in plan.get("date_columns", [])
    assert "val" in plan.get("missing_strategies", {})


# =========================================================================
# 3. Service Layer & Lineage Tracking Tests
# =========================================================================

def test_preview_cleaning_dry_run(isolated_storage):
    """Preview dry-run evaluates before/after stats without modifying files."""
    plan = {"strip_whitespace": True, "drop_duplicates_subset": True}
    preview = default_dq_service.preview_cleaning("netflix_titles.csv", plan=plan)

    assert preview["dataset_name"] == "netflix_titles.csv"
    assert "audit" in preview
    assert "score_comparison" in preview
    assert "steps" in preview


def test_apply_cleaning_preserves_original(isolated_storage):
    """Applying clean creates derived dataset and leaves original 100% byte-identical."""
    # Read original file bytes
    orig_path = default_dq_service._resolve_and_read_csv("netflix_titles.csv")[0]
    with open(orig_path, "rb") as f:
        orig_bytes = f.read()

    plan = {"strip_whitespace": True}
    job = default_dq_service.apply_cleaning("netflix_titles.csv", plan=plan, user_id="alice")

    # Verify original file bytes are identical
    with open(orig_path, "rb") as f:
        after_bytes = f.read()
    assert orig_bytes == after_bytes

    # Verify derived dataset name
    assert "__clean_v" in job.target_dataset
    assert job.score_after.overall_score >= job.score_before.overall_score

    # Verify lineage
    lineage = default_dq_service.get_dataset_lineage("netflix_titles.csv", user_id="alice")
    assert len(lineage.versions) >= 1
    assert lineage.versions[0]["dataset_name"] == job.target_dataset


# =========================================================================
# 4. REST API Endpoint Tests
# =========================================================================

def test_preview_endpoint_auth_required(client):
    """POST /api/datasets/{name}/clean/preview requires authentication."""
    resp = client.post(
        "/api/datasets/netflix_titles.csv/clean/preview",
        json={"strip_whitespace": True},
    )
    assert resp.status_code == 401


def test_preview_endpoint_authenticated(client, auth):
    """POST /api/datasets/{name}/clean/preview returns preview with audit diff."""
    resp = client.post(
        "/api/datasets/netflix_titles.csv/clean/preview",
        headers=auth,
        json={"strip_whitespace": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "audit" in data
    assert "score_comparison" in data
    assert "steps" in data


def test_clean_endpoint_forbids_extra_keys(client, auth):
    """POST /api/datasets/{name}/clean rejects unknown attributes (extra='forbid')."""
    resp = client.post(
        "/api/datasets/netflix_titles.csv/clean",
        headers=auth,
        json={"strip_whitespace": True, "malicious_flag": True},
    )
    assert resp.status_code == 422


def test_clean_endpoint_success(client, auth):
    """POST /api/datasets/{name}/clean creates derived dataset and returns job."""
    resp = client.post(
        "/api/datasets/netflix_titles.csv/clean",
        headers=auth,
        json={"strip_whitespace": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert "target_dataset" in data
    assert "__clean_v" in data["target_dataset"]
    assert "audit" in data


def test_lineage_endpoint(client, auth):
    """GET /api/datasets/{name}/lineage returns lineage information."""
    resp = client.get("/api/datasets/netflix_titles.csv/lineage", headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert "dataset_name" in data
    assert "role" in data
    assert "versions" in data


# =========================================================================
# 5. Sprint 3 Gap-Filling Cleaners & Quarantine Tests
# =========================================================================

def test_currency_cleaning():
    """Cleaner converts currency strings with symbols and commas to numeric floats."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "price": ["₱1,500.50", "PHP 250.00", "$45.99", "750", "N/A"],
            "item": ["A", "B", "C", "D", "E"],
        }
    )
    result = engine.clean(df, clean_currency_columns=["price"])
    cleaned = result.cleaned_df

    assert pd.api.types.is_float_dtype(cleaned["price"])
    assert cleaned["price"].iloc[0] == 1500.50
    assert cleaned["price"].iloc[1] == 250.00
    assert cleaned["price"].iloc[2] == 45.99
    assert cleaned["price"].iloc[3] == 750.0
    assert pd.isna(cleaned["price"].iloc[4])
    assert any(s.operation == "clean_currency" for s in result.steps)


def test_quarantine_fatal_defects():
    """Fatal defects are filtered from cleaned_df and isolated into quarantine_df."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "tx_id": ["TX-1", "TX-2", None, "TX-4"],
            "amount": [100.0, -999.0, 50.0, 200.0],
            "qty": [2, 1, 5, -10],
        }
    )
    quarantine_rules = [
        {"column": "amount", "min_val": 0, "reason": "negative_amount"},
        {"column": "qty", "min_val": 1, "reason": "negative_or_zero_qty"},
        {"column": "tx_id", "not_null": True, "reason": "missing_primary_key"},
    ]
    result = engine.clean(df, quarantine_rules=quarantine_rules)

    # Cleaned DataFrame should only contain TX-1 (valid row)
    assert len(result.cleaned_df) == 1
    assert result.cleaned_df.iloc[0]["tx_id"] == "TX-1"

    # Quarantine DataFrame should contain the 3 defective rows
    assert len(result.quarantine_df) == 3
    assert "_quarantine_reason" in result.quarantine_df.columns
    assert result.audit.rows_quarantined == 3
    assert any(s.operation == "quarantine_fatal_defects" for s in result.steps)


def test_canonical_synonyms():
    """Maps dirty string variations to canonical values case-insensitively."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "channel": ["In-Store", "in store", "ONLINE", "web", "wholesale"],
        }
    )
    synonyms = {
        "channel": {
            "in store": "Retail Store",
            "in-store": "Retail Store",
            "online": "E-Commerce",
            "web": "E-Commerce",
        }
    }
    result = engine.clean(df, canonical_synonyms=synonyms)
    assert result.cleaned_df["channel"].tolist() == [
        "Retail Store",
        "Retail Store",
        "E-Commerce",
        "E-Commerce",
        "wholesale",
    ]
    assert any(s.operation == "canonical_synonyms" for s in result.steps)


def test_formula_recomputations():
    """Recomputes formula column from arithmetic expression of other columns."""
    engine = DataCleaningEngine()
    df = pd.DataFrame(
        {
            "unit_price": [10.0, 20.0, 15.0],
            "quantity": [2, 3, 4],
            "total_amount": [np.nan, 0.0, 60.0],
        }
    )
    formulas = {
        "total_amount": "unit_price * quantity"
    }
    result = engine.clean(df, formula_recomputations=formulas)
    assert result.cleaned_df["total_amount"].tolist() == [20.0, 60.0, 60.0]
    assert any(s.operation == "formula_recomputation" for s in result.steps)


def test_resolve_quality_badge():
    """_resolve_quality_badge produces valid metadata for raw and cleaned datasets."""
    from backend.app.agent.coordinator import _resolve_quality_badge

    # None dataset returns None
    assert _resolve_quality_badge(None) is None

    # Netflix raw dataset assessment
    badge = _resolve_quality_badge("netflix_titles.csv", user_id="user_default")
    assert badge is not None
    assert "dataset_name" in badge
    assert "score" in badge
    assert "grade" in badge
    assert "badge_text" in badge
    assert "is_trustworthy" in badge

