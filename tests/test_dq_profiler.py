"""Tests for Data Quality Profiler engine and API endpoint (Phase A)."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from backend.app.data_quality.profiler import DataProfiler, ProfileResult
from backend.app.data_quality.service import default_dq_service


def test_empty_dataframe():
    """Verify DataProfiler handles an empty DataFrame gracefully."""
    profiler = DataProfiler()
    df = pd.DataFrame()
    profile = profiler.profile(df)

    assert profile.summary.total_rows == 0
    assert profile.summary.total_columns == 0
    assert profile.summary.total_cells == 0
    assert profile.summary.total_missing_cells == 0
    assert profile.summary.missing_percentage == 0.0
    assert profile.summary.duplicate_rows == 0
    assert len(profile.columns) == 0


def test_standard_dataframe_profiling():
    """Verify dataset summary and column stats on a controlled dataset."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", None],
            "age": [25, 30, 35, 40, np.nan],
            "score": [85.5, 90.0, 78.5, 92.0, 88.0],
            "is_active": [True, True, False, True, False],
        }
    )

    profiler = DataProfiler()
    profile = profiler.profile(df)

    # Dataset summary assertions
    assert profile.summary.total_rows == 5
    assert profile.summary.total_columns == 5
    assert profile.summary.total_cells == 25
    assert profile.summary.total_missing_cells == 2
    assert profile.summary.missing_percentage == 8.0
    assert profile.summary.duplicate_rows == 0

    # Column type inference
    assert profile.columns["id"].semantic_type == "numeric"
    assert profile.columns["name"].semantic_type == "text"
    assert profile.columns["age"].semantic_type == "numeric"
    assert profile.columns["score"].semantic_type == "numeric"
    assert profile.columns["is_active"].semantic_type == "boolean"

    # Numeric stats assertions
    age_stats = profile.columns["age"].numeric_stats
    assert age_stats is not None
    assert age_stats["min"] == 25.0
    assert age_stats["max"] == 40.0
    assert age_stats["mean"] == 32.5
    assert age_stats["median"] == 32.5

    # Missing counts
    assert profile.columns["name"].null_count == 1
    assert profile.columns["age"].null_count == 1
    assert profile.columns["id"].null_count == 0


def test_duplicate_row_detection():
    """Verify duplicate detection counts exact duplicate rows."""
    df = pd.DataFrame(
        {
            "col_a": [1, 2, 1, 3],
            "col_b": ["x", "y", "x", "z"],
        }
    )

    profiler = DataProfiler()
    profile = profiler.profile(df)

    assert profile.summary.total_rows == 4
    assert profile.summary.duplicate_rows == 1
    assert profile.summary.duplicate_percentage == 25.0


def test_serialization_dict_and_json():
    """Verify profile can be serialized to dictionary and valid JSON."""
    df = pd.DataFrame({"num": [10, 20, None], "label": ["A", "B", "A"]})
    profiler = DataProfiler()
    profile = profiler.profile(df)

    data_dict = profile.to_dict()
    assert isinstance(data_dict, dict)
    assert "summary" in data_dict
    assert "columns" in data_dict
    assert "missing_rankings" in data_dict

    json_str = profile.to_json()
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["summary"]["total_rows"] == 3


def test_date_detection_on_large_series():
    """Verify semantic type recognizes datetime even with > 500 rows."""
    dates = pd.date_range("2020-01-01", periods=600, freq="D").strftime("%Y-%m-%d").tolist()
    df = pd.DataFrame({"event_date": dates})
    profiler = DataProfiler()
    profile = profiler.profile(df)
    assert profile.columns["event_date"].semantic_type == "datetime"
    assert profile.columns["event_date"].datetime_stats is not None
    assert profile.columns["event_date"].datetime_stats["min_date"].startswith("2020-01-01")


def test_netflix_dataset_profiling():
    """Integration test profiling netflix_titles.csv if available in data/raw/."""
    netflix_path = Path("data/raw/netflix_titles.csv")
    if not netflix_path.exists():
        pytest.skip("netflix_titles.csv not available in data/raw/")

    df = pd.read_csv(netflix_path)
    profiler = DataProfiler()
    profile = profiler.profile(df)

    assert profile.summary.total_rows == 8807
    assert profile.summary.total_columns == 14
    assert profile.summary.total_cells == 123298
    assert profile.summary.total_missing_cells == 13117
    assert profile.summary.duplicate_rows == 0

    # Ensure missing rankings are sorted descending
    missing = profile.missing_rankings
    assert len(missing) > 0
    counts = [item["null_count"] for item in missing]
    assert counts == sorted(counts, reverse=True)


# --- REST API Endpoint Tests ---

def test_profile_endpoint_unauthenticated(client):
    """GET /api/datasets/{name}/profile requires authentication."""
    resp = client.get("/api/datasets/netflix_titles.csv/profile")
    assert resp.status_code == 401


def test_profile_endpoint_authenticated(client, auth):
    """GET /api/datasets/{name}/profile returns valid profile data when authenticated."""
    resp = client.get("/api/datasets/netflix_titles.csv/profile", headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "columns" in data
    assert data["summary"]["total_rows"] == 2  # isolated_storage fixture writes 2 rows
    assert data["summary"]["total_columns"] == 3


def test_profile_endpoint_not_found(client, auth):
    """GET /api/datasets/{name}/profile returns 404 for nonexistent datasets."""
    resp = client.get("/api/datasets/non_existent.csv/profile", headers=auth)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_profile_endpoint_tenant_isolation(client, auth, token):
    """Private dataset uploaded by Alice cannot be profiled by Bob."""
    # Alice uploads private dataset
    upload_resp = client.post(
        "/api/upload",
        headers=auth,
        json={"filename": "alice_private.csv", "content": "col1,col2\n10,20\n30,40\n"},
    )
    assert upload_resp.status_code == 200

    # Alice can profile it
    alice_resp = client.get("/api/datasets/alice_private.csv/profile", headers=auth)
    assert alice_resp.status_code == 200
    assert alice_resp.json()["summary"]["total_rows"] == 2

    # Bob cannot profile it (returns 404)
    bob_auth = {"Authorization": "Bearer " + token("bob")}
    bob_resp = client.get("/api/datasets/alice_private.csv/profile", headers=bob_auth)
    assert bob_resp.status_code == 404
