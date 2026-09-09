from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal
from backend.app.paths import filename as validate_filename
from backend.app.config import MAX_UPLOAD_BYTES

class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    @field_validator('question', 'prompt', check_fields=False)
    @classmethod
    def nonempty_text(cls, value):
        if value is not None and not value.strip():
            raise ValueError('Text must not be blank')
        return value


class QuestionRequest(RequestModel):
    question: str = Field(min_length=1, max_length=12000)
    chart_type: Optional[str] = None
    chart_theme: Literal["light", "dark"] = "light"
    session_id: Optional[str] = None
    provider: Optional[Literal["groq", "gemini"]] = None


class AnalysisResponse(BaseModel):
    summary: str
    chart_base64: Optional[str] = None
    chart_svg: Optional[str] = None
    chart_spec: Optional[Dict[str, Any]] = None
    operation: str
    unsupported_reason: Optional[str] = None
    usage: Dict[str, Any]
    model_used: str = "gemini"


class CreateSessionRequest(RequestModel):
    dataset_name: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)


    @field_validator("dataset_name")
    @classmethod
    def safe_dataset(cls, value):
        return validate_filename(value) if value is not None else value


class SessionResponse(BaseModel):
    session_id: str
    title: str
    dataset_name: str
    user_id: Optional[str] = None
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
    is_private: bool = False


class UserQuotaResponse(BaseModel):
    user_id: str
    date: str
    tokens_used: int
    daily_limit: int
    tokens_remaining: int
    percentage_used: float
    reset_time: str = "Midnight UTC"


class RecentGraphInfo(BaseModel):
    session_id: str
    session_title: str
    dataset_name: str
    prompt: str = Field(min_length=1, max_length=12000)
    chart_base64: Optional[str] = None
    chart_svg: Optional[str] = None
    chart_type: Optional[str] = None
    created_at: Optional[str] = None


class UploadDatasetRequest(RequestModel):
    filename: str
    content: str = Field(min_length=1, max_length=MAX_UPLOAD_BYTES)


    @field_validator("filename")
    @classmethod
    def safe_filename(cls, value):
        return validate_filename(value)


class UploadResponse(BaseModel):
    name: str
    filename: Optional[str] = None
    rows: int = 0
    columns: int = 0
    size_bytes: int = 0
    type: str = "dataset"  # "dataset" | "knowledge"
    message: Optional[str] = None


class CellUpdate(RequestModel):
    row_index: int = Field(ge=0)
    column: str
    value: Any


class UpdateDatasetRequest(RequestModel):
    updates: List[CellUpdate] = Field(min_length=1, max_length=1000)


class AddRowRequest(RequestModel):
    row_data: Dict[str, Any]


class CreateWidgetRequest(RequestModel):
    prompt: str = Field(min_length=1, max_length=12000)
    chart_type: Optional[str] = None
    chart_theme: Literal["light", "dark"] = "light"
    provider: Optional[Literal["groq", "gemini"]] = None


class PinWidgetRequest(RequestModel):
    title: Optional[str] = None
    prompt: Optional[str] = None
    chart_base64: Optional[str] = None
    chart_svg: Optional[str] = None
    chart_spec: Optional[Dict[str, Any]] = None
    operation: Optional[str] = None
    chart_type: Optional[str] = None



