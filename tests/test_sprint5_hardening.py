"""Tests for Sprint 5: UI Polish, Multi-Tenant Isolation, Quotas & Deployment Hardening."""

import pytest
from fastapi.testclient import TestClient

from backend.app.auth.quota_manager import QuotaManager
from backend.app.config import MAX_UPLOAD_BYTES, DAILY_TOKEN_LIMIT
from backend.app.data_engine.dataset_manager import default_dataset_manager
from backend.app.data_quality.service import default_dq_service
from backend.app.file_storage import file_store
from backend.app.memory.session_store import default_session_store


# =========================================================================
# 1. Upload Size Limit Enforcement (5 MB Railway Boundary)
# =========================================================================

def test_upload_under_5mb_accepted(client: TestClient, token):
    """CSV uploads within 5 MB are parsed and saved successfully."""
    auth_header = {"Authorization": "Bearer " + token(user="alice")}
    csv_content = "id,name,value\n1,Alice,100\n2,Bob,200\n"

    res = client.post(
        "/api/upload",
        headers=auth_header,
        json={"filename": "small_dataset.csv", "content": csv_content},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["filename"] == "small_dataset.csv"
    assert data["rows"] == 2
    assert data["columns"] == 3


def test_upload_over_5mb_rejected_with_413(client: TestClient, token, monkeypatch):
    """Uploads exceeding MAX_UPLOAD_BYTES (5 MB) are rejected immediately with HTTP 413."""
    from backend.app.api import routes
    auth_header = {"Authorization": "Bearer " + token(user="alice")}

    # Test routes byte limit triggers 413
    monkeypatch.setattr(routes, "MAX_UPLOAD_BYTES", 50)
    res = client.post(
        "/api/upload",
        headers=auth_header,
        json={"filename": "oversized.csv", "content": "a,b\n" + "1,2\n" * 20},
    )
    assert res.status_code == 413
    assert "exceeds size limit" in res.json().get("detail", "").lower()


def test_upload_exceeding_pydantic_schema_rejected_with_422(client: TestClient, token):
    """Payloads exceeding MAX_UPLOAD_BYTES characters fail schema validation with HTTP 422."""
    auth_header = {"Authorization": "Bearer " + token(user="alice")}
    oversized_content = "x" * (MAX_UPLOAD_BYTES + 100)

    res = client.post(
        "/api/upload",
        headers=auth_header,
        json={"filename": "oversized_chars.csv", "content": oversized_content},
    )
    assert res.status_code == 422


# =========================================================================
# 2. Multi-Tenant Workspace & Dataset Isolation
# =========================================================================

def test_multi_tenant_dataset_isolation(client: TestClient, token):
    """Private uploads are strictly isolated between different tenants (e.g., alice vs bob)."""
    alice_auth = {"Authorization": "Bearer " + token(user="alice")}
    bob_auth = {"Authorization": "Bearer " + token(user="bob")}

    # Alice uploads private dataset
    res_a = client.post(
        "/api/upload",
        headers=alice_auth,
        json={"filename": "alice_private.csv", "content": "colA,colB\n1,2\n"},
    )
    assert res_a.status_code == 200

    # Bob uploads private dataset
    res_b = client.post(
        "/api/upload",
        headers=bob_auth,
        json={"filename": "bob_private.csv", "content": "colX,colY\n9,9\n"},
    )
    assert res_b.status_code == 200

    # Alice lists datasets -> should see alice_private.csv, but NOT bob_private.csv
    list_a = client.get("/api/datasets", headers=alice_auth).json()
    names_a = [d["name"] for d in list_a]
    assert "alice_private.csv" in names_a
    assert "bob_private.csv" not in names_a

    # Bob lists datasets -> should see bob_private.csv, but NOT alice_private.csv
    list_b = client.get("/api/datasets", headers=bob_auth).json()
    names_b = [d["name"] for d in list_b]
    assert "bob_private.csv" in names_b
    assert "alice_private.csv" not in names_b


# =========================================================================
# 3. Cleaning Lineage, Quarantine, and Version Persistence
# =========================================================================

def test_cleaning_generates_quarantine_and_complete_lineage(isolated_storage):
    """Applying cleaning on dirty data produces clean_v1, quarantine_v1, and coherent lineage."""
    owner = "alice"
    raw_filename = "transactions.csv"
    # Row 1 is valid, row 2 has negative total_amount (fatal corruption targeted for quarantine)
    raw_csv = (
        "transaction_id,item,total_amount\n"
        "TXN-001,Widget,500.00\n"
        "TXN-ERR,Corrupt,-9999.00\n"
    )
    file_store.save(owner, raw_filename, raw_csv, kind="csv")

    plan = {
        "strip_whitespace": True,
        "drop_duplicates_subset": True,
        "quarantine_rules": {
            "non_negative_columns": ["total_amount"],
        },
    }

    job = default_dq_service.apply_cleaning(raw_filename, plan, user_id=owner)

    assert job.target_dataset == "transactions__clean_v1.csv"
    assert job.quarantine_dataset == "transactions__quarantine_v1.csv"
    assert job.audit.rows_quarantined == 1

    # Verify both clean and quarantine files exist in file_store
    clean_path = file_store.ensure_local_path(owner, "transactions__clean_v1.csv", kind="csv")
    quarantine_path = file_store.ensure_local_path(owner, "transactions__quarantine_v1.csv", kind="csv")

    assert clean_path.exists()
    assert quarantine_path.exists()

    # Verify quarantine CSV contains defect row and quarantine metadata columns
    quarantine_content = quarantine_path.read_text(encoding="utf-8")
    assert "TXN-ERR" in quarantine_content
    assert "_quarantine_reason" in quarantine_content

    # Verify lineage queried on the original dataset
    parent_lineage = default_dq_service.get_dataset_lineage(raw_filename, user_id=owner)
    assert len(parent_lineage.versions) == 1
    assert parent_lineage.versions[0]["dataset_name"] == "transactions__clean_v1.csv"
    assert parent_lineage.versions[0]["quarantine_dataset"] == "transactions__quarantine_v1.csv"

    # Verify lineage queried on the clean child dataset
    clean_lineage = default_dq_service.get_dataset_lineage("transactions__clean_v1.csv", user_id=owner)
    assert clean_lineage.role == "cleaned"
    assert clean_lineage.parent_dataset == "transactions.csv"
    assert len(clean_lineage.versions) == 1
    assert clean_lineage.versions[0]["quarantine_dataset"] == "transactions__quarantine_v1.csv"

    # Verify lineage queried on the quarantine child dataset
    quarantine_lineage = default_dq_service.get_dataset_lineage("transactions__quarantine_v1.csv", user_id=owner)
    assert quarantine_lineage.role == "quarantine"
    assert quarantine_lineage.parent_dataset == "transactions.csv"


# =========================================================================
# 4. Session Dataset Switching Across Versions
# =========================================================================

def test_session_switching_between_raw_clean_and_quarantine(client: TestClient, token):
    """User can switch a chat session between raw, cleaned, and quarantine versions."""
    owner = "alice"
    auth_header = {"Authorization": "Bearer " + token(user=owner)}

    # Upload raw file
    raw_csv = "id,val\n1,10\n2,-50\n"
    client.post(
        "/api/upload",
        headers=auth_header,
        json={"filename": "metric.csv", "content": raw_csv},
    )

    # Clean the file with quarantine rule for non-negative values
    clean_res = client.post(
        "/api/datasets/metric.csv/clean",
        headers=auth_header,
        json={
            "strip_whitespace": True,
            "quarantine_rules": {"non_negative_columns": ["val"]},
        },
    )
    assert clean_res.status_code == 200
    job_data = clean_res.json()
    clean_dataset = job_data["target_dataset"]
    quarantine_dataset = job_data["quarantine_dataset"]
    assert quarantine_dataset == "metric__quarantine_v1.csv"

    # Create session on raw dataset
    session = default_session_store.create_session(
        dataset_name="metric.csv",
        title="Metric Analysis",
        user_id=owner,
    )
    session_id = session.session_id

    # 1. Switch to clean dataset
    switch_clean = client.patch(
        f"/api/sessions/{session_id}/dataset",
        headers=auth_header,
        json={"dataset_name": clean_dataset},
    )
    assert switch_clean.status_code == 200
    assert switch_clean.json()["dataset_name"] == clean_dataset

    # 2. Switch to quarantine dataset
    switch_quarantine = client.patch(
        f"/api/sessions/{session_id}/dataset",
        headers=auth_header,
        json={"dataset_name": quarantine_dataset},
    )
    assert switch_quarantine.status_code == 200
    assert switch_quarantine.json()["dataset_name"] == quarantine_dataset

    # 3. Switch back to raw original dataset
    switch_raw = client.patch(
        f"/api/sessions/{session_id}/dataset",
        headers=auth_header,
        json={"dataset_name": "metric.csv"},
    )
    assert switch_raw.status_code == 200
    assert switch_raw.json()["dataset_name"] == "metric.csv"


# =========================================================================
# 5. Quota Guard Enforcement (Guest vs Authenticated vs Admin)
# =========================================================================

def test_quota_limits_guest_vs_authenticated(isolated_storage):
    """Quota manager applies 10,000 limit for guest, 50,000 for authenticated, and bypasses admin."""
    qm = QuotaManager()

    # Guest user: limit is GUEST_LIMIT (10,000)
    assert qm._get_limit("user_default") == 10000
    assert qm.check_quota("user_default") is True

    # Authenticated user: limit is DAILY_TOKEN_LIMIT (50,000)
    assert qm._get_limit("alice") == DAILY_TOKEN_LIMIT
    assert qm.check_quota("alice") is True

    # Admin: bypasses quota regardless of token/query consumption
    assert qm.is_admin("user_admin_ralph") is True
    assert qm.check_quota("user_admin_ralph") is True
