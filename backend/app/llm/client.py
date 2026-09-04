import os
from google import genai
from openai import OpenAI
from backend.app.config import GEMINI_API_KEY, GROQ_API_KEY


def get_gemini_client() -> genai.Client:
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


def call_llm(prompt: str, client: genai.Client | None = None, model: str = "gemini-2.5-flash"):
    if client is None:
        client = get_gemini_client()
    groq_client = get_groq_client()
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response, "gemini"
    except Exception as e:
        if groq_client and is_quota_error(e):
            groq_resp = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
            )
            return groq_resp, "groq"
        raise
