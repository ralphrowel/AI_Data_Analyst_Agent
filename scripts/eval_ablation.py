"""Automated ablation study runner for Visiq Data Quality & Cleaning Engine.

Evaluates how individual cleaning transformations contribute to downstream
LLM analyst answer accuracy. Supports leave-one-out and single-cleaner configs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 stdout on Windows
try:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from backend.app.data_quality.cleaner import DataCleaningEngine
from backend.app.data_quality.service import default_dq_service
from scripts.eval_runner import run_benchmark

BENCHMARKS_DIR = PROJECT_ROOT / "data" / "benchmarks"
DIRTY_DATASET_PATH = BENCHMARKS_DIR / "dirty_retail_injected.csv"
CLEAN_GT_PATH = BENCHMARKS_DIR / "clean_ground_truth.csv"
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"

ABLATION_CONFIGS = [
    {
        "name": "01_raw_dirty_baseline",
        "label": "Raw (No Cleaning)",
        "clean": False,
        "plan": {},
    },
    {
        "name": "02_full_pipeline",
        "label": "Full Cleaning Pipeline",
        "clean": True,
        "plan": {
            "strip_whitespace": True,
            "deduplicate": True,
            "handle_dates": True,
            "handle_categories": True,
            "quarantine_outliers": True,
        },
    },
    {
        "name": "03_no_dedup",
        "label": "Ablation: Without Deduplication",
        "clean": True,
        "plan": {
            "strip_whitespace": True,
            "deduplicate": False,
            "handle_dates": True,
            "handle_categories": True,
            "quarantine_outliers": True,
        },
    },
    {
        "name": "04_no_category_cleaning",
        "label": "Ablation: Without Category Normalization",
        "clean": True,
        "plan": {
            "strip_whitespace": True,
            "deduplicate": True,
            "handle_dates": True,
            "handle_categories": False,
            "quarantine_outliers": True,
        },
    },
    {
        "name": "05_no_date_normalization",
        "label": "Ablation: Without Date Normalization",
        "clean": True,
        "plan": {
            "strip_whitespace": True,
            "deduplicate": True,
            "handle_dates": False,
            "handle_categories": True,
            "quarantine_outliers": True,
        },
    },
    {
        "name": "06_no_quarantine",
        "label": "Ablation: Without Outlier Quarantine",
        "clean": True,
        "plan": {
            "strip_whitespace": True,
            "deduplicate": True,
            "handle_dates": True,
            "handle_categories": True,
            "quarantine_outliers": False,
        },
    },
]


def prepare_ablated_dataset(
    dirty_path: Path,
    config: Dict[str, Any],
    cleaner: DataCleaningEngine,
) -> Path:
    """Prepares or generates the dataset for a specific ablation configuration."""
    if not config["clean"]:
        return dirty_path

    out_path = BENCHMARKS_DIR / f"ablated_{config['name']}.csv"
    dirty_df = pd.read_csv(dirty_path)

    plan = config["plan"]

    # Basic cleaning transformations based on flags
    df = dirty_df.copy()

    # 1. Outlier quarantine (Run first so invalid/blank rows are quarantined)
    if plan.get("quarantine_outliers", True):
        invalid_mask = (
            (pd.to_numeric(df["total_amount_php"], errors="coerce") < 0)
            | (pd.to_numeric(df["quantity"], errors="coerce") < 0)
            | (pd.to_numeric(df["unit_price_php"], errors="coerce") < 0)
            | (df["transaction_id"].isna())
            | (df["transaction_id"].astype(str).str.strip().isin(["", "nan", "None"]))
            | (df["date"].astype(str).str.contains("INVALID", na=False))
        )
        df = df[~invalid_mask].copy()

    # 2. Deduplication (Run on remaining valid transactions)
    if plan.get("deduplicate", True):
        if "transaction_id" in df.columns:
            df = df.drop_duplicates(subset=["transaction_id"], keep="first")
        else:
            df = df.drop_duplicates(keep="first")

    # 3. Categorical normalization
    if plan.get("handle_categories", True):
        for col in ["region", "category", "store_branch", "payment_method"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # Regional alias mapping
                if col == "region":
                    alias_map = {
                        "metro manila": "NCR",
                        "metromanila": "NCR",
                        "manila": "NCR",
                        "ncr": "NCR",
                        "central visayas": "Region VII",
                        "region vii": "Region VII",
                        "calabarzon": "Region IV-A",
                        "region iv-a": "Region IV-A",
                        "davao region": "Region XI",
                        "region xi": "Region XI",
                    }
                    df[col] = df[col].apply(lambda x: alias_map.get(x.lower(), x))
                # Title casing for payment methods and categories
                if col == "payment_method":
                    pm_map = {"gcash": "GCash", "maya": "Maya", "cash": "Cash", "credit card": "Credit Card"}
                    df[col] = df[col].apply(lambda x: pm_map.get(x.lower(), x.title()))
                if col == "category":
                    cat_map = {"electronics": "Electronics", "groceries": "Groceries", "apparel": "Apparel", "health & beauty": "Health & Beauty"}
                    df[col] = df[col].apply(lambda x: cat_map.get(x.lower(), x.title()))

    # 4. Date normalization (uses mixed format to parse DD/MM/YYYY, ISO, timestamps without losing rows)
    if plan.get("handle_dates", True) and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed").dt.strftime("%Y-%m-%d")

    # 5. Currency & numeric parsing
    for col in ["total_amount_php", "unit_price_php"]:
        if col in df.columns:
            s = df[col].astype(str).str.replace("₱", "", regex=False).str.replace("PHP", "", regex=False).str.replace(",", "", regex=False).str.strip()
            df[col] = pd.to_numeric(s, errors="coerce")

    # If total_amount_php is NaN, recompute from unit_price * quantity
    if "total_amount_php" in df.columns and "unit_price_php" in df.columns and "quantity" in df.columns:
        recompute_mask = df["total_amount_php"].isna() & df["unit_price_php"].notna() & df["quantity"].notna()
        df.loc[recompute_mask, "total_amount_php"] = (df.loc[recompute_mask, "unit_price_php"] * df.loc[recompute_mask, "quantity"]).round(2)

    df.to_csv(out_path, index=False, encoding="utf-8")
    return out_path


def run_ablation_study(
    dirty_path: Path = DIRTY_DATASET_PATH,
    provider: str = "groq",
    limit: Optional[int] = None,
) -> pd.DataFrame:
    cleaner = DataCleaningEngine()
    results_summary = []

    print(f"\n================================================================================")
    print(f"RUNNING PER-CLEANER ABLATION STUDY")
    print(f"Configs: {len(ABLATION_CONFIGS)} | Provider: {provider}")
    print(f"================================================================================\n")

    for i, cfg in enumerate(ABLATION_CONFIGS, 1):
        print(f"\n[{i}/{len(ABLATION_CONFIGS)}] Preparing configuration: {cfg['label']}...")
        eval_csv = prepare_ablated_dataset(dirty_path, cfg, cleaner)

        bench_result = run_benchmark(
            dataset_path=eval_csv,
            provider=provider,
            use_cache=True,
            limit=limit,
        )

        results_summary.append(
            {
                "Config": cfg["name"],
                "Description": cfg["label"],
                "Total Queries": bench_result["total_queries"],
                "Crashes": bench_result["execution_crashes"],
                "Crash Rate (%)": bench_result["crash_rate_pct"],
                "Correct Answers": bench_result["exact_matches"],
                "Accuracy (%)": bench_result["accuracy_pct"],
            }
        )

    summary_df = pd.DataFrame(results_summary)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = RESULTS_DIR / "ablation_summary.csv"
    summary_df.to_csv(out_csv, index=False)

    print(f"\n================================================================================")
    print(f"ABLATION STUDY SUMMARY")
    print(f"================================================================================")
    print(summary_df.to_string(index=False))
    print(f"\nSummary table saved to: {out_csv}\n")

    return summary_df


def main():
    parser = argparse.ArgumentParser(description="Run Data Cleaning Ablation Experiments.")
    parser.add_argument("--dirty-dataset", type=str, default=str(DIRTY_DATASET_PATH))
    parser.add_argument("--provider", type=str, default="groq")
    parser.add_argument("--limit", type=int, default=None, help="Limit questions per configuration")
    args = parser.parse_args()

    run_ablation_study(
        dirty_path=Path(args.dirty_dataset),
        provider=args.provider,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
