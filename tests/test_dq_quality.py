"""Tests for Data Quality Validation Engine, Scorer, Service, and API Endpoints (Phase B)."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from backend.app.data_quality.checks import DataQualityEngine
from backend.app.data_quality.models import (
    IssueCategory,
    QualityAssessmentResult,
    QualityIssue,
    QualityReport,
    QualityScoreResult,
    ScoreWeights,
    Severity,
)
from backend.app.data_quality.scorer import DataQualityScorer
from backend.app.data_quality.service import default_dq_service


# =========================================================================
# 1. Quality Checks Engine Unit Tests
# =========================================================================

def test_missing_values_detection_and_severities():
    """Verify missing values trigger appropriate severity (CRITICAL vs WARNING) and counts."""
    df = pd.DataFrame(
        {
            "col_complete": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "col_partial": ["a", "b", "c", None, None, "f", "g", "h", "i", "j"],  # 20% missing -> Critical threshold
            "col_whitespace": ["ok", "   ", "ok", "   ", "ok", "ok", "ok", "ok", "ok", "ok"],  # 20% missing -> Critical threshold
            "col_low_missing": ["a", "b", "c", "d", "e", "f", "g", "h", "i", None],  # 10% -> Warning
        }
    )

    engine = DataQualityEngine(critical_missing_threshold=20.0)
    report = engine.analyze(df)

    missing_issues = [i for i in report.issues if i.category == IssueCategory.MISSING]
    assert len(missing_issues) == 3

    partial = next(i for i in missing_issues if i.column == "col_partial")
    assert partial.affected_count == 2
    assert partial.severity == Severity.CRITICAL

    ws = next(i for i in missing_issues if i.column == "col_whitespace")
    assert ws.affected_count == 2
    assert ws.severity == Severity.CRITICAL

    low = next(i for i in missing_issues if i.column == "col_low_missing")
    assert low.affected_count == 1
    assert low.severity == Severity.WARNING


def test_duplicate_rows_and_key_collisions():
    """Verify detection of exact row duplicates and primary key collisions."""
    df = pd.DataFrame(
        {
            "user_id": ["u1", "u2", "u1", "u3"],
            "city": ["NY", "LA", "NY", "SF"],
        }
    )

    engine = DataQualityEngine()
    report = engine.analyze(df, id_columns=["user_id"])

    dup_issues = [i for i in report.issues if i.category == IssueCategory.DUPLICATE]
    assert len(dup_issues) == 2

    exact_dup = next(i for i in dup_issues if i.column is None)
    assert exact_dup.affected_count == 1
    assert exact_dup.severity == Severity.WARNING

    pk_dup = next(i for i in dup_issues if i.column == "user_id")
    assert pk_dup.affected_count == 2
    assert pk_dup.severity == Severity.CRITICAL
    assert "u1" in pk_dup.sample_values


def test_auto_id_detection_without_explicit_id_columns():
    """Engine automatically detects candidate ID columns ending in _id or named show_id."""
    df = pd.DataFrame(
        {
            "show_id": ["s1", "s2", "s1", "s4"],
            "title": ["A", "B", "C", "D"],
        }
    )
    engine = DataQualityEngine()
    report = engine.analyze(df)

    id_dups = [i for i in report.issues if i.category == IssueCategory.DUPLICATE and i.column == "show_id"]
    assert len(id_dups) == 1
    assert id_dups[0].affected_count == 2


def test_format_validation():
    """Verify email, phone, and custom regex pattern matching."""
    df = pd.DataFrame(
        {
            "email": ["valid@example.com", "broken_email", "user@test.org", "bad@.com"],
            "code": ["ABC-123", "ABC-999", "INVALID", "XYZ-000"],
        }
    )

    engine = DataQualityEngine()
    report = engine.analyze(
        df,
        format_rules={
            "email": "email",
            "code": r"^[A-Z]{3}-\d{3}$",
        },
    )

    format_issues = [i for i in report.issues if i.category == IssueCategory.INVALID_FORMAT]
    assert len(format_issues) == 2

    email_issue = next(i for i in format_issues if i.column == "email")
    assert email_issue.affected_count == 2
    assert "broken_email" in email_issue.sample_values

    code_issue = next(i for i in format_issues if i.column == "code")
    assert code_issue.affected_count == 1
    assert "INVALID" in code_issue.sample_values


def test_invalid_date_auto_detection():
    """Text column containing predominantly dates flags unparseable date values (Fix D5)."""
    df = pd.DataFrame(
        {
            "joined_date": [
                "2023-01-15",
                "2023-02-20",
                "2023-03-10",
                "not-a-date",
                "2023-05-12",
                "2023-06-18",
                "corrupted-val",
                "2023-08-22",
            ]
        }
    )

    engine = DataQualityEngine()
    report = engine.analyze(df)

    date_issues = [
        i
        for i in report.issues
        if i.category == IssueCategory.INVALID_FORMAT and i.column == "joined_date"
    ]
    assert len(date_issues) == 1
    assert date_issues[0].affected_count == 2
    assert "not-a-date" in date_issues[0].sample_values
    assert "corrupted-val" in date_issues[0].sample_values


def test_mixed_numeric_type_detection():
    """Predominantly numeric column with non-numeric strings flags INVALID_TYPE (Fix D5)."""
    df = pd.DataFrame(
        {
            "price": ["10.5", "20.0", "30.25", "N/A", "50.0", "unknown", "75.5", "100.0"]
        }
    )

    engine = DataQualityEngine()
    report = engine.analyze(df)

    type_issues = [
        i
        for i in report.issues
        if i.category == IssueCategory.INVALID_TYPE and i.column == "price"
    ]
    assert len(type_issues) == 1
    assert type_issues[0].affected_count == 2
    assert "N/A" in type_issues[0].sample_values
    assert "unknown" in type_issues[0].sample_values


def test_range_validation():
    """Verify bounds checking for numeric fields."""
    df = pd.DataFrame({"age": [25, -5, 42, 135, 30]})

    engine = DataQualityEngine()
    report = engine.analyze(df, range_rules={"age": {"min": 0, "max": 120}})

    range_issues = [i for i in report.issues if i.category == IssueCategory.INVALID_RANGE]
    assert len(range_issues) == 1
    assert range_issues[0].affected_count == 2
    assert -5 in range_issues[0].sample_values
    assert 135 in range_issues[0].sample_values


def test_categorical_consistency_and_noise_suppression():
    """Verify categorical casing detection and free-text noise suppression (Fix D6)."""
    df = pd.DataFrame(
        {
            # Low cardinality: should trigger casing inconsistency
            "status": ["Active", "active", "ACTIVE", "Pending", "Active"] * 3,
            # High cardinality unique free text: should NOT trigger casing inconsistency
            "notes": [
                f"Customer note number {i} regarding order details"
                for i in range(1, 16)
            ],
            # Configured allowed categories
            "tier": ["Bronze", "Silver", "Gold", "Diamond_Invalid", "Bronze"] * 3,
        }
    )

    engine = DataQualityEngine()
    report = engine.analyze(
        df,
        category_rules={"tier": ["Bronze", "Silver", "Gold"]},
    )

    cat_issues = [i for i in report.issues if i.category == IssueCategory.INCONSISTENT_CATEGORY]

    # Status column must be flagged
    status_issue = next(i for i in cat_issues if i.column == "status")
    assert status_issue.affected_count == 12

    # Notes column must NOT be flagged (noise suppression)
    notes_issue = [i for i in cat_issues if i.column == "notes"]
    assert len(notes_issue) == 0

    # Tier column must be flagged for unknown enum value
    tier_issue = next(i for i in cat_issues if i.column == "tier")
    assert tier_issue.affected_count == 3
    assert "Diamond_Invalid" in tier_issue.sample_values


def test_outlier_detection_and_noise_suppression():
    """Statistical outliers detected via IQR, while ID and year columns are suppressed (Fix D6)."""
    # 13 rows with one obvious numeric outlier
    vals = [10, 11, 12, 10, 11, 12, 10, 11, 12, 10, 11, 12, 500]
    years = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 1925]
    ids = list(range(1, 14))

    df = pd.DataFrame(
        {
            "id": ids,
            "metric": vals,
            "release_year": years,
        }
    )

    engine = DataQualityEngine(outlier_method="iqr")
    report = engine.analyze(df, id_columns=["id"])

    outlier_issues = [i for i in report.issues if i.category == IssueCategory.OUTLIER]
    # Only metric column should be reported as outlier
    assert len(outlier_issues) == 1
    assert outlier_issues[0].column == "metric"
    assert outlier_issues[0].affected_count == 1
    assert 500 in outlier_issues[0].sample_values


def test_empty_dataframe_quality():
    """Empty DataFrame returns a zero-issue report without failing."""
    df = pd.DataFrame()
    engine = DataQualityEngine()
    report = engine.analyze(df)
    assert report.total_rows == 0
    assert report.total_issues_count == 0
    assert len(report.issues) == 0


# =========================================================================
# 2. Quality Scoring Engine Unit Tests
# =========================================================================

def test_score_weights_validation():
    """ScoreWeights requires dimensions to sum to 1.0."""
    valid = ScoreWeights(completeness=0.3, validity=0.3, uniqueness=0.2, consistency=0.2)
    assert valid.completeness == 0.3

    with pytest.raises(ValueError, match="must sum to 1.0"):
        ScoreWeights(completeness=0.5, validity=0.5, uniqueness=0.5, consistency=0.5)


def test_perfect_dataset_scoring():
    """Pristine dataset scores 100% Grade A and is trustworthy."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": ["Alice", "Bob", "Charlie", "David"],
            "score": [95.0, 88.0, 92.0, 100.0],
        }
    )

    scorer = DataQualityScorer()
    result = scorer.score(df, id_columns=["id"], range_rules={"score": {"min": 0, "max": 100}})

    assert result.overall_score == 100.0
    assert result.grade == "A"
    assert result.is_trustworthy is True
    assert result.dimensions["completeness"].score == 100.0
    assert result.dimensions["validity"].score == 100.0
    assert result.dimensions["uniqueness"].score == 100.0
    assert result.dimensions["consistency"].score == 100.0


def test_uniqueness_no_double_counting():
    """Exact duplicate rows that also collide on ID are not penalized twice (Fix D7)."""
    # 4 rows, rows 0 and 2 are exact duplicates
    df = pd.DataFrame(
        {
            "id": ["A", "B", "A", "C"],
            "val": [10, 20, 10, 30],
        }
    )

    scorer = DataQualityScorer()
    result = scorer.score(df, id_columns=["id"])

    # Rows affected by uniqueness defects: indices 0 and 2 (2 rows total out of 4)
    # Uniqueness score should be (1.0 - 2/4) * 100 = 50.0%
    # If double-counted, defects would be 1 (exact) + 2 (key) = 3 -> 25.0%
    uniqueness_dim = result.dimensions["uniqueness"]
    assert uniqueness_dim.defects_count == 2
    assert uniqueness_dim.score == 50.0


def test_dirty_dataset_penalties_and_grading():
    """Dirty dataset with issues across all dimensions receives low grade."""
    df = pd.DataFrame(
        {
            "id": [1, 1, 2, 3],  # duplicate
            "age": [25, -10, None, 40],  # out of range + missing
            "status": ["Active", "active", "ACTIVE", "Pending"],  # casing
        }
    )

    scorer = DataQualityScorer()
    result = scorer.score(df, id_columns=["id"], range_rules={"age": {"min": 0, "max": 120}})

    assert result.overall_score < 90.0
    assert result.dimensions["completeness"].score < 100.0
    assert result.dimensions["validity"].score < 100.0
    assert result.dimensions["uniqueness"].score < 100.0
    assert result.dimensions["consistency"].score < 100.0


def test_score_comparison_and_improvement():
    """Score comparison quantifies quality delta between datasets."""
    before_df = pd.DataFrame(
        {
            "id": [1, 2, 2, 3],
            "val": [10.0, 20.0, 20.0, None],
        }
    )
    after_df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "val": [10.0, 20.0, 30.0],
        }
    )

    scorer = DataQualityScorer()
    comparison = scorer.compare(before_df, after_df, id_columns=["id"])

    assert comparison.score_delta > 0
    assert comparison.after.overall_score > comparison.before.overall_score
    assert comparison.after.dimensions["completeness"].score == 100.0
    assert comparison.after.dimensions["uniqueness"].score == 100.0


def test_models_serialization_and_roundtrip():
    """QualityAssessmentResult serializes cleanly to dict/json and round-trips via from_dict."""
    df = pd.DataFrame({"col": [1, 2, None]})
    engine = DataQualityEngine()
    report = engine.analyze(df)
    scorer = DataQualityScorer()
    score_result = scorer.score(df, existing_report=report)

    assessment = QualityAssessmentResult(
        dataset_name="test.csv",
        source_fingerprint="abc123hash",
        engine_version="1.0.0",
        generated_at="2026-10-06T00:00:00Z",
        summary={"total_rows": 3, "overall_score": score_result.overall_score},
        dimensions={k: v.to_dict() for k, v in score_result.dimensions.items()},
        issues=report.issues,
        score=score_result,
        suggested_plan=None,
    )

    d = assessment.to_dict()
    assert d["dataset_name"] == "test.csv"
    assert d["source_fingerprint"] == "abc123hash"
    assert len(d["issues"]) == 1

    # Roundtrip from_dict
    restored = QualityAssessmentResult.from_dict(d)
    assert restored.dataset_name == assessment.dataset_name
    assert restored.source_fingerprint == assessment.source_fingerprint
    assert restored.score.overall_score == assessment.score.overall_score
    assert len(restored.issues) == 1


# =========================================================================
# 3. Service Layer and Caching Tests
# =========================================================================

def test_service_fingerprint_caching(isolated_storage):
    """DataQualityService computes and caches assessments in storage by file hash."""
    # netflix_titles.csv is seeded by isolated_storage fixture
    result_1 = default_dq_service.assess_dataset("netflix_titles.csv")
    assert result_1.source_fingerprint is not None
    assert result_1.score.overall_score > 0

    # Second call should return cached assessment
    result_2 = default_dq_service.assess_dataset("netflix_titles.csv", force_refresh=False)
    assert result_2.source_fingerprint == result_1.source_fingerprint
    assert result_2.score.overall_score == result_1.score.overall_score

    # Force refresh recomputes
    result_3 = default_dq_service.assess_dataset("netflix_titles.csv", force_refresh=True)
    assert result_3.source_fingerprint == result_1.source_fingerprint


# =========================================================================
# 4. REST API Endpoint Tests
# =========================================================================

def test_quality_endpoint_unauthenticated(client):
    """GET /api/datasets/{name}/quality requires authentication."""
    resp = client.get("/api/datasets/netflix_titles.csv/quality")
    assert resp.status_code == 401


def test_quality_endpoint_authenticated(client, auth):
    """GET /api/datasets/{name}/quality returns assessment and score when authenticated."""
    resp = client.get("/api/datasets/netflix_titles.csv/quality", headers=auth)
    assert resp.status_code == 200
    data = resp.json()

    assert "dataset_name" in data
    assert "source_fingerprint" in data
    assert "summary" in data
    assert "dimensions" in data
    assert "issues" in data
    assert "score" in data
    assert data["summary"]["total_rows"] == 2
    assert "completeness" in data["dimensions"]
    assert "validity" in data["dimensions"]
    assert "uniqueness" in data["dimensions"]
    assert "consistency" in data["dimensions"]


def test_quality_endpoint_not_found(client, auth):
    """GET /api/datasets/{name}/quality returns 404 for missing datasets."""
    resp = client.get("/api/datasets/non_existent.csv/quality", headers=auth)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_quality_endpoint_invalid_filename(client, auth):
    """GET /api/datasets/{name}/quality returns 400 for unsafe Windows reserved device names."""
    resp = client.get("/api/datasets/CON.csv/quality", headers=auth)
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


def test_quality_endpoint_refresh_flag(client, auth):
    """GET /api/datasets/{name}/quality?refresh=true forces re-evaluation."""
    resp = client.get("/api/datasets/netflix_titles.csv/quality?refresh=true", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["dataset_name"] == "netflix_titles.csv"
