"""Generate synthetic Philippine Retail Dataset (Clean Reference and Injected Dirty Test).

Adheres to Sprint 2 benchmark specification:
- 5,000 clean baseline transactions (exact ground truth)
- Additive noise: +400 duplicates (8%), +100 fatal outliers (2% quarantine targets)
- In-place recoverable modifications: currency strings (10%), categorical drift (12%), unambiguous dates (8%)
- Theoretical accuracy ceiling: 100.0% when properly cleaned and quarantined.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import Dict, List, Tuple
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "data" / "benchmarks"

# Fixed domain taxonomy
REGIONS = ["NCR", "Region IV-A", "Region VII", "Region XI"]
STORES_BY_REGION = {
    "NCR": ["SM Megamall", "SM Mall of Asia", "Greenbelt Makati", "Robinsons Galleria"],
    "Region IV-A": ["SM City Dasmariñas", "Robinsons Place Antipolo", "Southwoods Mall"],
    "Region VII": ["SM City Cebu", "Ayala Center Cebu", "Robinsons Galleria Cebu"],
    "Region XI": ["SM City Davao", "Abreeza Mall Davao", "Gaisano Mall of Davao"],
}

CATALOG = {
    "Electronics": [
        ("Wireless Noise-Canceling Headphones", 3500.00),
        ("Mechanical Gaming Keyboard", 2800.00),
        ("Fast-Charging Power Bank 20000mAh", 1250.00),
        ("4K Ultra HD Action Camera", 6200.00),
        ("USB-C Multiport Adapter Hub", 850.00),
        ("Smart Fitness Tracker Band", 1850.00),
    ],
    "Apparel": [
        ("Men's Tailored Linen Barong", 3200.00),
        ("Women's Casual Oversized Tee", 450.00),
        ("Denim Slim-Fit Stretch Jeans", 1450.00),
        ("Waterproof Hooded Windbreaker", 1850.00),
        ("Breathable Athletic Running Shorts", 650.00),
    ],
    "Groceries": [
        ("Premium Dinorado Rice 5kg", 320.00),
        ("Pure Coconut Cooking Oil 1L", 145.00),
        ("Local Artisan Arabica Coffee Beans 250g", 380.00),
        ("Calamansi Honey Concentrate 500ml", 220.00),
        ("Organic Coconut Sugar 500g", 195.00),
    ],
    "Health & Beauty": [
        ("Daily Defense Broad-Spectrum Sunscreen SPF50", 550.00),
        ("Hydrating Hyaluronic Acid Serum 30ml", 780.00),
        ("Exfoliating Papaya Kojic Soap Bar", 95.00),
        ("Restorative Hair Care Argan Oil 100ml", 420.00),
        ("Herbal Anti-Dandruff Shampoo 400ml", 310.00),
    ],
}

PAYMENT_METHODS = ["GCash", "Maya", "Cash", "Credit Card"]
PAYMENT_WEIGHTS = [0.45, 0.20, 0.20, 0.15]


def generate_clean_dataset(n_rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Generates the clean reference ground-truth dataset."""
    rng = random.Random(seed)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    total_days = (end_date - start_date).days

    records: List[Dict[str, any]] = []

    for i in range(1, n_rows + 1):
        txn_id = f"TXN-2024-{i:05d}"
        random_day = start_date + timedelta(days=rng.randint(0, total_days))
        date_str = random_day.strftime("%Y-%m-%d")

        region = rng.choice(REGIONS)
        store_branch = rng.choice(STORES_BY_REGION[region])
        category = rng.choice(list(CATALOG.keys()))
        item_name, base_price = rng.choice(CATALOG[category])

        # Realistic price jitter (+/- 10%) rounded to nearest 10 PHP
        price_jitter = rng.uniform(0.90, 1.10)
        unit_price = round(base_price * price_jitter, 2)
        quantity = rng.randint(1, 8)
        total_amount = round(unit_price * quantity, 2)
        payment_method = rng.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0]

        records.append(
            {
                "transaction_id": txn_id,
                "date": date_str,
                "region": region,
                "store_branch": store_branch,
                "category": category,
                "item_name": item_name,
                "unit_price_php": unit_price,
                "quantity": quantity,
                "total_amount_php": total_amount,
                "payment_method": payment_method,
            }
        )

    df = pd.DataFrame(records)
    return df


def inject_dirty_errors(clean_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Injects realistic, targeted errors:

    1. Additive Duplicates (+400 rows = +8%)
    2. Additive Fatal Outliers (+100 rows = +2% quarantine targets)
    3. In-Place Currency String Poisoning (500 rows = 10%)
    4. In-Place Categorical Drift & Whitespace (600 rows = 12%)
    5. In-Place Unambiguous Date Format Variations (400 rows = 8%)
    """
    rng = random.Random(seed)
    df = clean_df.copy()
    n_clean = len(df)

    # Cast columns to object dtype so string corruptions can be stored
    df["total_amount_php"] = df["total_amount_php"].astype(object)
    df["unit_price_php"] = df["unit_price_php"].astype(object)
    df["region"] = df["region"].astype(object)
    df["category"] = df["category"].astype(object)
    df["date"] = df["date"].astype(object)
    df["payment_method"] = df["payment_method"].astype(object)

    # -------------------------------------------------------------------------
    # 1. In-Place Injections (Mutating existing clean rows in recoverable ways)
    # -------------------------------------------------------------------------

    # 1a. Currency String Poisoning (500 rows / 10%)
    curr_indices = rng.sample(range(n_clean), 500)
    for idx in curr_indices:
        val = df.at[idx, "total_amount_php"]
        pattern = rng.choice(["peso_symbol", "php_prefix", "comma_formatted", "recomputable_na"])
        if pattern == "peso_symbol":
            df.at[idx, "total_amount_php"] = f"₱ {val:,.2f}"
        elif pattern == "php_prefix":
            df.at[idx, "total_amount_php"] = f"PHP {val:,.2f}"
        elif pattern == "comma_formatted":
            df.at[idx, "total_amount_php"] = f"{val:,.2f}"
        elif pattern == "recomputable_na":
            # Missing total, but unit_price and quantity are preserved so it is 100% recomputable
            df.at[idx, "total_amount_php"] = "N/A"

    # Also poison some unit_price_php with currency strings
    price_indices = rng.sample(range(n_clean), 300)
    for idx in price_indices:
        pval = df.at[idx, "unit_price_php"]
        df.at[idx, "unit_price_php"] = f"₱{pval:,.2f}" if rng.random() > 0.5 else f"{pval:,.2f}"

    # 1b. Categorical Drift & Whitespace (600 rows / 12%)
    cat_indices = rng.sample(range(n_clean), 600)
    for idx in cat_indices:
        drift_type = rng.choice(["whitespace", "lowercase", "alias", "category_case"])
        if drift_type == "whitespace":
            df.at[idx, "region"] = f"  {df.at[idx, 'region']}  "
            df.at[idx, "category"] = f" {df.at[idx, 'category']} "
        elif drift_type == "lowercase":
            df.at[idx, "region"] = df.at[idx, "region"].lower()
            df.at[idx, "payment_method"] = df.at[idx, "payment_method"].lower()
        elif drift_type == "alias":
            # Canonical alias mapping: Metro Manila -> NCR, Cebu City -> Region VII
            if df.at[idx, "region"] == "NCR":
                df.at[idx, "region"] = rng.choice(["Metro Manila", "MetroManila", "manila"])
            elif df.at[idx, "region"] == "Region VII":
                df.at[idx, "region"] = "Central Visayas"
            elif df.at[idx, "region"] == "Region IV-A":
                df.at[idx, "region"] = "CALABARZON"
            elif df.at[idx, "region"] == "Region XI":
                df.at[idx, "region"] = "Davao Region"
        elif drift_type == "category_case":
            df.at[idx, "category"] = df.at[idx, "category"].upper()

    # 1c. Unambiguous Date Format Variations (400 rows / 8%)
    # Uses day > 12 when slashes/dashes are used to avoid day/month ambiguity
    date_indices = rng.sample(range(n_clean), 400)
    for idx in date_indices:
        orig_date = str(df.at[idx, "date"]).strip()
        try:
            dt = datetime.strptime(orig_date, "%Y-%m-%d")
        except ValueError:
            continue

        style = rng.choice(["slash_dd_mm", "text_month", "dash_dd_month_yyyy", "timestamp"])
        if style == "slash_dd_mm":
            # If day <= 12, pick a day > 12 to eliminate ambiguity
            safe_day = dt.day if dt.day > 12 else dt.day + 12
            safe_dt = dt.replace(day=min(safe_day, 28))
            df.at[idx, "date"] = safe_dt.strftime("%d/%m/%Y")
        elif style == "text_month":
            df.at[idx, "date"] = dt.strftime("%d-%b-%Y")  # e.g. 15-Mar-2024
        elif style == "dash_dd_month_yyyy":
            df.at[idx, "date"] = dt.strftime("%B %d, %Y")  # e.g. March 15, 2024
        elif style == "timestamp":
            df.at[idx, "date"] = f"{orig_date} 09:30:00"

    # -------------------------------------------------------------------------
    # 2. Additive Injections (Extra rows added on top of clean baseline)
    # -------------------------------------------------------------------------

    # 2a. Additive Duplicates (400 exact duplicate rows)
    dup_sample_indices = rng.sample(range(n_clean), 400)
    duplicate_rows = df.iloc[dup_sample_indices].copy()

    # 2b. Additive Fatal Outliers / Quarantine Targets (100 rows)
    quarantine_rows = []
    for q_idx in range(1, 101):
        q_type = rng.choice(["negative_price", "negative_qty", "blank_id", "corrupted_text"])
        random_day = datetime(2024, rng.randint(1, 12), rng.randint(1, 28)).strftime("%Y-%m-%d")

        if q_type == "negative_price":
            row = {
                "transaction_id": f"TXN-2024-ERR-{q_idx:04d}",
                "date": random_day,
                "region": "NCR",
                "store_branch": "SM Megamall",
                "category": "Electronics",
                "item_name": "Defective Returned Unit",
                "unit_price_php": -1500.00,
                "quantity": 1,
                "total_amount_php": -1500.00,
                "payment_method": "Cash",
            }
        elif q_type == "negative_qty":
            row = {
                "transaction_id": f"TXN-2024-ERR-{q_idx:04d}",
                "date": random_day,
                "region": "Region VII",
                "store_branch": "SM City Cebu",
                "category": "Apparel",
                "item_name": "Reversed Inventory Adjustment",
                "unit_price_php": 850.00,
                "quantity": -2,
                "total_amount_php": -1700.00,
                "payment_method": "Cash",
            }
        elif q_type == "blank_id":
            row = {
                "transaction_id": "",  # Blank primary key
                "date": random_day,
                "region": "Region XI",
                "store_branch": "SM City Davao",
                "category": "Groceries",
                "item_name": "Unregistered Scan",
                "unit_price_php": 120.00,
                "quantity": 3,
                "total_amount_php": 360.00,
                "payment_method": "Cash",
            }
        else:  # corrupted_text
            row = {
                "transaction_id": f"TXN-2024-ERR-{q_idx:04d}",
                "date": "INVALID_DATE",
                "region": "UNKNOWN_REGION",
                "store_branch": "Corrupted Terminal #99",
                "category": "CORRUPTED",
                "item_name": "###DATA_ERROR###",
                "unit_price_php": "NaN",
                "quantity": 0,
                "total_amount_php": "ERROR",
                "payment_method": "NONE",
            }
        quarantine_rows.append(row)

    quarantine_df = pd.DataFrame(quarantine_rows)

    # Combine: clean mutated base + additive duplicates + additive quarantine rows
    combined_dirty_df = pd.concat([df, duplicate_rows, quarantine_df], ignore_index=True)

    # Shuffle the dirty dataset so errors are distributed throughout
    combined_dirty_df = combined_dirty_df.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    return combined_dirty_df


def main():
    parser = argparse.ArgumentParser(description="Generate Philippine Retail Benchmark Datasets.")
    parser.add_argument("--rows", type=int, default=5000, help="Number of clean baseline rows (default: 5000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    args = parser.parse_args()

    BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Generating clean reference dataset ({args.rows:,} rows, seed={args.seed})...")
    clean_df = generate_clean_dataset(n_rows=args.rows, seed=args.seed)
    clean_path = BENCHMARKS_DIR / "clean_ground_truth.csv"
    clean_df.to_csv(clean_path, index=False, encoding="utf-8")
    print(f"      Saved clean reference: {clean_path} ({clean_path.stat().st_size:,} bytes)")

    print(f"[2/3] Injecting realistic errors (additive duplicates + quarantine outliers + in-place mutations)...")
    dirty_df = inject_dirty_errors(clean_df, seed=args.seed)
    dirty_path = BENCHMARKS_DIR / "dirty_retail_injected.csv"
    dirty_df.to_csv(dirty_path, index=False, encoding="utf-8")
    print(f"      Saved dirty injected dataset: {dirty_path} ({len(dirty_df):,} rows, {dirty_path.stat().st_size:,} bytes)")

    # Print validation summary
    clean_sum = clean_df["total_amount_php"].sum()
    print("\n[3/3] Baseline Validation:")
    print(f"      Clean Total Revenue Ground Truth: PHP {clean_sum:,.2f}")
    print(f"      Clean Transaction Count: {len(clean_df):,}")
    print(f"      Dirty Total Rows: {len(dirty_df):,} (+{len(dirty_df) - len(clean_df):,} additive rows)")
    print("Generation complete.\n")


if __name__ == "__main__":
    main()
