"""Verification script for Step 8: Upload UI, Hardening & End-to-End Regression."""
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
from backend.app.rag.retriever import default_retriever
from backend.app.data_engine.dataset_manager import default_dataset_manager


def test_upload_and_hardening():
    print("=" * 60)
    print("STEP 8 VERIFICATION: Upload API, Auto-Indexing & Hardening")
    print("=" * 60)

    client = TestClient(app)

    # -------------------------------------------------------------
    # Test 1: Upload CSV Dataset via POST /api/upload
    # -------------------------------------------------------------
    print("\n--- Test 1: CSV Dataset Upload & Immediate Discovery ---")
    csv_filename = "test_inventory.csv"
    csv_content = """product_id,category,price,stock,rating
p101,Electronics,299.99,50,4.5
p102,Electronics,899.00,20,4.8
p103,Furniture,149.50,15,4.2
p104,Office Supplies,12.99,200,4.1
p105,Furniture,499.00,8,4.7
"""

    resp1 = client.post("/api/upload", json={"filename": csv_filename, "content": csv_content})
    print(f"Status Code: {resp1.status_code}")
    assert resp1.status_code == 200, f"Expected 200, got: {resp1.text}"

    data1 = resp1.json()
    print(f"  Uploaded name: {data1.get('name')}")
    print(f"  Rows detected: {data1.get('rows')}")
    print(f"  Columns: {data1.get('columns')}")
    print(f"  Type: {data1.get('type')}")
    print(f"  Message: {data1.get('message')}")

    assert data1.get("rows") == 5, f"Expected 5 rows, got {data1.get('rows')}"
    assert data1.get("columns") == 5, f"Expected 5 columns, got {data1.get('columns')}"
    assert data1.get("type") == "dataset"

    # Verify newly uploaded dataset appears in GET /api/datasets
    datasets_resp = client.get("/api/datasets").json()
    names = [d["name"] for d in datasets_resp]
    print(f"Available datasets: {names}")
    assert csv_filename in names, f"{csv_filename} should appear in /api/datasets"

    # Create a new session with this dataset
    session_resp = client.post("/api/sessions", json={"dataset_name": csv_filename, "title": "Inventory Audit"}).json()
    print(f"Created session: {session_resp.get('session_id')} attached to {session_resp.get('dataset_name')}")
    assert session_resp.get("dataset_name") == csv_filename
    print("  >>> Test 1 PASSED!")

    # -------------------------------------------------------------
    # Test 2: Upload Knowledge Document & Auto-RAG Indexing
    # -------------------------------------------------------------
    print("\n--- Test 2: Knowledge Document Upload & Auto-RAG Vector Search ---")
    doc_filename = "test_inventory_guidelines.md"
    doc_content = """# Inventory Guidelines & Policies

## Stock Management Thresholds
1. **Critical Reorder Level**: Any SKU with fewer than 10 units in stock must trigger an urgent replenishment order.
2. **High-Margin Priority**: Products priced over $400 are classified as high-margin assets and require insurance tracking.
3. **Rating Standards**: Items with ratings below 4.3 must undergo quarterly customer feedback reviews.
"""

    resp2 = client.post("/api/upload", json={"filename": doc_filename, "content": doc_content})
    print(f"Status Code: {resp2.status_code}")
    assert resp2.status_code == 200, f"Expected 200, got: {resp2.text}"

    data2 = resp2.json()
    print(f"  Uploaded name: {data2.get('name')}")
    print(f"  Type: {data2.get('type')}")
    print(f"  Message: {data2.get('message')}")
    assert data2.get("type") == "knowledge"

    # Immediately search vector store for newly uploaded guideline
    search_results = default_retriever.search("Critical Reorder Level threshold for SKU", top_k=2)
    print(f"RAG search matches: {len(search_results)}")
    assert len(search_results) > 0, "Expected vector search to immediately locate uploaded document"
    top_match = search_results[0]
    print(f"  Top Match Source: {top_match['source']}")
    print(f"  Score: {top_match['score']}")
    print(f"  Content: {top_match['content'][:120]}...")
    assert top_match["source"] == doc_filename
    assert "fewer than 10 units" in top_match["content"]
    print("  >>> Test 2 PASSED!")

    # -------------------------------------------------------------
    # Clean up test files
    # -------------------------------------------------------------
    print("\n--- Cleaning up temporary test files ---")
    raw_path = default_dataset_manager.raw_data_dir / csv_filename
    if raw_path.exists():
        raw_path.unlink()
        print(f"  Cleaned {raw_path}")
    if csv_filename in default_dataset_manager._cache:
        del default_dataset_manager._cache[csv_filename]
    if csv_filename in default_dataset_manager._desc_cache:
        del default_dataset_manager._desc_cache[csv_filename]

    knowledge_path = default_retriever.indexer.knowledge_dir / doc_filename
    if knowledge_path.exists():
        knowledge_path.unlink()
        print(f"  Cleaned {knowledge_path}")
    default_retriever.refresh()

    print("\n" + "=" * 60)
    print("ALL STEP 8 HARDENING TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_upload_and_hardening()
