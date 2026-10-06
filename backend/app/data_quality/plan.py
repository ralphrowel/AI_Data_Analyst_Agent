"""Suggested Cleaning Plan generator and validation schemas for Visiq."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from backend.app.data_engine.profiler import has_date_like
from backend.app.data_quality.models import IssueCategory, QualityReport


class CleaningPlanRequest(BaseModel):
    """Validated cleaning plan payload for preview and execution."""

    model_config = ConfigDict(extra="forbid")

    strip_whitespace: bool = Field(True, description="Trim leading/trailing whitespaces across string cells")
    normalize_column_names: bool = Field(False, description="Trim whitespaces from column headers (default off)")
    casing_rules: Optional[Dict[str, str]] = Field(None, description="Standardize casing per column: 'lower', 'upper', 'title'")
    categorical_mappings: Optional[Dict[str, Dict[str, str]]] = Field(None, description="Map categorical values per column")
    date_columns: Optional[List[str]] = Field(None, description="Normalize listed columns to ISO-8601 (YYYY-MM-DD)")
    range_rules: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Clamp or nullify numeric out-of-bounds values")
    drop_duplicates_subset: Optional[Union[List[str], bool]] = Field(None, description="True for all columns, or list of subset columns")
    missing_strategies: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Imputation strategies per column")
    type_conversions: Optional[Dict[str, str]] = Field(None, description="Strict type casting per column ('int', 'float', 'str', 'datetime')")

    def to_engine_options(self) -> Dict[str, Any]:
        """Converts model to dictionary arguments for DataCleaningEngine.clean()."""
        return self.model_dump(exclude_none=True)


def generate_suggested_plan(report: QualityReport, df: pd.DataFrame) -> Dict[str, Any]:
    """Generates an explainable, deterministic recommended cleaning plan from QualityReport."""
    plan: Dict[str, Any] = {
        "strip_whitespace": True,
        "normalize_column_names": False,
    }

    # 1. Duplicates
    has_duplicates = any(
        i.category == IssueCategory.DUPLICATE for i in report.issues
    )
    if has_duplicates:
        plan["drop_duplicates_subset"] = True

    # 2. Inconsistent Casing
    casing_cols = [
        i.column
        for i in report.issues
        if i.category == IssueCategory.INCONSISTENT_CATEGORY
        and i.column is not None
        and "case" in i.description.lower()
    ]
    if casing_cols:
        plan["casing_rules"] = {col: "title" for col in set(casing_cols)}

    # 3. Dates
    date_cols: List[str] = []
    for issue in report.issues:
        if (
            issue.category == IssueCategory.INVALID_FORMAT
            and issue.column is not None
            and "date" in issue.description.lower()
        ):
            date_cols.append(issue.column)

    # Check date-like columns in dataframe
    for col in df.columns:
        if (
            (pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object)
            and has_date_like(df[col])
        ):
            date_cols.append(col)

    if date_cols:
        plan["date_columns"] = sorted(list(set(date_cols)))

    # 4. Missing values
    missing_strategies: Dict[str, Dict[str, Any]] = {}
    for issue in report.issues:
        if issue.category == IssueCategory.MISSING and issue.column and issue.column in df.columns:
            col = issue.column
            series = df[col]
            null_pct = issue.affected_percentage

            # Only suggest automatic imputation if missingness is moderate (< 40%)
            if null_pct < 40.0:
                if pd.api.types.is_numeric_dtype(series):
                    missing_strategies[col] = {"strategy": "median"}
                elif pd.api.types.is_string_dtype(series) or series.dtype == object:
                    mode_series = series.dropna().mode()
                    if not mode_series.empty and mode_series.iloc[0] != "":
                        missing_strategies[col] = {"strategy": "mode"}
                    else:
                        missing_strategies[col] = {"strategy": "constant", "value": "Unknown"}

    if missing_strategies:
        plan["missing_strategies"] = missing_strategies

    # 5. Out of range
    range_rules: Dict[str, Dict[str, Any]] = {}
    for issue in report.issues:
        if issue.category == IssueCategory.INVALID_RANGE and issue.column:
            # Match bounds from description if possible
            range_rules[issue.column] = {"action": "clamp"}
    if range_rules:
        plan["range_rules"] = range_rules

    return plan
