"""Verification script for Step 6: RAG Indexing, Vector Search, and Tool Integration."""
import os
import sys

# Ensure UTF-8 stdout encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.rag.indexer import DocumentIndexer
from backend.app.rag.retriever import default_retriever
from backend.app.tools.rag_tools import search_documents
from backend.app.tools.base import default_registry
import backend.app.tools.registry_setup
from backend.app.agent.coordinator import AgentCoordinator
from backend.app.memory.session_store import default_session_store


def test_rag_layer():
    print("=" * 60)
    print("STEP 6 VERIFICATION: RAG Layer (Embeddings + Vector Search)")
    print("=" * 60)

    # -------------------------------------------------------------
    # Test 1: Indexer Document Ingestion and Chunking
    # -------------------------------------------------------------
    print("\n--- Part 1: Document Indexer Verification ---")
    indexer = DocumentIndexer()
    chunks = indexer.build_index()
    print(f"Total documents indexed: {len(indexer.load_documents())}")
    print(f"Total passages chunked: {len(chunks)}")
    print(f"Vocabulary size: {len(indexer.vocabulary)}")
    assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"
    assert len(indexer.vocabulary) > 50, f"Expected vocabulary > 50 words, got {len(indexer.vocabulary)}"
    for c in chunks:
        assert c.vector is not None, f"Chunk {c.chunk_id} vector is None"
        print(f"  - Chunk: {c.chunk_id} | Source: {c.source} | Title: {c.title}")
    print("  >>> Indexer PASSED!")

    # -------------------------------------------------------------
    # Test 2: In-Memory Cosine Similarity Vector Search
    # -------------------------------------------------------------
    print("\n--- Part 2: Vector Search with default_retriever ---")
    queries = [
        "content rating criteria",
        "duration splitting into minutes and seasons",
        "unique identifier for each title",
    ]

    for q in queries:
        results = default_retriever.search(q, top_k=2)
        print(f"\nQuery: '{q}'")
        print(f"  Matches found: {len(results)}")
        assert len(results) > 0, f"Expected matches for query '{q}'"
        for r in results:
            print(f"  Source: {r['source']} | Score: {r['score']}")
            print(f"  Snippet: {r['content'][:120]}...")
            assert r["score"] > 0, "Score should be greater than 0"
        print("  >>> Query PASSED!")

    # -------------------------------------------------------------
    # Test 3: search_documents Tool via Registry
    # -------------------------------------------------------------
    print("\n--- Part 3: Tool Execution via default_registry ---")
    rag_fn = default_registry.get("search_documents")
    assert rag_fn is not None, "search_documents not found in default_registry"
    tool_results = rag_fn(query="ratings categorization mature and family", top_k=2)
    print(f"Tool results count: {len(tool_results)}")
    assert len(tool_results) > 0, "Expected at least 1 match from search_documents"
    print(f"Top result source: {tool_results[0]['source']} (score: {tool_results[0]['score']})")
    print(f"Snippet: {tool_results[0]['content'][:140]}...")
    print("  >>> Registry Tool PASSED!")

    # -------------------------------------------------------------
    # Test 4: End-to-End AgentCoordinator RAG Query Execution
    # -------------------------------------------------------------
    print("\n--- Part 4: End-to-End Coordinator RAG Execution ---")
    session = default_session_store.ensure_default_session()
    coordinator = AgentCoordinator()

    rag_question = "What does the TV-MA rating mean in the data dictionary?"
    print(f"Question: '{rag_question}'")
    response = coordinator.process_query(session.session_id, rag_question)

    print(f"  Route: {response.get('route')}")
    print(f"  Operation: {response.get('operation')}")
    print(f"  Summary: {response.get('summary')}")
    print(f"  Model used: {response.get('model_used')}")
    print(f"  Usage: {response.get('usage')}")

    assert response.get("route") == "rag", f"Expected route 'rag', got '{response.get('route')}'"
    assert response.get("summary"), "Summary must not be empty"
    assert response.get("operation") == "search_documents", f"Expected operation 'search_documents', got '{response.get('operation')}'"
    print("  >>> Coordinator RAG Query PASSED!")

    print("\n" + "=" * 60)
    print("ALL STEP 6 RAG TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_rag_layer()
