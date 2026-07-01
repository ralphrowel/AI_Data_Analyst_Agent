import re
import warnings
import pandas as pd


def _is_text_col(series: pd.Series) -> bool:
    return pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)


def has_comma_separated(series: pd.Series) -> bool:
    if not _is_text_col(series):
        return False
    non_null = series.dropna()
    if len(non_null) < 5:
        return False
    return non_null.astype(str).str.contains(",", na=False).mean() > 0.2


def has_number_with_unit(series: pd.Series) -> bool:
    if not _is_text_col(series):
        return False
    non_null = series.dropna().astype(str)
    if len(non_null) < 5:
        return False
    return non_null.str.match(r"^\d+(\.\d+)?\s*[a-zA-Z]+").mean() > 0.5


def has_date_like(series: pd.Series) -> bool:
    if not _is_text_col(series):
        return False
    non_null = series.dropna()
    if len(non_null) < 3:
        return False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.to_datetime(non_null, errors="coerce").notna().mean() > 0.6


def has_mixed_numeric(series: pd.Series) -> bool:
    if not _is_text_col(series):
        return False
    non_null = series.dropna()
    if len(non_null) < 5:
        return False
    ratio = pd.to_numeric(non_null, errors="coerce").notna().mean()
    return 0.5 <= ratio < 0.99


def has_high_null_rate(series: pd.Series) -> bool:
    return series.isna().mean() > 0.4


def is_id_column(series: pd.Series) -> bool:
    non_null = series.dropna()
    if len(non_null) < 2:
        return False
    return series.nunique() == len(series)


def get_id_columns(df: pd.DataFrame) -> list:
    return [col for col in df.columns if is_id_column(df[col])]


def profile_dataframe(df: pd.DataFrame) -> str:
    lines = ["[DATA PROFILE]"]

    for col in df.columns:
        s = df[col]
        notes = []

        if has_comma_separated(s):
            notes.append("contains comma-separated values — split before counting or grouping")
        if has_number_with_unit(s):
            notes.append("contains numbers with unit suffixes (e.g. '90 min', '2 Seasons') — extract numeric part before aggregation")
        if has_date_like(s):
            notes.append("looks like date strings — parse before date filtering or sorting")
        if has_mixed_numeric(s):
            notes.append("mostly numeric but contains some non-numeric values — may need cleaning before aggregation")
        if has_high_null_rate(s):
            notes.append(f"high missing rate ({s.isna().mean():.0%}) — consider whether this column is usable")
        if is_id_column(s):
            notes.append("every value is unique — likely an ID column, not useful for aggregation")

        for note in notes:
            lines.append(f'  column "{col}": {note}')

    if len(lines) == 1:
        lines.append("  No structural issues detected.")

    return "\n".join(lines)
