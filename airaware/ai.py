"""Optional generative-AI enhancement via the Gemini API.

This module is strictly optional:
- It activates ONLY when ``GEMINI_API_KEY`` is present in Streamlit secrets
  (``.streamlit/secrets.toml`` locally or Cloud secrets in deployment).
- Without a key, every function degrades gracefully and the app uses the
  local rule engine. Nothing here is ever presented as AI-generated when
  the API was not actually called.
- Uses only the Python standard library (urllib) - no extra dependencies.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

try:
    import streamlit as st
except Exception:  # pragma: no cover - allows unit tests without runtime
    st = None  # type: ignore[assignment]

DEFAULT_MODEL = "gemini-2.0-flash"
_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_TIMEOUT_S = 25


def _secrets_get(key: str, default=None):
    """Safely read a secret; returns default outside Streamlit runtime."""
    if st is None:
        return default
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def gemini_configured() -> bool:
    """True only when a Gemini API key is actually configured."""
    return bool(_secrets_get("GEMINI_API_KEY"))


def gemini_model() -> str:
    return str(_secrets_get("GEMINI_MODEL", DEFAULT_MODEL))


def generate_text(prompt: str, max_output_tokens: int = 1200) -> Optional[str]:
    """Call the Gemini generateContent API.

    Returns the generated text, or None on ANY failure (no key, network
    error, quota, parse error). Callers must treat None as 'AI unavailable'
    and fall back to the rule engine.
    """
    api_key = _secrets_get("GEMINI_API_KEY")
    if not api_key:
        return None

    model = gemini_model()
    url = f"{_API_BASE}/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": max_output_tokens,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
        return text or None
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError,
            IndexError, json.JSONDecodeError, TimeoutError, OSError):
        return None


def build_assistant_prompt(measurement_summary: str, profile_summary: str,
                           top_recommendations: list[str]) -> str:
    """Compose a focused prompt for explaining existing rule-based advice."""
    recs = "\n".join(f"- {r}" for r in top_recommendations[:8])
    return (
        "You are AirAware AI, a careful urban air-quality assistant for "
        "Indian cities. Using ONLY the facts below, write a warm, concise, "
        "practical daily briefing (max ~250 words) for this person. Do not "
        "invent pollution numbers or medical claims; advise consulting a "
        "doctor for health decisions.\n\n"
        f"Measurement context:\n{measurement_summary}\n\n"
        f"Person's situation:\n{profile_summary}\n\n"
        f"Rule-engine recommendations to explain:\n{recs}\n\n"
        "Structure: (1) what today's air means for them, (2) the 3 most "
        "important actions today with reasons, (3) one indoor tip, (4) one "
        "green-transport suggestion. Plain language, no jargon."
    )
