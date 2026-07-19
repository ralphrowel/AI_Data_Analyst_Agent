import pandas as pd


def _parse_minutes(dur):
    try:
        if pd.notna(dur) and "min" in str(dur):
            return int(str(dur).replace(" min", "").strip())
    except (ValueError, AttributeError):
        pass
    return pd.NA


def _parse_seasons(dur):
    try:
        if pd.notna(dur) and "Season" in str(dur):
            return int(str(dur).replace(" Seasons", "").replace(" Season", "").strip())
    except (ValueError, AttributeError):
        pass
    return pd.NA


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    df["duration_minutes"] = df.apply(
        lambda row: _parse_minutes(row["duration"]) if row["type"] == "Movie" else pd.NA,
        axis=1,
    ).astype("Int64")

    df["duration_seasons"] = df.apply(
        lambda row: _parse_seasons(row["duration"]) if row["type"] == "TV Show" else pd.NA,
        axis=1,
    ).astype("Int64")

    return df


COLUMN_NOTES = """
COLUMN_NOTES (numeric column guidance):
  - duration_minutes: integer column for Movie rows only. Use this for movie-length questions (e.g. "longest movie", "average movie duration").
  - duration_seasons: integer column for TV Show rows only. Use this for season-count questions (e.g. "most seasons", "shows with more than 3 seasons").
  - original duration column is a string - do NOT use it for numeric comparisons or aggregations.
"""


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

    lines.append(COLUMN_NOTES)

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/netflix_titles.csv"
    df = load_data(path)
    print(describe_dataframe(df))
