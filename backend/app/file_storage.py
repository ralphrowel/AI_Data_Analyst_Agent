"""
Portable file storage abstraction.

In development (no SUPABASE_SERVICE_KEY set): reads/writes to the local filesystem.
In production (SUPABASE_SERVICE_KEY present): reads/writes to Supabase Storage bucket,
keeping a local temp cache for the current process lifetime.

Usage:
    from backend.app.file_storage import file_store
    file_store.save(user_id="alice", filename="data.csv", content="col\n1\n")
    text = file_store.load(user_id="alice", filename="data.csv")
    file_store.delete(user_id="alice", filename="data.csv")
    paths = file_store.list_files(user_id="alice")
"""
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class _LocalFileStore:
    """Local filesystem backend — used in development and tests."""

    def __init__(self, uploads_dir: Path, knowledge_dir: Path):
        self._uploads_dir = uploads_dir
        self._knowledge_dir = knowledge_dir

    @property
    def uploads_dir(self) -> Path:
        try:
            from backend.app.data_engine.dataset_manager import default_dataset_manager
            return getattr(default_dataset_manager, "uploads_dir", None) or self._uploads_dir
        except Exception:
            return self._uploads_dir

    @property
    def knowledge_dir(self) -> Path:
        try:
            from backend.app import config
            return getattr(config, "KNOWLEDGE_DIR", self._knowledge_dir)
        except Exception:
            return self._knowledge_dir

    def _path(self, user_id: str, filename: str, kind: str = "csv") -> Path:
        from backend.app.paths import inside
        base = self.knowledge_dir if kind == "doc" else self.uploads_dir
        return inside(base, user_id, filename)

    def save(self, user_id: str, filename: str, content: str, kind: str = "csv") -> Path:
        from backend.app.paths import inside, atomic_text
        base = self.knowledge_dir if kind == "doc" else self.uploads_dir
        path = inside(base, user_id, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_text(path, content)
        return path

    def load(self, user_id: str, filename: str, kind: str = "csv") -> Optional[str]:
        try:
            return self._path(user_id, filename, kind).read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def delete(self, user_id: str, filename: str, kind: str = "csv") -> None:
        try:
            self._path(user_id, filename, kind).unlink(missing_ok=True)
        except Exception:
            pass

    def list_files(self, user_id: str, kind: str = "csv") -> list[Path]:
        from backend.app.paths import inside
        base = self.knowledge_dir if kind == "doc" else self.uploads_dir
        try:
            user_dir = inside(base, user_id)
            return list(user_dir.glob("*")) if user_dir.exists() else []
        except ValueError:
            return []

    def exists(self, user_id: str, filename: str, kind: str = "csv") -> bool:
        try:
            return self._path(user_id, filename, kind).exists()
        except Exception:
            return False

    def ensure_local_path(self, user_id: str, filename: str, kind: str = "csv") -> Optional[Path]:
        try:
            p = self._path(user_id, filename, kind)
            return p if p.exists() else None
        except Exception:
            return None


class _SupabaseFileStore:
    """
    Supabase Storage backend — used in production.
    Files are stored in the bucket under <kind>/<user_id>/<filename>.
    Downloaded files are cached locally so pandas and the RAG indexer
    can read them normally from disk.
    """

    def __init__(self, supabase_url: str, service_key: str, bucket: str,
                 uploads_dir: Path, knowledge_dir: Path):
        from supabase import create_client
        self._client = create_client(supabase_url, service_key)
        self._bucket = bucket
        self._tmp = Path(tempfile.mkdtemp(prefix="visiq_"))
        self._uploads_dir = uploads_dir
        self._knowledge_dir = knowledge_dir
        try:
            self._client.storage.create_bucket(bucket, options={"public": False})
            logger.info(f"Initialized Supabase Storage bucket: {bucket}")
        except Exception:
            pass
        logger.info(f"Supabase Storage backend active — bucket: {bucket}")

    @property
    def uploads_dir(self) -> Path:
        try:
            from backend.app.data_engine.dataset_manager import default_dataset_manager
            return getattr(default_dataset_manager, "uploads_dir", None) or self._uploads_dir
        except Exception:
            return self._uploads_dir

    @property
    def knowledge_dir(self) -> Path:
        try:
            from backend.app import config
            return getattr(config, "KNOWLEDGE_DIR", self._knowledge_dir)
        except Exception:
            return self._knowledge_dir

    def _remote_path(self, user_id: str, filename: str, kind: str) -> str:
        return f"{kind}/{user_id}/{filename}"

    def _local_mirror(self, user_id: str, filename: str, kind: str) -> Path:
        from backend.app.paths import inside
        base = self.knowledge_dir if kind == "doc" else self.uploads_dir
        try:
            path = inside(base, user_id, filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        except Exception:
            d = self._tmp / kind / user_id
            d.mkdir(parents=True, exist_ok=True)
            return d / filename

    def save(self, user_id: str, filename: str, content: str, kind: str = "csv") -> Path:
        from backend.app.paths import atomic_text
        data = content.encode("utf-8")
        remote = self._remote_path(user_id, filename, kind)
        self._client.storage.from_(self._bucket).upload(
            remote, data,
            file_options={"content-type": "text/plain", "upsert": "true"},
        )
        local = self._local_mirror(user_id, filename, kind)
        atomic_text(local, content)
        logger.info(f"Saved {remote} to Supabase Storage and mirrored locally")
        return local

    def load(self, user_id: str, filename: str, kind: str = "csv") -> Optional[str]:
        remote = self._remote_path(user_id, filename, kind)
        try:
            data: bytes = self._client.storage.from_(self._bucket).download(remote)
            local = self._local_mirror(user_id, filename, kind)
            local.write_bytes(data)
            return data.decode("utf-8")
        except Exception as e:
            logger.warning(f"Could not load {remote} from Supabase: {e}")
            return None

    def delete(self, user_id: str, filename: str, kind: str = "csv") -> None:
        remote = self._remote_path(user_id, filename, kind)
        try:
            self._client.storage.from_(self._bucket).remove([remote])
        except Exception as e:
            logger.warning(f"Could not delete {remote}: {e}")
        try:
            local = self._local_mirror(user_id, filename, kind)
            local.unlink(missing_ok=True)
        except Exception:
            pass

    def list_files(self, user_id: str, kind: str = "csv") -> list[Path]:
        prefix = f"{kind}/{user_id}"
        try:
            items = self._client.storage.from_(self._bucket).list(prefix)
            result = []
            for item in items:
                name = item.get("name", "")
                if name:
                    local = self._local_mirror(user_id, name, kind)
                    result.append(local)
            return result
        except Exception as e:
            logger.warning(f"Could not list {prefix}: {e}")
            return []

    def exists(self, user_id: str, filename: str, kind: str = "csv") -> bool:
        remote = self._remote_path(user_id, filename, kind)
        try:
            self._client.storage.from_(self._bucket).download(remote)
            return True
        except Exception:
            return False

    def ensure_local_path(self, user_id: str, filename: str, kind: str = "csv") -> Optional[Path]:
        local = self._local_mirror(user_id, filename, kind)
        if local.exists() and local.stat().st_size > 0:
            return local
        remote = self._remote_path(user_id, filename, kind)
        try:
            data: bytes = self._client.storage.from_(self._bucket).download(remote)
            local.write_bytes(data)
            return local
        except Exception as e:
            logger.warning(f"Could not download {remote} from Supabase: {e}")
            return None


def _make_store():
    from backend.app.config import (
        SUPABASE_URL, UPLOADS_DIR, KNOWLEDGE_DIR,
        SUPABASE_SERVICE_KEY, SUPABASE_STORAGE_BUCKET, APP_ENV,
    )
    if APP_ENV != "test" and SUPABASE_SERVICE_KEY and SUPABASE_URL:
        return _SupabaseFileStore(
            supabase_url=SUPABASE_URL,
            service_key=SUPABASE_SERVICE_KEY,
            bucket=SUPABASE_STORAGE_BUCKET,
            uploads_dir=UPLOADS_DIR,
            knowledge_dir=KNOWLEDGE_DIR,
        )
    logger.info("Using local filesystem for file storage.")
    return _LocalFileStore(uploads_dir=UPLOADS_DIR, knowledge_dir=KNOWLEDGE_DIR)


# Singleton — initialized once at import time
file_store = _make_store()
