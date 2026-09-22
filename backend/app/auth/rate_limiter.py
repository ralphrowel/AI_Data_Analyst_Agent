"""High-performance in-memory sliding-window rate limiter for FastAPI."""
import time
import logging
import threading
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from fastapi import Request, HTTPException, status, Depends

from backend.app.auth.supabase_auth import get_current_user, User

logger = logging.getLogger(__name__)


def get_client_identifier(request: Request, user_id: Optional[str] = None) -> str:
    """Extract distinct client key: user ID for authenticated users, IP for guests."""
    if user_id and user_id != "user_default":
        return f"user:{user_id}"

    # Extract remote IP behind proxies (Vercel, Railway, Cloudflare, etc.)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "unknown"

    return f"ip:{client_ip}"


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, cleanup_interval: float = 300.0):
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = cleanup_interval

    def check(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
        """Check if request is permitted under (limit, window_seconds).

        Returns:
            Tuple of (is_allowed, retry_after_seconds).
        """
        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            # Periodic housekeeping to keep memory bounded
            if now - self._last_cleanup > self._cleanup_interval:
                self._prune(now)

            timestamps = self._history[key]
            # Remove expired timestamps
            valid = [ts for ts in timestamps if ts > cutoff]
            self._history[key] = valid

            if len(valid) >= limit:
                oldest_in_window = valid[0]
                retry_after = max(1, int(oldest_in_window + window_seconds - now) + 1)
                return False, retry_after

            # Record this request
            self._history[key].append(now)
            return True, 0

    def reset(self, key: Optional[str] = None):
        """Reset limits for a key or all keys (useful for testing)."""
        with self._lock:
            if key:
                self._history.pop(key, None)
            else:
                self._history.clear()

    def _prune(self, now: float):
        """Remove keys with no activity in the last 15 minutes."""
        stale_cutoff = now - 900.0
        keys_to_remove = [
            k for k, ts_list in self._history.items()
            if not ts_list or ts_list[-1] <= stale_cutoff
        ]
        for k in keys_to_remove:
            del self._history[k]
        self._last_cleanup = now


# Global singleton instance
default_rate_limiter = SlidingWindowRateLimiter()


class RateLimit:
    """FastAPI Dependency for route-level burst rate limiting."""

    def __init__(self, limit: int, window_seconds: int = 60, name: str = "request"):
        self.limit = limit
        self.window = window_seconds
        self.name = name

    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> None:
        identifier = get_client_identifier(request, current_user.id if current_user else None)
        key = f"{self.name}:{identifier}"

        allowed, retry_after = default_rate_limiter.check(key, self.limit, self.window)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {key} on {request.url.path} (limit={self.limit}/{self.window}s)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit reached for {self.name}. Please wait {retry_after} second{'s' if retry_after > 1 else ''} before trying again.",
                headers={"Retry-After": str(retry_after)},
            )
