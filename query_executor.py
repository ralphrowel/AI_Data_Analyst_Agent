import re
import pandas as pd

from data_profiler import has_comma_separated, has_number_with_unit, get_id_columns

FREE_TEXT_COLUMNS = {"title", "description", "cast", "director"}
HIGH_CARD_TEXT = {"duration", "date_added"}


def _pick_chart_column(filtered_df, id_columns):
    """Find the best column for a value-counts chart from the filtered subset.

    Excludes free-text, high-cardinality-text, and id columns.
    Picks the column whose unique-value count is closest to the ideal 2–6 range.
    Returns (column_name, {value: count}) or (None, None).
    """
    exclude = FREE_TEXT_COLUMNS | HIGH_CARD_TEXT | set(id_columns)
    best_col = None
    best_counts = None
    best_distance = float("inf")

    for col in filtered_df.columns:
        if col in exclude:
            continue
        nunique = filtered_df[col].nunique()
        if nunique <= 1:
            continue
        distance = abs(nunique - 4)
        if distance < best_distance:
            best_distance = distance
            best_col = col
            best_counts = filtered_df[col].value_counts()

    if best_col is not None:
        return best_col, {str(k): int(v) for k, v in best_counts.items()}
    return None, None


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
        filters = plan["filter"] if isinstance(plan["filter"], list) else [plan["filter"]]
        for f in filters:
            col, val = f["column"], f["value"]
            op = f.get("operator", "contains")
            
            if op == "contains":
                filtered = filtered[filtered[col].astype(str).str.contains(str(val), case=False, na=False)]
            elif op == "eq":
                filtered = filtered[filtered[col].astype(str) == str(val)]
            elif op == "date_month_year":
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dt = pd.to_datetime(filtered[col], errors="coerce")
                month, year = val["month"], val["year"]
                filtered = filtered[(dt.dt.month == month) & (dt.dt.year == year)]
            elif op == "date_year":
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dt = pd.to_datetime(filtered[col], errors="coerce")
                filtered = filtered[dt.dt.year == val]
            elif op == "date_month":
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dt = pd.to_datetime(filtered[col], errors="coerce")
                filtered = filtered[dt.dt.month == val]

    id_columns = get_id_columns(filtered)
    result_count = len(filtered)

    if operation == "filter":
        chart_col, chart_counts = _pick_chart_column(filtered, id_columns)
        return {
            "operation": "filter",
            "matching_rows": result_count,
            "columns": list(filtered.columns),
            "sample": filtered.head(5).to_dict(orient="records"),
            "id_columns": id_columns,
            "chart_target_column": chart_col,
            "chart_counts": chart_counts,
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
        groups_count = len(result)

        CHART_TOP_N = 15
        if groups_count > 20:
            chart_slice = result.head(CHART_TOP_N)
            chart_results = {str(k): float(v) if isinstance(v, (int, float)) else str(v) for k, v in chart_slice.items()}
        else:
            chart_results = None

        return {
            "operation": "group_by_agg",
            "target_column": target,
            "agg_column": agg_col,
            "agg_func": agg_func,
            "results": {str(k): float(v) if isinstance(v, (int, float)) else str(v) for k, v in result.items()},
            "chart_results": chart_results,
            "groups_count": groups_count,
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
