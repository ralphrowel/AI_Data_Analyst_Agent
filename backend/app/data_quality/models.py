"""Domain models and data structures for Data Quality, Profiling, and Scoring."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class IssueCategory(str, Enum):
    MISSING = "MISSING"
    DUPLICATE = "DUPLICATE"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_RANGE = "INVALID_RANGE"
    INCONSISTENT_CATEGORY = "INCONSISTENT_CATEGORY"
    INVALID_TYPE = "INVALID_TYPE"
    OUTLIER = "OUTLIER"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


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


@dataclass
class QualityIssue:
    """Represents a discrete data quality defect, formatting violation, or anomaly."""

    category: IssueCategory
    severity: Severity
    column: Optional[str]
    description: str
    affected_count: int
    affected_percentage: float
    id: str = field(default_factory=generate_uuid)
    sample_values: List[Any] = field(default_factory=list)
    suggested_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["category"] = self.category.value if isinstance(self.category, IssueCategory) else str(self.category)
        data["severity"] = self.severity.value if isinstance(self.severity, Severity) else str(self.severity)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QualityIssue:
        return cls(
            id=data.get("id", generate_uuid()),
            category=IssueCategory(data["category"]),
            severity=Severity(data["severity"]),
            column=data.get("column"),
            description=data["description"],
            affected_count=data["affected_count"],
            affected_percentage=data["affected_percentage"],
            sample_values=data.get("sample_values", []),
            suggested_action=data.get("suggested_action"),
        )


@dataclass
class QualityReport:
    """Aggregated report of all data quality issues detected in a dataset."""

    total_rows: int
    total_columns: int
    total_issues_count: int
    issues_by_category: Dict[str, int]
    issues_by_severity: Dict[str, int]
    issues: List[QualityIssue]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "total_issues_count": self.total_issues_count,
            "issues_by_category": self.issues_by_category,
            "issues_by_severity": self.issues_by_severity,
            "issues": [issue.to_dict() for issue in self.issues],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QualityReport:
        return cls(
            total_rows=data["total_rows"],
            total_columns=data["total_columns"],
            total_issues_count=data["total_issues_count"],
            issues_by_category=data.get("issues_by_category", {}),
            issues_by_severity=data.get("issues_by_severity", {}),
            issues=[QualityIssue.from_dict(i) for i in data.get("issues", [])],
        )


@dataclass
class ScoreWeights:
    """Weight distribution for the 4 core data quality dimensions (must sum to 1.0)."""

    completeness: float = 0.30
    validity: float = 0.30
    uniqueness: float = 0.20
    consistency: float = 0.20

    def __post_init__(self):
        total = round(self.completeness + self.validity + self.uniqueness + self.consistency, 4)
        if total != 1.0:
            raise ValueError(f"Score weights must sum to 1.0 (got {total})")

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ScoreWeights:
        return cls(
            completeness=float(data.get("completeness", 0.30)),
            validity=float(data.get("validity", 0.30)),
            uniqueness=float(data.get("uniqueness", 0.20)),
            consistency=float(data.get("consistency", 0.20)),
        )


@dataclass
class DimensionScore:
    """Score and diagnostic metrics for an individual quality dimension."""

    name: str
    score: float  # 0.0 to 100.0
    weight: float
    weighted_score: float
    passed_items: int
    total_evaluated: int
    defects_count: int
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "weighted_score": self.weighted_score,
            "passed_items": self.passed_items,
            "total_evaluated": self.total_evaluated,
            "defects_count": self.defects_count,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DimensionScore:
        return cls(
            name=data["name"],
            score=data["score"],
            weight=data["weight"],
            weighted_score=data["weighted_score"],
            passed_items=data["passed_items"],
            total_evaluated=data["total_evaluated"],
            defects_count=data["defects_count"],
            details=data["details"],
        )


@dataclass
class QualityScoreResult:
    """Composite quality score, dimensional breakdown, grade, and evaluation metadata."""

    overall_score: float  # 0.0 to 100.0
    grade: str  # A, B, C, D, F
    grade_label: str
    is_trustworthy: bool
    dimensions: Dict[str, DimensionScore]
    weights: ScoreWeights

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "grade": self.grade,
            "grade_label": self.grade_label,
            "is_trustworthy": self.is_trustworthy,
            "dimensions": {k: v.to_dict() for k, v in self.dimensions.items()},
            "weights": self.weights.to_dict(),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QualityScoreResult:
        return cls(
            overall_score=data["overall_score"],
            grade=data["grade"],
            grade_label=data["grade_label"],
            is_trustworthy=data["is_trustworthy"],
            dimensions={k: DimensionScore.from_dict(v) for k, v in data.get("dimensions", {}).items()},
            weights=ScoreWeights.from_dict(data.get("weights", {})),
        )


@dataclass
class ScoreComparison:
    """Quantifies before/after cleaning improvements in quality scores."""

    before: QualityScoreResult
    after: QualityScoreResult
    score_delta: float
    grade_improved: bool
    dimension_deltas: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_score": self.before.overall_score,
            "after_score": self.after.overall_score,
            "score_delta": self.score_delta,
            "before_grade": self.before.grade,
            "after_grade": self.after.grade,
            "grade_improved": self.grade_improved,
            "dimension_deltas": self.dimension_deltas,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


@dataclass
class QualityAssessmentResult:
    """Complete dataset quality evaluation including issues, scores, and metadata."""

    dataset_name: str
    source_fingerprint: str
    engine_version: str
    generated_at: str
    summary: Dict[str, Any]
    dimensions: Dict[str, Any]
    issues: List[QualityIssue]
    score: QualityScoreResult
    suggested_plan: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "source_fingerprint": self.source_fingerprint,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "dimensions": self.dimensions,
            "issues": [issue.to_dict() for issue in self.issues],
            "score": self.score.to_dict(),
            "suggested_plan": self.suggested_plan,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QualityAssessmentResult:
        return cls(
            dataset_name=data["dataset_name"],
            source_fingerprint=data["source_fingerprint"],
            engine_version=data.get("engine_version", "1.0.0"),
            generated_at=data.get("generated_at", current_utc_iso()),
            summary=data.get("summary", {}),
            dimensions=data.get("dimensions", {}),
            issues=[QualityIssue.from_dict(i) for i in data.get("issues", [])],
            score=QualityScoreResult.from_dict(data["score"]),
            suggested_plan=data.get("suggested_plan"),
        )


@dataclass
class CleaningStep:
    """Record of a single atomic cleaning transformation."""

    step_number: int
    operation: str
    target_column: Optional[str]
    parameters: Dict[str, Any]
    rows_affected: int
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CleaningStep:
        return cls(
            step_number=data["step_number"],
            operation=data["operation"],
            target_column=data.get("target_column"),
            parameters=data.get("parameters", {}),
            rows_affected=data.get("rows_affected", 0),
            details=data.get("details", ""),
        )


@dataclass
class CleaningAuditSummary:
    """High-level explainable audit summary of a cleaning run."""

    original_rows: int
    duplicates_removed: int
    values_fixed: int
    values_imputed: int
    values_nullified: int
    final_rows: int
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CleaningAuditSummary:
        return cls(
            original_rows=data["original_rows"],
            duplicates_removed=data["duplicates_removed"],
            values_fixed=data["values_fixed"],
            values_imputed=data["values_imputed"],
            values_nullified=data["values_nullified"],
            final_rows=data["final_rows"],
            explanation=data.get("explanation", ""),
        )


@dataclass
class CleaningResult:
    """Encapsulates the cleaned DataFrame, audit log, and before/after metrics."""

    cleaned_df: Any  # pd.DataFrame
    steps: List[CleaningStep]
    audit: CleaningAuditSummary
    before_stats: Dict[str, Any]
    after_stats: Dict[str, Any]
    delta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_stats": self.before_stats,
            "after_stats": self.after_stats,
            "delta": self.delta,
            "audit": self.audit.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


@dataclass
class CleaningJob:
    """Persisted record of an applied cleaning execution between datasets."""

    job_id: str
    source_dataset: str
    source_fingerprint: str
    target_dataset: str
    plan: Dict[str, Any]
    steps: List[CleaningStep]
    audit: CleaningAuditSummary
    score_before: QualityScoreResult
    score_after: QualityScoreResult
    score_delta: float
    user_id: Optional[str] = None
    created_at: str = field(default_factory=current_utc_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_dataset": self.source_dataset,
            "source_fingerprint": self.source_fingerprint,
            "target_dataset": self.target_dataset,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "plan": self.plan,
            "audit": self.audit.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
            "score_before": self.score_before.to_dict(),
            "score_after": self.score_after.to_dict(),
            "score_delta": self.score_delta,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CleaningJob:
        return cls(
            job_id=data["job_id"],
            source_dataset=data["source_dataset"],
            source_fingerprint=data["source_fingerprint"],
            target_dataset=data["target_dataset"],
            user_id=data.get("user_id"),
            created_at=data.get("created_at", current_utc_iso()),
            plan=data.get("plan", {}),
            audit=CleaningAuditSummary.from_dict(data["audit"]),
            steps=[CleaningStep.from_dict(s) for s in data.get("steps", [])],
            score_before=QualityScoreResult.from_dict(data["score_before"]),
            score_after=QualityScoreResult.from_dict(data["score_after"]),
            score_delta=data.get("score_delta", 0.0),
        )


@dataclass
class DatasetLineage:
    """Dataset derivation lineage and version tracking."""

    dataset_name: str
    role: str  # "original" or "cleaned"
    parent_dataset: Optional[str] = None
    version: int = 1
    job_ids: List[str] = field(default_factory=list)
    versions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=current_utc_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DatasetLineage:
        return cls(
            dataset_name=data["dataset_name"],
            role=data.get("role", "original"),
            parent_dataset=data.get("parent_dataset"),
            version=data.get("version", 1),
            job_ids=data.get("job_ids", []),
            versions=data.get("versions", []),
            created_at=data.get("created_at", current_utc_iso()),
        )
