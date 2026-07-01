import json
from google import genai

ALLOWED_OPERATIONS = ["filter", "value_counts", "group_by_agg", "sort_limit"]

def build_query_prompt(question: str, data_description: str) -> str:
    return f"""You are a data analysis assistant. You will be given a description 
of a dataset and a user's question. Your job is to translate the question into 
a single structured operation, returned as JSON only — no explanation, no markdown.

DATASET DESCRIPTION:
{data_description}

ALLOWED OPERATIONS: {ALLOWED_OPERATIONS}

JSON FORMAT:
{{
  "operation": one of {ALLOWED_OPERATIONS},
  "filter": {{"column": "...", "value": "..."}} or null,
  "target_column": "the column to analyze",
  "agg_column": "the column to aggregate, only for group_by_agg" or null,
  "agg_func": "mean/sum/count, only for group_by_agg" or null,
  "sort_ascending": true or false, only for sort_limit,
  "limit": integer or null
}}

If the question cannot be answered with the available columns or operations, 
return {{"operation": "unsupported", "reason": "explain why in plain English"}}.

USER QUESTION: {question}

Return ONLY the JSON object, nothing else.
"""

def get_query_plan(question: str, data_description: str, client) -> dict:
    prompt = build_query_prompt(question, data_description)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    raw_text = response.text.strip()
    
    # Gemini sometimes wraps JSON in markdown code fences — strip those if present
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`").lstrip("json").strip()
    
    return json.loads(raw_text)


def build_summary_prompt(question: str, result: dict) -> str:
    return f"""The user asked: "{question}"

The data analysis produced this result:
{result}

Write a 2-3 sentence plain-English summary explaining what the result shows. 
Mention specific numbers where relevant. Do not mention that an AI was used.
Keep the tone factual and concise.
"""


def get_summary(question: str, result: dict, client) -> str:
    prompt = build_summary_prompt(question, result)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()