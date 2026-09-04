import json
from fastapi import APIRouter
from backend.app.api.schemas import QuestionRequest, AnalysisResponse
from backend.app.config import DEFAULT_DATASET_PATH
from backend.app.data_engine.loader import load_data, describe_dataframe
from backend.app.tools.chart_tool import generate_chart
from backend.app.llm.client import get_gemini_client, call_llm
from backend.app.legacy.query_planner import get_query_plan, get_summary
from backend.app.legacy.query_executor import execute_plan

router = APIRouter()

# Client and data initialization
client = get_gemini_client()
df = load_data(DEFAULT_DATASET_PATH)
data_description = describe_dataframe(df)

_suggestions_cache = None

SUGGESTION_PROMPT = """You are a data analyst. Based on this dataset description, generate exactly 4 example questions a user might want to ask. They should be diverse, practical, and demonstrate different analysis types (counting, top N, aggregation, filtering). Return ONLY a JSON array of 4 strings, no explanation.

Dataset:
{data_description}"""


@router.get("/")
def health_check():
    return {"status": "AI Data Analyst API is running", "architecture": "modular"}


@router.get("/api/suggestions")
def get_suggestions():
    global _suggestions_cache
    if _suggestions_cache is not None:
        return _suggestions_cache

    prompt = SUGGESTION_PROMPT.format(data_description=data_description)
    resp, provider = call_llm(prompt, client)
    raw = resp.text.strip() if provider == "gemini" else resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").lstrip("json").strip()
    _suggestions_cache = json.loads(raw)
    return _suggestions_cache


@router.post("/api/ask", response_model=AnalysisResponse)
def ask(request: QuestionRequest):
    # Step 1: question -> query plan
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
            model_used=plan_model,
        )

    # Step 3: execute the plan against real data
    exec_result = execute_plan(df, plan)

    # Step 4: get plain-English summary
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
            chart_base64 = generate_chart(
                exec_result,
                chart_type=request.chart_type,
                chart_theme=request.chart_theme,
            )
        except Exception as e:
            print(f"Chart generation error: {e}")

    return AnalysisResponse(
        summary=summary,
        chart_base64=chart_base64,
        operation=plan.get("operation", "unknown"),
        unsupported_reason=None,
        usage=combined_usage,
        model_used=model_used,
    )
