import pandas as pd
from pathlib import Path

# Manual notes for columns we know are tricky or ambiguous.
# Add to this as you discover more quirks in your data.
COLUMN_NOTES = {
    "duration": (
        "For rows where type='Movie', this is runtime in minutes (e.g. '90 min'). "
        "For rows where type='TV Show', this is number of seasons (e.g. '2 Seasons'), "
        "NOT minutes. These two meanings cannot be averaged together."
    ),
    "date_added": (
        "This is the date the title was added to Netflix, stored as text "
        "(e.g. 'September 25, 2021'), not the release date. "
        "It must be parsed before doing any date comparisons or filtering by year/month."
    ),
    "listed_in": (
        "This column can contain multiple genres in a single cell, separated by commas "
        "(e.g. 'International TV Shows, TV Dramas, TV Mysteries'). "
        "Counting genres requires splitting this column first, not treating each cell as one genre."
    ),
    "release_year": (
        "This is the year the title was originally released, which may be earlier "
        "than the year it was added to Netflix (see date_added)."
    ),
}


def load_data(csv_path: str) -> pd.DataFrame:
    """Load the CSV into a DataFrame."""
    df = pd.read_csv(csv_path)
    return df


def describe_dataframe(df: pd.DataFrame, sample_rows: int = 3) -> str:
    """
    Turn a DataFrame's structure into a text description that Gemini can use
    to understand the data without seeing all of it.
    """
    lines = []
    lines.append(f"Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
    lines.append("")
    lines.append("Columns and data types:")

    for col in df.columns:
        dtype = df[col].dtype
        n_missing = df[col].isna().sum()
        lines.append(f"  - {col} ({dtype}), missing values: {n_missing}")

        # If this column has a known quirk, attach the note right after it.
        if col in COLUMN_NOTES:
            lines.append(f"      NOTE: {COLUMN_NOTES[col]}")

    lines.append("")
    lines.append(f"Sample rows ({sample_rows}):")
    lines.append(df.head(sample_rows).to_string())

    return "\n".join(lines)


if __name__ == "__main__":
    df = load_data("data/netflix_titles.csv")
    description = describe_dataframe(df)
    print(description)