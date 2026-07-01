import re
import pandas as pd

from data_profiler import has_comma_separated, has_number_with_unit, get_id_columns


def _extract_numeric(value: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    return float(match.group(1)) if match else 0.0


def _extract_numeric_from_series(series: pd.Series) -> pd.Series:
    return series.dropna().apply(_extract_numeric)


def _split_and_count(series: pd.Series) -> pd.Series:
    all_items = []
    for val in series.dropna():
        all_items.extend([item.strip() for item in str(val).split(",")])
    return pd.Series(all_items).value_counts()


def execute_plan(df: pd.DataFrame, plan: dict) -> dict:
    operation = plan.get("operation")

    if operation == "unsupported":
        return {
            "operation": "unsupported",
            "reason": plan.get("reason", "No reason provided"),
        }

    filtered = df
    if plan.get("filter"):
        f = plan["filter"]
        col, val = f["column"], str(f["value"])
        filtered = df[df[col].astype(str).str.contains(val, case=False, na=False)]

    id_columns = get_id_columns(filtered)
    result_count = len(filtered)

    if operation == "filter":
        return {
            "operation": "filter",
            "matching_rows": result_count,
            "columns": list(filtered.columns),
            "sample": filtered.head(5).to_dict(orient="records"),
            "id_columns": id_columns,
        }

    elif operation == "value_counts":
        target = plan.get("target_column")
        limit = plan.get("limit") or 20

        if has_comma_separated(filtered[target]):
            counts = _split_and_count(filtered[target]).head(limit)
        else:
            counts = filtered[target].value_counts().head(limit)

        return {
            "operation": "value_counts",
            "target_column": target,
            "limit": limit,
            "counts": {str(k): int(v) for k, v in counts.items()},
            "total_values": int(filtered[target].nunique()),
            "id_columns": id_columns,
        }

    elif operation == "group_by_agg":
        target = plan["target_column"]
        agg_col = plan.get("agg_column") or target
        agg_func = plan.get("agg_func", "count")

        group = filtered.groupby(target)
        if agg_func in ("mean", "sum") and has_number_with_unit(filtered[agg_col]):
            result = group[agg_col].apply(lambda g: _extract_numeric_from_series(g).agg(agg_func))
        else:
            result = group[agg_col].agg(agg_func)

        result = result.sort_values(ascending=False)

        return {
            "operation": "group_by_agg",
            "target_column": target,
            "agg_column": agg_col,
            "agg_func": agg_func,
            "results": {str(k): float(v) if isinstance(v, (int, float)) else str(v) for k, v in result.items()},
            "groups_count": len(result),
            "id_columns": id_columns,
        }

    elif operation == "sort_limit":
        target = plan.get("target_column", list(filtered.columns)[0])
        ascending = plan.get("sort_ascending", False)
        limit = plan.get("limit", 5)

        sorted_df = filtered.sort_values(by=target, ascending=ascending).head(limit)

        return {
            "operation": "sort_limit",
            "target_column": target,
            "sort_ascending": ascending,
            "limit": limit,
            "results": sorted_df.to_dict(orient="records"),
            "total_after_filter": result_count,
            "id_columns": id_columns,
        }

    else:
        return {
            "operation": "unsupported",
            "reason": f"Unknown operation: {operation}",
        }
