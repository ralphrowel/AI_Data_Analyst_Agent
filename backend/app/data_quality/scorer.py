"""Data Quality Scoring Engine for Visiq.

Computes normalized multi-dimensional data quality scores:
- Completeness (missing data ratio)
- Validity (format, range, and type compliance ratio)
- Uniqueness (duplicate records and key collisions, without double-counting)
- Consistency (categorical standards and casing variations)

Calculates weighted composite quality scores, assigns letter grades,
and measures before/after quality improvements.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from backend.app.data_quality.checks import DataQualityEngine
from backend.app.data_quality.models import (
    DimensionScore,
    IssueCategory,
    QualityReport,
    QualityScoreResult,
    ScoreComparison,
    ScoreWeights,
)


class DataQualityScorer:
    """Calibrates and evaluates multi-dimensional data quality scores."""

    def __init__(
        self,
        weights: Optional[ScoreWeights] = None,
        quality_engine: Optional[DataQualityEngine] = None,
    ):
        self.weights = weights or ScoreWeights()
        self.quality_engine = quality_engine or DataQualityEngine()

    def score(
        self,
        df: pd.DataFrame,
        id_columns: Optional[List[str]] = None,
        range_rules: Optional[Dict[str, Dict[str, float]]] = None,
        format_rules: Optional[Dict[str, str]] = None,
        category_rules: Optional[Dict[str, List[str]]] = None,
        existing_report: Optional[QualityReport] = None,
    ) -> QualityScoreResult:
        """Evaluates a DataFrame and returns a comprehensive QualityScoreResult."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame")

        total_rows = len(df)
        total_cells = df.size

        if total_rows == 0 or total_cells == 0:
            return self._empty_score()

        report = existing_report or self.quality_engine.analyze(
            df,
            id_columns=id_columns,
            range_rules=range_rules,
            format_rules=format_rules,
            category_rules=category_rules,
        )

        # 1. Completeness Dimension
        missing_count = sum(
            issue.affected_count
            for issue in report.issues
            if issue.category == IssueCategory.MISSING
        )
        completeness_passed = max(0, total_cells - missing_count)
        completeness_score = round((completeness_passed / total_cells) * 100, 2)
        dim_completeness = DimensionScore(
            name="Completeness",
            score=completeness_score,
            weight=self.weights.completeness,
            weighted_score=round(completeness_score * self.weights.completeness, 2),
            passed_items=completeness_passed,
            total_evaluated=total_cells,
            defects_count=missing_count,
            details=f"{completeness_passed:,} of {total_cells:,} cells populated ({missing_count:,} missing).",
        )

        # 2. Validity Dimension (format, range, invalid type)
        validity_issues = [
            issue
            for issue in report.issues
            if issue.category
            in (
                IssueCategory.INVALID_FORMAT,
                IssueCategory.INVALID_RANGE,
                IssueCategory.INVALID_TYPE,
            )
        ]
        validity_defects = sum(issue.affected_count for issue in validity_issues)
        validity_score = max(
            0.0, round((1.0 - (validity_defects / max(1, total_cells))) * 100, 2)
        )
        dim_validity = DimensionScore(
            name="Validity",
            score=validity_score,
            weight=self.weights.validity,
            weighted_score=round(validity_score * self.weights.validity, 2),
            passed_items=max(0, total_cells - validity_defects),
            total_evaluated=total_cells,
            defects_count=validity_defects,
            details=f"{validity_defects:,} format, range, or type violations detected across dataset cells.",
        )

        # 3. Uniqueness Dimension (Fix D7: prevent double-counting exact vs key duplicates)
        resolved_id_cols = (
            id_columns
            if id_columns is not None
            else [
                col
                for col in df.columns
                if col.lower() in ("id", "pk", "uuid", "show_id")
                or col.lower().endswith(("_id", "_uuid"))
            ]
        )

        exact_dup_mask = df.duplicated()
        if resolved_id_cols:
            key_dup_mask = pd.Series(False, index=df.index)
            for k in resolved_id_cols:
                if k in df.columns:
                    key_dup_mask |= df.duplicated(subset=[k], keep=False)
            unique_defect_mask = exact_dup_mask | key_dup_mask
            duplicate_defects = int(unique_defect_mask.sum())
        else:
            duplicate_defects = int(exact_dup_mask.sum())

        duplicate_defects = min(total_rows, duplicate_defects)
        uniqueness_score = max(
            0.0, round((1.0 - (duplicate_defects / max(1, total_rows))) * 100, 2)
        )
        dim_uniqueness = DimensionScore(
            name="Uniqueness",
            score=uniqueness_score,
            weight=self.weights.uniqueness,
            weighted_score=round(uniqueness_score * self.weights.uniqueness, 2),
            passed_items=max(0, total_rows - duplicate_defects),
            total_evaluated=total_rows,
            defects_count=duplicate_defects,
            details=f"{duplicate_defects:,} unique records affected by duplication or key collisions in {total_rows:,} records.",
        )

        # 4. Consistency Dimension (casing variations, unknown categories)
        consistency_issues = [
            issue
            for issue in report.issues
            if issue.category == IssueCategory.INCONSISTENT_CATEGORY
        ]
        consistency_defects = sum(issue.affected_count for issue in consistency_issues)
        consistency_score = max(
            0.0, round((1.0 - (consistency_defects / max(1, total_cells))) * 100, 2)
        )
        dim_consistency = DimensionScore(
            name="Consistency",
            score=consistency_score,
            weight=self.weights.consistency,
            weighted_score=round(consistency_score * self.weights.consistency, 2),
            passed_items=max(0, total_cells - consistency_defects),
            total_evaluated=total_cells,
            defects_count=consistency_defects,
            details=f"{consistency_defects:,} inconsistent categorical values or casing variants detected.",
        )

        # Composite score
        overall_score = round(
            dim_completeness.weighted_score
            + dim_validity.weighted_score
            + dim_uniqueness.weighted_score
            + dim_consistency.weighted_score,
            2,
        )
        overall_score = min(100.0, max(0.0, overall_score))

        grade, grade_label, is_trustworthy = self._assign_grade(overall_score)

        return QualityScoreResult(
            overall_score=overall_score,
            grade=grade,
            grade_label=grade_label,
            is_trustworthy=is_trustworthy,
            dimensions={
                "completeness": dim_completeness,
                "validity": dim_validity,
                "uniqueness": dim_uniqueness,
                "consistency": dim_consistency,
            },
            weights=self.weights,
        )

    def compare(
        self,
        before_df: pd.DataFrame,
        after_df: pd.DataFrame,
        id_columns: Optional[List[str]] = None,
        range_rules: Optional[Dict[str, Dict[str, float]]] = None,
        format_rules: Optional[Dict[str, str]] = None,
        category_rules: Optional[Dict[str, List[str]]] = None,
    ) -> ScoreComparison:
        """Calculates quality scores before and after cleaning to measure improvement."""
        score_before = self.score(
            before_df,
            id_columns=id_columns,
            range_rules=range_rules,
            format_rules=format_rules,
            category_rules=category_rules,
        )
        score_after = self.score(
            after_df,
            id_columns=id_columns,
            range_rules=range_rules,
            format_rules=format_rules,
            category_rules=category_rules,
        )

        delta = round(score_after.overall_score - score_before.overall_score, 2)
        grades_hierarchy = {"F": 0, "D": 1, "C": 2, "B": 3, "A": 4}
        improved = grades_hierarchy.get(score_after.grade, 0) > grades_hierarchy.get(
            score_before.grade, 0
        )

        return ScoreComparison(
            before=score_before,
            after=score_after,
            score_delta=delta,
            grade_improved=improved,
            dimension_deltas={
                dim: round(
                    score_after.dimensions[dim].score - score_before.dimensions[dim].score, 2
                )
                for dim in score_before.dimensions
            },
        )

    def _assign_grade(self, score: float) -> tuple[str, str, bool]:
        if score >= 90.0:
            return "A", "Excellent — Trustworthy for production analytics", True
        if score >= 80.0:
            return "B", "Good — Minor non-critical anomalies present", True
        if score >= 70.0:
            return "C", "Fair — Noticeable defects requiring analyst review", False
        if score >= 60.0:
            return "D", "Poor — High risk of biased or inaccurate analysis", False
        return "F", "Critical — Untrustworthy data; do not use for analysis", False

    def _empty_score(self) -> QualityScoreResult:
        empty_dim = lambda name, w: DimensionScore(
            name=name,
            score=0.0,
            weight=w,
            weighted_score=0.0,
            passed_items=0,
            total_evaluated=0,
            defects_count=0,
            details="Empty dataset.",
        )
        return QualityScoreResult(
            overall_score=0.0,
            grade="F",
            grade_label="Empty dataset",
            is_trustworthy=False,
            dimensions={
                "completeness": empty_dim("Completeness", self.weights.completeness),
                "validity": empty_dim("Validity", self.weights.validity),
                "uniqueness": empty_dim("Uniqueness", self.weights.uniqueness),
                "consistency": empty_dim("Consistency", self.weights.consistency),
            },
            weights=self.weights,
        )
