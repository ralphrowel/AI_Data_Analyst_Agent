"""Agent / Router Layer: Routes user queries to Structured Data Tools, RAG, or Hybrid.

Uses an LLM classifier with prompt-guided intent analysis and zero-cost heuristic fallback.
"""
import json
import logging
import re
from typing import Any, Dict, List, Literal, Optional

from backend.app.agent.prompts import build_router_prompt
from backend.app.llm.client import call_llm

logger = logging.getLogger(__name__)

RouteType = Literal["structured", "rag", "hybrid"]


def _extract_route_json(raw_text: str) -> dict:
    """Safely extract classification JSON from model response."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {}


class QueryRouter:
    """Inspects user queries and classifies whether they require structured tools, RAG, or both."""

    def __init__(self, llm_client: Any = None, default_mode: str = "llm"):
        """
        Args:
            llm_client: Optional LLM client override.
            default_mode: 'llm' for intelligent classification with fallback,
                          or 'heuristic' for fast zero-cost keyword matching.
        """
        self.client = llm_client
        self.default_mode = default_mode

    def route(
        self,
        query: str,
        context: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> RouteType:
        """Route a user query based on intent and conversational context.

        Attempts LLM classification first (if mode is 'llm'), falling back to
        fast heuristic keyword matching if the call fails or returns ambiguous results.
        """
        active_mode = mode or self.default_mode
        if active_mode == "heuristic":
            return self.heuristic_route(query)

        try:
            return self.llm_route(query, context, provider=provider)
        except Exception as e:
            logger.warning(f"LLM routing error: {e}. Falling back to heuristic routing.")
            return self.heuristic_route(query)

    def llm_route(
        self,
        query: str,
        context: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[str] = None,
    ) -> RouteType:
        """Classify query using LLM reasoning."""
        prompt = build_router_prompt(query, context)
        resp, prov = call_llm(prompt, client=self.client, provider=provider)

        raw_text = (
            resp.text.strip()
            if prov == "gemini"
            else resp.choices[0].message.content.strip()
        )
        parsed = _extract_route_json(raw_text)
        classified = str(parsed.get("route", "")).lower().strip()

        if classified in ("structured", "rag", "hybrid"):
            return classified  # type: ignore

        # If LLM returned an unrecognized route string, use heuristic fallback
        return self.heuristic_route(query)

    def heuristic_route(self, query: str) -> RouteType:
        """Fast, zero-cost keyword and pattern matching fallback."""
        lower = query.lower()

        # RAG indicators (definitions, guidelines, terminology, domain explanations)
        rag_keywords = [
            "meaning", "definition", "what does", "what is the meaning", "define",
            "explain rating", "why was it rated", "guidelines", "methodology",
            "documentation", "glossary", "abbreviation", "data dictionary", "notes"
        ]
        has_rag = any(kw in lower for kw in rag_keywords)

        # Structured indicators (calculations, filters, aggregations, metrics)
        structured_keywords = [
            "count", "how many", "top", "average", "total", "sum", "list all",
            "filter", "highest", "lowest", "distribution", "breakdown", "columns",
            "most common", "percentage", "compare", "oldest", "newest", "median",
            "min", "max", "schema", "rows"
        ]
        has_structured = any(kw in lower for kw in structured_keywords)

        if has_rag and has_structured:
            return "hybrid"
        if has_rag:
            return "rag"
        return "structured"
