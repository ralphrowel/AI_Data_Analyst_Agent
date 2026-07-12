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
from query_planner import get_query_plan, get_summary
from query_executor import execute_plan
from chart_generator import generate_chart

# Load environment
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load data once at startup — not on every request
df = load_data("data/netflix_titles.csv")
data_description = describe_dataframe(df)

# FastAPI app
app = FastAPI()

# Allow React (running on a different port) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request shape — what React sends
class QuestionRequest(BaseModel):
    question: str
    chart_type: str | None = None

# Response shape — what we send back
class AnalysisResponse(BaseModel):
    summary: str
    chart_base64: str | None = None
    operation: str
    unsupported_reason: str | None = None
    usage: dict

@app.get("/")
def health_check():
    return {"status": "AI Data Analyst API is running"}

SUGGESTION_PROMPT = """You are a data analyst. Based on this dataset description, generate exactly 4 example questions a user might want to ask. They should be diverse, practical, and demonstrate different analysis types (counting, top N, aggregation, filtering). Return ONLY a JSON array of 4 strings, no explanation.

Dataset:
{data_description}"""

@app.get("/api/suggestions")
def get_suggestions():
    prompt = SUGGESTION_PROMPT.format(data_description=data_description)
    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    raw = resp.text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").lstrip("json").strip()
    import json
    return json.loads(raw)

@app.post("/api/ask", response_model=AnalysisResponse)
def ask(request: QuestionRequest):
    # Step 1: question → query plan
    plan = get_query_plan(request.question, data_description, client)

    # Step 2: handle unsupported questions immediately
    if plan.get("operation") == "unsupported":
        return AnalysisResponse(
            summary=plan.get("reason", "This question cannot be answered with the available data."),
            chart_base64=None,
            operation="unsupported",
            unsupported_reason=plan.get("reason"),
            usage={"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}
        )

    # Step 3: execute the plan against real data
    result = execute_plan(df, plan)

    # Step 4: get plain-English summary
    summary = get_summary(request.question, result, client)

    # Step 5: generate chart and convert to base64 string
    chart_base64 = None
    try:
        generate_chart(result)
        if os.path.exists("chart.png"):
            with open("chart.png", "rb") as f:
                chart_base64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Chart generation error: {e}")

    return AnalysisResponse(
        summary=summary,
        chart_base64=chart_base64,
        operation=plan.get("operation"),
        unsupported_reason=None,
        usage={"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}
    )