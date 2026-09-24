"""Per-client daily token allowance manager and quota guard."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from backend.app.config import DATA_DIR, DAILY_TOKEN_LIMIT, DAILY_QUERY_LIMIT, COMPANY_LIMIT_NOTICE

logger = logging.getLogger(__name__)


class QuotaManager:
    """Tracks and enforces daily query and token allowances per user."""

    COMPANY_LIMIT_MSG = COMPANY_LIMIT_NOTICE

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        default_limit: int = DAILY_TOKEN_LIMIT,
        default_query_limit: int = DAILY_QUERY_LIMIT,
    ):
        self.default_limit = default_limit
        self.default_query_limit = default_query_limit

    def _today_utc(self):
        return datetime.now(timezone.utc).strftime('%Y-%m-%d')

    GUEST_LIMIT = 10000

    def _get_limit(self, user_id: str) -> int:
        return self.GUEST_LIMIT if user_id == "user_default" else self.default_limit

    def _get_entry(self, user_id: str) -> Dict[str, Any]:
        from backend.app import storage
        entry = storage.get('quotas', user_id, self._today_utc())
        limit = self._get_limit(user_id)
        if not entry:
            return {
                'date': self._today_utc(),
                'tokens_used': 0,
                'daily_limit': limit,
                'queries_used': 0,
                'query_limit': self.default_query_limit,
            }
        entry['daily_limit'] = limit
        entry.setdefault('queries_used', 0)
        entry.setdefault('query_limit', self.default_query_limit)
        return entry

    def is_admin(self, user_id: str) -> bool:
        return user_id in ("user_admin_ralph", "ralph123")

    def check_quota(self, user_id: str, limit: Optional[int] = None) -> bool:
        """Check if user has remaining queries and tokens. Raises HTTP 429 if budget exceeded."""
        if self.is_admin(user_id):
            return True

        entry = self._get_entry(user_id)
        queries_used = entry.get("queries_used", 0)
        query_limit = entry.get("query_limit", self.default_query_limit)

        # 1. Check query count limit (10 queries max)
        if queries_used >= query_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self.COMPANY_LIMIT_MSG,
                headers={"Retry-After": "86400"},
            )

        # 2. Check token volume limit
        max_allowed = limit if limit is not None else entry.get("daily_limit", self._get_limit(user_id))
        used = entry.get("tokens_used", 0)

        if used >= max_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self.COMPANY_LIMIT_MSG,
                headers={"Retry-After": "86400"},
            )
        return True

    def record_query(self, user_id: str) -> int:
        """Atomically increment query counter for user today."""
        from backend.app import storage
        day = self._today_utc()
        limit = self._get_limit(user_id)
        with storage.transaction('quotas', user_id, day) as conn:
            entry = storage.get('quotas', user_id, day, conn) or {
                'date': day,
                'tokens_used': 0,
                'daily_limit': limit,
                'queries_used': 0,
                'query_limit': self.default_query_limit,
            }
            entry['daily_limit'] = limit
            entry.setdefault('query_limit', self.default_query_limit)
            entry['queries_used'] = entry.get('queries_used', 0) + 1
            storage.put('quotas', user_id, day, entry, conn)
            return entry['queries_used']

    def record_usage(self, user_id: str, tokens: int) -> int:
        """Atomically record tokens consumed by user today."""
        if tokens <= 0:
            return self.get_user_quota(user_id)["tokens_used"]

        from backend.app import storage
        day = self._today_utc()
        limit = self._get_limit(user_id)
        with storage.transaction('quotas', user_id, day) as conn:
            entry = storage.get('quotas', user_id, day, conn) or {
                'date': day,
                'tokens_used': 0,
                'daily_limit': limit,
                'queries_used': 0,
                'query_limit': self.default_query_limit,
            }
            entry['daily_limit'] = limit
            entry.setdefault('query_limit', self.default_query_limit)
            entry.setdefault('queries_used', 0)
            entry['tokens_used'] = entry.get('tokens_used', 0) + tokens
            storage.put('quotas', user_id, day, entry, conn)
            return entry['tokens_used']

    def get_user_quota(self, user_id: str) -> Dict[str, Any]:
        """Retrieve quota status for a user."""
        entry = self._get_entry(user_id)
        if self.is_admin(user_id):
            return {
                "user_id": user_id,
                "date": entry.get("date", self._today_utc()),
                "tokens_used": entry.get("tokens_used", 0),
                "daily_limit": 999999999,
                "tokens_remaining": 999999999,
                "percentage_used": 0.0,
                "queries_used": entry.get("queries_used", 0),
                "query_limit": 999999,
                "queries_remaining": 999999,
                "query_percentage_used": 0.0,
                "reset_time": "No Expiration",
                "is_admin": True,
                "company_notice": "Main Administrator • Unlimited Queries & Tokens",
            }
        limit = entry.get("daily_limit", self.default_limit)
        used = entry.get("tokens_used", 0)
        remaining = max(0, limit - used)
        percent = round((used / limit) * 100, 1) if limit > 0 else 100.0

        query_limit = entry.get("query_limit", self.default_query_limit)
        queries_used = entry.get("queries_used", 0)
        queries_remaining = max(0, query_limit - queries_used)
        query_percent = round((queries_used / query_limit) * 100, 1) if query_limit > 0 else 100.0

        return {
            "user_id": user_id,
            "date": entry.get("date", self._today_utc()),
            "tokens_used": used,
            "daily_limit": limit,
            "tokens_remaining": remaining,
            "percentage_used": min(100.0, percent),
            "queries_used": queries_used,
            "query_limit": query_limit,
            "queries_remaining": queries_remaining,
            "query_percentage_used": min(100.0, query_percent),
            "reset_time": "Midnight UTC",
            "company_notice": self.COMPANY_LIMIT_MSG,
        }

    def reset_quota(self, user_id: str):
        """Reset quota for a user (useful for testing and admin overrides)."""
        from backend.app import storage
        day = self._today_utc()
        storage.put('quotas', user_id, day, {
            'date': day,
            'tokens_used': 0,
            'daily_limit': self.default_limit,
            'queries_used': 0,
            'query_limit': self.default_query_limit,
        })


# Singleton instance
default_quota_manager = QuotaManager()
