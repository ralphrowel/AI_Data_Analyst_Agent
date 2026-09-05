from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from backend.app.config import RAW_DATA_DIR, DEFAULT_DATASET_PATH
from backend.app.data_engine.loader import load_data, describe_dataframe


class DatasetManager:
    """Discovers, caches, and provides access to raw datasets."""

    def __init__(self, raw_data_dir: Path = RAW_DATA_DIR):
        self.raw_data_dir = raw_data_dir
        self._cache: Dict[str, pd.DataFrame] = {}
        self._desc_cache: Dict[str, str] = {}

    def list_datasets(self) -> List[dict]:
        """List all available CSV datasets in the raw data directory."""
        datasets = []
        if not self.raw_data_dir.exists():
            return datasets

        for file_path in sorted(self.raw_data_dir.glob("*.csv")):
            try:
                stat = file_path.stat()
                df = self.get_dataset(file_path.name)
                datasets.append({
                    "name": file_path.name,
                    "rows": int(len(df)),
                    "columns": int(len(df.columns)),
                    "size_bytes": int(stat.st_size),
                })
            except Exception as e:
                # Fallback to basic file info if reading fails
                stat = file_path.stat()
                datasets.append({
                    "name": file_path.name,
                    "rows": 0,
                    "columns": 0,
                    "size_bytes": int(stat.st_size),
                })
        return datasets

    def get_dataset(self, name: Optional[str] = None) -> pd.DataFrame:
        """Get or load a DataFrame by its filename."""
        if not name:
            name = DEFAULT_DATASET_PATH.name

        if name not in self._cache:
            file_path = self.raw_data_dir / name
            if not file_path.exists():
                # Fall back to default if file not found
                file_path = DEFAULT_DATASET_PATH
                name = DEFAULT_DATASET_PATH.name

            df = load_data(file_path)
            self._cache[name] = df
            self._desc_cache[name] = describe_dataframe(df)

        return self._cache[name]

    def get_dataset_description(self, name: Optional[str] = None) -> str:
        """Get the cached string description of the dataset."""
        if not name:
            name = DEFAULT_DATASET_PATH.name
        if name not in self._desc_cache:
            self.get_dataset(name)
        return self._desc_cache.get(name, "")


# Singleton instance
default_dataset_manager = DatasetManager()
