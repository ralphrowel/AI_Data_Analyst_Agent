"""Agent Coordinator: Coordinates tool calls, multi-turn state, and LLM reasoning.

Orchestrates query resolution across Router, Tools (both structured and RAG),
and Session Memory as specified in Step 4 of the architectural plan.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.app.agent.router import QueryRouter
from backend.app.agent.prompts import (
    build_tool_selection_prompt,
    build_summary_prompt,
    build_rag_summary_prompt,
    build_hybrid_summary_prompt,
)
from backend.app.memory.session_store import SessionStore, default_session_store
from backend.app.tools.base import ToolRegistry, default_registry
from backend.app.tools.chart_tool import generate_chart
from backend.app.llm.client import call_llm, normalize_usage

logger = logging.getLogger(__name__)


def _extract_json(raw_text: str) -> dict:
    """Safely extract a JSON object from model response text."""
    text = raw_text.strip()
    # Strip markdown backticks
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    # Regex search for the first outermost JSON object {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {
        "tool": "unsupported",
        "parameters": {"reason": "Could not parse model response into a valid tool call."},
    }


class AgentCoordinator:
    """Orchestrates query resolution across Router, deterministic Tools, and Session Memory."""

    def __init__(
        self,
        router: Optional[QueryRouter] = None,
        memory: Optional[SessionStore] = None,
        registry: Optional[ToolRegistry] = None,
        llm_client: Any = None,
    ):
        self.router = router or QueryRouter()
        self.memory = memory or default_session_store
        self.registry = registry or default_registry
        self.client = llm_client

    def process_query(
        self,
        session_id: str,
        question: str,
        provider: Optional[str] = None,
        chart_type: Optional[str] = None,
        chart_theme: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a user question through routing, deterministic tool invocation, and summarization.

        Args:
            session_id: The ID of the active chat workspace.
            question: Natural language question from the user.
            provider: Optional LLM provider override ('gemini' or 'groq').
            chart_type: Optional chart type ('bar', 'line', 'pie', 'auto').
            chart_theme: Optional visual theme for matplotlib rendering.

        Returns:
            Dict containing summary, chart_base64, operation, result, usage, model_used, and route.
        """
        session = self.memory.get_session(session_id)
        if not session:
            session = self.memory.ensure_default_session()

        df = session.df
        data_description = session.data_description

        # Classify intent via router
        route = self.router.route(question, session.history, provider=provider)

        # Record user question in session history
        self.memory.add_turn(session.session_id, "user", question)

        # Track usage across multiple LLM steps in this turn
        usage_total = {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}
        models_used = set()

        def _accumulate_usage(resp, prov):
            u = normalize_usage(resp, prov)
            for k in ("prompt_tokens", "response_tokens", "total_tokens"):
                usage_total[k] += u.get(k, 0)
            models_used.add(prov)

        chart_base64 = None
        serializable_result: Any = None
        operation = "unknown"
        summary_text = ""

        # =====================================================================
        # ROUTE 1: RAG (Documentation & Knowledge Retrieval)
        # =====================================================================
        if route == "rag":
            operation = "search_documents"
            rag_tool = self.registry.get("search_documents")
            excerpts = rag_tool(query=question) if rag_tool else []
            serializable_result = excerpts

            rag_prompt = build_rag_summary_prompt(question, excerpts)
            resp, prov = call_llm(rag_prompt, client=self.client, provider=provider)
            _accumulate_usage(resp, prov)
            summary_text = (
                resp.text.strip()
                if prov == "gemini"
                else resp.choices[0].message.content.strip()
            )

        # =====================================================================
        # ROUTE 2 & 3: STRUCTURED or HYBRID
        # =====================================================================
        else:
            # Step A: Ask LLM to select tool and provide parameters
            schemas = self.registry.get_schemas()
            selection_prompt = build_tool_selection_prompt(
                question=question,
                data_description=data_description,
                tools_schemas=schemas,
                history=session.history[:-1],  # exclude current user turn from history snippet
            )

            resp, prov = call_llm(selection_prompt, client=self.client, provider=provider)
            _accumulate_usage(resp, prov)
            raw_text = (
                resp.text.strip()
                if prov == "gemini"
                else resp.choices[0].message.content.strip()
            )

            tool_decision = _extract_json(raw_text)
            tool_name = tool_decision.get("tool", "unsupported")
            params = tool_decision.get("parameters", {})
            operation = tool_name

            # Step B: Handle unsupported queries
            if tool_name == "unsupported":
                reason = params.get(
                    "reason",
                    "This question cannot be answered with the available data.",
                )
                model_used = list(models_used)[-1] if models_used else (prov or "gemini")
                self.memory.add_turn(
                    session.session_id,
                    "assistant",
                    reason,
                    metadata={"operation": "unsupported", "model_used": model_used, "route": route},
                )
                self.memory.update_tokens(session.session_id, usage_total, model_used)
                return {
                    "summary": reason,
                    "chart_base64": None,
                    "operation": "unsupported",
                    "unsupported_reason": reason,
                    "result": None,
                    "usage": usage_total,
                    "model_used": model_used,
                    "route": route,
                }

            # Step C: Retrieve & execute deterministic tool function
            tool_fn = self.registry.get(tool_name)
            if not tool_fn:
                # Fallback if an unregistered tool name was proposed
                logger.warning(f"Proposed tool '{tool_name}' not found in registry.")
                tool_fn = self.registry.get("get_dataset_schema")
                tool_name = "get_dataset_schema"
                params = {}
                operation = tool_name

            try:
                if tool_name == "search_documents":
                    raw_result = tool_fn(**params)
                else:
                    raw_result = tool_fn(df=df, **params)
            except Exception as err:
                logger.error(f"Execution error running '{tool_name}' with {params}: {err}")
                raw_result = {"error": str(err), "tool": tool_name}

            # Step D: Package result for JSON serialization & summary
            if isinstance(raw_result, pd.DataFrame):
                serializable_result = {
                    "total_matches": len(raw_result),
                    "sample_records": raw_result.head(10).where(pd.notna(raw_result), None).to_dict(orient="records"),
                }
            else:
                serializable_result = raw_result

            # Step E: Summarize
            if route == "hybrid":
                # For hybrid, also retrieve documentation context
                rag_tool = self.registry.get("search_documents")
                excerpts = rag_tool(query=question) if rag_tool else []
                hybrid_prompt = build_hybrid_summary_prompt(
                    question=question,
                    tool_result=serializable_result,
                    excerpts=excerpts,
                )
                sum_resp, sum_prov = call_llm(hybrid_prompt, client=self.client, provider=provider)
                _accumulate_usage(sum_resp, sum_prov)
                summary_text = (
                    sum_resp.text.strip()
                    if sum_prov == "gemini"
                    else sum_resp.choices[0].message.content.strip()
                )
            else:
                sum_prompt = build_summary_prompt(question, tool_name, serializable_result)
                sum_resp, sum_prov = call_llm(sum_prompt, client=self.client, provider=provider)
                _accumulate_usage(sum_resp, sum_prov)
                summary_text = (
                    sum_resp.text.strip()
                    if sum_prov == "gemini"
                    else sum_resp.choices[0].message.content.strip()
                )

            # Step F: Generate chart if appropriate
            chart_payload = None
            if tool_name == "get_unique_values" and isinstance(raw_result, dict) and len(raw_result) > 1:
                chart_payload = {
                    "operation": "value_counts",
                    "counts": raw_result,
                    "target_column": params.get("column", ""),
                }
            elif tool_name == "group_data" and isinstance(raw_result, dict) and len(raw_result) > 1:
                chart_payload = {
                    "operation": "group_by_agg",
                    "chart_results": raw_result,
                    "target_column": params.get("by_column", ""),
                    "agg_column": params.get("agg_column", ""),
                    "agg_func": params.get("agg_func", "count"),
                }
            elif tool_name == "sort_data" and isinstance(raw_result, list) and len(raw_result) > 1:
                chart_payload = {
                    "operation": "sort_limit",
                    "results": raw_result,
                    "target_column": params.get("by_column", ""),
                }

            if chart_payload:
                try:
                    chart_base64 = generate_chart(
                        chart_payload,
                        chart_type=chart_type,
                        chart_theme=chart_theme,
                    )
                except Exception as chart_err:
                    logger.warning(f"Chart generation error: {chart_err}")
                    chart_base64 = None

        # =====================================================================
        # UPDATE SESSION & RETURN
        # =====================================================================
        model_used = "groq" if "groq" in models_used else "gemini"
        self.memory.update_tokens(session.session_id, usage_total, model_used)
        self.memory.add_turn(
            session.session_id,
            "assistant",
            summary_text,
            metadata={
                "operation": operation,
                "model_used": model_used,
                "route": route,
            },
        )

        return {
            "summary": summary_text,
            "chart_base64": chart_base64,
            "operation": operation,
            "result": serializable_result,
            "usage": usage_total,
            "model_used": model_used,
            "route": route,
        }
