"""Verification script for Step 5: Intelligent LLM Query Routing and Heuristic Fallback."""
import os
import sys

# Ensure UTF-8 stdout encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.agent.router import QueryRouter


def test_router():
    print("=" * 60)
    print("STEP 5 VERIFICATION: Query Router (LLM & Heuristic)")
    print("=" * 60)

    router = QueryRouter()

    # -------------------------------------------------------------
    # Test 1: LLM-based Routing for Canonical Test Queries
    # -------------------------------------------------------------
    print("\n--- Part 1: LLM Intent Classification ---")
    canonical_cases = [
        ("Top 5 oldest movies", "structured"),
        ("What is the average duration of movies?", "structured"),
        ("What does TV-MA mean?", "rag"),
        ("Explain the criteria for a PG-13 rating in the guidelines", "rag"),
        ("List all TV-MA shows and explain why they received this rating", "hybrid"),
        ("Count titles in each rating and explain the definitions of those ratings", "hybrid"),
    ]

    for query, expected_route in canonical_cases:
        actual_route = router.route(query, mode="llm")
        print(f"Query: '{query}'")
        print(f"  -> Expected: {expected_route} | Actual: {actual_route}")
        assert actual_route == expected_route, f"Mismatch for '{query}': expected {expected_route}, got {actual_route}"
        print("  -> PASSED!")

    # -------------------------------------------------------------
    # Test 2: Heuristic Fallback (Zero-Cost Offline Classification)
    # -------------------------------------------------------------
    print("\n--- Part 2: Fast Heuristic Keyword Fallback ---")
    heuristic_cases = [
        ("Top 10 highest paying data scientist jobs", "structured"),
        ("How many rows in this dataset?", "structured"),
        ("What is the meaning of the abbreviation NC-17?", "rag"),
        ("Define the rating guidelines in the documentation", "rag"),
        ("Count how many shows are TV-MA and explain the definition of TV-MA", "hybrid"),
    ]

    for query, expected_route in heuristic_cases:
        actual_route = router.heuristic_route(query)
        print(f"Query: '{query}'")
        print(f"  -> Expected: {expected_route} | Actual: {actual_route}")
        assert actual_route == expected_route, f"Mismatch for '{query}': expected {expected_route}, got {actual_route}"
        print("  -> PASSED!")

    # -------------------------------------------------------------
    # Test 3: Multi-turn Conversational Context
    # -------------------------------------------------------------
    print("\n--- Part 3: Routing with Conversational Context ---")
    history = [
        {"role": "user", "content": "What does TV-MA stand for?"},
        {"role": "assistant", "content": "TV-MA stands for Mature Audience Only."},
    ]
    followup_query = "Now how many TV-MA shows are in the dataset?"
    route_context = router.route(followup_query, context=history, mode="llm")
    print(f"Follow-up Query: '{followup_query}'")
    print(f"  -> Result: {route_context}")
    assert route_context in ("structured", "hybrid"), f"Expected structured or hybrid, got {route_context}"
    print("  -> PASSED!")

    print("\n" + "=" * 60)
    print("ALL STEP 5 ROUTER TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_router()
