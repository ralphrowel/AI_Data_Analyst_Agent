import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.auth.rate_limiter import SlidingWindowRateLimiter, default_rate_limiter
from backend.app.main import app

client = TestClient(app)


def test_sliding_window_unit():
    limiter = SlidingWindowRateLimiter()
    key = "test_user_1"

    # Allow 3 requests in 10-second window
    for _ in range(3):
        allowed, retry_after = limiter.check(key, limit=3, window_seconds=10)
        assert allowed is True
        assert retry_after == 0

    # 4th request must be blocked
    allowed, retry_after = limiter.check(key, limit=3, window_seconds=10)
    assert allowed is False
    assert retry_after > 0
    assert retry_after <= 11

    # Different key should not be affected
    other_allowed, _ = limiter.check("test_user_2", limit=3, window_seconds=10)
    assert other_allowed is True


def test_rate_limiter_reset():
    limiter = SlidingWindowRateLimiter()
    key = "test_reset"

    for _ in range(2):
        limiter.check(key, limit=2, window_seconds=60)

    # Exceeded
    allowed, _ = limiter.check(key, limit=2, window_seconds=60)
    assert allowed is False

    # Reset
    limiter.reset(key)
    allowed, _ = limiter.check(key, limit=2, window_seconds=60)
    assert allowed is True


def test_suggestions_endpoint_rate_limit():
    default_rate_limiter.reset()
    headers = {"Authorization": "Bearer demo_default"}

    # Mock LLM suggestions to return immediately without external network calls
    with patch("backend.app.api.routes.call_llm", side_effect=Exception("mocked")):
        # Limit is 30 requests per minute
        for i in range(30):
            resp = client.get("/api/suggestions", headers=headers)
            assert resp.status_code == 200, f"Call {i+1} failed with {resp.status_code}"

        # 31st request must trigger 429 Too Many Requests
        resp = client.get("/api/suggestions", headers=headers)
        assert resp.status_code == 429
        data = resp.json()
        assert "Rate limit" in data["detail"]
        assert "Retry-After" in resp.headers

    # Cleanup
    default_rate_limiter.reset()
