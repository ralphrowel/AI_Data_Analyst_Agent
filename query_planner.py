import json
import os
from google import genai
from openai import OpenAI

ALLOWED_OPERATIONS = ["filter", "value_counts", "group_by_agg", "sort_limit"]

def _get_groq_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")

def _is_quota_error(e):
    error_str = str(e).lower()
    return "429" in error_str or "quota" in error_str or "resource exhausted" in error_str or "rate limit" in error_str

def _normalize_usage(response, provider):
    if provider == "groq":
        return {
            "prompt_tokens": response.usage.prompt_tokens,
            "response_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
    return {
        "prompt_tokens": response.usage_metadata.prompt_token_count,
        "response_tokens": response.usage_metadata.candidates_token_count,
        "total_tokens": response.usage_metadata.total_token_count,
    }

def _call_llm(prompt, client, model="gemini-2.5-flash"):
    groq_client = _get_groq_client()
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response, "gemini"
    except Exception as e:
        if groq_client and _is_quota_error(e):
            groq_resp = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
            )
            return groq_resp, "groq"
        raise

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
    usage = _normalize_usage(response, provider)

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
    usage = _normalize_usage(response, provider)

    return {"summary": text, "usage": usage, "model_used": provider}
