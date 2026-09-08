from typing import Optional, Dict, Any, List
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
    chart_svg: Optional[str] = None
    chart_spec: Optional[Dict[str, Any]] = None
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
    widget_count: int = 0
    token_usage: Dict[str, int]
    last_message: Optional[str] = None


class DatasetInfo(BaseModel):
    name: str
    rows: int
    columns: int
    size_bytes: int
    modified_at: Optional[str] = None


class RecentGraphInfo(BaseModel):
    session_id: str
    session_title: str
    dataset_name: str
    prompt: str
    chart_base64: Optional[str] = None
    chart_svg: Optional[str] = None
    chart_type: Optional[str] = None
    created_at: Optional[str] = None


class UploadDatasetRequest(BaseModel):
    filename: str
    content: str


class UploadResponse(BaseModel):
    name: str
    filename: Optional[str] = None
    rows: int = 0
    columns: int = 0
    size_bytes: int = 0
    type: str = "dataset"  # "dataset" | "knowledge"
    message: Optional[str] = None


class CellUpdate(BaseModel):
    row_index: int
    column: str
    value: Any


class UpdateDatasetRequest(BaseModel):
    updates: List[CellUpdate]


class AddRowRequest(BaseModel):
    row_data: Dict[str, Any]


class CreateWidgetRequest(BaseModel):
    prompt: str
    chart_type: Optional[str] = None
    chart_theme: str = "light"
    provider: Optional[str] = None


class PinWidgetRequest(BaseModel):
    title: Optional[str] = None
    prompt: Optional[str] = None
    chart_base64: Optional[str] = None
    chart_svg: Optional[str] = None
    chart_spec: Optional[Dict[str, Any]] = None
    operation: Optional[str] = None
    chart_type: Optional[str] = None



