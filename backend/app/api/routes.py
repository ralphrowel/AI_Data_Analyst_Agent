import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from backend.app.paths import inside
from backend.app.config import MAX_UPLOAD_BYTES
from backend.app.api.schemas import (
    QuestionRequest,
    AnalysisResponse,
    CreateSessionRequest,
    SessionResponse,
    DatasetInfo,
    UploadDatasetRequest,
    UploadResponse,
    UpdateDatasetRequest,
    AddRowRequest,
    CreateWidgetRequest,
    PinWidgetRequest,
    RecentGraphInfo,
    UserQuotaResponse,
)
from backend.app.config import USE_LEGACY_AGENT, KNOWLEDGE_DIR
from backend.app.agent.coordinator import default_coordinator
from backend.app.agent.widget_engine import default_widget_engine
from backend.app.rag.retriever import get_user_retriever

from backend.app.tools.chart_tool import generate_chart, extract_chart_spec
from backend.app.llm.client import get_gemini_client, call_llm
from backend.app.legacy.query_planner import get_query_plan, get_summary
from backend.app.legacy.query_executor import execute_plan
from backend.app.memory.session_store import default_session_store
from backend.app.data_engine.dataset_manager import default_dataset_manager
from backend.app.auth.supabase_auth import get_current_user, get_optional_user, User
from backend.app.auth.quota_manager import default_quota_manager


router = APIRouter()

client = get_gemini_client()

# Cache suggestions per dataset name and user
_suggestions_cache: dict = {}

SUGGESTION_PROMPT = """You are a data analyst. Based on this dataset description, generate exactly 4 example questions a user might want to ask. They should be diverse, practical, and demonstrate different analysis types (counting, top N, aggregation, filtering). Return ONLY a JSON array of 4 strings, no explanation.

Dataset:
{data_description}"""


@router.get("/")
def health_check():
    return {"status": "Visiq AI Data Analyst API is running", "architecture": "modular"}


# --- Auth & Quota Endpoints ---

@router.get("/api/auth/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Return profile and daily token quota information for authenticated user."""
    quota = default_quota_manager.get_user_quota(current_user.id)
    return {
        "user": current_user.model_dump(),
        "quota": quota,
    }


@router.get("/api/user/quota", response_model=UserQuotaResponse)
def get_user_quota(current_user: User = Depends(get_current_user)):
    """Retrieve daily token quota usage and remaining allowance for the current user."""
    return default_quota_manager.get_user_quota(current_user.id)


# --- Datasets Endpoints ---

@router.get("/api/datasets", response_model=List[DatasetInfo])
def list_datasets(current_user: User = Depends(get_current_user)):
    """List all available datasets (global + private user uploads)."""
    return default_dataset_manager.list_datasets(user_id=current_user.id)


@router.post("/api/upload", response_model=UploadResponse)
def upload_file(req: UploadDatasetRequest, current_user: User = Depends(get_current_user)):
    """Upload a CSV dataset privately scoped to the user or a knowledge document for RAG."""
    filename = req.filename
    if len(req.content.encode("utf-8")) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Upload exceeds size limit")
    lower_name = filename.lower()

    if lower_name.endswith(".csv"):
        # Parse before replacing an existing dataset, so bad input cannot destroy it.
        import io
        import pandas as pd
        try:
            pd.read_csv(io.StringIO(req.content))
        except (pd.errors.ParserError, pd.errors.EmptyDataError, ValueError):
            raise HTTPException(422, "Invalid CSV dataset")
        # Save privately in user-scoped upload folder
        target_dir = inside(default_dataset_manager.uploads_dir, current_user.id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = inside(default_dataset_manager.uploads_dir, current_user.id, filename)

        try:
            from backend.app.paths import atomic_text
            atomic_text(target_path, req.content)

            # Invalidate caches so newly uploaded dataset is available immediately
            default_dataset_manager.invalidate_cache(filename, user_id=current_user.id)

            df = default_dataset_manager.get_dataset(filename, user_id=current_user.id)
            default_dataset_manager.log_activity(
                filename,
                "upload",
                f"Uploaded {filename} ({len(df):,} rows, {len(df.columns)} cols)",
                {"rows": len(df), "columns": len(df.columns), "user_id": current_user.id},
            )
            return {
                "name": filename,
                "filename": filename,
                "rows": len(df),
                "columns": len(df.columns),
                "size_bytes": target_path.stat().st_size,
                "type": "dataset",
                "message": f"Dataset '{filename}' successfully saved ({len(df)} rows, {len(df.columns)} columns).",
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail="Request could not be processed")

    elif lower_name.endswith((".md", ".txt")):
        target_path = inside(KNOWLEDGE_DIR, current_user.id, filename)
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            from backend.app.paths import atomic_text
            atomic_text(target_path, req.content)
            from backend.app import storage
            storage.put('knowledge', current_user.id, filename,
                        {'name': filename, 'size_bytes': target_path.stat().st_size})

            # Auto-trigger RAG indexing upon upload
            get_user_retriever(current_user.id).refresh()

            return {
                "name": filename,
                "rows": 0,
                "columns": 0,
                "size_bytes": target_path.stat().st_size,
                "type": "knowledge",
                "message": f"Knowledge document '{filename}' successfully indexed for RAG.",
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail="Request could not be processed")

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload CSV datasets (.csv) or knowledge documents (.md, .txt).",
        )


@router.get("/api/datasets/{name}/rows")
def get_dataset_rows(
    name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated rows, search filtering, and column metadata for a dataset."""
    try:
        data = default_dataset_manager.get_rows_paginated(
            name=name,
            page=page,
            page_size=page_size,
            search=search or "",
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=current_user.id,
        )
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Request could not be processed")


@router.post("/api/datasets/{name}/update")
def update_dataset_cells(name: str, req: UpdateDatasetRequest, current_user: User = Depends(get_current_user)):
    """Update cell values in the dataset and sync with disk and LLM descriptions."""
    try:
        raw_updates = [u.model_dump() if hasattr(u, "model_dump") else u.dict() for u in req.updates]
        result = default_dataset_manager.update_cells(name, raw_updates, user_id=current_user.id)
        cache_key = f"{current_user.id}:{name}"
        if cache_key in _suggestions_cache:
            del _suggestions_cache[cache_key]
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Request could not be processed")


@router.post("/api/datasets/{name}/rows/add")
def add_dataset_row(name: str, req: AddRowRequest, current_user: User = Depends(get_current_user)):
    """Append a new row to the dataset."""
    try:
        result = default_dataset_manager.add_row(name, req.row_data, user_id=current_user.id)
        cache_key = f"{current_user.id}:{name}"
        if cache_key in _suggestions_cache:
            del _suggestions_cache[cache_key]
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Request could not be processed")


@router.delete("/api/datasets/{name}/rows/{row_index}")
def delete_dataset_row(name: str, row_index: int, current_user: User = Depends(get_current_user)):
    """Delete a row by index from the dataset."""
    try:
        result = default_dataset_manager.delete_row(name, row_index, user_id=current_user.id)
        cache_key = f"{current_user.id}:{name}"
        if cache_key in _suggestions_cache:
            del _suggestions_cache[cache_key]
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Request could not be processed")


# --- Sessions Endpoints ---

@router.get("/api/sessions", response_model=List[SessionResponse])
def list_sessions(current_user: User = Depends(get_current_user)):
    """List all active chat sessions belonging to the authenticated user."""
    return default_session_store.list_sessions(user_id=current_user.id)


@router.post("/api/sessions", response_model=SessionResponse)
def create_session(request: CreateSessionRequest, current_user: User = Depends(get_current_user)):
    """Create a new chat session scoped to the authenticated user."""
    try:
        default_dataset_manager._resolve_path(request.dataset_name, current_user.id)
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "Dataset not found")
    session = default_session_store.create_session(
        dataset_name=request.dataset_name,
        title=request.title,
        user_id=current_user.id,
    )
    return session.to_dict()


@router.get("/api/sessions/{session_id}")
def get_session(session_id: str, current_user: User = Depends(get_current_user)):
    """Get full details and history for a specific session."""
    session = default_session_store.get_session(session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")
    data = session.to_dict()
    data["history"] = session.history
    return data


@router.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, current_user: User = Depends(get_current_user)):
    """Delete a chat session owned by the authenticated user."""
    success = default_session_store.delete_session(session_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")
    return {"deleted": True, "session_id": session_id}


# --- Dashboard Widgets Endpoints ---

@router.get("/api/sessions/{session_id}/widgets")
def list_session_widgets(session_id: str, current_user: User = Depends(get_current_user)):
    """Retrieve all dashboard widgets for a session."""
    session = default_session_store.get_session(session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")
    return default_session_store.get_widgets(session_id)


@router.post("/api/sessions/{session_id}/widgets")
def create_session_widget(session_id: str, req: CreateWidgetRequest, current_user: User = Depends(get_current_user)):
    """Compile a user prompt into a live widget and attach it to the session dashboard."""
    session = default_session_store.get_session(session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")

    try:
        widget = default_widget_engine.create_widget_from_prompt(
            session=session,
            prompt=req.prompt,
            chart_type=req.chart_type,
            chart_theme=req.chart_theme,
            provider=req.provider,
        )
        return widget
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Request could not be processed")


@router.post("/api/sessions/{session_id}/widgets/pin")
def pin_session_widget(session_id: str, req: PinWidgetRequest, current_user: User = Depends(get_current_user)):
    """Pin an existing visual insight from conversation to the dashboard."""
    session = default_session_store.get_session(session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")

    try:
        widget = default_widget_engine.create_widget_from_chat(
            session=session,
            title=req.title,
            prompt=req.prompt,
            chart_base64=req.chart_base64,
            chart_svg=req.chart_svg,
            chart_spec=req.chart_spec,
            operation=req.operation,
            chart_type=req.chart_type,
        )
        return widget
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Request could not be processed")


@router.post("/api/sessions/{session_id}/widgets/recompute")
def recompute_session_widgets(session_id: str, chart_theme: str = "light", current_user: User = Depends(get_current_user)):
    """Recompute all widgets against updated session.df with ZERO AI calls."""
    session = default_session_store.get_session(session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")

    try:
        updated = default_widget_engine.recompute_widgets(session, chart_theme=chart_theme)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Request could not be processed")


@router.delete("/api/sessions/{session_id}/widgets/{widget_id}")
def delete_session_widget(session_id: str, widget_id: str, current_user: User = Depends(get_current_user)):
    """Delete a dashboard widget."""
    session = default_session_store.get_session(session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")
    success = default_session_store.delete_widget(session_id, widget_id)
    if not success:
        raise HTTPException(status_code=404, detail="Widget not found")
    return {"deleted": True, "widget_id": widget_id}


@router.get("/api/recent-graphs", response_model=List[RecentGraphInfo])
def get_recent_graphs(limit: int = Query(8, ge=1, le=100), current_user: User = Depends(get_current_user)):
    """Retrieve recent graphs created in the user's workspaces."""
    graphs = []
    seen_charts = set()

    user_sessions = [default_session_store.get_session(s["session_id"], current_user.id) for s in default_session_store.list_sessions(current_user.id)]

    for session in reversed(user_sessions):
        # Check pinned widgets
        for w in reversed(session.widgets):
            c_svg = w.get("chart_svg")
            c_b64 = w.get("chart_base64")
            key = (session.session_id, (c_svg or c_b64 or "")[:40])
            if (c_svg or c_b64) and key not in seen_charts:
                seen_charts.add(key)
                graphs.append({
                    "session_id": session.session_id,
                    "session_title": session.title,
                    "dataset_name": session.dataset_name,
                    "prompt": w.get("title") or w.get("prompt") or "Pinned Insight",
                    "chart_base64": c_b64,
                    "chart_svg": c_svg,
                    "chart_type": w.get("chart_type") or w.get("operation") or "chart",
                    "created_at": w.get("created_at") or session.created_at,
                })
                if len(graphs) >= limit:
                    return graphs

        # Check session turns
        history = session.history
        for i, turn in enumerate(history):
            meta = turn.get("metadata") or {}
            c_svg = meta.get("chart_svg")
            c_b64 = meta.get("chart_base64")
            if c_svg or c_b64:
                key = (session.session_id, (c_svg or c_b64 or "")[:40])
                if key not in seen_charts:
                    seen_charts.add(key)
                    prompt = "Visual Insight"
                    if i > 0 and history[i - 1].get("role") == "user":
                        prompt = history[i - 1].get("content", "")
                    graphs.append({
                        "session_id": session.session_id,
                        "session_title": session.title,
                        "dataset_name": session.dataset_name,
                        "prompt": prompt[:70],
                        "chart_base64": c_b64,
                        "chart_svg": c_svg,
                        "chart_type": meta.get("operation", "chart"),
                        "created_at": session.created_at,
                    })
                    if len(graphs) >= limit:
                        return graphs

    return graphs


@router.get("/api/dataset-changes")
def get_dataset_changes(current_user: User = Depends(get_current_user)):
    """Retrieve recent dataset changes, modifications, and uploads."""
    return default_dataset_manager.get_activity_log(current_user.id)


# --- Analytics & Question Answering ---

@router.get("/api/suggestions")
def get_suggestions(
    provider: Optional[str] = None,
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    session = default_session_store.get_session(session_id, user_id=current_user.id)
    dataset_name = session.dataset_name if session else "netflix_titles.csv"
    cache_key = f"{current_user.id}:{dataset_name}"

    if cache_key in _suggestions_cache:
        return _suggestions_cache[cache_key]

    try:
        desc = session.data_description if session else default_dataset_manager.get_dataset_description(dataset_name, user_id=current_user.id)
        prompt = SUGGESTION_PROMPT.format(data_description=desc)
        resp, provider_used = call_llm(prompt, client, provider=provider)
        raw = resp.text.strip() if provider_used == "gemini" else resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").lstrip("json").strip()
        parsed = json.loads(raw)
        if isinstance(parsed, list) and len(parsed) > 0:
            _suggestions_cache[cache_key] = parsed
            return _suggestions_cache[cache_key]
    except Exception:
        pass

    fallback = [
        "How many Movies vs TV Shows are there?",
        "What are the top 5 countries by number of titles?",
        "How many titles were released each year from 2015 to 2020?",
        "Which genres are the most common in the dataset?",
    ]
    return fallback


@router.post("/api/ask", response_model=AnalysisResponse)
def ask(request: QuestionRequest, current_user: User = Depends(get_current_user)):
    # 1. QUOTA GUARD: Check if user has exceeded their daily token limit
    default_quota_manager.check_quota(current_user.id)

    # 2. SESSION OWNERSHIP: Verify session belongs to current user
    if request.session_id:
        session = default_session_store.get_session(request.session_id, user_id=current_user.id)
        if not session:
            raise HTTPException(status_code=404, detail="Workspace session not found or belongs to another user")
    else:
        session = default_session_store.ensure_default_session(user_id=current_user.id)
        request.session_id = session.session_id

    # Safety feature flag: fallback to legacy agent if explicitly enabled in .env
    if USE_LEGACY_AGENT:
        df = session.df
        data_description = session.data_description

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
            # Record minimal token usage consumed by planning
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
        chart_svg = None
        chart_spec = None
        if exec_result.get("operation") != "unsupported":
            try:
                chart_base64, chart_svg = generate_chart(
                    exec_result,
                    chart_type=request.chart_type,
                    chart_theme=request.chart_theme,
                )
                chart_spec = extract_chart_spec(
                    exec_result,
                    chart_type=request.chart_type,
                )
            except HTTPException:
                raise
            except Exception as e:
                print(f"Chart generation error: {e}")

        # Atomically record token consumption against user's daily quota

        return AnalysisResponse(
            summary=summary,
            chart_base64=chart_base64,
            chart_svg=chart_svg,
            chart_spec=chart_spec,
            operation=plan.get("operation", "unknown"),
            unsupported_reason=None,
            usage=combined_usage,
            model_used=model_used,
        )

    # Modern Agent Coordinator pipeline (Step 7)
    res = default_coordinator.process_query(
        session_id=request.session_id,
        question=request.question,
        provider=request.provider,
        chart_type=request.chart_type,
        chart_theme=request.chart_theme,
        user_id=current_user.id,
    )

    # Atomically record tokens consumed against user's daily quota
    consumed_tokens = res.get("usage", {}).get("total_tokens", 0)

    return AnalysisResponse(
        summary=res.get("summary", ""),
        chart_base64=res.get("chart_base64"),
        chart_svg=res.get("chart_svg"),
        chart_spec=res.get("chart_spec"),
        operation=res.get("operation", "unknown"),
        unsupported_reason=res.get("unsupported_reason"),
        usage=res.get("usage", {}),
        model_used=res.get("model_used", "gemini"),
    )
