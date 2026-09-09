"""RAG retrieval tool for unstructured knowledge lookup.

Allows the agent to search dataset documentation, column definitions,
and methodology notes as specified in the System Change Proposal.
"""
from typing import Any, Dict, List
from backend.app.rag.retriever import get_user_retriever


def search_documents(query: str, top_k: int = 3, user_id: str = None) -> List[Dict[str, Any]]:
    """Search unstructured documentation and return relevant excerpts with source metadata.

    Args:
        query: Natural language query or concept to look up in the documentation.
        top_k: Number of relevant passages to retrieve (default: 3).

    Returns:
        List of matched chunks with snippet text, score, and source document name.
    """
    if not user_id:
        raise ValueError("User required for retrieval")
    return get_user_retriever(user_id).search(query, top_k=min(max(top_k, 1), 20))
