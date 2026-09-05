import os
import logging
from google import genai
from openai import OpenAI
from backend.app.config import (
    GEMINI_API_KEY,
    GROQ_API_KEY,
    DEFAULT_LLM_PROVIDER,
    GEMINI_MODEL,
    GROQ_MODEL,
)

logger = logging.getLogger(__name__)


def get_gemini_client() -> genai.Client | None:
    if not GEMINI_API_KEY:
        return None
    return genai.Client(api_key=GEMINI_API_KEY)


def get_groq_client() -> OpenAI | None:
    if not GROQ_API_KEY:
        return None
    return OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


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


def call_llm(
    prompt: str,
    client: genai.Client | None = None,
    model: str | None = None,
    provider: str | None = None,
):
    selected_provider = (provider or DEFAULT_LLM_PROVIDER).lower()
    groq_client = get_groq_client()
    if client is None:
        client = get_gemini_client()

    gemini_model = model or GEMINI_MODEL
    groq_model = GROQ_MODEL

    # If Groq is the preferred provider
    if selected_provider == "groq" and groq_client:
        try:
            groq_resp = groq_client.chat.completions.create(
                model=groq_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return groq_resp, "groq"
        except Exception as e:
            logger.warning(f"Groq call failed: {e}. Falling back to Gemini...")
            if client:
                try:
                    response = client.models.generate_content(
                        model=gemini_model, contents=prompt
                    )
                    return response, "gemini"
                except Exception as gemini_err:
                    logger.error(f"Gemini fallback also failed: {gemini_err}")
            raise

    # If Gemini is the preferred provider
    if client:
        try:
            response = client.models.generate_content(
                model=gemini_model, contents=prompt
            )
            return response, "gemini"
        except Exception as e:
            if groq_client and is_quota_error(e):
                logger.warning(f"Gemini quota reached: {e}. Falling back to Groq...")
                groq_resp = groq_client.chat.completions.create(
                    model=groq_model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return groq_resp, "groq"
            raise

    # If only Groq is available
    if groq_client:
        groq_resp = groq_client.chat.completions.create(
            model=groq_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return groq_resp, "groq"

    raise RuntimeError("No LLM client is configured. Please check your API keys.")
