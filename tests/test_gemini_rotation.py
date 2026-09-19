"""
Tests for multi-Gemini-key quota rotation in llm/client.py.
All tests use monkeypatching — no real API calls are made.
"""
import types
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_gemini_response(total=100):
    """Minimal fake Gemini response with usage_metadata."""
    resp = types.SimpleNamespace()
    resp.usage_metadata = types.SimpleNamespace(
        prompt_token_count=80,
        candidates_token_count=20,
        total_token_count=total,
    )
    resp.text = "ok"
    return resp


def _quota_error():
    return Exception("429 RESOURCE_EXHAUSTED: quota exceeded")


def _other_error():
    return ValueError("Bad prompt: blocked by safety filter")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_single_key_success(monkeypatch):
    """A single key works normally — no rotation needed."""
    from backend.app.llm import client as llm

    calls = []
    def fake_generate(model, contents):
        calls.append(model)
        return _make_gemini_response()

    fake_gc = types.SimpleNamespace(models=types.SimpleNamespace(generate_content=fake_generate))
    monkeypatch.setattr(llm, "get_gemini_clients", lambda: [fake_gc])

    resp, provider = llm._try_gemini_clients("gemini-2.5-flash", "hello")
    assert provider == "gemini"
    assert len(calls) == 1


def test_key1_quota_rotates_to_key2(monkeypatch):
    """Key 1 hits 429 → key 2 succeeds."""
    from backend.app.llm import client as llm

    call_count = [0]
    def fake_generate(model, contents):
        call_count[0] += 1
        if call_count[0] == 1:
            raise _quota_error()
        return _make_gemini_response()

    fake_gc = types.SimpleNamespace(models=types.SimpleNamespace(generate_content=fake_generate))
    monkeypatch.setattr(llm, "get_gemini_clients", lambda: [fake_gc, fake_gc])

    resp, provider = llm._try_gemini_clients("gemini-2.5-flash", "hello")
    assert provider == "gemini"
    assert call_count[0] == 2  # tried key 1 (fail) + key 2 (ok)


def test_all_keys_exhausted_raises(monkeypatch):
    """Both keys hit 429 → raises the last exception."""
    from backend.app.llm import client as llm

    def fake_generate(model, contents):
        raise _quota_error()

    fake_gc = types.SimpleNamespace(models=types.SimpleNamespace(generate_content=fake_generate))
    monkeypatch.setattr(llm, "get_gemini_clients", lambda: [fake_gc, fake_gc])

    with pytest.raises(Exception, match="429"):
        llm._try_gemini_clients("gemini-2.5-flash", "hello")


def test_non_quota_error_not_retried(monkeypatch):
    """A non-quota error on key 1 is raised immediately — key 2 is never tried."""
    from backend.app.llm import client as llm

    call_count = [0]
    def fake_generate(model, contents):
        call_count[0] += 1
        raise _other_error()

    fake_gc = types.SimpleNamespace(models=types.SimpleNamespace(generate_content=fake_generate))
    monkeypatch.setattr(llm, "get_gemini_clients", lambda: [fake_gc, fake_gc])

    with pytest.raises(ValueError, match="safety filter"):
        llm._try_gemini_clients("gemini-2.5-flash", "hello")

    assert call_count[0] == 1  # stopped after first key, did NOT try key 2


def test_no_gemini_keys_raises(monkeypatch):
    """If no keys are configured, a clear RuntimeError is raised."""
    from backend.app.llm import client as llm

    monkeypatch.setattr(llm, "get_gemini_clients", lambda: [])

    with pytest.raises(RuntimeError, match="No Gemini API keys configured"):
        llm._try_gemini_clients("gemini-2.5-flash", "hello")


def test_normalize_usage_gemini():
    """normalize_usage correctly reads Gemini's usage_metadata fields."""
    from backend.app.llm.client import normalize_usage
    resp = _make_gemini_response(total=150)
    usage = normalize_usage(resp, "gemini")
    assert usage["total_tokens"] == 150
    assert usage["prompt_tokens"] == 80
    assert usage["response_tokens"] == 20
