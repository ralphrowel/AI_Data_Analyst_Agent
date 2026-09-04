"""Deterministic structured data tools for the AI Data Analyst Agent.

Replaces arbitrary code generation with controlled, verifiable operations
over pandas DataFrames as outlined in the System Change Proposal.
"""
from typing import Any, List, Optional
import pandas as pd


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
    # Placeholder skeleton for modular architecture
    if operator == "eq":
        return df[df[column].astype(str) == str(value)]
    elif operator == "contains":
        return df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
    return df


def aggregate_data(
    df: pd.DataFrame,
    column: str,
    agg_func: str,
) -> Any:
    """Compute an aggregate metric (mean, sum, count, min, max) on a column."""
    # Placeholder skeleton for modular architecture
    if agg_func == "count":
        return int(df[column].count())
    elif hasattr(df[column], agg_func):
        return getattr(df[column], agg_func)()
    return None


def group_data(
    df: pd.DataFrame,
    by_column: str,
    agg_column: str,
    agg_func: str = "count",
    limit: int = 10,
) -> dict:
    """Group rows by a column and aggregate another column."""
    # Placeholder skeleton for modular architecture
    grouped = df.groupby(by_column)[agg_column].agg(agg_func)
    sorted_grouped = grouped.sort_values(ascending=False).head(limit)
    return {str(k): float(v) if isinstance(v, (int, float)) else str(v) for k, v in sorted_grouped.items()}


def sort_data(
    df: pd.DataFrame,
    by_column: str,
    ascending: bool = False,
    limit: int = 10,
) -> list[dict]:
    """Sort the dataset by a given column and return top rows."""
    # Placeholder skeleton for modular architecture
    return df.sort_values(by=by_column, ascending=ascending).head(limit).to_dict(orient="records")


def get_unique_values(
    df: pd.DataFrame,
    column: str,
    limit: int = 20,
) -> dict:
    """Return top unique values and their frequencies."""
    # Placeholder skeleton for modular architecture
    counts = df[column].value_counts().head(limit)
    return {str(k): int(v) for k, v in counts.items()}
