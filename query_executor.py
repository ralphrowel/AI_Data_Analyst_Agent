import re
import pandas as pd


def _extract_numeric(value: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    return float(match.group(1)) if match else 0.0


def _try_parse_duration(series: pd.Series) -> pd.Series:
    if series.dtype != object:
        return series
    sample = series.dropna().iloc[0] if not series.dropna().empty else ""
    if re.search(r"\d+\s*(min|Season|Seasons)", str(sample), re.IGNORECASE):
        return series.dropna().apply(_extract_numeric)
    return series


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

    result_count = len(filtered)

    if operation == "filter":
        return {
            "operation": "filter",
            "matching_rows": result_count,
            "columns": list(filtered.columns),
            "sample": filtered.head(5).to_dict(orient="records"),
        }

    elif operation == "value_counts":
        target = plan.get("target_column")
        limit = plan.get("limit") or 20

        if target == "listed_in":
            counts = _split_and_count(filtered[target]).head(limit)
        else:
            counts = filtered[target].value_counts().head(limit)

        return {
            "operation": "value_counts",
            "target_column": target,
            "limit": limit,
            "counts": {str(k): int(v) for k, v in counts.items()},
            "total_values": int(filtered[target].nunique()),
        }

    elif operation == "group_by_agg":
        target = plan["target_column"]
        agg_col = plan.get("agg_column") or target
        agg_func = plan.get("agg_func", "count")

        # If aggregation involves mean/sum on duration, parse numeric
        group = filtered.groupby(target)
        if agg_func in ("mean", "sum") and agg_col == "duration":
            series = _try_parse_duration(filtered[agg_col])
            result = group.apply(lambda g: _try_parse_duration(g[agg_col]).agg(agg_func))
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
        }

    else:
        return {
            "operation": "unsupported",
            "reason": f"Unknown operation: {operation}",
        }
