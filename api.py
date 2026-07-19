import os
import base64
import io
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

from dataloader import load_data, describe_dataframe
from query_planner import get_query_plan, get_summary, _call_llm
from query_executor import execute_plan
from chart_generator import generate_chart

_suggestions_cache = None

# Load environment
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load data once at startup — not on every request
df = load_data("data/netflix_titles.csv")
data_description = describe_dataframe(df)

# FastAPI app
app = FastAPI()

# Allow React (running on a different port) to talk to this API
_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in _raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request shape — what React sends
class QuestionRequest(BaseModel):
    question: str
    chart_type: str | None = None
    chart_theme: str = "light"

# Response shape — what we send back
class AnalysisResponse(BaseModel):
    summary: str
    chart_base64: str | None = None
    operation: str
    unsupported_reason: str | None = None
    usage: dict
    model_used: str = "gemini"

@app.get("/")
def health_check():
    return {"status": "AI Data Analyst API is running"}

SUGGESTION_PROMPT = """You are a data analyst. Based on this dataset description, generate exactly 4 example questions a user might want to ask. They should be diverse, practical, and demonstrate different analysis types (counting, top N, aggregation, filtering). Return ONLY a JSON array of 4 strings, no explanation.

Dataset:
{data_description}"""

@app.get("/api/suggestions")
def get_suggestions():
    global _suggestions_cache
    if _suggestions_cache is not None:
        return _suggestions_cache

    prompt = SUGGESTION_PROMPT.format(data_description=data_description)
    resp, _provider = _call_llm(prompt, client)
    raw = resp.text.strip() if _provider == "gemini" else resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").lstrip("json").strip()
    import json
    _suggestions_cache = json.loads(raw)
    return _suggestions_cache

@app.post("/api/ask", response_model=AnalysisResponse)
def ask(request: QuestionRequest):
    # Step 1: question → query plan
    result = get_query_plan(request.question, data_description, client)
    plan = result["plan"]
    plan_usage = result["usage"]
    plan_model = result["model_used"]

    # Step 2: handle unsupported questions immediately
    if plan.get("operation") == "unsupported":
        return AnalysisResponse(
            summary=plan.get("reason", "This question cannot be answered with the available data."),
            chart_base64=None,
            operation="unsupported",
            unsupported_reason=plan.get("reason"),
            usage=plan_usage,
            model_used=plan_model
        )

    # Step 3: execute the plan against real data
    exec_result = execute_plan(df, plan)

    # Step 4: get plain-English summary (also capture usage + model from the second call)
    summary_result = get_summary(request.question, exec_result, client)
    summary = summary_result["summary"]
    summary_usage = summary_result["usage"]
    summary_model = summary_result["model_used"]

    # Combine usage from both calls
    combined_usage = {
        "prompt_tokens": plan_usage["prompt_tokens"] + summary_usage["prompt_tokens"],
        "response_tokens": plan_usage["response_tokens"] + summary_usage["response_tokens"],
        "total_tokens": plan_usage["total_tokens"] + summary_usage["total_tokens"],
    }
    model_used = "groq" if (plan_model == "groq" or summary_model == "groq") else "gemini"

    # Step 5: generate chart (in-memory, no file I/O)
    chart_base64 = None
    if exec_result.get("operation") != "unsupported":
        try:
            chart_base64 = generate_chart(exec_result, chart_type=request.chart_type, chart_theme=request.chart_theme)
        except Exception as e:
            print(f"Chart generation error: {e}")

    return AnalysisResponse(
        summary=summary,
        chart_base64=chart_base64,
        operation=plan.get("operation"),
        unsupported_reason=None,
        usage=combined_usage,
        model_used=model_used
    )