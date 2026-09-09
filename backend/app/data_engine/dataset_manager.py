from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from backend.app.paths import inside, filename
from backend.app import storage
from backend.app.config import RAW_DATA_DIR, UPLOADS_DIR, DEFAULT_DATASET_PATH
from backend.app.data_engine.loader import load_data, describe_dataframe


class DatasetManager:
    """Discovers, caches, and provides access to raw and user-uploaded datasets."""

    def __init__(self, raw_data_dir: Path = RAW_DATA_DIR, uploads_dir: Path = UPLOADS_DIR):
        self.raw_data_dir = raw_data_dir
        self.uploads_dir = uploads_dir
        self._cache: Dict[str, pd.DataFrame] = {}
        self._desc_cache: Dict[str, str] = {}

    def _cache_key(self, name: str, user_id: Optional[str] = None) -> str:
        """Create a cache key combining dataset name and optional user_id."""
        return f"{user_id or ''}:{name}"

    def _resolve_path(self, name: Optional[str] = None, user_id: Optional[str] = None) -> Path:
        """Resolve file path: checks user's private upload folder first, then global raw data."""
        name = filename(name or DEFAULT_DATASET_PATH.name)
        if user_id:
            private = inside(self.uploads_dir, user_id, name)
            if private.exists(): return private
        shared = inside(self.raw_data_dir, name)
        if shared.exists(): return shared
        raise FileNotFoundError('Dataset not found')

    def _write_path(self, name, user_id):
        if not user_id: raise ValueError('User required for mutations')
        path = inside(self.uploads_dir, user_id, name or DEFAULT_DATASET_PATH.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def log_activity(self, dataset_name, action, description, details=None, user_id=None):
        from datetime import datetime, timezone
        import uuid
        user_id = user_id or (details or {}).get('user_id')
        if not user_id: raise ValueError('Activity owner required')
        entry = dict(id=str(uuid.uuid4()), dataset_name=dataset_name, action=action,
                     description=description, details=details or {}, timestamp=datetime.now(timezone.utc).isoformat())
        storage.put('activity', user_id, entry['id'], entry)
        path = self._resolve_path(dataset_name, user_id)
        df = load_data(path)
        storage.put('datasets', user_id, dataset_name, dict(name=dataset_name, rows=len(df),
            columns=len(df.columns), size_bytes=path.stat().st_size, modified_at=entry['timestamp'], is_private=True))
        return entry

    def get_activity_log(self, user_id):
        return sorted(storage.list_records('activity', user_id), key=lambda r:r['timestamp'], reverse=True)[:20]

    def list_datasets(self, user_id: Optional[str] = None) -> List[dict]:
        """List all datasets available to the user (global datasets + private user uploads)."""
        datasets = []
        seen_names = set()
        from datetime import datetime, timezone

        # 1. User private uploads
        if user_id:
            user_dir = inside(self.uploads_dir, user_id)
            if user_dir.exists():
                for file_path in sorted(user_dir.glob("*.csv")):
                    try:
                        stat = file_path.stat()
                        df = self.get_dataset(file_path.name, user_id=user_id)
                        mtime_iso = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                        datasets.append({
                            "name": file_path.name,
                            "rows": int(len(df)),
                            "columns": int(len(df.columns)),
                            "size_bytes": int(stat.st_size),
                            "modified_at": mtime_iso,
                            "is_private": True,
                        })
                        seen_names.add(file_path.name)
                    except Exception:
                        pass

        # 2. Global shared datasets
        if self.raw_data_dir.exists():
            for file_path in sorted(self.raw_data_dir.glob("*.csv")):
                if file_path.name in seen_names:
                    continue
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
                        "is_private": False,
                    })
                except Exception:
                    stat = file_path.stat()
                    mtime_iso = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    datasets.append({
                        "name": file_path.name,
                        "rows": 0,
                        "columns": 0,
                        "size_bytes": int(stat.st_size),
                        "modified_at": mtime_iso,
                        "is_private": False,
                    })
        for dataset in datasets:
            storage.put('datasets', user_id or 'shared', dataset['name'], dataset)
        return datasets

    def get_dataset(self, name: Optional[str] = None, user_id: Optional[str] = None) -> pd.DataFrame:
        """Get or load a DataFrame by its filename and optional user_id."""
        if not name:
            name = DEFAULT_DATASET_PATH.name

        key = self._cache_key(name, user_id)
        file_path = self._resolve_path(name, user_id)
        df = load_data(file_path)
        self._cache[key] = df
        self._desc_cache[key] = describe_dataframe(df)

        return self._cache[key]

    def get_dataset_description(self, name: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """Get the cached string description of the dataset."""
        if not name:
            name = DEFAULT_DATASET_PATH.name
        key = self._cache_key(name, user_id)
        self.get_dataset(name, user_id=user_id)
        return self._desc_cache.get(key, "")

    def get_rows_paginated(
        self,
        name: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        search: str = "",
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        user_id: Optional[str] = None,
    ) -> dict:
        """Fetch paginated, filtered, and sorted records with row indices."""
        df = self.get_dataset(name, user_id=user_id)
        working_df = df.copy()
        working_df["_row_index"] = working_df.index

        # Apply global search across columns if provided
        if search and search.strip():
            q = search.strip().lower()
            mask = pd.Series(False, index=working_df.index)
            for col in df.columns:
                mask = mask | working_df[col].astype(str).str.lower().str.contains(q, na=False, regex=False)
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

    def update_cells(self, name: Optional[str], updates: List[dict], user_id: Optional[str] = None) -> dict:
        """Update cell values in the in-memory dataset, sync with disk and description cache."""
        df = self.get_dataset(name, user_id=user_id)
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

        file_path = self._write_path(name, user_id)
        df.to_csv(file_path, index=False)
        key = self._cache_key(name, user_id)
        self._desc_cache[key] = describe_dataframe(df)
        self.log_activity(name, "cell_update", f"Updated {updated_count} cells in {name}", {"updated_count": updated_count}, user_id=user_id)

        return {"success": True, "updated_count": updated_count}

    def add_row(self, name: Optional[str], row_data: dict, user_id: Optional[str] = None) -> dict:
        """Add a new row to the dataset and save."""
        df = self.get_dataset(name, user_id=user_id)
        if not name:
            name = DEFAULT_DATASET_PATH.name

        key = self._cache_key(name, user_id)
        new_row = {col: row_data.get(col, None) for col in df.columns}
        new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        self._cache[key] = new_df
        file_path = self._write_path(name, user_id)
        new_df.to_csv(file_path, index=False)
        self._desc_cache[key] = describe_dataframe(new_df)
        new_idx = int(len(new_df) - 1)
        self.log_activity(name, "add_row", f"Appended record #{new_idx + 1} to {name}", {"new_index": new_idx}, user_id=user_id)

        return {"success": True, "new_index": new_idx}

    def delete_row(self, name: Optional[str], row_index: int, user_id: Optional[str] = None) -> dict:
        """Delete a row by index from the dataset and save."""
        df = self.get_dataset(name, user_id=user_id)
        if not name:
            name = DEFAULT_DATASET_PATH.name

        key = self._cache_key(name, user_id)
        if row_index in df.index:
            new_df = df.drop(index=row_index).reset_index(drop=True)
            self._cache[key] = new_df
            file_path = self._write_path(name, user_id)
            new_df.to_csv(file_path, index=False)
            self._desc_cache[key] = describe_dataframe(new_df)
            self.log_activity(name, "delete_row", f"Deleted row #{row_index + 1} from {name}", {"row_index": row_index}, user_id=user_id)
            return {"success": True}
        return {"success": False, "error": "Index not found"}

    def invalidate_cache(self, name: str, user_id: Optional[str] = None):
        """Invalidate in-memory DataFrame and description caches for a dataset."""
        key = self._cache_key(name, user_id)
        if key in self._cache:
            del self._cache[key]
        if key in self._desc_cache:
            del self._desc_cache[key]
        # Also invalidate global key if present
        if name in self._cache:
            del self._cache[name]
        if name in self._desc_cache:
            del self._desc_cache[name]


# Singleton instance
default_dataset_manager = DatasetManager()
