"""Generate independent held-out dataset to evaluate generalization without circularity.

Uses distinct column naming, product categories, and unseen noise patterns:
- Abbreviated numbers ("₱1.2k", "3.5K")
- European decimal notation ("1.250,50")
- Unseen channel/merchant typos ("shoppee", "lazada_ph", "tik tok")
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import Dict, List
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "data" / "benchmarks"

CHANNELS = ["Shopee Mall", "Lazada", "TikTok Shop", "Brand Direct Web"]
MERCHANTS = ["Unilever Official", "P&G Beauty", "Nestle Nutrition", "Century Pacific", "Monde Nissin"]
REGIONS = ["Metro Manila", "Central Luzon", "Western Visayas", "Northern Mindanao"]

PRODUCTS = [
    ("Oat Milk Barista Blend 1L", 185.00),
    ("Canned Tuna Flakes in Oil 180g", 42.00),
    ("Instant Roasted White Coffee 30g x 10s", 125.00),
    ("Gentle Micellar Cleansing Water 400ml", 340.00),
    ("Ultra Soft Bamboo Toilet Tissue 12 Rolls", 295.00),
    ("Disinfectant Surface Spray 500ml", 210.00),
]


def generate_held_out_clean(n_rows: int = 2500, seed: int = 101) -> pd.DataFrame:
    rng = random.Random(seed)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    total_days = (end_date - start_date).days

    records: List[Dict[str, any]] = []

    for i in range(1, n_rows + 1):
        order_id = f"ORD-FMCG-{i:05d}"
        random_day = start_date + timedelta(days=rng.randint(0, total_days))
        date_str = random_day.strftime("%Y-%m-%d")

        channel = rng.choice(CHANNELS)
        merchant = rng.choice(MERCHANTS)
        region = rng.choice(REGIONS)
        item_title, base_price = rng.choice(PRODUCTS)

        unit_price = round(base_price * rng.uniform(0.95, 1.05), 2)
        qty = rng.randint(1, 12)
        gross_rev = round(unit_price * qty, 2)

        records.append(
            {
                "order_id": order_id,
                "order_date": date_str,
                "delivery_region": region,
                "merchant_name": merchant,
                "product_title": item_title,
                "item_price_php": unit_price,
                "order_qty": qty,
                "gross_revenue_php": gross_rev,
                "sales_channel": channel,
            }
        )

    return pd.DataFrame(records)


def inject_held_out_noise(clean_df: pd.DataFrame, seed: int = 101) -> pd.DataFrame:
    rng = random.Random(seed)
    df = clean_df.copy()
    n_clean = len(df)

    # Cast to object
    df["gross_revenue_php"] = df["gross_revenue_php"].astype(object)
    df["item_price_php"] = df["item_price_php"].astype(object)
    df["sales_channel"] = df["sales_channel"].astype(object)
    df["delivery_region"] = df["delivery_region"].astype(object)

    # 1. Unseen abbreviation noise: "₱1.2k" or "2.5K" (150 rows)
    abbrev_indices = rng.sample(range(n_clean), 150)
    for idx in abbrev_indices:
        val = clean_df.at[idx, "gross_revenue_php"]
        if val >= 1000:
            df.at[idx, "gross_revenue_php"] = f"₱{val/1000:.1f}k" if rng.random() > 0.5 else f"{val/1000:.1f}K"

    # 2. European decimal comma notation: "1.250,50" (150 rows)
    euro_indices = rng.sample(range(n_clean), 150)
    for idx in euro_indices:
        val = clean_df.at[idx, "gross_revenue_php"]
        formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        df.at[idx, "gross_revenue_php"] = formatted

    # 3. Channel typos: "shoppee", "lazada_ph", "tik tok" (200 rows)
    channel_indices = rng.sample(range(n_clean), 200)
    for idx in channel_indices:
        ch = str(df.at[idx, "sales_channel"])
        if "Shopee" in ch:
            df.at[idx, "sales_channel"] = rng.choice(["shoppee", "Shopeee Mall", "shopee_app"])
        elif "Lazada" in ch:
            df.at[idx, "sales_channel"] = rng.choice(["lazada_ph", "LAZADA", "laz mall"])
        elif "TikTok" in ch:
            df.at[idx, "sales_channel"] = rng.choice(["tik tok", "tiktok_shop", "TT Shop"])

    # 4. Additive Duplicates (+200 rows = +8%)
    dup_sample = df.iloc[rng.sample(range(n_clean), 200)].copy()

    # 5. Additive Fatal Outliers (+50 rows = +2% quarantine)
    fatal_rows = []
    for f_idx in range(1, 51):
        fatal_rows.append(
            {
                "order_id": f"ORD-ERR-{f_idx:04d}",
                "order_date": "2024-05-15",
                "delivery_region": "Metro Manila",
                "merchant_name": "Unregistered Merchant",
                "product_title": "Cancelled Pre-Order",
                "item_price_php": -250.00,
                "order_qty": -1,
                "gross_revenue_php": -250.00,
                "sales_channel": "Direct",
            }
        )
    fatal_df = pd.DataFrame(fatal_rows)

    combined_df = pd.concat([df, dup_sample, fatal_df], ignore_index=True)
    return combined_df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Generate Independent Held-Out FMCG Dataset.")
    parser.add_argument("--rows", type=int, default=2500, help="Clean rows (default: 2500)")
    parser.add_argument("--seed", type=int, default=101, help="Seed (default: 101)")
    args = parser.parse_args()

    BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[1/2] Generating held-out clean baseline ({args.rows:,} rows)...")
    clean_df = generate_held_out_clean(n_rows=args.rows, seed=args.seed)
    clean_path = BENCHMARKS_DIR / "held_out_clean.csv"
    clean_df.to_csv(clean_path, index=False, encoding="utf-8")

    print(f"[2/2] Injecting unseen noise (abbreviations, European decimals, channel typos)...")
    messy_df = inject_held_out_noise(clean_df, seed=args.seed)
    messy_path = BENCHMARKS_DIR / "held_out_messy.csv"
    messy_df.to_csv(messy_path, index=False, encoding="utf-8")

    print(f"      Saved: {clean_path} ({len(clean_df):,} rows)")
    print(f"      Saved: {messy_path} ({len(messy_df):,} rows)")
    print(f"      Ground Truth Revenue: PHP {clean_df['gross_revenue_php'].sum():,.2f}")
    print("Held-out generation complete.\n")


if __name__ == "__main__":
    main()
