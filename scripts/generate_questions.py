"""Programmatically generate 52 benchmark evaluation questions with ground-truth answers.

All expected values are computed directly via Pandas from clean_ground_truth.csv.
No manual placeholder numbers.
Strict relative tolerance of 0.1% (0.001).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DATASET_PATH = PROJECT_ROOT / "data" / "benchmarks" / "clean_ground_truth.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "benchmarks" / "questions_benchmark.json"


def generate_benchmark_suite() -> List[Dict[str, Any]]:
    if not CLEAN_DATASET_PATH.exists():
        raise FileNotFoundError(f"Clean reference dataset not found at {CLEAN_DATASET_PATH}")

    df = pd.read_csv(CLEAN_DATASET_PATH)
    df["date"] = pd.to_datetime(df["date"])

    questions: List[Dict[str, Any]] = []

    def add_q(
        q_id: str,
        category: str,
        question: str,
        target_tool: str,
        ground_truth: Any,
        vulnerability: str,
        result_type: str = "number",
        tolerance_pct: float = 0.001,
    ):
        questions.append(
            {
                "id": q_id,
                "category": category,
                "question": question,
                "target_tool": target_tool,
                "ground_truth_value": ground_truth,
                "result_type": result_type,
                "tolerance_pct": tolerance_pct,
                "error_vulnerability": vulnerability,
            }
        )

    # =========================================================================
    # 1. Aggregations (15 questions)
    # Vulnerabilities: Duplicates (inflates sum/count), Currency Strings (type errors)
    # =========================================================================
    add_q(
        "agg_01_total_revenue",
        "aggregation",
        "What is the total sales amount in PHP across all transactions?",
        "aggregate_data",
        round(float(df["total_amount_php"].sum()), 2),
        "duplicates_and_currency_strings",
    )
    add_q(
        "agg_02_transaction_count",
        "aggregation",
        "How many total transactions are recorded in the dataset?",
        "aggregate_data",
        int(len(df)),
        "duplicates_and_quarantine_rows",
    )
    add_q(
        "agg_03_total_quantity",
        "aggregation",
        "What is the total quantity of all items sold?",
        "aggregate_data",
        int(df["quantity"].sum()),
        "duplicates_and_fatal_outliers",
    )
    add_q(
        "agg_04_average_order_value",
        "aggregation",
        "What is the average transaction total amount in PHP?",
        "aggregate_data",
        round(float(df["total_amount_php"].mean()), 2),
        "currency_strings_and_fatal_outliers",
    )
    add_q(
        "agg_05_average_unit_price",
        "aggregation",
        "What is the average unit price across all products sold?",
        "aggregate_data",
        round(float(df["unit_price_php"].mean()), 2),
        "currency_strings_and_negative_prices",
    )
    add_q(
        "agg_06_max_unit_price",
        "aggregation",
        "What is the maximum unit price of any item sold in the dataset?",
        "aggregate_data",
        round(float(df["unit_price_php"].max()), 2),
        "currency_strings",
    )
    add_q(
        "agg_07_min_unit_price",
        "aggregation",
        "What is the minimum unit price of any item sold in the dataset?",
        "aggregate_data",
        round(float(df["unit_price_php"].min()), 2),
        "negative_outlier_prices",
    )
    add_q(
        "agg_08_average_quantity",
        "aggregation",
        "What is the average quantity of items purchased per transaction?",
        "aggregate_data",
        round(float(df["quantity"].mean()), 2),
        "negative_quantities_and_duplicates",
    )
    add_q(
        "agg_09_total_gcash_revenue",
        "aggregation",
        "What is the total sales amount in PHP for payments made via GCash?",
        "aggregate_data",
        round(float(df[df["payment_method"] == "GCash"]["total_amount_php"].sum()), 2),
        "payment_method_lowercase_and_currency_strings",
    )
    add_q(
        "agg_10_total_maya_revenue",
        "aggregation",
        "What is the total sales amount in PHP for transactions paid using Maya?",
        "aggregate_data",
        round(float(df[df["payment_method"] == "Maya"]["total_amount_php"].sum()), 2),
        "payment_method_casing_and_currency_strings",
    )
    add_q(
        "agg_11_total_cash_revenue",
        "aggregation",
        "What is the total sales amount in PHP for cash transactions?",
        "aggregate_data",
        round(float(df[df["payment_method"] == "Cash"]["total_amount_php"].sum()), 2),
        "payment_method_casing_and_currency_strings",
    )
    add_q(
        "agg_12_total_credit_card_revenue",
        "aggregation",
        "What is the total sales amount in PHP for credit card transactions?",
        "aggregate_data",
        round(float(df[df["payment_method"] == "Credit Card"]["total_amount_php"].sum()), 2),
        "payment_method_casing_and_currency_strings",
    )
    add_q(
        "agg_13_max_transaction_total",
        "aggregation",
        "What is the highest single transaction total amount in PHP?",
        "aggregate_data",
        round(float(df["total_amount_php"].max()), 2),
        "currency_strings",
    )
    add_q(
        "agg_14_min_transaction_total",
        "aggregation",
        "What is the lowest valid single transaction total amount in PHP?",
        "aggregate_data",
        round(float(df["total_amount_php"].min()), 2),
        "negative_amount_fatal_outliers",
    )
    add_q(
        "agg_15_total_electronics_revenue",
        "aggregation",
        "What is the total sales amount in PHP for the Electronics category?",
        "aggregate_data",
        round(float(df[df["category"] == "Electronics"]["total_amount_php"].sum()), 2),
        "category_whitespace_and_currency_strings",
    )

    # =========================================================================
    # 2. Filtered Lookups (15 questions)
    # Vulnerabilities: Categorical drift, whitespace, regional aliases
    # =========================================================================
    add_q(
        "filt_01_ncr_transaction_count",
        "filtered_lookup",
        "How many transactions were completed in the NCR region?",
        "filter_rows",
        int(len(df[df["region"] == "NCR"])),
        "regional_alias_and_casing",
    )
    add_q(
        "filt_02_ncr_total_revenue",
        "filtered_lookup",
        "What is the total sales amount in PHP for the NCR region?",
        "filter_rows",
        round(float(df[df["region"] == "NCR"]["total_amount_php"].sum()), 2),
        "regional_alias_and_currency_strings",
    )
    add_q(
        "filt_03_region_vii_count",
        "filtered_lookup",
        "How many transactions occurred in Region VII?",
        "filter_rows",
        int(len(df[df["region"] == "Region VII"])),
        "regional_alias_central_visayas",
    )
    add_q(
        "filt_04_region_vii_revenue",
        "filtered_lookup",
        "What is the total revenue in PHP generated in Region VII?",
        "filter_rows",
        round(float(df[df["region"] == "Region VII"]["total_amount_php"].sum()), 2),
        "regional_alias_and_currency_strings",
    )
    add_q(
        "filt_05_region_iv_a_count",
        "filtered_lookup",
        "How many transactions were recorded in Region IV-A?",
        "filter_rows",
        int(len(df[df["region"] == "Region IV-A"])),
        "regional_alias_calabarzon",
    )
    add_q(
        "filt_06_region_xi_count",
        "filtered_lookup",
        "How many transactions were recorded in Region XI?",
        "filter_rows",
        int(len(df[df["region"] == "Region XI"])),
        "regional_alias_davao_region",
    )
    add_q(
        "filt_07_sm_megamall_count",
        "filtered_lookup",
        "How many transactions occurred at the SM Megamall store branch?",
        "filter_rows",
        int(len(df[df["store_branch"] == "SM Megamall"])),
        "store_name_whitespace",
    )
    add_q(
        "filt_08_sm_megamall_revenue",
        "filtered_lookup",
        "What is the total sales revenue in PHP at SM Megamall?",
        "filter_rows",
        round(float(df[df["store_branch"] == "SM Megamall"]["total_amount_php"].sum()), 2),
        "store_whitespace_and_currency_strings",
    )
    add_q(
        "filt_09_ayala_center_cebu_count",
        "filtered_lookup",
        "How many transactions were logged at Ayala Center Cebu?",
        "filter_rows",
        int(len(df[df["store_branch"] == "Ayala Center Cebu"])),
        "store_branch_drift",
    )
    add_q(
        "filt_10_apparel_transaction_count",
        "filtered_lookup",
        "How many transactions belong to the Apparel category?",
        "filter_rows",
        int(len(df[df["category"] == "Apparel"])),
        "category_casing_and_whitespace",
    )
    add_q(
        "filt_11_groceries_transaction_count",
        "filtered_lookup",
        "How many transactions belong to the Groceries category?",
        "filter_rows",
        int(len(df[df["category"] == "Groceries"])),
        "category_casing_and_whitespace",
    )
    add_q(
        "filt_12_health_beauty_count",
        "filtered_lookup",
        "How many transactions are in the Health & Beauty category?",
        "filter_rows",
        int(len(df[df["category"] == "Health & Beauty"])),
        "category_whitespace_and_ampersand",
    )
    add_q(
        "filt_13_high_value_transactions",
        "filtered_lookup",
        "How many transactions have a total amount greater than 20000 PHP?",
        "filter_rows",
        int(len(df[df["total_amount_php"] > 20000])),
        "currency_strings_preventing_gt_filter",
    )
    add_q(
        "filt_14_single_item_orders",
        "filtered_lookup",
        "How many transactions had a quantity of exactly 1 item?",
        "filter_rows",
        int(len(df[df["quantity"] == 1])),
        "duplicates_and_fatal_outliers",
    )
    add_q(
        "filt_15_bulk_orders",
        "filtered_lookup",
        "How many transactions had a quantity of 5 or more items?",
        "filter_rows",
        int(len(df[df["quantity"] >= 5])),
        "duplicates_and_negative_quantities",
    )

    # =========================================================================
    # 3. Group-By & Distributions (12 questions)
    # Vulnerabilities: Categorical fragmentation splitting single categories into multiple buckets
    # =========================================================================
    top_cat = df.groupby("category")["total_amount_php"].sum().idxmax()
    add_q(
        "grp_01_top_category_by_revenue",
        "group_distribution",
        "Which product category generated the highest total sales revenue?",
        "group_data",
        top_cat,
        "category_fragmentation_and_currency_strings",
        result_type="string",
    )
    top_reg = df.groupby("region")["total_amount_php"].sum().idxmax()
    add_q(
        "grp_02_top_region_by_revenue",
        "group_distribution",
        "Which region generated the highest total sales amount in PHP?",
        "group_data",
        top_reg,
        "regional_alias_fragmentation",
        result_type="string",
    )
    top_pay = df["payment_method"].value_counts().idxmax()
    add_q(
        "grp_03_most_frequent_payment_method",
        "group_distribution",
        "What is the most frequently used payment method by transaction count?",
        "group_data",
        top_pay,
        "payment_method_lowercase_fragmentation",
        result_type="string",
    )
    top_store = df.groupby("store_branch")["total_amount_php"].sum().idxmax()
    add_q(
        "grp_04_top_store_by_revenue",
        "group_distribution",
        "Which store branch generated the highest total revenue in PHP?",
        "group_data",
        top_store,
        "store_name_whitespace_fragmentation",
        result_type="string",
    )
    apparel_rev = round(float(df[df["category"] == "Apparel"]["total_amount_php"].sum()), 2)
    add_q(
        "grp_05_apparel_total_revenue",
        "group_distribution",
        "What is the total sales amount in PHP for Apparel?",
        "group_data",
        apparel_rev,
        "category_casing_and_currency_strings",
    )
    groceries_rev = round(float(df[df["category"] == "Groceries"]["total_amount_php"].sum()), 2)
    add_q(
        "grp_06_groceries_total_revenue",
        "group_distribution",
        "What is the total sales amount in PHP for Groceries?",
        "group_data",
        groceries_rev,
        "category_casing_and_currency_strings",
    )
    hb_rev = round(float(df[df["category"] == "Health & Beauty"]["total_amount_php"].sum()), 2)
    add_q(
        "grp_07_health_beauty_total_revenue",
        "group_distribution",
        "What is the total sales amount in PHP for Health & Beauty?",
        "group_data",
        hb_rev,
        "category_whitespace_and_currency_strings",
    )
    reg_iv_a_rev = round(float(df[df["region"] == "Region IV-A"]["total_amount_php"].sum()), 2)
    add_q(
        "grp_08_region_iv_a_total_revenue",
        "group_distribution",
        "What is the total sales revenue in PHP for Region IV-A?",
        "group_data",
        reg_iv_a_rev,
        "regional_alias_calabarzon",
    )
    reg_xi_rev = round(float(df[df["region"] == "Region XI"]["total_amount_php"].sum()), 2)
    add_q(
        "grp_09_region_xi_total_revenue",
        "group_distribution",
        "What is the total sales revenue in PHP for Region XI?",
        "group_data",
        reg_xi_rev,
        "regional_alias_davao_region",
    )
    least_pay = df["payment_method"].value_counts().idxmin()
    add_q(
        "grp_10_least_frequent_payment_method",
        "group_distribution",
        "What is the least common payment method by transaction count?",
        "group_data",
        least_pay,
        "payment_method_casing_fragmentation",
        result_type="string",
    )
    lowest_rev_cat = df.groupby("category")["total_amount_php"].sum().idxmin()
    add_q(
        "grp_11_lowest_revenue_category",
        "group_distribution",
        "Which product category generated the lowest total sales amount?",
        "group_data",
        lowest_rev_cat,
        "category_casing_fragmentation",
        result_type="string",
    )
    lowest_rev_reg = df.groupby("region")["total_amount_php"].sum().idxmin()
    add_q(
        "grp_12_lowest_revenue_region",
        "group_distribution",
        "Which region had the lowest total sales revenue in PHP?",
        "group_data",
        lowest_rev_reg,
        "regional_alias_fragmentation",
        result_type="string",
    )

    # =========================================================================
    # 4. Temporal Trends (10 questions)
    # Vulnerabilities: Date format inconsistencies, string slashes vs dashes
    # =========================================================================
    q1_mask = (df["date"] >= "2024-01-01") & (df["date"] <= "2024-03-31")
    add_q(
        "temp_01_q1_revenue",
        "temporal_trend",
        "What is the total sales amount in PHP for Q1 2024 (January to March)?",
        "filter_rows",
        round(float(df[q1_mask]["total_amount_php"].sum()), 2),
        "date_formatting_inconsistency",
    )
    q2_mask = (df["date"] >= "2024-04-01") & (df["date"] <= "2024-06-30")
    add_q(
        "temp_02_q2_revenue",
        "temporal_trend",
        "What is the total sales amount in PHP for Q2 2024 (April to June)?",
        "filter_rows",
        round(float(df[q2_mask]["total_amount_php"].sum()), 2),
        "date_formatting_inconsistency",
    )
    q3_mask = (df["date"] >= "2024-07-01") & (df["date"] <= "2024-09-30")
    add_q(
        "temp_03_q3_revenue",
        "temporal_trend",
        "What is the total sales amount in PHP for Q3 2024 (July to September)?",
        "filter_rows",
        round(float(df[q3_mask]["total_amount_php"].sum()), 2),
        "date_formatting_inconsistency",
    )
    q4_mask = (df["date"] >= "2024-10-01") & (df["date"] <= "2024-12-31")
    add_q(
        "temp_04_q4_revenue",
        "temporal_trend",
        "What is the total sales amount in PHP for Q4 2024 (October to December)?",
        "filter_rows",
        round(float(df[q4_mask]["total_amount_php"].sum()), 2),
        "date_formatting_inconsistency",
    )
    dec_mask = (df["date"] >= "2024-12-01") & (df["date"] <= "2024-12-31")
    add_q(
        "temp_05_december_revenue",
        "temporal_trend",
        "What is the total sales amount in PHP in the month of December 2024?",
        "filter_rows",
        round(float(df[dec_mask]["total_amount_php"].sum()), 2),
        "date_formatting_inconsistency",
    )
    dec_count = int(len(df[dec_mask]))
    add_q(
        "temp_06_december_transactions",
        "temporal_trend",
        "How many transactions were recorded in December 2024?",
        "filter_rows",
        dec_count,
        "date_formatting_and_duplicates",
    )
    jan_mask = (df["date"] >= "2024-01-01") & (df["date"] <= "2024-01-31")
    add_q(
        "temp_07_january_revenue",
        "temporal_trend",
        "What is the total sales amount in PHP in the month of January 2024?",
        "filter_rows",
        round(float(df[jan_mask]["total_amount_php"].sum()), 2),
        "date_formatting_inconsistency",
    )
    h1_mask = (df["date"] >= "2024-01-01") & (df["date"] <= "2024-06-30")
    add_q(
        "temp_08_first_half_revenue",
        "temporal_trend",
        "What is the total sales amount in PHP for the first half of 2024 (H1)?",
        "filter_rows",
        round(float(df[h1_mask]["total_amount_php"].sum()), 2),
        "date_formatting_inconsistency",
    )
    h2_mask = (df["date"] >= "2024-07-01") & (df["date"] <= "2024-12-31")
    add_q(
        "temp_09_second_half_revenue",
        "temporal_trend",
        "What is the total sales amount in PHP for the second half of 2024 (H2)?",
        "filter_rows",
        round(float(df[h2_mask]["total_amount_php"].sum()), 2),
        "date_formatting_inconsistency",
    )
    h1_count = int(len(df[h1_mask]))
    add_q(
        "temp_10_first_half_transactions",
        "temporal_trend",
        "How many total transactions were completed during the first half of 2024?",
        "filter_rows",
        h1_count,
        "date_formatting_and_duplicates",
    )

    return questions


def main():
    print("[1/2] Computing exact ground-truth values via Pandas on clean reference dataset...")
    questions = generate_benchmark_suite()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)

    print(f"[2/2] Generated and saved {len(questions)} verified questions to {OUTPUT_PATH}")

    # Summary by category
    cats = {}
    for q in questions:
        cats[q["category"]] = cats.get(q["category"], 0) + 1

    print("\nBenchmark Composition:")
    for cat, count in cats.items():
        print(f"  - {cat:20s}: {count:2d} questions")
    print(f"Total: {len(questions)} benchmark questions ready for evaluation.\n")


if __name__ == "__main__":
    main()
