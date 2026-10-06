"""Data Profiler Engine: structural and statistical profiling for tabular datasets."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from backend.app.data_quality.models import ColumnProfile, DatasetSummary, ProfileResult


class DataProfiler:
    """Generates structural and statistical profiles for pandas DataFrames."""

    def __init__(self, top_n_categories: int = 5):
        self.top_n_categories = top_n_categories

    def profile(self, df: pd.DataFrame) -> ProfileResult:
        """Profiles a DataFrame and returns a comprehensive ProfileResult."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame")

        total_rows = len(df)
        total_columns = len(df.columns)
        total_cells = df.size

        if total_rows == 0 or total_columns == 0:
            return ProfileResult(
                summary=DatasetSummary(
                    total_rows=0,
                    total_columns=total_columns,
                    total_cells=0,
                    total_missing_cells=0,
                    missing_percentage=0.0,
                    duplicate_rows=0,
                    duplicate_percentage=0.0,
                    memory_bytes=0,
                    column_types_breakdown={},
                ),
                columns={},
                missing_rankings=[],
            )

        # Duplicate calculation
        duplicate_rows = int(df.duplicated().sum()) if total_rows > 0 else 0
        duplicate_pct = round((duplicate_rows / total_rows * 100), 2) if total_rows > 0 else 0.0

        memory_usage = int(df.memory_usage(deep=True).sum()) if total_rows > 0 else 0

        # Column-level profiling
        columns_profile: Dict[str, ColumnProfile] = {}
        semantic_counts: Dict[str, int] = {}
        missing_rankings_list: List[Dict[str, Any]] = []
        total_missing_cells = 0

        for col in df.columns:
            col_prof = self._profile_column(df[col], total_rows)
            columns_profile[col] = col_prof
            semantic_counts[col_prof.semantic_type] = semantic_counts.get(col_prof.semantic_type, 0) + 1
            total_missing_cells += col_prof.null_count

            if col_prof.null_count > 0:
                missing_rankings_list.append(
                    {
                        "column": col,
                        "null_count": col_prof.null_count,
                        "null_percentage": col_prof.null_percentage,
                        "semantic_type": col_prof.semantic_type,
                    }
                )

        missing_pct = round((total_missing_cells / total_cells * 100), 2) if total_cells > 0 else 0.0

        # Sort missing columns descending by null count
        missing_rankings_list.sort(key=lambda x: x["null_count"], reverse=True)

        summary = DatasetSummary(
            total_rows=total_rows,
            total_columns=total_columns,
            total_cells=total_cells,
            total_missing_cells=total_missing_cells,
            missing_percentage=missing_pct,
            duplicate_rows=duplicate_rows,
            duplicate_percentage=duplicate_pct,
            memory_bytes=memory_usage,
            column_types_breakdown=semantic_counts,
        )

        return ProfileResult(
            summary=summary,
            columns=columns_profile,
            missing_rankings=missing_rankings_list,
        )

    def _infer_semantic_type(self, series: pd.Series) -> str:
        """Infers high-level semantic data type (numeric, boolean, datetime, text)."""
        dtype_str = str(series.dtype).lower()

        if "bool" in dtype_str:
            return "boolean"
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"

        # Check if text series can be recognized as datetime by sampling up to 50 rows
        non_nulls = series.dropna()
        if len(non_nulls) > 0:
            sample = non_nulls.head(50)
            try:
                converted = pd.to_datetime(sample, errors="coerce", format="mixed")
                if len(sample) > 0 and (converted.notna().sum() / len(sample)) >= 0.8:
                    return "datetime"
            except Exception:
                pass

        return "text"

    def _profile_column(self, series: pd.Series, total_rows: int) -> ColumnProfile:
        """Generates statistical and cardinality metrics for a single column."""
        col_name = str(series.name)
        dtype_str = str(series.dtype)

        # Detect nulls (standard NaN and whitespace-only strings)
        if pd.api.types.is_string_dtype(series) or series.dtype == object:
            null_mask = series.isna() | (series.astype(str).str.strip() == "")
        else:
            null_mask = series.isna()

        null_count = int(null_mask.sum())
        null_pct = round((null_count / total_rows * 100), 2) if total_rows > 0 else 0.0

        unique_count = int(series.nunique(dropna=True))
        unique_pct = round((unique_count / total_rows * 100), 2) if total_rows > 0 else 0.0

        semantic_type = self._infer_semantic_type(series)

        numeric_stats = None
        text_stats = None
        datetime_stats = None

        non_nulls = series.dropna()

        if semantic_type == "numeric" and len(non_nulls) > 0:
            numeric_stats = {
                "min": float(np.nanmin(non_nulls)),
                "max": float(np.nanmax(non_nulls)),
                "mean": round(float(non_nulls.mean()), 4),
                "median": round(float(non_nulls.median()), 4),
                "std": round(float(non_nulls.std(ddof=1)), 4) if len(non_nulls) > 1 else 0.0,
                "q25": round(float(non_nulls.quantile(0.25)), 4),
                "q75": round(float(non_nulls.quantile(0.75)), 4),
            }
        elif semantic_type == "datetime" and len(non_nulls) > 0:
            dt_series = pd.to_datetime(non_nulls, errors="coerce")
            valid_dates = dt_series.dropna()
            if len(valid_dates) > 0:
                datetime_stats = {
                    "min_date": str(valid_dates.min()),
                    "max_date": str(valid_dates.max()),
                }
        elif semantic_type in ("text", "boolean") and len(non_nulls) > 0:
            str_series = non_nulls.astype(str)
            lengths = str_series.str.len()
            value_counts = str_series.value_counts().head(self.top_n_categories).to_dict()

            text_stats = {
                "min_length": int(lengths.min()),
                "max_length": int(lengths.max()),
                "avg_length": round(float(lengths.mean()), 2),
                "top_values": {str(k): int(v) for k, v in value_counts.items()},
            }

        return ColumnProfile(
            name=col_name,
            dtype=dtype_str,
            semantic_type=semantic_type,
            total_count=total_rows,
            null_count=null_count,
            null_percentage=null_pct,
            unique_count=unique_count,
            unique_percentage=unique_pct,
            numeric_stats=numeric_stats,
            text_stats=text_stats,
            datetime_stats=datetime_stats,
        )
