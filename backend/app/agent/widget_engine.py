"""Widget Engine: Compiles natural language prompts into live visual widgets and
provides deterministic recomputation against active session datasets without AI overhead.
"""
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.app.llm.client import call_llm, get_gemini_client
from backend.app.memory.session_store import ChatSession
from backend.app.tools.base import default_registry
from backend.app.tools.chart_tool import generate_chart, extract_chart_spec
from backend.app.agent.coordinator import _sanitize_chart_data

logger = logging.getLogger(__name__)

WIDGET_COMPILER_PROMPT = """You are a Data Analytics Visual Widget Compiler.
Given a dataset schema and a user request, you must compile the request into a deterministic aggregation recipe.

Dataset Schema & Summary:
{data_description}

User Request: "{prompt}"
Preferred Chart Type: {preferred_chart_type}

You must select ONE deterministic tool from:
1. "group_data": by_column (str), agg_column (str), agg_func ("count" | "mean" | "sum"), limit (int)
2. "get_unique_values": column (str), limit (int)
3. "aggregate_data": column (str), agg_func ("count" | "mean" | "sum" | "min" | "max")

Return ONLY a JSON object with this exact structure:
{{
  "title": "A concise, clean title for the widget",
  "widget_type": "chart" or "kpi",
  "chart_type": "bar" or "line" or "pie",
  "tool_name": "group_data" or "get_unique_values" or "aggregate_data",
  "parameters": {{ ... }},
  "metric_label": "Label if KPI widget or y-axis metric name"
}}
"""


def _extract_json_block(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {}


class WidgetEngine:
    def __init__(self):
        self.client = get_gemini_client()

    def create_widget_from_prompt(
        self,
        session: ChatSession,
        prompt: str,
        chart_type: Optional[str] = None,
        chart_theme: str = "light",
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compile user prompt into a live widget recipe via LLM once, then run locally."""
        df = session.df
        desc = session.data_description

        preferred = chart_type or "auto"
        compiler_prompt = WIDGET_COMPILER_PROMPT.format(
            data_description=desc,
            prompt=prompt,
            preferred_chart_type=preferred,
        )

        resp, prov = call_llm(compiler_prompt, client=self.client, provider=provider)
        raw = resp.text.strip() if prov == "gemini" else resp.choices[0].message.content.strip()
        config = _extract_json_block(raw)

        # Sensible fallbacks if compiler failed
        title = config.get("title") or prompt
        widget_type = config.get("widget_type", "chart")
        resolved_chart_type = chart_type or config.get("chart_type", "bar")
        tool_name = config.get("tool_name", "get_unique_values")
        params = config.get("parameters", {})

        if tool_name not in ("group_data", "get_unique_values", "aggregate_data"):
            tool_name = "get_unique_values"
            params = {"column": df.columns[0], "limit": 10}

        recipe = {
            "tool_name": tool_name,
            "parameters": params,
            "chart_type": resolved_chart_type,
            "widget_type": widget_type,
            "title": title,
        }

        # Deterministically compute initial data
        computed = self._execute_recipe(df, recipe, prompt=prompt, chart_theme=chart_theme)

        widget = {
            "id": f"w_{uuid.uuid4().hex[:8]}",
            "title": title,
            "prompt": prompt,
            "widget_type": widget_type,
            "chart_type": resolved_chart_type,
            "recipe": recipe,
            "chart_base64": computed.get("chart_base64"),
            "chart_svg": computed.get("chart_svg"),
            "chart_spec": computed.get("chart_spec"),
            "metric_value": computed.get("metric_value"),
            "metric_label": computed.get("metric_label") or config.get("metric_label", "Total"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        session.widgets.append(widget)
        return widget

    def create_widget_from_chat(
        self,
        session: ChatSession,
        title: Optional[str] = None,
        prompt: Optional[str] = None,
        chart_base64: Optional[str] = None,
        chart_svg: Optional[str] = None,
        chart_spec: Optional[dict] = None,
        operation: Optional[str] = None,
        chart_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Pin a chart message directly from conversation to the dashboard."""
        widget = {
            "id": f"w_{uuid.uuid4().hex[:8]}",
            "title": title or prompt or "Pinned Visual Insight",
            "prompt": prompt or "Pinned from chat",
            "widget_type": "chart",
            "chart_type": chart_type or "bar",
            "recipe": {
                "operation": operation or "chat_pin",
                "chart_type": chart_type or "bar",
            },
            "chart_base64": chart_base64,
            "chart_svg": chart_svg,
            "chart_spec": chart_spec,
            "metric_value": None,
            "metric_label": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        session.widgets.append(widget)
        return widget

    def recompute_widgets(
        self,
        session: ChatSession,
        chart_theme: str = "light",
    ) -> List[Dict[str, Any]]:
        """Recompute all widgets against updated session.df with ZERO AI calls."""
        df = session.df
        for widget in session.widgets:
            recipe = widget.get("recipe", {})
            tool_name = recipe.get("tool_name")
            params = recipe.get("parameters", {})

            if not tool_name:
                continue

            try:
                computed = self._execute_recipe(
                    df,
                    recipe,
                    prompt=widget.get("prompt", ""),
                    chart_theme=chart_theme,
                )
                widget["chart_base64"] = computed.get("chart_base64")
                widget["chart_svg"] = computed.get("chart_svg")
                widget["chart_spec"] = computed.get("chart_spec")
                widget["metric_value"] = computed.get("metric_value")
                widget["last_updated"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.warning(f"Failed to recompute widget {widget.get('id')}: {e}")

        return session.widgets

    def _execute_recipe(
        self,
        df: pd.DataFrame,
        recipe: dict,
        prompt: str = "",
        chart_theme: str = "light",
    ) -> dict:
        """Execute a deterministic tool recipe on a DataFrame and generate visual assets."""
        tool_name = recipe.get("tool_name")
        params = recipe.get("parameters", {})
        chart_type = recipe.get("chart_type", "bar")
        widget_type = recipe.get("widget_type", "chart")

        tool_fn = default_registry.get(tool_name)
        if not tool_fn:
            return {}

        raw_result = tool_fn(df=df, **params)

        if widget_type == "kpi" or isinstance(raw_result, (int, float, str)):
            return {
                "metric_value": f"{raw_result:,}" if isinstance(raw_result, (int, float)) else str(raw_result),
                "metric_label": recipe.get("title") or "Metric",
            }

        if isinstance(raw_result, dict) and raw_result:
            sanitized = _sanitize_chart_data(raw_result, prompt)
            target_col = params.get("by_column") or params.get("column") or "category"

            if tool_name == "group_data":
                chart_payload = {
                    "operation": "group_by_agg",
                    "chart_results": sanitized,
                    "target_column": target_col,
                    "agg_column": params.get("agg_column", ""),
                    "agg_func": params.get("agg_func", "count"),
                }
            else:
                chart_payload = {
                    "operation": "value_counts",
                    "counts": sanitized,
                    "target_column": target_col,
                }

            base64_str, svg_str = generate_chart(
                chart_payload,
                chart_type=chart_type,
                chart_theme=chart_theme,
            )
            spec = extract_chart_spec(chart_payload, chart_type=chart_type)
            return {
                "chart_base64": base64_str,
                "chart_svg": svg_str,
                "chart_spec": spec,
            }


        return {}


default_widget_engine = WidgetEngine()
