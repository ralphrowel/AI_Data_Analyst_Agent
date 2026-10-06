"""Data Quality Service: orchestrates profiling, assessment, and lineage for Visiq."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
import pandas as pd

from backend.app.data_engine.dataset_manager import default_dataset_manager
from backend.app.data_quality.models import ProfileResult
from backend.app.data_quality.profiler import DataProfiler

logger = logging.getLogger(__name__)


class DataQualityService:
    """Service layer connecting Visiq storage and data engines to data quality capabilities."""

    def __init__(self, profiler: Optional[DataProfiler] = None):
        self.profiler = profiler or DataProfiler()

    def profile_dataset(self, dataset_name: str, user_id: Optional[str] = None) -> ProfileResult:
        """Loads a raw CSV dataset and computes its statistical and semantic profile.

        Note: Reads the underlying CSV directly to inspect ground-truth user data,
        avoiding artificial derived columns produced by specialized analysis loaders.
        """
        # Resolve file path with path containment
        file_path = default_dataset_manager._resolve_path(dataset_name, user_id=user_id)
        if not file_path or not file_path.exists():
            raise FileNotFoundError(f"Dataset '{dataset_name}' not found.")

        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame()
        except Exception as e:
            logger.error("Failed to read CSV for profiling: %s", e)
            raise ValueError(f"Could not parse dataset '{dataset_name}': {e}") from e

        return self.profiler.profile(df)


# Global singleton instance
default_dq_service = DataQualityService()
