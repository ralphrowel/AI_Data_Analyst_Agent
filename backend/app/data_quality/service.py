"""Data Quality Service: orchestrates profiling, assessment, cleaning, and lineage for Visiq."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import pandas as pd

from backend.app.data_engine.dataset_manager import default_dataset_manager
from backend.app.data_quality.checks import DataQualityEngine
from backend.app.data_quality.cleaner import DataCleaningEngine, to_safe_csv_text
from backend.app.data_quality.models import (
    CleaningJob,
    CleaningResult,
    DatasetLineage,
    IssueCategory,
    ProfileResult,
    QualityAssessmentResult,
    QualityReport,
    current_utc_iso,
    generate_uuid,
)
from backend.app.data_quality.plan import generate_suggested_plan
from backend.app.data_quality.profiler import DataProfiler
from backend.app.data_quality.scorer import DataQualityScorer
from backend.app.file_storage import file_store
from backend.app.storage import get as storage_get, put as storage_put

logger = logging.getLogger(__name__)


class DataQualityService:
    """Service layer connecting Visiq storage and data engines to data quality capabilities."""

    def __init__(
        self,
        profiler: Optional[DataProfiler] = None,
        quality_engine: Optional[DataQualityEngine] = None,
        scorer: Optional[DataQualityScorer] = None,
        cleaner: Optional[DataCleaningEngine] = None,
    ):
        self.profiler = profiler or DataProfiler()
        self.quality_engine = quality_engine or DataQualityEngine()
        self.scorer = scorer or DataQualityScorer(quality_engine=self.quality_engine)
        self.cleaner = cleaner or DataCleaningEngine()

    def _resolve_and_read_csv(
        self, dataset_name: str, user_id: Optional[str] = None
    ) -> tuple[Path, pd.DataFrame, str]:
        """Resolves file path, reads raw CSV data, and computes content SHA-256 fingerprint."""
        file_path = default_dataset_manager._resolve_path(dataset_name, user_id=user_id)
        if not file_path or not file_path.exists():
            raise FileNotFoundError(f"Dataset '{dataset_name}' not found.")

        try:
            with open(file_path, "rb") as f:
                content_bytes = f.read()
            fingerprint = hashlib.sha256(content_bytes).hexdigest()
        except Exception as e:
            logger.error("Failed to read file bytes for '%s': %s", dataset_name, e)
            raise ValueError(f"Could not read dataset '{dataset_name}': {e}") from e

        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame()
        except Exception as e:
            logger.error("Failed to parse CSV for '%s': %s", dataset_name, e)
            raise ValueError(f"Could not parse dataset '{dataset_name}': {e}") from e

        return file_path, df, fingerprint

    def profile_dataset(self, dataset_name: str, user_id: Optional[str] = None) -> ProfileResult:
        """Loads a raw CSV dataset and computes its statistical and semantic profile."""
        _, df, _ = self._resolve_and_read_csv(dataset_name, user_id=user_id)
        return self.profiler.profile(df)

    def assess_dataset(
        self,
        dataset_name: str,
        user_id: Optional[str] = None,
        force_refresh: bool = False,
        id_columns: Optional[List[str]] = None,
        range_rules: Optional[Dict[str, Dict[str, float]]] = None,
        format_rules: Optional[Dict[str, str]] = None,
        category_rules: Optional[Dict[str, List[str]]] = None,
    ) -> QualityAssessmentResult:
        """Evaluates quality and scores dataset, utilizing SHA-256 fingerprint caching in app_records."""
        file_path, df, fingerprint = self._resolve_and_read_csv(dataset_name, user_id=user_id)
        owner = user_id or "system"

        # Check fingerprint cache
        if not force_refresh:
            try:
                cached = storage_get("dq_reports", owner, dataset_name)
                if cached and isinstance(cached, dict):
                    if cached.get("source_fingerprint") == fingerprint:
                        logger.info(
                            "Serving cached quality assessment for '%s' (owner: %s, hash: %s)",
                            dataset_name,
                            owner,
                            fingerprint[:8],
                        )
                        return QualityAssessmentResult.from_dict(cached)
            except Exception as e:
                logger.warning("Cache lookup error for '%s': %s", dataset_name, e)

        # Run fresh analysis
        report = self.quality_engine.analyze(
            df,
            id_columns=id_columns,
            range_rules=range_rules,
            format_rules=format_rules,
            category_rules=category_rules,
        )

        score_result = self.scorer.score(
            df,
            id_columns=id_columns,
            range_rules=range_rules,
            format_rules=format_rules,
            category_rules=category_rules,
            existing_report=report,
        )

        # Generate deterministic suggested cleaning plan
        suggested_plan = generate_suggested_plan(report, df)

        # Compute summary metrics
        total_cells = df.size
        missing_count = sum(
            i.affected_count for i in report.issues if i.category == IssueCategory.MISSING
        )
        missing_pct = round((missing_count / max(1, total_cells)) * 100, 2) if total_cells > 0 else 0.0

        summary: Dict[str, Any] = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_cells": total_cells,
            "missing_cells": missing_count,
            "missing_percentage": missing_pct,
            "duplicate_rows": int(df.duplicated().sum()) if len(df) > 0 else 0,
            "invalid_dates": sum(
                i.affected_count
                for i in report.issues
                if i.category == IssueCategory.INVALID_FORMAT
                and ("date" in i.description.lower() or "iso_date" in i.description.lower())
            ),
            "invalid_types": report.issues_by_category.get(IssueCategory.INVALID_TYPE.value, 0),
            "outliers": report.issues_by_category.get(IssueCategory.OUTLIER.value, 0),
            "overall_score": score_result.overall_score,
            "grade": score_result.grade,
            "grade_label": score_result.grade_label,
            "is_trustworthy": score_result.is_trustworthy,
        }

        assessment = QualityAssessmentResult(
            dataset_name=dataset_name,
            source_fingerprint=fingerprint,
            engine_version="1.0.0",
            generated_at=current_utc_iso(),
            summary=summary,
            dimensions={k: v.to_dict() for k, v in score_result.dimensions.items()},
            issues=report.issues,
            score=score_result,
            suggested_plan=suggested_plan,
        )

        # Cache in storage
        try:
            storage_put("dq_reports", owner, dataset_name, assessment.to_dict())
            logger.info("Cached quality report for '%s' (owner: %s)", dataset_name, owner)
        except Exception as e:
            logger.warning("Failed to store quality report cache for '%s': %s", dataset_name, e)

        return assessment

    def preview_cleaning(
        self,
        dataset_name: str,
        plan: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dry-runs a cleaning plan without saving any files or mutating dataset state."""
        _, raw_df, fingerprint = self._resolve_and_read_csv(dataset_name, user_id=user_id)

        # Execute cleaning statelessly in-memory
        cleaning_result = self.cleaner.clean(raw_df, **plan)

        # Score before and after
        comparison = self.scorer.compare(raw_df, cleaning_result.cleaned_df)

        return {
            "dataset_name": dataset_name,
            "source_fingerprint": fingerprint,
            "audit": cleaning_result.audit.to_dict(),
            "before_stats": cleaning_result.before_stats,
            "after_stats": cleaning_result.after_stats,
            "delta": cleaning_result.delta,
            "score_comparison": comparison.to_dict(),
            "steps": [s.to_dict() for s in cleaning_result.steps],
        }

    def apply_cleaning(
        self,
        dataset_name: str,
        plan: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> CleaningJob:
        """Executes a cleaning plan, saves derived clean dataset, and records audit & lineage."""
        _, raw_df, source_fingerprint = self._resolve_and_read_csv(dataset_name, user_id=user_id)
        owner = user_id or "system"

        # Execute cleaning pipeline
        cleaning_result = self.cleaner.clean(raw_df, **plan)

        # Score before and after
        score_before = self.scorer.score(raw_df)
        score_after = self.scorer.score(cleaning_result.cleaned_df)
        score_delta = round(score_after.overall_score - score_before.overall_score, 2)

        # Generate target filename preserving original
        base_stem = re.sub(r"__clean_v\d+$", "", Path(dataset_name).stem)
        ext = Path(dataset_name).suffix or ".csv"

        # Lookup lineage to determine next version number
        parent_lineage_data = None
        try:
            parent_lineage_data = storage_get("dataset_lineage", owner, f"{base_stem}{ext}")
        except Exception:
            pass

        if parent_lineage_data and isinstance(parent_lineage_data, dict):
            parent_lineage = DatasetLineage.from_dict(parent_lineage_data)
            next_version = len(parent_lineage.versions) + 1
        else:
            parent_lineage = DatasetLineage(
                dataset_name=f"{base_stem}{ext}",
                role="original",
                version=0,
                job_ids=[],
                versions=[],
            )
            next_version = 1

        target_dataset = f"{base_stem}__clean_v{next_version}{ext}"

        # Convert cleaned DataFrame to safe CSV string
        clean_csv_text = to_safe_csv_text(cleaning_result.cleaned_df)

        # Persist derived clean CSV via file_store
        file_store.save(owner, target_dataset, clean_csv_text, kind="csv")

        # Build Job record
        job_id = generate_uuid()
        job = CleaningJob(
            job_id=job_id,
            source_dataset=dataset_name,
            source_fingerprint=source_fingerprint,
            target_dataset=target_dataset,
            user_id=user_id,
            plan=plan,
            steps=cleaning_result.steps,
            audit=cleaning_result.audit,
            score_before=score_before,
            score_after=score_after,
            score_delta=score_delta,
            created_at=current_utc_iso(),
        )

        # Update parent lineage
        version_entry = {
            "version": next_version,
            "dataset_name": target_dataset,
            "job_id": job_id,
            "score_before": score_before.overall_score,
            "score_after": score_after.overall_score,
            "created_at": job.created_at,
        }
        parent_lineage.job_ids.append(job_id)
        parent_lineage.versions.append(version_entry)

        # Create child lineage
        child_lineage = DatasetLineage(
            dataset_name=target_dataset,
            role="cleaned",
            parent_dataset=dataset_name,
            version=next_version,
            job_ids=[job_id],
            versions=[version_entry],
            created_at=job.created_at,
        )

        # Save job and lineage records in storage
        try:
            storage_put("dq_jobs", owner, job_id, job.to_dict())
            storage_put("dataset_lineage", owner, f"{base_stem}{ext}", parent_lineage.to_dict())
            storage_put("dataset_lineage", owner, target_dataset, child_lineage.to_dict())
        except Exception as e:
            logger.warning("Failed to persist DQ job or lineage records: %s", e)

        # Register dataset in DatasetManager activity and dataset catalog
        if user_id:
            try:
                default_dataset_manager.log_activity(
                    target_dataset,
                    action="create_clean_dataset",
                    description=f"Derived cleaned dataset '{target_dataset}' from '{dataset_name}'",
                    details={"job_id": job_id, "score_delta": score_delta},
                    user_id=user_id,
                )
            except Exception as e:
                logger.warning("Failed to log activity for clean dataset: %s", e)

        return job

    def get_dataset_lineage(
        self, dataset_name: str, user_id: Optional[str] = None
    ) -> DatasetLineage:
        """Retrieves derivation lineage and version history for a dataset."""
        owner = user_id or "system"
        try:
            record = storage_get("dataset_lineage", owner, dataset_name)
            if record and isinstance(record, dict):
                return DatasetLineage.from_dict(record)
        except Exception as e:
            logger.warning("Failed to load lineage for '%s': %s", dataset_name, e)

        # Check if dataset has base original counterpart
        base_stem = re.sub(r"__clean_v\d+$", "", Path(dataset_name).stem)
        ext = Path(dataset_name).suffix or ".csv"
        original_name = f"{base_stem}{ext}"
        if original_name != dataset_name:
            try:
                record = storage_get("dataset_lineage", owner, original_name)
                if record and isinstance(record, dict):
                    return DatasetLineage.from_dict(record)
            except Exception:
                pass

        return DatasetLineage(
            dataset_name=dataset_name,
            role="original",
            parent_dataset=None,
            version=1,
            job_ids=[],
            versions=[],
            created_at=current_utc_iso(),
        )


# Global singleton instance
default_dq_service = DataQualityService()
