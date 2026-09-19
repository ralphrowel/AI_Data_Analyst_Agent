import logging
from google import genai
from openai import OpenAI
from backend.app.config import (
    GEMINI_API_KEYS,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    DEFAULT_LLM_PROVIDER,
    GEMINI_MODEL,
    GROQ_MODEL,
)

logger = logging.getLogger(__name__)

if GEMINI_API_KEYS:
    logger.info(f"{len(GEMINI_API_KEYS)} Gemini key(s) configured.")
else:
    logger.warning("No Gemini API keys configured.")


# ---------------------------------------------------------------------------
# Client factories
# ---------------------------------------------------------------------------

def get_gemini_clients() -> list[genai.Client]:
    """Return one genai.Client per configured Gemini API key."""
    return [genai.Client(api_key=k) for k in GEMINI_API_KEYS]


def get_gemini_client() -> genai.Client | None:
    """Backward-compatible: returns the first Gemini client, or None."""
    if not GEMINI_API_KEY:
        return None
    return genai.Client(api_key=GEMINI_API_KEY)


def get_groq_client() -> OpenAI | None:
    if not GROQ_API_KEY:
        return None
    return OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_quota_error(e: Exception) -> bool:
    error_str = str(e).lower()
    return (
        "429" in error_str
        or "quota" in error_str
        or "resource exhausted" in error_str
        or "rate limit" in error_str
    )


def normalize_usage(response, provider: str) -> dict:
    if provider == "groq":
        return {
            "prompt_tokens": response.usage.prompt_tokens,
            "response_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
    return {
        "prompt_tokens": response.usage_metadata.prompt_token_count,
        "response_tokens": response.usage_metadata.candidates_token_count,
        "total_tokens": response.usage_metadata.total_token_count,
    }


def _try_gemini_clients(gemini_model: str, prompt: str):
    """
    Attempt the prompt against each configured Gemini key in order.
    Rotates to the next key only on quota / rate-limit errors (429).
    Any other error is raised immediately without trying further keys.
    Raises the last quota error if every key is exhausted.
    """
    clients = get_gemini_clients()
    if not clients:
        raise RuntimeError("No Gemini API keys configured.")

    last_err: Exception | None = None
    for i, gc in enumerate(clients):
        try:
            response = gc.models.generate_content(model=gemini_model, contents=prompt)
            if i > 0:
                logger.info(f"Gemini key {i + 1} succeeded after {i} quota failure(s).")
            return response, "gemini"
        except Exception as e:
            if is_quota_error(e):
                logger.warning(
                    f"Gemini key {i + 1}/{len(clients)} quota exhausted. "
                    + ("Trying next key..." if i + 1 < len(clients) else "All keys exhausted.")
                )
                last_err = e
                continue
            # Non-quota error — surface immediately, do not retry other keys
            raise

    raise last_err  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Core dispatcher
# ---------------------------------------------------------------------------

def _call_llm(
    prompt: str,
    client: genai.Client | None = None,
    model: str | None = None,
    provider: str | None = None,
):
    selected_provider = (provider or DEFAULT_LLM_PROVIDER).lower()
    groq_client = get_groq_client()
    gemini_model = model or GEMINI_MODEL

    # ------------------------------------------------------------------
    # Groq preferred
    # ------------------------------------------------------------------
    if selected_provider == "groq" and groq_client:
        try:
            groq_resp = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            return groq_resp, "groq"
        except Exception as e:
            logger.warning(f"Groq call failed: {e}. Falling back to Gemini...")
            if GEMINI_API_KEYS:
                try:
                    return _try_gemini_clients(gemini_model, prompt)
                except Exception as gemini_err:
                    logger.error(f"All Gemini keys also failed: {gemini_err}")
            raise

    # ------------------------------------------------------------------
    # Gemini preferred — with multi-key rotation
    # ------------------------------------------------------------------
    if GEMINI_API_KEYS:
        try:
            return _try_gemini_clients(gemini_model, prompt)
        except Exception as e:
            if groq_client and is_quota_error(e):
                logger.warning(f"All Gemini keys exhausted: {e}. Falling back to Groq...")
                groq_resp = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                )
                return groq_resp, "groq"
            raise

    # ------------------------------------------------------------------
    # Groq only (no Gemini keys configured)
    # ------------------------------------------------------------------
    if groq_client:
        groq_resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return groq_resp, "groq"

    raise RuntimeError("No LLM client is configured. Please check your API keys.")


# ---------------------------------------------------------------------------
# Public entry point — metered
# ---------------------------------------------------------------------------

def call_llm(prompt, client=None, model=None, provider=None):
    """Meter every successful provider call, including routing and widgets."""
    from backend.app.auth.context import request_user_id
    from backend.app.auth.quota_manager import default_quota_manager
    user_id = request_user_id.get()
    if user_id:
        default_quota_manager.check_quota(user_id)
    response, used_provider = _call_llm(prompt, client=client, model=model, provider=provider)
    if user_id:
        usage = normalize_usage(response, used_provider)
        default_quota_manager.record_usage(user_id, usage.get('total_tokens', 0) or 0)
    return response, used_provider
