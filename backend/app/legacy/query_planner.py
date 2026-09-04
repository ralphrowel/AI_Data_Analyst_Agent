import json
import os
from google import genai
from openai import OpenAI
from backend.app.llm.client import call_llm, normalize_usage

ALLOWED_OPERATIONS = ["filter", "value_counts", "group_by_agg", "sort_limit"]


def _call_llm(prompt, client, model="gemini-2.5-flash"):
    return call_llm(prompt, client, model=model)


def _strip_json_fences(raw_text):
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`").lstrip("json").strip()
    return raw_text


def build_query_prompt(question: str, data_description: str) -> str:
    return f"""You are a data analysis assistant. You will be given a description 
of a dataset and a user's question. Your job is to translate the question into 
a single structured operation, returned as JSON only — no explanation, no markdown.

DATASET DESCRIPTION:
{data_description}

ALLOWED OPERATIONS: {ALLOWED_OPERATIONS}

FILTER CAPABILITIES:
- Multiple filters: pass a list of filter objects to combine with AND
- Each filter supports operators:
  * "contains" (default): case-insensitive substring match on string column
  * "eq": exact string match
  * "date_month_year": {{"month": int, "year": int}} on a date-like column
  * "date_year": int on a date-like column
  * "date_month": int on a date-like column

JSON FORMAT:
{{
  "operation": one of {ALLOWED_OPERATIONS},
  "filter": [{{"column": "...", "operator": "...", "value": ...}}] or null,
  "target_column": "the column to analyze",
  "agg_column": "the column to aggregate, only for group_by_agg" or null,
  "agg_func": "mean/sum/count, only for group_by_agg" or null,
  "sort_ascending": true or false, only for sort_limit,
  "limit": integer or null
}}

OPERATION GUIDANCE:
- Use "value_counts" for any question asking about most common, most frequent, or top N of a column. The "limit" field controls how many results to return.
- Use "group_by_agg" when grouping one column and computing a number (sum, mean, count) from another column.
- Use "sort_limit" only when sorting the raw rows of the dataset itself, not aggregated results.
- "unsupported" should only be used when the question genuinely cannot be answered with the available columns — not because of uncertainty about which operation to use.

If the question cannot be answered with the available columns or operations, 
return {{"operation": "unsupported", "reason": "explain why in plain English"}}.

USER QUESTION: {question}

Return ONLY the JSON object, nothing else.
"""


def get_query_plan(question: str, data_description: str, client) -> dict:
    prompt = build_query_prompt(question, data_description)
    response, provider = _call_llm(prompt, client)

    raw_text = response.text.strip() if provider == "gemini" else response.choices[0].message.content.strip()
    raw_text = _strip_json_fences(raw_text)
    plan = json.loads(raw_text)
    usage = normalize_usage(response, provider)

    return {"plan": plan, "usage": usage, "model_used": provider}


def build_summary_prompt(question: str, result: dict) -> str:
    return f"""The user asked: "{question}"

The data analysis produced this result:
{result}

Write a 2-3 sentence plain-English summary explaining what the result shows. 
Mention specific numbers where relevant. Do not mention that an AI was used.
Keep the tone factual and concise.
"""


def get_summary(question: str, result: dict, client) -> dict:
    prompt = build_summary_prompt(question, result)
    response, provider = _call_llm(prompt, client)

    text = response.text.strip() if provider == "gemini" else response.choices[0].message.content.strip()
    usage = normalize_usage(response, provider)

    return {"summary": text, "usage": usage, "model_used": provider}
