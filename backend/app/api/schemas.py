from typing import Optional, Dict, Any
from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
    chart_type: Optional[str] = None
    chart_theme: str = "light"
    session_id: Optional[str] = None
    provider: Optional[str] = None


class AnalysisResponse(BaseModel):
    summary: str
    chart_base64: Optional[str] = None
    operation: str
    unsupported_reason: Optional[str] = None
    usage: Dict[str, Any]
    model_used: str = "gemini"


class CreateSessionRequest(BaseModel):
    dataset_name: Optional[str] = None
    title: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    title: str
    dataset_name: str
    created_at: str
    message_count: int
    token_usage: Dict[str, int]


class DatasetInfo(BaseModel):
    name: str
    rows: int
    columns: int
    size_bytes: int


class UploadDatasetRequest(BaseModel):
    filename: str
    content: str
