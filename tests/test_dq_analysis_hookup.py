"""Tests for Phase D: Connecting Clean Datasets and Quality Insights to Visiq Analysis Pipeline."""

import json
from types import SimpleNamespace as NS
import pandas as pd
import pytest

from backend.app.agent.coordinator import default_coordinator
from backend.app.data_quality.service import default_dq_service
from backend.app.memory.session_store import (
    ChatSession,
    default_session_store,
    restore_session,
)
from backend.app.tools.base import default_registry
from backend.app.tools.structured_tools import get_quality_report


def reply(text):
    return (
        NS(
            choices=[NS(message=NS(content=text))],
            usage=NS(prompt_tokens=5, completion_tokens=2, total_tokens=7),
        ),
        "groq",
    )


# =========================================================================
# 1. Session Store Backward Compatibility & Switching
# =========================================================================

def test_restore_session_backward_compatibility():
    """Old session records without original_dataset field restore cleanly."""
    legacy_row = {
        "session_id": "legacy_123",
        "title": "Legacy Analysis",
        "dataset_name": "sales.csv",
        "user_id": "alice",
        "created_at": "2026-01-01T00:00:00Z",
        "history": [],
        "widgets": [],
        "token_usage": {"prompt_tokens": 10, "response_tokens": 20, "total_tokens": 30},
    }

    session = restore_session(legacy_row)
    assert session.session_id == "legacy_123"
    assert session.dataset_name == "sales.csv"
    assert session.original_dataset == "sales.csv"
    assert session.to_dict()["original_dataset"] == "sales.csv"


def test_session_dataset_switching(isolated_storage):
    """Switching a session updates dataset_name while preserving original_dataset."""
    session = default_session_store.create_session(
        dataset_name="netflix_titles.csv",
        title="Test Switch Session",
        user_id="alice",
    )
    assert session.dataset_name == "netflix_titles.csv"
    assert session.original_dataset == "netflix_titles.csv"

    # Switch session dataset
    updated = default_session_store.switch_dataset(
        session.session_id,
        "netflix_titles__clean_v1.csv",
        user_id="alice",
    )
    assert updated is not None
    assert updated.dataset_name == "netflix_titles__clean_v1.csv"
    assert updated.original_dataset == "netflix_titles.csv"

    # Reload from store
    reloaded = default_session_store.get_session(session.session_id, user_id="alice")
    assert reloaded.dataset_name == "netflix_titles__clean_v1.csv"
    assert reloaded.original_dataset == "netflix_titles.csv"


# =========================================================================
# 2. REST API: PATCH /api/sessions/{session_id}/dataset
# =========================================================================

def test_switch_session_dataset_unauthenticated(client):
    """PATCH /api/sessions/{id}/dataset requires authentication."""
    resp = client.patch(
        "/api/sessions/demo_guest_netflix/dataset",
        json={"dataset_name": "netflix_titles.csv"},
    )
    assert resp.status_code == 401


def test_switch_session_dataset_not_found(client, auth):
    """PATCH /api/sessions/{id}/dataset returns 404 for non-existent session."""
    resp = client.patch(
        "/api/sessions/nonexistent_session/dataset",
        headers=auth,
        json={"dataset_name": "netflix_titles.csv"},
    )
    assert resp.status_code == 404


def test_switch_session_dataset_nonexistent_dataset(client, auth):
    """PATCH /api/sessions/{id}/dataset returns 404 if target dataset does not exist."""
    session_resp = client.post("/api/sessions", headers=auth, json={"dataset_name": "netflix_titles.csv"})
    sid = session_resp.json()["session_id"]

    resp = client.patch(
        f"/api/sessions/{sid}/dataset",
        headers=auth,
        json={"dataset_name": "non_existent_file.csv"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_switch_session_dataset_success(client, auth):
    """Create clean dataset, switch session to it, and verify session metadata."""
    # 1. Alice applies cleaning to netflix_titles.csv
    clean_resp = client.post(
        "/api/datasets/netflix_titles.csv/clean",
        headers=auth,
        json={"strip_whitespace": True},
    )
    assert clean_resp.status_code == 200
    target_clean = clean_resp.json()["target_dataset"]

    # 2. Alice creates a session on original dataset
    session_resp = client.post(
        "/api/sessions",
        headers=auth,
        json={"dataset_name": "netflix_titles.csv", "title": "Before Clean Session"},
    )
    assert session_resp.status_code == 200
    sid = session_resp.json()["session_id"]
    assert session_resp.json()["dataset_name"] == "netflix_titles.csv"

    # 3. Alice switches session to the clean dataset
    patch_resp = client.patch(
        f"/api/sessions/{sid}/dataset",
        headers=auth,
        json={"dataset_name": target_clean},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["dataset_name"] == target_clean
    assert data["original_dataset"] == "netflix_titles.csv"

    # 4. GET /api/sessions/{id} returns the new active dataset
    get_resp = client.get(f"/api/sessions/{sid}", headers=auth)
    assert get_resp.status_code == 200
    assert get_resp.json()["dataset_name"] == target_clean


def test_switch_session_dataset_tenant_isolation(client, auth, token):
    """Bob cannot switch Alice's session dataset."""
    session_resp = client.post("/api/sessions", headers=auth, json={"dataset_name": "netflix_titles.csv"})
    sid = session_resp.json()["session_id"]

    bob_auth = {"Authorization": "Bearer " + token("bob")}
    resp = client.patch(
        f"/api/sessions/{sid}/dataset",
        headers=bob_auth,
        json={"dataset_name": "netflix_titles.csv"},
    )
    assert resp.status_code == 404


# =========================================================================
# 3. Tool Registry: get_quality_report Tool
# =========================================================================

def test_get_quality_report_tool_direct():
    """get_quality_report tool computes issues, health score, and dimension breakdowns."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 2, 3],  # duplicate
            "val": [10.0, None, 30.0, 40.0],  # missing
            "status": ["Active", "active", "ACTIVE", "Pending"],  # casing
        }
    )

    report_dict = get_quality_report(df)
    assert report_dict["total_rows"] == 4
    assert report_dict["total_columns"] == 3
    assert report_dict["overall_score"] < 100.0
    assert "grade" in report_dict
    assert "is_trustworthy" in report_dict
    assert "completeness_score" in report_dict
    assert "validity_score" in report_dict
    assert "uniqueness_score" in report_dict
    assert "consistency_score" in report_dict
    assert report_dict["total_issues_count"] > 0
    assert len(report_dict["top_issues"]) > 0


def test_coordinator_tool_calling_quality_report(client, auth, monkeypatch):
    """Agent coordinator executes get_quality_report when proposed by LLM."""
    from backend.app.llm import client as llm

    # Route to structured
    monkeypatch.setattr(default_coordinator.router, "route", lambda *a, **k: "structured")

    # Mock tool decision to choose get_quality_report, then provide summary
    tool_decision = {"tool": "get_quality_report", "parameters": {}}
    responses = [
        reply(json.dumps(tool_decision)),
        reply("The dataset has an overall quality score of 85% (Grade B) with 2 missing values."),
    ]
    pending = iter(responses)
    monkeypatch.setattr(llm, "_call_llm", lambda *a, **k: next(pending))

    session_resp = client.post("/api/sessions", headers=auth, json={"dataset_name": "netflix_titles.csv"})
    sid = session_resp.json()["session_id"]

    resp = client.post(
        "/api/ask",
        headers=auth,
        json={
            "question": "How clean is this dataset?",
            "session_id": sid,
            "provider": "groq",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["operation"] == "get_quality_report"
    assert "quality" in data["summary"].lower() or "score" in data["summary"].lower()
