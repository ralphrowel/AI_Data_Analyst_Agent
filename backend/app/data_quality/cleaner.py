"""Deterministic Data Cleaning Engine for Visiq.

Executes an ordered, deterministic, and auditable transformation pipeline:
1. Header whitespace trimming (opt-in; preserves pinned widgets by default)
2. Whitespace trimming across string columns
3. Categorical & Casing standardization
4. Date normalization to ISO-8601 (YYYY-MM-DD) with accurate audit
5. Range bounds enforcement (clamp or nullify)
6. Duplicate removal (exact rows or identifier subset)
7. Missing-value imputation (mean, median, mode, constant, ffill, bfill, drop)
8. Strict type conversions with accurate cell diff and coercion tracking
9. Formula-injection sanitization for secure spreadsheet export
10. Before / After comparison & human-readable explanation audit
"""
from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from backend.app.data_quality.models import (
    CleaningAuditSummary,
    CleaningResult,
    CleaningStep,
)

FORMULA_TRIGGERS = re.compile(r"^[\=\+\-\@\t\r]")


def sanitize_formula_injection(df: pd.DataFrame) -> pd.DataFrame:
    """Protects against formula injection in CSV exports by quoting formula triggers."""
    export_df = df.copy()
    str_cols = export_df.select_dtypes(include=["object", "str"]).columns
    for col in str_cols:
        export_df[col] = export_df[col].apply(
            lambda val: f"'{val}"
            if isinstance(val, str) and FORMULA_TRIGGERS.match(val)
            else val
        )
    return export_df


def to_safe_csv_text(df: pd.DataFrame) -> str:
    """Converts DataFrame to sanitized CSV string."""
    sanitized = sanitize_formula_injection(df)
    buf = io.StringIO()
    sanitized.to_csv(buf, index=False, encoding="utf-8")
    return buf.getvalue()


class DataCleaningEngine:
    """Executes deterministic cleaning transformations and produces auditable results."""

    def clean(
        self,
        df: pd.DataFrame,
        strip_whitespace: bool = True,
        normalize_column_names: bool = False,
        casing_rules: Optional[Dict[str, str]] = None,  # col -> 'lower', 'upper', 'title'
        categorical_mappings: Optional[Dict[str, Dict[str, str]]] = None,
        date_columns: Optional[List[str]] = None,
        range_rules: Optional[Dict[str, Dict[str, Any]]] = None,  # col -> {'min': x, 'max': y, 'action': 'clamp'|'nullify'}
        drop_duplicates_subset: Optional[List[str] | bool] = None,  # True for all cols or list of cols
        missing_strategies: Optional[Dict[str, Dict[str, Any]]] = None,  # col -> {'strategy': '...', 'value': ...}
        type_conversions: Optional[Dict[str, str]] = None,  # col -> 'int', 'float', 'str', 'datetime'
    ) -> CleaningResult:
        """Executes the transformation pipeline statelessly and compiles an auditable result."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame")

        steps: List[CleaningStep] = []
        working_df = df.copy()

        # Audit counters
        values_fixed = 0
        values_imputed = 0
        values_nullified = 0
        duplicates_removed = 0

        # Capture before statistics
        before_stats = self._calc_stats(working_df)

        def record_step(
            operation: str,
            target_column: Optional[str],
            parameters: Dict[str, Any],
            rows_affected: int,
            details: str,
        ) -> None:
            steps.append(
                CleaningStep(
                    step_number=len(steps) + 1,
                    operation=operation,
                    target_column=target_column,
                    parameters=parameters,
                    rows_affected=rows_affected,
                    details=details,
                )
            )

        # Step 1: Normalize column headers (strip whitespace - opt-in)
        if normalize_column_names:
            old_cols = list(working_df.columns)
            new_cols = [str(c).strip() for c in old_cols]
            renamed_count = sum(1 for o, n in zip(old_cols, new_cols) if o != n)
            if renamed_count > 0:
                working_df.columns = new_cols
                record_step(
                    operation="normalize_column_names",
                    target_column=None,
                    parameters={"rename_map": dict(zip(old_cols, new_cols))},
                    rows_affected=renamed_count,
                    details=f"Stripped whitespace from {renamed_count} column header(s).",
                )

        # Step 2: Whitespace trimming across string cells
        if strip_whitespace:
            str_cols = working_df.select_dtypes(include=["object", "str"]).columns
            total_stripped = 0
            for col in str_cols:
                original = working_df[col].dropna().astype(str)
                stripped = original.str.strip()
                diff = int((original != stripped).sum())
                if diff > 0:
                    working_df[col] = working_df[col].apply(
                        lambda x: x.strip() if isinstance(x, str) else x
                    )
                    total_stripped += diff
            if total_stripped > 0:
                values_fixed += total_stripped
                record_step(
                    operation="strip_whitespace",
                    target_column=None,
                    parameters={},
                    rows_affected=total_stripped,
                    details=f"Trimmed leading/trailing whitespaces in {total_stripped:,} cells.",
                )

        # Step 3: Categorical & Casing standardization
        if casing_rules:
            for col, case_type in casing_rules.items():
                if col in working_df.columns and (
                    pd.api.types.is_string_dtype(working_df[col]) or working_df[col].dtype == object
                ):
                    non_nulls = working_df[col].dropna().astype(str)
                    if case_type == "lower":
                        transformed = non_nulls.str.lower()
                    elif case_type == "upper":
                        transformed = non_nulls.str.upper()
                    elif case_type == "title":
                        transformed = non_nulls.str.title()
                    else:
                        continue
                    diff = int((non_nulls != transformed).sum())
                    if diff > 0:
                        working_df.loc[non_nulls.index, col] = transformed
                        values_fixed += diff
                        record_step(
                            operation="casing_standardization",
                            target_column=col,
                            parameters={"case_type": case_type},
                            rows_affected=diff,
                            details=f"Standardized casing to '{case_type}' for {diff:,} values in '{col}'.",
                        )

        if categorical_mappings:
            for col, mapping in categorical_mappings.items():
                if col in working_df.columns:
                    mask = working_df[col].isin(mapping.keys())
                    count = int(mask.sum())
                    if count > 0:
                        working_df[col] = working_df[col].replace(mapping)
                        values_fixed += count
                        record_step(
                            operation="categorical_mapping",
                            target_column=col,
                            parameters={"mapping": mapping},
                            rows_affected=count,
                            details=f"Mapped {count:,} values in '{col}' to standardized categories.",
                        )

        # Step 4: Date Normalization (Fix D1: accurately distinguish fixed vs coerced nulls)
        if date_columns:
            for col in date_columns:
                if col in working_df.columns:
                    non_null_mask = working_df[col].notna() & (
                        working_df[col].astype(str).str.strip() != ""
                    )
                    if not non_null_mask.any():
                        continue

                    parsed = pd.to_datetime(
                        working_df[col], errors="coerce", format="mixed"
                    )
                    valid_mask = parsed.notna() & non_null_mask
                    coerced_mask = parsed.isna() & non_null_mask

                    valid_count = int(valid_mask.sum())
                    coerced_count = int(coerced_mask.sum())

                    # Apply ISO-8601 string formatting
                    formatted_dates = parsed.dt.strftime("%Y-%m-%d")
                    working_df[col] = formatted_dates

                    values_fixed += valid_count
                    values_nullified += coerced_count

                    detail_msg = f"Normalized {valid_count:,} dates in '{col}' to ISO-8601 (YYYY-MM-DD)."
                    if coerced_count > 0:
                        detail_msg += f" {coerced_count:,} unparseable values coerced to null."

                    record_step(
                        operation="date_normalization",
                        target_column=col,
                        parameters={"format": "%Y-%m-%d", "coerced_nulls": coerced_count},
                        rows_affected=valid_count,
                        details=detail_msg,
                    )

        # Step 5: Range Enforcement (Clamp or Nullify)
        if range_rules:
            for col, bounds in range_rules.items():
                if col in working_df.columns and pd.api.types.is_numeric_dtype(working_df[col]):
                    min_val = bounds.get("min")
                    max_val = bounds.get("max")
                    action = bounds.get("action", "clamp")  # 'clamp' or 'nullify'

                    series = working_df[col].dropna()
                    out_of_bounds = pd.Series(False, index=series.index)
                    if min_val is not None:
                        out_of_bounds |= series < min_val
                    if max_val is not None:
                        out_of_bounds |= series > max_val

                    affected = int(out_of_bounds.sum())
                    if affected > 0:
                        if action == "nullify":
                            working_df.loc[out_of_bounds[out_of_bounds].index, col] = np.nan
                            values_nullified += affected
                        else:  # clamp
                            working_df[col] = working_df[col].clip(lower=min_val, upper=max_val)
                            values_fixed += affected

                        record_step(
                            operation="range_enforcement",
                            target_column=col,
                            parameters=bounds,
                            rows_affected=affected,
                            details=f"Applied range rule ({action}) to {affected:,} values in '{col}'.",
                        )

        # Step 6: Duplicate Removal
        if drop_duplicates_subset is not None:
            before_rows = len(working_df)
            if drop_duplicates_subset is True:
                working_df = working_df.drop_duplicates(keep="first")
            elif isinstance(drop_duplicates_subset, list):
                valid_subset = [c for c in drop_duplicates_subset if c in working_df.columns]
                if valid_subset:
                    working_df = working_df.drop_duplicates(subset=valid_subset, keep="first")
            dups_removed = before_rows - len(working_df)
            if dups_removed > 0:
                duplicates_removed += dups_removed
                record_step(
                    operation="drop_duplicates",
                    target_column=None,
                    parameters={"subset": drop_duplicates_subset},
                    rows_affected=dups_removed,
                    details=f"Removed {dups_removed:,} duplicate records (kept first occurrence).",
                )

        # Step 7: Missing-Value Handling
        if missing_strategies:
            for col, strat in missing_strategies.items():
                if col not in working_df.columns:
                    continue

                method = strat.get("strategy", "constant").lower()
                fill_val = strat.get("value")
                null_mask = working_df[col].isna() | (
                    (pd.api.types.is_string_dtype(working_df[col]) | (working_df[col].dtype == object))
                    & (working_df[col].astype(str).str.strip() == "")
                )
                null_count = int(null_mask.sum())

                if null_count == 0:
                    continue

                # Ensure empty strings are standard NaNs before fillna operations
                if null_mask.any():
                    working_df.loc[null_mask, col] = np.nan

                if method == "drop":
                    working_df = working_df.dropna(subset=[col])
                    record_step(
                        operation="drop_missing",
                        target_column=col,
                        parameters=strat,
                        rows_affected=null_count,
                        details=f"Dropped {null_count:,} rows with missing values in '{col}'.",
                    )
                elif method == "mean" and pd.api.types.is_numeric_dtype(working_df[col]):
                    val = float(working_df[col].mean())
                    working_df[col] = working_df[col].fillna(val)
                    values_imputed += null_count
                    record_step(
                        operation="fill_mean",
                        target_column=col,
                        parameters={"computed_mean": round(val, 4)},
                        rows_affected=null_count,
                        details=f"Imputed {null_count:,} missing values in '{col}' with mean ({val:.2f}).",
                    )
                elif method == "median" and pd.api.types.is_numeric_dtype(working_df[col]):
                    val = float(working_df[col].median())
                    working_df[col] = working_df[col].fillna(val)
                    values_imputed += null_count
                    record_step(
                        operation="fill_median",
                        target_column=col,
                        parameters={"computed_median": round(val, 4)},
                        rows_affected=null_count,
                        details=f"Imputed {null_count:,} missing values in '{col}' with median ({val:.2f}).",
                    )
                elif method == "mode":
                    mode_series = working_df[col].mode()
                    if not mode_series.empty:
                        val = mode_series.iloc[0]
                        working_df[col] = working_df[col].fillna(val)
                        values_imputed += null_count
                        record_step(
                            operation="fill_mode",
                            target_column=col,
                            parameters={"computed_mode": str(val)},
                            rows_affected=null_count,
                            details=f"Imputed {null_count:,} missing values in '{col}' with mode ('{val}').",
                        )
                elif method == "constant" and fill_val is not None:
                    working_df[col] = working_df[col].fillna(fill_val)
                    values_imputed += null_count
                    record_step(
                        operation="fill_constant",
                        target_column=col,
                        parameters={"value": fill_val},
                        rows_affected=null_count,
                        details=f"Imputed {null_count:,} missing values in '{col}' with constant '{fill_val}'.",
                    )
                elif method == "ffill":
                    working_df[col] = working_df[col].ffill()
                    values_imputed += null_count
                    record_step(
                        operation="forward_fill",
                        target_column=col,
                        parameters={},
                        rows_affected=null_count,
                        details=f"Forward-filled {null_count:,} missing values in '{col}'.",
                    )
                elif method == "bfill":
                    working_df[col] = working_df[col].bfill()
                    values_imputed += null_count
                    record_step(
                        operation="backward_fill",
                        target_column=col,
                        parameters={},
                        rows_affected=null_count,
                        details=f"Backward-filled {null_count:,} missing values in '{col}'.",
                    )

        # Step 8: Strict Type Conversions (Fix D2: accurately record cell diffs and coerced nulls)
        if type_conversions:
            for col, target_type in type_conversions.items():
                if col not in working_df.columns:
                    continue
                try:
                    before_series = working_df[col].copy()
                    target_lower = target_type.lower()

                    if target_lower in ("int", "int64", "integer"):
                        converted = pd.to_numeric(working_df[col], errors="coerce").astype("Int64")
                    elif target_lower in ("float", "float64"):
                        converted = pd.to_numeric(working_df[col], errors="coerce").astype(float)
                    elif target_lower in ("str", "string"):
                        converted = working_df[col].astype(str)
                    elif target_lower in ("datetime", "date"):
                        converted = pd.to_datetime(working_df[col], errors="coerce")
                    else:
                        continue

                    # Accurate audit measurement
                    newly_nullified = int((before_series.notna() & converted.isna()).sum())
                    changed_cells = int((before_series.astype(str) != converted.astype(str)).sum())

                    working_df[col] = converted

                    if newly_nullified > 0:
                        values_nullified += newly_nullified
                    if changed_cells > newly_nullified:
                        values_fixed += (changed_cells - newly_nullified)

                    record_step(
                        operation="type_conversion",
                        target_column=col,
                        parameters={"target_type": target_type, "coerced_nulls": newly_nullified},
                        rows_affected=changed_cells,
                        details=(
                            f"Casted column '{col}' to strict type '{target_type}' "
                            f"({changed_cells:,} cells modified, {newly_nullified:,} coerced to null)."
                        ),
                    )
                except Exception:
                    pass

        # Capture after statistics and compute delta
        after_stats = self._calc_stats(working_df)
        delta = {
            "rows_removed": before_stats["total_rows"] - after_stats["total_rows"],
            "missing_cells_resolved": before_stats["missing_cells"] - after_stats["missing_cells"],
            "duplicates_removed": duplicates_removed,
            "values_fixed": values_fixed,
            "values_imputed": values_imputed,
            "values_nullified": values_nullified,
            "total_operations": len(steps),
        }

        # Human-readable explanation summary
        explanation = (
            f"Original {before_stats['total_rows']:,} rows → "
            f"removed {duplicates_removed:,} duplicates → "
            f"fixed {values_fixed:,} values → "
            f"imputed {values_imputed:,} missing → "
            f"nullified {values_nullified:,} invalid → "
            f"final {after_stats['total_rows']:,} rows."
        )

        audit = CleaningAuditSummary(
            original_rows=before_stats["total_rows"],
            duplicates_removed=duplicates_removed,
            values_fixed=values_fixed,
            values_imputed=values_imputed,
            values_nullified=values_nullified,
            final_rows=after_stats["total_rows"],
            explanation=explanation,
        )

        return CleaningResult(
            cleaned_df=working_df,
            steps=steps,
            audit=audit,
            before_stats=before_stats,
            after_stats=after_stats,
            delta=delta,
        )

    def _calc_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        rows = len(df)
        cols = len(df.columns)
        total_cells = df.size
        missing = int(df.isna().sum().sum())
        duplicates = int(df.duplicated().sum()) if rows > 0 else 0
        missing_pct = round((missing / total_cells * 100), 2) if total_cells > 0 else 0.0

        return {
            "total_rows": rows,
            "total_columns": cols,
            "total_cells": total_cells,
            "missing_cells": missing,
            "missing_percentage": missing_pct,
            "duplicate_rows": duplicates,
        }
