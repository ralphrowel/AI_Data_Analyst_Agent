"""Deterministic structured data tools for the AI Data Analyst Agent.

Replaces arbitrary code generation with controlled, verifiable operations
over pandas DataFrames as outlined in the System Change Proposal.
"""
from typing import Any, List, Optional
import pandas as pd


def _resolve_column(df: pd.DataFrame, col_name: str) -> str:
    """Case-insensitive and whitespace-tolerant column name resolution."""
    if not col_name:
        return col_name
    if col_name in df.columns:
        return col_name
    cleaned = col_name.strip().lower().replace(" ", "_")
    for c in df.columns:
        if c.strip().lower().replace(" ", "_") == cleaned:
            return c
    return col_name


def get_dataset_schema(df: pd.DataFrame) -> dict:
    """Return dataset column names, types, null counts, and row count."""
    return {
        "row_count": len(df),
        "columns": [
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "missing_count": int(df[col].isna().sum()),
            }
            for col in df.columns
        ],
    }


def filter_rows(
    df: pd.DataFrame,
    column: str,
    operator: str,
    value: Any,
) -> pd.DataFrame:
    """Filter rows deterministically based on column, operator, and value."""
    actual_col = _resolve_column(df, column)
    if actual_col not in df.columns:
        return df.iloc[0:0]

    op = str(operator).lower().strip()
    s = df[actual_col]

    if op in ("eq", "equals", "=="):
        # If both are numeric
        try:
            num_val = float(value)
            num_s = pd.to_numeric(s, errors="coerce")
            return df[num_s == num_val]
        except (ValueError, TypeError):
            pass
        # Case-insensitive string match
        return df[s.astype(str).str.strip().str.lower() == str(value).strip().lower()]

    elif op in ("contains", "like"):
        return df[s.astype(str).str.contains(str(value), case=False, na=False)]

    elif op in ("gt", ">"):
        num_s = pd.to_numeric(s, errors="coerce")
        return df[num_s > float(value)]

    elif op in ("gte", ">="):
        num_s = pd.to_numeric(s, errors="coerce")
        return df[num_s >= float(value)]

    elif op in ("lt", "<"):
        num_s = pd.to_numeric(s, errors="coerce")
        return df[num_s < float(value)]

    elif op in ("lte", "<="):
        num_s = pd.to_numeric(s, errors="coerce")
        return df[num_s <= float(value)]

    return df


def aggregate_data(
    df: pd.DataFrame,
    column: str,
    agg_func: str,
) -> Any:
    """Compute an aggregate metric (mean, sum, count, min, max) on a column."""
    actual_col = _resolve_column(df, column)
    if actual_col not in df.columns:
        return None

    func = str(agg_func).lower().strip()
    if func == "count":
        return int(df[actual_col].count())

    num_series = pd.to_numeric(df[actual_col], errors="coerce")
    if func in ("mean", "avg", "average"):
        val = num_series.mean()
        return round(float(val), 2) if pd.notna(val) else None
    elif func == "sum":
        val = num_series.sum()
        return round(float(val), 2) if pd.notna(val) else None
    elif func == "min":
        val = num_series.min()
        return float(val) if pd.notna(val) else None
    elif func == "max":
        val = num_series.max()
        return float(val) if pd.notna(val) else None

    return None


def group_data(
    df: pd.DataFrame,
    by_column: str,
    agg_column: str,
    agg_func: str = "count",
    limit: int = 10,
) -> dict:
    """Group rows by a column and aggregate another column."""
    by_col = _resolve_column(df, by_column)
    agg_col = _resolve_column(df, agg_column)

    if by_col not in df.columns or agg_col not in df.columns:
        return {}

    func = str(agg_func).lower().strip()
    if func == "count":
        grouped = df.groupby(by_col)[agg_col].count()
    else:
        # Numeric aggregation
        temp_df = df[[by_col, agg_col]].copy()
        temp_df[agg_col] = pd.to_numeric(temp_df[agg_col], errors="coerce")
        agg_map = {"avg": "mean", "average": "mean"}
        mapped_func = agg_map.get(func, func)
        grouped = temp_df.groupby(by_col)[agg_col].agg(mapped_func)

    sorted_grouped = grouped.dropna().sort_values(ascending=False).head(limit)
    return {
        str(k): round(float(v), 2) if isinstance(v, (int, float)) else str(v)
        for k, v in sorted_grouped.items()
    }


def sort_data(
    df: pd.DataFrame,
    by_column: str,
    ascending: bool = False,
    limit: int = 10,
) -> list[dict]:
    """Sort the dataset by a given column and return top rows."""
    actual_col = _resolve_column(df, by_column)
    if actual_col not in df.columns:
        return []

    # Sort numerically if possible, else string
    sorted_df = df.sort_values(by=actual_col, ascending=ascending).head(limit)
    # Replace NaN with None for valid JSON serialization
    records = sorted_df.where(pd.notna(sorted_df), None).to_dict(orient="records")
    return records


def get_unique_values(
    df: pd.DataFrame,
    column: str,
    limit: int = 20,
) -> dict:
    """Return top unique values and their frequencies."""
    actual_col = _resolve_column(df, column)
    if actual_col not in df.columns:
        return {}

    counts = df[actual_col].value_counts().head(limit)
    return {str(k): int(v) for k, v in counts.items()}

