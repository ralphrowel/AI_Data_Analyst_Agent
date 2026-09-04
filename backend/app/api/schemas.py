from typing import Optional, Dict, Any
from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
    chart_type: Optional[str] = None
    chart_theme: str = "light"
    session_id: Optional[str] = None


class AnalysisResponse(BaseModel):
    summary: str
    chart_base64: Optional[str] = None
    operation: str
    unsupported_reason: Optional[str] = None
    usage: Dict[str, Any]
    model_used: str = "gemini"
