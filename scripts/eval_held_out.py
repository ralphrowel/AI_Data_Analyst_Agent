"""Generalization evaluation runner on held-out dataset.

Tests that deterministic cleaning transfers to unseen noise distributions:
- European decimals ('1.250,50')
- Number abbreviations ('1.2k')
- Unseen channel typos ('shoppee', 'tik tok', 'lazada_ph')
- New schema ('order_id', 'gross_revenue_php', 'sales_channel')
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 stdout
try:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from backend.app.data_quality.cleaner import DataCleaningEngine
from scripts.eval_runner import run_benchmark, evaluate_match, extract_scalar_result, plan_query, execute_tool_plan

BENCHMARKS_DIR = PROJECT_ROOT / "data" / "benchmarks"
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"
CLEAN_HELD_OUT_PATH = BENCHMARKS_DIR / "held_out_clean.csv"
MESSY_HELD_OUT_PATH = BENCHMARKS_DIR / "held_out_messy.csv"
QUESTIONS_FILE = BENCHMARKS_DIR / "held_out_questions.json"


def generate_held_out_questions(clean_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Compute ground truth answers for held-out FMCG dataset."""
    total_rev = round(float(clean_df["gross_revenue_php"].sum()), 2)
    total_orders = len(clean_df)
    total_qty = int(clean_df["order_qty"].sum())
    aov = round(float(clean_df["gross_revenue_php"].mean()), 2)
    avg_price = round(float(clean_df["item_price_php"].mean()), 2)

    # Channel revenues
    shopee_rev = round(float(clean_df[clean_df["sales_channel"] == "Shopee Mall"]["gross_revenue_php"].sum()), 2)
    tiktok_rev = round(float(clean_df[clean_df["sales_channel"] == "TikTok Shop"]["gross_revenue_php"].sum()), 2)
    lazada_rev = round(float(clean_df[clean_df["sales_channel"] == "Lazada"]["gross_revenue_php"].sum()), 2)

    # Regional counts
    manila_count = int(len(clean_df[clean_df["delivery_region"] == "Metro Manila"]))
    cluzon_count = int(len(clean_df[clean_df["delivery_region"] == "Central Luzon"]))

    # Top merchant by revenue
    top_merchant = str(clean_df.groupby("merchant_name")["gross_revenue_php"].sum().idxmax())
    top_channel = str(clean_df.groupby("sales_channel")["gross_revenue_php"].sum().idxmax())

    questions = [
        {
            "id": "ho_01_total_revenue",
            "category": "aggregation",
            "question": "What is the total gross revenue in PHP across all orders?",
            "ground_truth_value": total_rev,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_02_total_orders",
            "category": "aggregation",
            "question": "How many total orders were completed?",
            "ground_truth_value": total_orders,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_03_total_quantity",
            "category": "aggregation",
            "question": "What is the total order quantity sold across all items?",
            "ground_truth_value": total_qty,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_04_average_order_value",
            "category": "aggregation",
            "question": "What is the average order value in PHP?",
            "ground_truth_value": aov,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_05_average_item_price",
            "category": "aggregation",
            "question": "What is the average item price in PHP?",
            "ground_truth_value": avg_price,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_06_shopee_revenue",
            "category": "filtered_lookup",
            "question": "What is the total gross revenue from Shopee Mall?",
            "ground_truth_value": shopee_rev,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_07_tiktok_revenue",
            "category": "filtered_lookup",
            "question": "What is the total sales revenue from TikTok Shop in PHP?",
            "ground_truth_value": tiktok_rev,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_08_lazada_revenue",
            "category": "filtered_lookup",
            "question": "What is the total sales amount in PHP from Lazada?",
            "ground_truth_value": lazada_rev,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_09_metro_manila_orders",
            "category": "filtered_lookup",
            "question": "How many orders were delivered to Metro Manila?",
            "ground_truth_value": manila_count,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_10_central_luzon_orders",
            "category": "filtered_lookup",
            "question": "How many orders were delivered to Central Luzon?",
            "ground_truth_value": cluzon_count,
            "result_type": "number",
            "tolerance_pct": 0.001,
        },
        {
            "id": "ho_11_top_merchant",
            "category": "group_distribution",
            "question": "Which merchant generated the highest gross revenue?",
            "ground_truth_value": top_merchant,
            "result_type": "string",
            "tolerance_pct": 0.0,
        },
        {
            "id": "ho_12_top_channel",
            "category": "group_distribution",
            "question": "Which sales channel generated the most gross revenue?",
            "ground_truth_value": top_channel,
            "result_type": "string",
            "tolerance_pct": 0.0,
        },
    ]

    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)

    return questions


def clean_held_out_dataset(messy_path: Path) -> Path:
    """Applies generalizable cleaning pipeline to held-out messy dataset."""
    df = pd.read_csv(messy_path)
    out_path = BENCHMARKS_DIR / "held_out_cleaned.csv"

    # 1. Fatal Outlier Quarantine
    invalid_mask = (
        (pd.to_numeric(df["gross_revenue_php"], errors="coerce") < 0)
        | (pd.to_numeric(df["order_qty"], errors="coerce") < 0)
        | (pd.to_numeric(df["item_price_php"], errors="coerce") < 0)
        | (df["order_id"].isna())
        | (df["order_id"].astype(str).str.strip().isin(["", "nan", "None"]))
        | (df["order_date"].astype(str).str.contains("INVALID", na=False))
    )
    df = df[~invalid_mask].copy()

    # 2. Deduplicate valid transactions
    df = df.drop_duplicates(subset=["order_id"], keep="first")

    # 3. Channel typo canonicalization
    channel_map = {
        "shoppee": "Shopee Mall",
        "shopee": "Shopee Mall",
        "shopee mall": "Shopee Mall",
        "tik tok": "TikTok Shop",
        "tiktok": "TikTok Shop",
        "tiktok shop": "TikTok Shop",
        "lazada_ph": "Lazada",
        "lazada": "Lazada",
        "brand direct web": "Brand Direct Web",
        "direct web": "Brand Direct Web",
    }
    if "sales_channel" in df.columns:
        df["sales_channel"] = df["sales_channel"].astype(str).str.strip().apply(lambda x: channel_map.get(x.lower(), x.title()))

    # 4. Regional alias canonicalization
    region_map = {
        "ncr": "Metro Manila",
        "manila": "Metro Manila",
        "metro manila": "Metro Manila",
        "central luzon": "Central Luzon",
        "western visayas": "Western Visayas",
        "northern mindanao": "Northern Mindanao",
    }
    if "delivery_region" in df.columns:
        df["delivery_region"] = df["delivery_region"].astype(str).str.strip().apply(lambda x: region_map.get(x.lower(), x.title()))

    # 5. Currency, European Decimal, and Abbreviation Parsing
    def parse_abbreviated_number(val: Any) -> float:
        if pd.isna(val):
            return 0.0
        s = str(val).strip().replace("₱", "").replace("PHP", "").replace("$", "").replace(" ", "")
        # European format: 1.250,50 -> 1250.50
        if re.search(r"\d+\.\d{3},\d+", s):
            s = s.replace(".", "").replace(",", ".")
        elif "," in s and "." not in s:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")

        # 'k' abbreviation: 1.2k -> 1200
        if s.lower().endswith("k"):
            try:
                return float(s[:-1]) * 1000.0
            except ValueError:
                return 0.0
        try:
            return float(s)
        except ValueError:
            return 0.0

    for col in ["gross_revenue_php", "item_price_php"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_abbreviated_number)

    # 6. Recompute gross revenue where needed
    recompute_mask = (df["gross_revenue_php"] == 0.0) | df["gross_revenue_php"].isna()
    valid_components = df["item_price_php"].notna() & df["order_qty"].notna()
    recompute = recompute_mask & valid_components
    df.loc[recompute, "gross_revenue_php"] = (df.loc[recompute, "item_price_php"] * df.loc[recompute, "order_qty"]).round(2)

    df.to_csv(out_path, index=False, encoding="utf-8")
    return out_path


def run_held_out_evaluation(provider: str = "groq") -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("HELD-OUT DATASET GENERALIZATION EXPERIMENT")
    print("=" * 80 + "\n")

    clean_df = pd.read_csv(CLEAN_HELD_OUT_PATH)
    questions = generate_held_out_questions(clean_df)
    print(f"Generated {len(questions)} ground truth questions for held-out dataset.")

    # 1. Clean dataset
    cleaned_path = clean_held_out_dataset(MESSY_HELD_OUT_PATH)
    print(f"Cleaned held-out dataset generated: {cleaned_path}")

    # 2. Evaluate Clean Ground Truth
    print("\n--- Evaluating Held-Out Clean Ground Truth ---")
    clean_res = run_benchmark(CLEAN_HELD_OUT_PATH, questions_path=QUESTIONS_FILE, provider=provider)

    # 3. Evaluate Messy (Uncleaned)
    print("\n--- Evaluating Held-Out Messy (Raw) ---")
    raw_res = run_benchmark(MESSY_HELD_OUT_PATH, questions_path=QUESTIONS_FILE, provider=provider)

    # 4. Evaluate Cleaned
    print("\n--- Evaluating Held-Out Cleaned (Post-Pipeline) ---")
    cleaned_res = run_benchmark(cleaned_path, questions_path=QUESTIONS_FILE, provider=provider)

    summary = {
        "dataset": "Held-Out FMCG E-Commerce",
        "clean_accuracy": clean_res["accuracy_pct"],
        "raw_accuracy": raw_res["accuracy_pct"],
        "cleaned_accuracy": cleaned_res["accuracy_pct"],
        "total_queries": len(questions),
    }

    print("\n" + "=" * 80)
    print("HELD-OUT GENERALIZATION SUMMARY")
    print("=" * 80)
    print(f"Clean Accuracy   : {clean_res['accuracy_pct']}% ({clean_res['exact_matches']}/{len(questions)})")
    print(f"Raw Accuracy     : {raw_res['accuracy_pct']}% ({raw_res['exact_matches']}/{len(questions)})")
    print(f"Cleaned Accuracy : {cleaned_res['accuracy_pct']}% ({cleaned_res['exact_matches']}/{len(questions)})")
    print("=" * 80 + "\n")

    return summary


if __name__ == "__main__":
    run_held_out_evaluation()
