"""Per-client daily token allowance manager and quota guard."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from backend.app.config import DATA_DIR, DAILY_TOKEN_LIMIT

logger = logging.getLogger(__name__)


class QuotaManager:
    """Tracks and enforces daily token allowances per user."""

    def __init__(self, storage_path: Optional[Path] = None, default_limit: int = DAILY_TOKEN_LIMIT):
        self.default_limit = default_limit

    def _today_utc(self):
        return datetime.now(timezone.utc).strftime('%Y-%m-%d')

    def _get_entry(self, user_id):
        from backend.app import storage
        return storage.get('quotas', user_id, self._today_utc()) or {'date': self._today_utc(), 'tokens_used': 0, 'daily_limit': self.default_limit}

    def check_quota(self, user_id: str, limit: Optional[int] = None) -> bool:
        """Check if user has remaining tokens. Raises HTTP 429 if budget exceeded."""
        entry = self._get_entry(user_id)
        max_allowed = limit if limit is not None else entry.get("daily_limit", self.default_limit)
        used = entry.get("tokens_used", 0)

        if used >= max_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily free token budget reached ({max_allowed:,} tokens). Resets at midnight UTC.",
                headers={"Retry-After": "86400"},
            )
        return True

    def record_usage(self, user_id: str, tokens: int) -> int:
        """Atomically record tokens consumed by user today."""
        if tokens <= 0:
            return self.get_user_quota(user_id)["tokens_used"]

        from backend.app import storage
        day = self._today_utc()
        with storage.transaction('quotas', user_id, day) as conn:
            entry = storage.get('quotas', user_id, day, conn) or {'date': day, 'tokens_used': 0, 'daily_limit': self.default_limit}
            entry['tokens_used'] += tokens
            storage.put('quotas', user_id, day, entry, conn)
            return entry['tokens_used']

    def get_user_quota(self, user_id: str) -> Dict[str, Any]:
        """Retrieve quota status for a user."""
        entry = self._get_entry(user_id)
        limit = entry.get("daily_limit", self.default_limit)
        used = entry.get("tokens_used", 0)
        remaining = max(0, limit - used)
        percent = round((used / limit) * 100, 1) if limit > 0 else 100.0

        return {
            "user_id": user_id,
            "date": entry.get("date", self._today_utc()),
            "tokens_used": used,
            "daily_limit": limit,
            "tokens_remaining": remaining,
            "percentage_used": min(100.0, percent),
            "reset_time": "Midnight UTC",
        }

    def reset_quota(self, user_id: str):
        """Reset quota for a user (useful for testing and admin overrides)."""
        from backend.app import storage
        day = self._today_utc()
        storage.put('quotas', user_id, day, {'date': day, 'tokens_used': 0, 'daily_limit': self.default_limit})

# Singleton instance
default_quota_manager = QuotaManager()
