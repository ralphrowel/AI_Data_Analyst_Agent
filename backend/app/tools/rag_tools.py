"""RAG retrieval tool for unstructured knowledge lookup.

Allows the agent to search dataset documentation, column definitions,
and methodology notes as specified in the System Change Proposal.
"""
from typing import Any, Dict, List
from backend.app.rag.retriever import default_retriever


def search_documents(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Search unstructured documentation and return relevant excerpts with source metadata.

    Args:
        query: Natural language query or concept to look up in the documentation.
        top_k: Number of relevant passages to retrieve (default: 3).

    Returns:
        List of matched chunks with snippet text, score, and source document name.
    """
    return default_retriever.search(query, top_k=top_k)
