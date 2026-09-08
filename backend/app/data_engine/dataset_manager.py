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
        self._activity_log: List[dict] = []

    def log_activity(self, dataset_name: str, action: str, description: str, details: Optional[dict] = None) -> dict:
        """Log a recent dataset change or transformation."""
        from datetime import datetime, timezone
        import uuid
        entry = {
            "id": str(uuid.uuid4())[:8],
            "dataset_name": dataset_name,
            "action": action,  # "upload" | "cell_update" | "add_row" | "delete_row" | "sync"
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }
        self._activity_log.insert(0, entry)
        if len(self._activity_log) > 50:
            self._activity_log = self._activity_log[:50]
        return entry

    def get_activity_log(self) -> List[dict]:
        """Retrieve recent dataset changes, auto-seeding if empty."""
        from datetime import datetime, timezone
        if not self._activity_log:
            for d in self.list_datasets():
                self._activity_log.append({
                    "id": d["name"][:8],
                    "dataset_name": d["name"],
                    "action": "sync",
                    "description": f"Synchronized {d['name']} ({d['rows']:,} rows, {d['columns']} cols)",
                    "timestamp": d.get("modified_at") or datetime.now(timezone.utc).isoformat(),
                    "details": {"rows": d["rows"], "columns": d["columns"]},
                })
        return self._activity_log[:20]

    def list_datasets(self) -> List[dict]:
        """List all available CSV datasets in the raw data directory."""
        datasets = []
        if not self.raw_data_dir.exists():
            return datasets

        from datetime import datetime, timezone

        for file_path in sorted(self.raw_data_dir.glob("*.csv")):
            try:
                stat = file_path.stat()
                df = self.get_dataset(file_path.name)
                mtime_iso = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                datasets.append({
                    "name": file_path.name,
                    "rows": int(len(df)),
                    "columns": int(len(df.columns)),
                    "size_bytes": int(stat.st_size),
                    "modified_at": mtime_iso,
                })
            except Exception as e:
                # Fallback to basic file info if reading fails
                stat = file_path.stat()
                mtime_iso = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                datasets.append({
                    "name": file_path.name,
                    "rows": 0,
                    "columns": 0,
                    "size_bytes": int(stat.st_size),
                    "modified_at": mtime_iso,
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

    def get_rows_paginated(
        self,
        name: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        search: str = "",
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> dict:
        """Fetch paginated, filtered, and sorted records with row indices."""
        df = self.get_dataset(name)
        working_df = df.copy()
        working_df["_row_index"] = working_df.index

        # Apply global search across columns if provided
        if search and search.strip():
            q = search.strip().lower()
            mask = pd.Series(False, index=working_df.index)
            for col in df.columns:
                mask = mask | working_df[col].astype(str).str.lower().str.contains(q, na=False)
            working_df = working_df[mask]

        # Apply sorting
        if sort_by and sort_by in df.columns:
            ascending = (sort_order.lower() == "asc")
            working_df = working_df.sort_values(by=sort_by, ascending=ascending)

        total_rows = len(working_df)
        page = max(1, page)
        page_size = max(1, min(page_size, 200))
        total_pages = max(1, (total_rows + page_size - 1) // page_size)

        start = (page - 1) * page_size
        end = start + page_size
        page_slice = working_df.iloc[start:end]

        # Clean NaN/None for JSON serialization
        records = page_slice.replace({float("nan"): None}).to_dict(orient="records")

        column_meta = []
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            if "int" in dtype_str:
                simple_type = "integer"
            elif "float" in dtype_str:
                simple_type = "number"
            elif "date" in dtype_str:
                simple_type = "date"
            else:
                simple_type = "text"
            column_meta.append({"name": col, "type": simple_type})

        return {
            "dataset_name": name or DEFAULT_DATASET_PATH.name,
            "columns": column_meta,
            "rows": records,
            "total_rows": total_rows,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def update_cells(self, name: Optional[str], updates: List[dict]) -> dict:
        """Update cell values in the in-memory dataset, sync with disk and description cache."""
        df = self.get_dataset(name)
        if not name:
            name = DEFAULT_DATASET_PATH.name

        updated_count = 0
        for upd in updates:
            row_idx = upd.get("row_index")
            col = upd.get("column")
            val = upd.get("value")

            if row_idx is not None and col in df.columns and row_idx in df.index:
                col_dtype = df[col].dtype
                try:
                    if pd.isna(val) or val == "" or val is None:
                        df.at[row_idx, col] = None
                    elif "int" in str(col_dtype):
                        df.at[row_idx, col] = int(val)
                    elif "float" in str(col_dtype):
                        df.at[row_idx, col] = float(val)
                    else:
                        df.at[row_idx, col] = str(val)
                    updated_count += 1
                except Exception:
                    df.at[row_idx, col] = val
                    updated_count += 1

        file_path = self.raw_data_dir / name
        df.to_csv(file_path, index=False)
        self._desc_cache[name] = describe_dataframe(df)
        self.log_activity(name, "cell_update", f"Updated {updated_count} cells in {name}", {"updated_count": updated_count})

        return {"success": True, "updated_count": updated_count}

    def add_row(self, name: Optional[str], row_data: dict) -> dict:
        """Add a new row to the dataset and save."""
        df = self.get_dataset(name)
        if not name:
            name = DEFAULT_DATASET_PATH.name

        new_row = {col: row_data.get(col, None) for col in df.columns}
        new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        self._cache[name] = new_df
        file_path = self.raw_data_dir / name
        new_df.to_csv(file_path, index=False)
        self._desc_cache[name] = describe_dataframe(new_df)
        new_idx = int(len(new_df) - 1)
        self.log_activity(name, "add_row", f"Appended record #{new_idx + 1} to {name}", {"new_index": new_idx})

        return {"success": True, "new_index": new_idx}

    def delete_row(self, name: Optional[str], row_index: int) -> dict:
        """Delete a row by index from the dataset and save."""
        df = self.get_dataset(name)
        if not name:
            name = DEFAULT_DATASET_PATH.name

        if row_index in df.index:
            new_df = df.drop(index=row_index).reset_index(drop=True)
            self._cache[name] = new_df
            file_path = self.raw_data_dir / name
            new_df.to_csv(file_path, index=False)
            self._desc_cache[name] = describe_dataframe(new_df)
            self.log_activity(name, "delete_row", f"Deleted row #{row_index + 1} from {name}", {"row_index": row_index})
            return {"success": True}
        return {"success": False, "error": "Index not found"}


# Singleton instance
default_dataset_manager = DatasetManager()
