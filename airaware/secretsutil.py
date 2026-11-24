"""Shared Streamlit-secrets accessor.

Both ``airaware.ai`` and ``airaware.providers`` need the same defensive
read of ``st.secrets`` (which is unavailable or malformed outside the
Streamlit runtime and in unit tests). Keeping one implementation here
avoids two copies drifting apart; each consumer still exposes its own
``_secrets_get`` name so tests can monkeypatch it per module.
"""

from __future__ import annotations

try:
    import streamlit as st
except Exception:  # noqa: BLE001 # pragma: no cover - unit tests without runtime
    st = None  # type: ignore[assignment]


def secrets_get(key: str, default=None):
    """Safely read a secret; returns default outside Streamlit runtime."""
    if st is None:
        return default
    try:
        return st.secrets.get(key, default)
    except Exception:  # noqa: BLE001 - secrets may be unavailable/malformed
        return default
