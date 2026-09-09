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
from backend.app.tools.chart_tool import generate_chart, extract_chart_spec
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


def _sanitize_chart_data(raw_dict: dict, question: str) -> dict:
    """Sanitize and limit chart data so charts are never clogged or unreadable.
    Filters to user-specified year ranges, sorts chronologically for time series,
    and caps categorical charts at the top 10 items.
    """
    if not raw_dict or len(raw_dict) <= 1:
        return {}

    def _is_year(val):
        try:
            n = int(str(val).strip())
            return 1900 <= n <= 2100
        except (ValueError, TypeError):
            return False

    all_year_keys = all(_is_year(k) for k in raw_dict.keys())

    if all_year_keys:
        # Check if user mentioned a year range in the question (e.g. '2015 to 2020')
        years_in_q = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", question)]
        if len(years_in_q) >= 2:
            start_yr, end_yr = min(years_in_q), max(years_in_q)
            filtered = {
                str(k): v for k, v in raw_dict.items()
                if start_yr <= int(str(k).strip()) <= end_yr
            }
            if len(filtered) > 1:
                return dict(sorted(filtered.items(), key=lambda x: int(str(x[0]).strip())))
        elif len(years_in_q) == 1:
            target_yr = years_in_q[0]
            if str(target_yr) in [str(k) for k in raw_dict.keys()] and len(raw_dict) > 15:
                return {}

        # Default for year data: sort chronologically and cap at most recent 12 years
        sorted_years = sorted(raw_dict.items(), key=lambda x: int(str(x[0]).strip()))
        if len(sorted_years) > 12:
            sorted_years = sorted_years[-12:]
        return dict(sorted_years)

    # For categorical data: always cap at top 10 to avoid unreadable, clogged charts
    sorted_items = sorted(
        raw_dict.items(),
        key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
        reverse=True
    )
    return dict(sorted_items[:10])


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
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a user question through routing, deterministic tool invocation, and summarization.

        Args:
            session_id: The ID of the active chat workspace.
            question: Natural language question from the user.
            provider: Optional LLM provider override ('gemini' or 'groq').
            chart_type: Optional chart type ('bar', 'line', 'pie', 'auto').
            chart_theme: Optional visual theme for matplotlib rendering.
            user_id: Optional user identifier for workspace isolation.

        Returns:
            Dict containing summary, chart_base64, operation, result, usage, model_used, and route.
        """
        session = self.memory.get_session(session_id, user_id=user_id)
        if not session:
            session = self.memory.ensure_default_session(user_id=user_id or "user_default")

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
        chart_svg = None
        chart_spec = None
        serializable_result: Any = None
        operation = "unknown"
        summary_text = ""

        # =====================================================================
        # ROUTE 1: RAG (Documentation & Knowledge Retrieval)
        # =====================================================================
        if route == "rag":
            operation = "search_documents"
            rag_tool = self.registry.get("search_documents")
            excerpts = rag_tool(query=question, user_id=session.user_id) if rag_tool else []
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
                history=session.history,  # snapshot was loaded before appending this turn
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
                    params.pop("user_id", None)
                    raw_result = tool_fn(**params, user_id=session.user_id)
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
                excerpts = rag_tool(query=question, user_id=session.user_id) if rag_tool else []
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
                assumption = None
                if any(w in question.lower() for w in ["best", "worst", "popular", "top", "favorite", "greatest", "successful"]):
                    thought = tool_decision.get("thought", "")
                    if thought and any(k in thought.lower() for k in ["interpret", "assume", "proxy", "lack", "no rating"]):
                        assumption = thought
                sum_prompt = build_summary_prompt(question, tool_name, serializable_result, assumption=assumption)
                sum_resp, sum_prov = call_llm(sum_prompt, client=self.client, provider=provider)
                _accumulate_usage(sum_resp, sum_prov)
                summary_text = (
                    sum_resp.text.strip()
                    if sum_prov == "gemini"
                    else sum_resp.choices[0].message.content.strip()
                )

            # Step F: Generate chart if appropriate
            chart_payload = None
            if tool_name == "get_unique_values" and isinstance(raw_result, dict):
                # Don't chart if question was asking about a specific entity (e.g. 'Wakanda') rather than an overall breakdown
                is_specific_query = any(w in question.lower() for w in ["from ", "by ", "with ", "in ", "directed by"]) and not any(w in question.lower() for w in ["top", "all", "most", "breakdown", "distribution", "every", "common", "frequencies", "compare"])
                if not is_specific_query:
                    top_counts = _sanitize_chart_data(raw_result, question)
                    if len(top_counts) > 1:
                        chart_payload = {
                            "operation": "value_counts",
                            "counts": top_counts,
                            "target_column": params.get("column", ""),
                        }
            elif tool_name == "group_data" and isinstance(raw_result, dict):
                if len(raw_result) > 1:
                    sanitized = _sanitize_chart_data(raw_result, question)
                    if len(sanitized) > 1:
                        chart_payload = {
                            "operation": "group_by_agg",
                            "chart_results": sanitized,
                            "target_column": params.get("by_column", ""),
                            "agg_column": params.get("agg_column", ""),
                            "agg_func": params.get("agg_func", "count"),
                        }
                elif len(raw_result) == 1 and df is not None and "release_year" in df.columns:
                    # Single key (e.g. {'TV Show': 1.76}): expand over release_year if user asked for graph/trend
                    agg_col = params.get("agg_column") or "duration_seasons"
                    agg_func = params.get("agg_func") or "mean"
                    by_col = params.get("by_column", "")
                    by_val = list(raw_result.keys())[0]
                    sub_df = df[df[by_col].astype(str).str.lower() == str(by_val).lower()] if by_col in df.columns else df
                    if agg_col in sub_df.columns:
                        grouped = (
                            sub_df.dropna(subset=["release_year", agg_col])
                            .groupby("release_year")[agg_col]
                            .agg(agg_func)
                            .round(2)
                            .to_dict()
                        )
                        grouped = _sanitize_chart_data(grouped, question)
                        if len(grouped) > 1:
                            chart_payload = {
                                "operation": "group_by_agg",
                                "chart_results": grouped,
                                "target_column": "release_year",
                                "agg_column": agg_col,
                                "agg_func": agg_func,
                            }
            elif tool_name == "filter_rows" and isinstance(raw_result, pd.DataFrame) and len(raw_result) > 1:
                filter_col = params.get("column", "")
                chosen_col = None
                if filter_col in raw_result.columns and raw_result[filter_col].nunique() > 1:
                    chosen_col = filter_col
                else:
                    for cand in ["duration", "duration_seasons", "release_year", "rating", "type", "country", "listed_in"]:
                        if cand in raw_result.columns and raw_result[cand].nunique() > 1:
                            chosen_col = cand
                            break
                if chosen_col:
                    counts = raw_result[chosen_col].dropna().astype(str).value_counts().to_dict()
                    counts = _sanitize_chart_data(counts, question)
                    if len(counts) > 1:
                        chart_payload = {
                            "operation": "filter",
                            "chart_counts": counts,
                            "chart_target_column": chosen_col,
                        }
            elif tool_name == "aggregate_data" and df is not None:
                agg_col = params.get("column", "")
                agg_func = params.get("agg_func", "mean")
                is_line_request = chart_type == "line" or any(w in question.lower() for w in ["line", "trend", "over time", "by year", "history"])
                if is_line_request and "release_year" in df.columns and agg_col in df.columns:
                    sub_df = df
                    if "tv show" in question.lower() and "type" in df.columns:
                        sub_df = df[df["type"].astype(str).str.lower().str.contains("tv")]
                    elif "movie" in question.lower() and "type" in df.columns:
                        sub_df = df[df["type"].astype(str).str.lower().str.contains("movie")]
                    grouped = (
                        sub_df.dropna(subset=["release_year", agg_col])
                        .groupby("release_year")[agg_col]
                        .agg(agg_func)
                        .round(2)
                        .to_dict()
                    )
                    grouped = _sanitize_chart_data(grouped, question)
                    if len(grouped) > 1:
                        chart_payload = {
                            "operation": "group_by_agg",
                            "chart_results": grouped,
                            "target_column": "release_year",
                            "agg_column": agg_col,
                            "agg_func": agg_func,
                        }
                elif agg_col in df.columns:
                    counts = df[agg_col].dropna().astype(str).value_counts().to_dict()
                    counts = _sanitize_chart_data(counts, question)
                    if len(counts) > 1:
                        chart_payload = {
                            "operation": "value_counts",
                            "counts": counts,
                            "target_column": agg_col,
                        }
            elif tool_name == "sort_data" and isinstance(raw_result, list) and len(raw_result) > 1:
                chart_payload = {
                    "operation": "sort_limit",
                    "results": raw_result[:10],
                    "target_column": params.get("by_column", ""),
                }

            if chart_payload:
                try:
                    chart_base64, chart_svg = generate_chart(
                        chart_payload,
                        chart_type=chart_type,
                        chart_theme=chart_theme,
                    )
                    chart_spec = extract_chart_spec(
                        chart_payload,
                        chart_type=chart_type,
                    )
                except Exception as chart_err:
                    logger.warning(f"Chart generation error: {chart_err}")
                    chart_base64 = None
                    chart_svg = None
                    chart_spec = None

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
                "chart_base64": chart_base64,
                "chart_svg": chart_svg,
                "chart_spec": chart_spec,
            },
        )

        return {
            "summary": summary_text,
            "chart_base64": chart_base64,
            "chart_svg": chart_svg,
            "chart_spec": chart_spec,
            "operation": operation,
            "unsupported_reason": None,
            "result": serializable_result,
            "usage": usage_total,
            "model_used": model_used,
            "route": route,
        }


# Global singleton coordinator instance
default_coordinator = AgentCoordinator()

