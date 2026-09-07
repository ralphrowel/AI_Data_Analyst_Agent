"""Verification script for Step 4: AgentCoordinator tool execution against SessionStore."""
import os
import sys

# Ensure UTF-8 stdout encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.agent.coordinator import AgentCoordinator
from backend.app.agent.router import QueryRouter
from backend.app.memory.session_store import default_session_store
from backend.app.tools.base import default_registry
import backend.app.tools.registry_setup  # ensure all tools are registered


def test_coordinator():
    print("=" * 60)
    print("STEP 4 VERIFICATION: AgentCoordinator Tool Execution")
    print("=" * 60)

    coordinator = AgentCoordinator(
        router=QueryRouter(),
        memory=default_session_store,
        registry=default_registry,
    )

    # -------------------------------------------------------------
    # Test 1: Structured query on Netflix dataset (Default Session)
    # -------------------------------------------------------------
    session_1 = default_session_store.ensure_default_session()
    print(f"\n[Test 1] Session 1: {session_1.title} ({session_1.dataset_name})")
    q1 = "What are the top 5 countries producing content on Netflix?"
    print(f"Question: '{q1}'")

    res1 = coordinator.process_query(session_1.session_id, q1)
    print(f"  Route: {res1.get('route')}")
    print(f"  Operation: {res1.get('operation')}")
    print(f"  Model Used: {res1.get('model_used')}")
    print(f"  Result Keys: {list(res1.get('result', {}).keys()) if isinstance(res1.get('result'), dict) else type(res1.get('result'))}")
    print(f"  Result Preview: {res1.get('result')}")
    print(f"  Summary: {res1.get('summary')}")
    print(f"  Chart Generated: {res1.get('chart_base64') is not None}")
    print(f"  Session Tokens: {session_1.token_usage}")
    print(f"  Session Turns: {len(session_1.history)}")

    assert res1.get("operation") in ("get_unique_values", "group_data"), f"Unexpected operation: {res1.get('operation')}"
    assert res1.get("summary"), "Summary should not be empty"
    assert res1.get("chart_base64") is not None, "Expected chart_base64 for top 5 countries"
    assert len(session_1.history) == 2, f"Expected 2 history turns, got {len(session_1.history)}"
    print("  >>> Test 1 PASSED!")

    # -------------------------------------------------------------
    # Test 2: Structured query on Tech Salaries dataset (New Session)
    # -------------------------------------------------------------
    print("\n[Test 2] Creating Tech Salaries session...")
    salaries_csv = "salaries.csv" if os.path.exists(os.path.join(root_dir, "data", "raw", "salaries.csv")) else None
    if not salaries_csv:
        # Check whatever files exist in data/raw
        raw_files = os.listdir(os.path.join(root_dir, "data", "raw"))
        print(f"  Files in data/raw: {raw_files}")
        for f in raw_files:
            if f != "netflix_titles.csv" and f.endswith(".csv"):
                salaries_csv = f
                break

    if salaries_csv:
        session_2 = default_session_store.create_session(dataset_name=salaries_csv, title="Tech Salaries Void")
        print(f"Session 2: {session_2.title} ({session_2.dataset_name})")
        q2 = "What are the most common job titles?"
        print(f"Question: '{q2}'")

        res2 = coordinator.process_query(session_2.session_id, q2)
        print(f"  Route: {res2.get('route')}")
        print(f"  Operation: {res2.get('operation')}")
        print(f"  Result Preview: {res2.get('result')}")
        print(f"  Summary: {res2.get('summary')}")
        print(f"  Session 2 Tokens: {session_2.token_usage}")
        print(f"  Session 1 Tokens (isolated): {session_1.token_usage}")

        assert res2.get("operation") in ("get_unique_values", "group_data"), f"Unexpected operation: {res2.get('operation')}"
        assert res2.get("summary"), "Summary should not be empty"
        print("  >>> Test 2 PASSED!")
    else:
        print("  Skipping Test 2 (no secondary CSV in data/raw)")

    # -------------------------------------------------------------
    # Test 3: Unsupported query
    # -------------------------------------------------------------
    print("\n[Test 3] Unsupported query")
    q3 = "What is the director's personal phone number and home address?"
    print(f"Question: '{q3}'")
    res3 = coordinator.process_query(session_1.session_id, q3)
    print(f"  Operation: {res3.get('operation')}")
    print(f"  Summary: {res3.get('summary')}")
    assert res3.get("operation") == "unsupported", f"Expected unsupported, got {res3.get('operation')}"
    print("  >>> Test 3 PASSED!")

    # -------------------------------------------------------------
    # Test 4: Dataset schema query
    # -------------------------------------------------------------
    print("\n[Test 4] Schema query")
    q4 = "What columns exist in this dataset and how many rows are there?"
    print(f"Question: '{q4}'")
    res4 = coordinator.process_query(session_1.session_id, q4)
    print(f"  Operation: {res4.get('operation')}")
    print(f"  Summary: {res4.get('summary')}")
    assert res4.get("operation") == "get_dataset_schema", f"Expected get_dataset_schema, got {res4.get('operation')}"
    print("  >>> Test 4 PASSED!")

    print("\n" + "=" * 60)
    print("ALL STEP 4 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_coordinator()
