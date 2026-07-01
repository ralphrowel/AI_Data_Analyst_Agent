import pandas as pd


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df


def describe_dataframe(df: pd.DataFrame, sample_rows: int = 3) -> str:
    lines = []
    lines.append(f"Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
    lines.append("")
    lines.append("Columns and data types:")

    for col in df.columns:
        dtype = df[col].dtype
        n_missing = df[col].isna().sum()
        lines.append(f"  - {col} ({dtype}), missing values: {n_missing}")

    lines.append("")
    lines.append(f"Sample rows ({sample_rows}):")
    lines.append(df.head(sample_rows).to_string())

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/netflix_titles.csv"
    df = load_data(path)
    print(describe_dataframe(df))
