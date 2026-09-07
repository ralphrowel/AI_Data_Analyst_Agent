"""Verification script for Step 7: API Route Switching to AgentCoordinator."""
import os
import sys

# Ensure UTF-8 stdout encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.memory.session_store import default_session_store


def test_api_coordinator():
    print("=" * 60)
    print("STEP 7 VERIFICATION: /api/ask with AgentCoordinator Pipeline")
    print("=" * 60)

    client = TestClient(app)

    # Ensure default session exists
    session = default_session_store.ensure_default_session()

    # -------------------------------------------------------------
    # Test 1: Structured Query through /api/ask
    # -------------------------------------------------------------
    print("\n--- Test 1: Structured Query via /api/ask ---")
    payload1 = {
        "question": "What are the top 5 countries producing content on Netflix?",
        "session_id": session.session_id,
        "chart_type": "auto",
        "chart_theme": "light",
    }
    resp1 = client.post("/api/ask", json=payload1)
    print(f"Status Code: {resp1.status_code}")
    assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}: {resp1.text}"

    data1 = resp1.json()
    print(f"  Operation: {data1.get('operation')}")
    print(f"  Model Used: {data1.get('model_used')}")
    print(f"  Chart Generated: {data1.get('chart_base64') is not None}")
    print(f"  Summary: {data1.get('summary')[:140]}...")
    print(f"  Usage: {data1.get('usage')}")

    assert data1.get("operation") in ("get_unique_values", "group_data"), f"Unexpected op: {data1.get('operation')}"
    assert data1.get("chart_base64") is not None, "Expected chart base64"
    assert data1.get("summary"), "Summary must not be empty"
    print("  >>> Test 1 PASSED!")

    # -------------------------------------------------------------
    # Test 2: RAG Query through /api/ask
    # -------------------------------------------------------------
    print("\n--- Test 2: RAG Query via /api/ask ---")
    payload2 = {
        "question": "What does TV-MA mean in the dataset?",
        "session_id": session.session_id,
    }
    resp2 = client.post("/api/ask", json=payload2)
    print(f"Status Code: {resp2.status_code}")
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}: {resp2.text}"

    data2 = resp2.json()
    print(f"  Operation: {data2.get('operation')}")
    print(f"  Summary: {data2.get('summary')[:140]}...")
    assert data2.get("operation") == "search_documents", f"Expected search_documents, got {data2.get('operation')}"
    assert "TV-MA" in data2.get("summary") or "mature" in data2.get("summary").lower() or "adult" in data2.get("summary").lower()
    print("  >>> Test 2 PASSED!")

    # -------------------------------------------------------------
    # Test 3: Unsupported Query through /api/ask
    # -------------------------------------------------------------
    print("\n--- Test 3: Unsupported Query via /api/ask ---")
    payload3 = {
        "question": "What is the director's personal home address and secret bank account?",
        "session_id": session.session_id,
    }
    resp3 = client.post("/api/ask", json=payload3)
    print(f"Status Code: {resp3.status_code}")
    assert resp3.status_code == 200, f"Expected 200, got {resp3.status_code}: {resp3.text}"

    data3 = resp3.json()
    print(f"  Operation: {data3.get('operation')}")
    print(f"  Summary: {data3.get('summary')}")
    assert data3.get("operation") == "unsupported"
    print("  >>> Test 3 PASSED!")

    print("\n" + "=" * 60)
    print("ALL STEP 7 API ROUTE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_api_coordinator()
