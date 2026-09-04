"""Agent / Router Layer: Routes user queries to Structured Data Tools, RAG, or Hybrid."""
from typing import Literal

RouteType = Literal["structured", "rag", "hybrid"]


class QueryRouter:
    """Inspects each user query and decides whether it requires structured tools, RAG, or both."""

    def __init__(self, llm_client=None):
        self.client = llm_client

    def route(self, query: str, context: list | None = None) -> RouteType:
        """Route a user query based on intent and conversational context.

        Skeleton implementation ready for LLM classifier integration.
        """
        lower = query.lower()
        # Simple heuristic fallback for skeleton
        if any(term in lower for term in ["meaning", "definition", "what does", "how is", "column"]):
            if any(term in lower for term in ["count", "how many", "top", "average", "total"]):
                return "hybrid"
            return "rag"
        return "structured"
