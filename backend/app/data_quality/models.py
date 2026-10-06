"""Domain models and data structures for Data Quality & Profiling."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ColumnProfile:
    """Statistical and semantic profile of a single dataset column."""

    name: str
    dtype: str
    semantic_type: str  # numeric, text, datetime, boolean, other
    total_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    numeric_stats: Optional[Dict[str, float]] = None
    text_stats: Optional[Dict[str, Any]] = None
    datetime_stats: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DatasetSummary:
    """Dataset-level shape, duplicate, and null overview."""

    total_rows: int
    total_columns: int
    total_cells: int
    total_missing_cells: int
    missing_percentage: float
    duplicate_rows: int
    duplicate_percentage: float
    memory_bytes: int
    column_types_breakdown: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProfileResult:
    """Full dataset profile result with summary and column breakdown."""

    summary: DatasetSummary
    columns: Dict[str, ColumnProfile]
    missing_rankings: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "columns": {col: prof.to_dict() for col, prof in self.columns.items()},
            "missing_rankings": self.missing_rankings,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)
