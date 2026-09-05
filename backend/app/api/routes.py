import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from backend.app.api.schemas import (
    QuestionRequest,
    AnalysisResponse,
    CreateSessionRequest,
    SessionResponse,
    DatasetInfo,
    UploadDatasetRequest,
)
from backend.app.tools.chart_tool import generate_chart
from backend.app.llm.client import get_gemini_client, call_llm
from backend.app.legacy.query_planner import get_query_plan, get_summary
from backend.app.legacy.query_executor import execute_plan
from backend.app.memory.session_store import default_session_store
from backend.app.data_engine.dataset_manager import default_dataset_manager

router = APIRouter()

client = get_gemini_client()

# Cache suggestions per dataset name
_suggestions_cache: dict = {}

SUGGESTION_PROMPT = """You are a data analyst. Based on this dataset description, generate exactly 4 example questions a user might want to ask. They should be diverse, practical, and demonstrate different analysis types (counting, top N, aggregation, filtering). Return ONLY a JSON array of 4 strings, no explanation.

Dataset:
{data_description}"""


@router.get("/")
def health_check():
    return {"status": "AI Data Analyst API is running", "architecture": "modular"}


# --- Datasets Endpoints ---

@router.get("/api/datasets", response_model=List[DatasetInfo])
def list_datasets():
    """List all available raw datasets."""
    return default_dataset_manager.list_datasets()


@router.post("/api/upload", response_model=DatasetInfo)
def upload_dataset(req: UploadDatasetRequest):
    """Upload a new CSV file from local device and save to data/raw/."""
    filename = req.filename.strip()
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are currently supported.")

    target_path = default_dataset_manager.raw_data_dir / filename
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(req.content)

        # Force refresh dataset cache
        if filename in default_dataset_manager._cache:
            del default_dataset_manager._cache[filename]
        if filename in default_dataset_manager._desc_cache:
            del default_dataset_manager._desc_cache[filename]

        df = default_dataset_manager.get_dataset(filename)
        return {
            "name": filename,
            "rows": len(df),
            "columns": len(df.columns),
            "size_bytes": target_path.stat().st_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded file: {e}")


# --- Sessions Endpoints ---

@router.get("/api/sessions", response_model=List[SessionResponse])
def list_sessions():
    """List all active chat sessions."""
    return default_session_store.list_sessions()


@router.post("/api/sessions", response_model=SessionResponse)
def create_session(request: CreateSessionRequest):
    """Create a new chat session attached to a specific dataset."""
    session = default_session_store.create_session(
        dataset_name=request.dataset_name,
        title=request.title,
    )
    return session.to_dict()


@router.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    """Get full details and history for a specific session."""
    session = default_session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    data = session.to_dict()
    data["history"] = session.history
    return data


@router.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a chat session."""
    success = default_session_store.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True, "session_id": session_id}


# --- Analytics & Question Answering ---

@router.get("/api/suggestions")
def get_suggestions(provider: Optional[str] = None, session_id: Optional[str] = None):
    session = default_session_store.get_session(session_id)
    dataset_name = session.dataset_name if session else "netflix_titles.csv"

    if dataset_name in _suggestions_cache:
        return _suggestions_cache[dataset_name]

    desc = session.data_description if session else default_dataset_manager.get_dataset_description(dataset_name)
    prompt = SUGGESTION_PROMPT.format(data_description=desc)
    resp, provider_used = call_llm(prompt, client, provider=provider)
    raw = resp.text.strip() if provider_used == "gemini" else resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").lstrip("json").strip()
    _suggestions_cache[dataset_name] = json.loads(raw)
    return _suggestions_cache[dataset_name]


@router.post("/api/ask", response_model=AnalysisResponse)
def ask(request: QuestionRequest):
    # Retrieve the session and its isolated dataset
    session = default_session_store.get_session(request.session_id)
    df = session.df
    data_description = session.data_description

    # Record user message in session history
    default_session_store.add_turn(session.session_id, "user", request.question)

    # Step 1: question -> query plan
    result = get_query_plan(request.question, data_description, client, provider=request.provider)
    plan = result["plan"]
    plan_usage = result["usage"]
    plan_model = result["model_used"]

    # Step 2: handle unsupported questions immediately
    if plan.get("operation") == "unsupported":
        reason = plan.get("reason", "This question cannot be answered with the available data.")
        default_session_store.add_turn(session.session_id, "assistant", reason, {"operation": "unsupported"})
        return AnalysisResponse(
            summary=reason,
            chart_base64=None,
            operation="unsupported",
            unsupported_reason=plan.get("reason"),
            usage=plan_usage,
            model_used=plan_model,
        )

    # Step 3: execute the plan against the session's specific data
    exec_result = execute_plan(df, plan)

    # Step 4: get plain-English summary
    summary_result = get_summary(request.question, exec_result, client, provider=request.provider)
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

    # Update session token accumulation & record assistant turn
    default_session_store.update_tokens(session.session_id, combined_usage, model_used)
    default_session_store.add_turn(session.session_id, "assistant", summary, {
        "operation": plan.get("operation", "unknown"),
        "model_used": model_used,
    })

    # Step 5: generate chart
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
