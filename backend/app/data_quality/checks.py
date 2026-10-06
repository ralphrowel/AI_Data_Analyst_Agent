"""Data Quality Checks Engine for Visiq.

Detects quality problems across core dimensions:
- MISSING (nulls, whitespace-only strings)
- DUPLICATE (exact duplicate rows, primary key collisions)
- INVALID_FORMAT (regex patterns, unparseable dates)
- INVALID_TYPE (mixed numeric columns with non-numeric strings)
- INVALID_RANGE (bounds violations: min / max)
- INCONSISTENT_CATEGORY (casing discrepancies, unknown enum values)
- OUTLIER (statistical anomalies via IQR and Z-Score with noise suppression)
"""
from __future__ import annotations

import re
import warnings
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from backend.app.data_engine.profiler import (
    has_date_like,
    has_mixed_numeric,
    is_id_column,
)
from backend.app.data_quality.models import (
    IssueCategory,
    QualityIssue,
    QualityReport,
    Severity,
)

# Standard regex patterns
PATTERNS = {
    "email": re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"),
    "phone": re.compile(r"^\+?[0-9\s\-()]{7,20}$"),
    "iso_date": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
}

YEAR_COLUMN_NAMES = frozenset(
    {"year", "release_year", "birth_year", "start_year", "end_year", "model_year", "pub_year"}
)


class DataQualityEngine:
    """Executes rule-based and statistical quality checks on pandas DataFrames."""

    def __init__(
        self,
        critical_missing_threshold: float = 20.0,
        outlier_method: str = "iqr",
        sample_limit: int = 5,
    ):
        self.critical_missing_threshold = critical_missing_threshold
        self.outlier_method = outlier_method
        self.sample_limit = sample_limit

    def analyze(
        self,
        df: pd.DataFrame,
        id_columns: Optional[List[str]] = None,
        range_rules: Optional[Dict[str, Dict[str, float]]] = None,
        format_rules: Optional[Dict[str, str]] = None,
        category_rules: Optional[Dict[str, List[str]]] = None,
    ) -> QualityReport:
        """Runs comprehensive quality checks and compiles a QualityReport."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame")

        total_rows = len(df)
        total_columns = len(df.columns)

        if total_rows == 0:
            return QualityReport(
                total_rows=0,
                total_columns=total_columns,
                total_issues_count=0,
                issues_by_category={},
                issues_by_severity={},
                issues=[],
            )

        # Candidate ID columns if not explicitly passed
        resolved_id_cols = (
            list(id_columns)
            if id_columns is not None
            else [
                col
                for col in df.columns
                if col.lower() in ("id", "pk", "uuid", "show_id")
                or col.lower().endswith(("_id", "_uuid"))
            ]
        )

        issues: List[QualityIssue] = []

        # 1. Missing values check
        issues.extend(self._check_missing_values(df, total_rows))

        # 2. Duplicate rows and key collisions
        issues.extend(self._check_duplicates(df, total_rows, resolved_id_cols))

        # 3. Format validation (rules + auto-detected date parsing)
        issues.extend(self._check_formats(df, total_rows, format_rules))

        # 4. Mixed-type detection
        issues.extend(self._check_types(df, total_rows))

        # 5. Range validation
        if range_rules:
            issues.extend(self._check_ranges(df, total_rows, range_rules))

        # 6. Categorical consistency checks (with high-cardinality noise suppression)
        issues.extend(self._check_categorical_consistency(df, total_rows, category_rules))

        # 7. Statistical outlier detection (with ID/year noise suppression)
        issues.extend(self._check_outliers(df, total_rows, resolved_id_cols))

        # Summary statistics
        issues_by_category: Dict[str, int] = {}
        issues_by_severity: Dict[str, int] = {}

        for issue in issues:
            cat_name = issue.category.value
            sev_name = issue.severity.value
            issues_by_category[cat_name] = issues_by_category.get(cat_name, 0) + issue.affected_count
            issues_by_severity[sev_name] = issues_by_severity.get(sev_name, 0) + issue.affected_count

        return QualityReport(
            total_rows=total_rows,
            total_columns=total_columns,
            total_issues_count=sum(issues_by_category.values()),
            issues_by_category=issues_by_category,
            issues_by_severity=issues_by_severity,
            issues=issues,
        )

    def _check_missing_values(self, df: pd.DataFrame, total_rows: int) -> List[QualityIssue]:
        issues = []
        for col in df.columns:
            series = df[col]
            # Detect NaN or whitespace-only strings
            if pd.api.types.is_string_dtype(series) or series.dtype == object:
                mask = series.isna() | (series.astype(str).str.strip() == "")
            else:
                mask = series.isna()

            null_count = int(mask.sum())
            if null_count > 0:
                null_pct = round((null_count / total_rows) * 100, 2)
                severity = (
                    Severity.CRITICAL
                    if null_pct >= self.critical_missing_threshold
                    else Severity.WARNING
                )
                issues.append(
                    QualityIssue(
                        category=IssueCategory.MISSING,
                        severity=severity,
                        column=col,
                        description=f"Column '{col}' has {null_count:,} missing values ({null_pct}%).",
                        affected_count=null_count,
                        affected_percentage=null_pct,
                        suggested_action="Impute with default/mode/median or drop if non-critical.",
                    )
                )
        return issues

    def _check_duplicates(
        self, df: pd.DataFrame, total_rows: int, id_columns: List[str]
    ) -> List[QualityIssue]:
        issues = []

        # Exact duplicate rows
        dup_mask = df.duplicated()
        dup_count = int(dup_mask.sum())
        if dup_count > 0:
            dup_pct = round((dup_count / total_rows) * 100, 2)
            issues.append(
                QualityIssue(
                    category=IssueCategory.DUPLICATE,
                    severity=Severity.WARNING,
                    column=None,
                    description=f"Found {dup_count:,} exact duplicate rows ({dup_pct}%).",
                    affected_count=dup_count,
                    affected_percentage=dup_pct,
                    suggested_action="Deduplicate rows preserving first or last occurrence.",
                )
            )

        # Primary key identifier duplicates
        for key_col in id_columns:
            if key_col in df.columns:
                key_dup_mask = df.duplicated(subset=[key_col], keep=False)
                key_dup_count = int(key_dup_mask.sum())
                if key_dup_count > 0:
                    key_dup_pct = round((key_dup_count / total_rows) * 100, 2)
                    samples = (
                        df.loc[key_dup_mask, key_col]
                        .dropna()
                        .head(self.sample_limit)
                        .tolist()
                    )
                    issues.append(
                        QualityIssue(
                            category=IssueCategory.DUPLICATE,
                            severity=Severity.CRITICAL,
                            column=key_col,
                            description=f"Primary key identifier '{key_col}' has {key_dup_count:,} duplicate occurrences.",
                            affected_count=key_dup_count,
                            affected_percentage=key_dup_pct,
                            sample_values=samples,
                            suggested_action="Verify identifier generation or deduplicate on primary key.",
                        )
                    )
        return issues

    def _check_formats(
        self,
        df: pd.DataFrame,
        total_rows: int,
        format_rules: Optional[Dict[str, str]],
    ) -> List[QualityIssue]:
        issues = []
        rules = format_rules or {}

        # 1. User-specified format rules
        for col, format_name in rules.items():
            if col not in df.columns:
                continue

            series = df[col].dropna().astype(str).str.strip()
            series = series[series != ""]
            if len(series) == 0:
                continue

            regex = PATTERNS.get(format_name.lower())
            if regex is None:
                try:
                    regex = re.compile(format_name)
                except re.error:
                    continue

            invalid_mask = ~series.str.match(regex)
            invalid_count = int(invalid_mask.sum())
            if invalid_count > 0:
                invalid_pct = round((invalid_count / total_rows) * 100, 2)
                sample_invalids = series[invalid_mask].head(self.sample_limit).tolist()
                issues.append(
                    QualityIssue(
                        category=IssueCategory.INVALID_FORMAT,
                        severity=Severity.WARNING,
                        column=col,
                        description=f"Column '{col}' has {invalid_count:,} values failing format rule '{format_name}'.",
                        affected_count=invalid_count,
                        affected_percentage=invalid_pct,
                        sample_values=sample_invalids,
                        suggested_action=f"Normalize or correct values to conform with '{format_name}'.",
                    )
                )

        # 2. Auto-detect invalid date strings (Fix D5)
        for col in df.columns:
            if col in rules:
                continue  # Already checked by explicit format rule

            series = df[col]
            if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
                continue

            # Check if column looks like dates
            if has_date_like(series):
                cleaned = series.dropna().astype(str).str.strip()
                cleaned = cleaned[cleaned != ""]
                if len(cleaned) < 3:
                    continue

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    parsed = pd.to_datetime(cleaned, errors="coerce")

                invalid_mask = parsed.isna()
                invalid_count = int(invalid_mask.sum())
                if invalid_count > 0:
                    invalid_pct = round((invalid_count / total_rows) * 100, 2)
                    samples = cleaned[invalid_mask].head(self.sample_limit).tolist()
                    issues.append(
                        QualityIssue(
                            category=IssueCategory.INVALID_FORMAT,
                            severity=Severity.WARNING,
                            column=col,
                            description=f"Column '{col}' appears to contain dates but has {invalid_count:,} unparseable values ({invalid_pct}%).",
                            affected_count=invalid_count,
                            affected_percentage=invalid_pct,
                            sample_values=samples,
                            suggested_action="Standardize date strings to ISO format (YYYY-MM-DD) or coerce invalid entries to null.",
                        )
                    )

        return issues

    def _check_types(self, df: pd.DataFrame, total_rows: int) -> List[QualityIssue]:
        """Detects mixed numeric/text types in predominantly numeric columns (Fix D5)."""
        issues = []
        for col in df.columns:
            series = df[col]
            if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
                continue

            if has_mixed_numeric(series):
                non_null = series.dropna().astype(str).str.strip()
                non_empty = non_null[non_null != ""]
                if len(non_empty) < 5:
                    continue

                parsed = pd.to_numeric(non_empty, errors="coerce")
                invalid_mask = parsed.isna()
                invalid_count = int(invalid_mask.sum())
                if invalid_count > 0:
                    invalid_pct = round((invalid_count / total_rows) * 100, 2)
                    samples = non_empty[invalid_mask].head(self.sample_limit).tolist()
                    issues.append(
                        QualityIssue(
                            category=IssueCategory.INVALID_TYPE,
                            severity=Severity.WARNING,
                            column=col,
                            description=f"Column '{col}' is predominantly numeric but contains {invalid_count:,} non-numeric values ({invalid_pct}%).",
                            affected_count=invalid_count,
                            affected_percentage=invalid_pct,
                            sample_values=samples,
                            suggested_action="Coerce non-numeric values to null or convert column to numeric type.",
                        )
                    )
        return issues

    def _check_ranges(
        self,
        df: pd.DataFrame,
        total_rows: int,
        range_rules: Dict[str, Dict[str, float]],
    ) -> List[QualityIssue]:
        issues = []
        for col, bounds in range_rules.items():
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue

            series = df[col].dropna()
            min_val = bounds.get("min")
            max_val = bounds.get("max")

            invalid_mask = pd.Series(False, index=series.index)
            desc_parts = []
            if min_val is not None:
                invalid_mask |= series < min_val
                desc_parts.append(f"< {min_val}")
            if max_val is not None:
                invalid_mask |= series > max_val
                desc_parts.append(f"> {max_val}")

            invalid_count = int(invalid_mask.sum())
            if invalid_count > 0:
                invalid_pct = round((invalid_count / total_rows) * 100, 2)
                samples = series[invalid_mask].head(self.sample_limit).tolist()
                issues.append(
                    QualityIssue(
                        category=IssueCategory.INVALID_RANGE,
                        severity=Severity.WARNING,
                        column=col,
                        description=f"Column '{col}' has {invalid_count:,} values out of range ({' or '.join(desc_parts)}).",
                        affected_count=invalid_count,
                        affected_percentage=invalid_pct,
                        sample_values=samples,
                        suggested_action="Cap/clamp values within allowed boundaries or nullify invalid entries.",
                    )
                )
        return issues

    def _check_categorical_consistency(
        self,
        df: pd.DataFrame,
        total_rows: int,
        category_rules: Optional[Dict[str, List[str]]],
    ) -> List[QualityIssue]:
        issues = []
        text_cols = df.select_dtypes(include=["object", "str"]).columns

        for col in text_cols:
            series = df[col].dropna().astype(str).str.strip()
            series = series[series != ""]
            if len(series) == 0:
                continue

            raw_unique = series.unique()
            unique_count = len(raw_unique)
            total_non_null = len(series)

            # Noise suppression: skip casing check on high-cardinality free text (Fix D6)
            is_free_text = (total_non_null >= 10) and (unique_count > 20) and ((unique_count / total_non_null) > 0.5)

            if not is_free_text:
                lower_map: Dict[str, List[str]] = {}
                for val in raw_unique:
                    key = val.lower()
                    lower_map.setdefault(key, []).append(val)

                inconsistent_groups = [vals for vals in lower_map.values() if len(vals) > 1]
                if inconsistent_groups:
                    inconsistent_variants = [v for group in inconsistent_groups for v in group]
                    affected_count = int(series.isin(inconsistent_variants).sum())
                    affected_pct = round((affected_count / total_rows) * 100, 2)
                    sample_display = [
                        f"{{{', '.join(group)}}}"
                        for group in inconsistent_groups[: self.sample_limit]
                    ]

                    issues.append(
                        QualityIssue(
                            category=IssueCategory.INCONSISTENT_CATEGORY,
                            severity=Severity.INFO,
                            column=col,
                            description=f"Column '{col}' contains case inconsistencies: {'; '.join(sample_display)}.",
                            affected_count=affected_count,
                            affected_percentage=affected_pct,
                            sample_values=sample_display,
                            suggested_action="Standardize casing using uppercase, lowercase, or titlecase mapping.",
                        )
                    )

            # Predefined allowed categories
            if category_rules and col in category_rules:
                allowed = set(category_rules[col])
                unknown_mask = ~series.isin(allowed)
                unknown_count = int(unknown_mask.sum())
                if unknown_count > 0:
                    unknown_pct = round((unknown_count / total_rows) * 100, 2)
                    sample_unknowns = series[unknown_mask].head(self.sample_limit).tolist()
                    issues.append(
                        QualityIssue(
                            category=IssueCategory.INCONSISTENT_CATEGORY,
                            severity=Severity.WARNING,
                            column=col,
                            description=f"Column '{col}' has {unknown_count:,} values not in configured categories.",
                            affected_count=unknown_count,
                            affected_percentage=unknown_pct,
                            sample_values=sample_unknowns,
                            suggested_action="Map unknown categories to defined terms or label as 'Other'.",
                        )
                    )

        return issues

    def _check_outliers(
        self,
        df: pd.DataFrame,
        total_rows: int,
        id_columns: List[str],
    ) -> List[QualityIssue]:
        issues = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 10:
                continue

            # Noise suppression: skip ID columns and year columns (Fix D6)
            if col in id_columns or is_id_column(df[col]):
                continue
            if col.lower() in YEAR_COLUMN_NAMES:
                continue

            if self.outlier_method == "iqr":
                q25 = float(series.quantile(0.25))
                q75 = float(series.quantile(0.75))
                iqr = q75 - q25
                if iqr <= 0:
                    continue
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                outlier_mask = (series < lower_bound) | (series > upper_bound)
            else:  # z-score
                mean = series.mean()
                std = series.std(ddof=1)
                if std == 0 or np.isnan(std):
                    continue
                z_scores = np.abs((series - mean) / std)
                outlier_mask = z_scores > 3.0

            outlier_count = int(outlier_mask.sum())
            if outlier_count > 0:
                outlier_pct = round((outlier_count / total_rows) * 100, 2)
                sample_outliers = series[outlier_mask].head(self.sample_limit).tolist()
                issues.append(
                    QualityIssue(
                        category=IssueCategory.OUTLIER,
                        severity=Severity.INFO,
                        column=col,
                        description=f"Column '{col}' has {outlier_count:,} statistical outliers ({self.outlier_method.upper()} method).",
                        affected_count=outlier_count,
                        affected_percentage=outlier_pct,
                        sample_values=sample_outliers,
                        suggested_action="Inspect domain context; consider winsorizing or capping if erroneous.",
                    )
                )

        return issues
