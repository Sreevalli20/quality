"""User-timezone helpers for time-of-day features.

The day-ahead planning outlook and the daily-plan "now" marker describe
*local* hours. ``datetime.now().astimezone()`` resolves against the
*server's* timezone - fine on a developer laptop, wrong on Streamlit
Community Cloud (UTC) for users elsewhere. These helpers let the user
pick their timezone (kept in ``st.session_state["user_tz"]``) so windows
and slot markers reflect their clock, not the server's.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    import streamlit as st
except Exception:  # noqa: BLE001 # pragma: no cover - unit tests without runtime
    st = None  # type: ignore[assignment]

# The audience is Indian cities; IST is the sensible default. Users
# elsewhere can change it in the sidebar.
DEFAULT_TZ = "Asia/Kolkata"

# A compact, curated list - covers India plus common remote-work zones.
TZ_OPTIONS = [
    "Asia/Kolkata", "Asia/Dubai", "Asia/Singapore", "Asia/Tokyo",
    "Australia/Sydney", "Europe/London", "Europe/Berlin",
    "America/New_York", "America/Los_Angeles", "UTC",
]


def _session_get(key: str, default=None):
    """Safely read session state; returns default outside Streamlit."""
    if st is None:
        return default
    try:
        return st.session_state.get(key, default)
    except Exception:  # noqa: BLE001 - no runtime context in tests
        return default


def user_timezone_name() -> str:
    """The IANA name of the user's chosen timezone."""
    name = _session_get("user_tz") or DEFAULT_TZ
    try:
        ZoneInfo(str(name))
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return DEFAULT_TZ
    return str(name)


def user_tz() -> ZoneInfo:
    """ZoneInfo for the user's chosen timezone."""
    try:
        return ZoneInfo(user_timezone_name())
    except Exception:  # noqa: BLE001 - never break rendering over a tz
        return ZoneInfo(DEFAULT_TZ)


def local_now(tz: ZoneInfo | None = None) -> datetime:
    """Current time expressed in the user's timezone (aware)."""
    return datetime.now(timezone.utc).astimezone(tz or user_tz())


def tz_label() -> str:
    """Short human label for the active timezone, e.g. 'IST (UTC+5:30)'."""
    name = user_timezone_name()
    try:
        offset = local_now().strftime("UTC%z")
        offset = offset[:-2] + ":" + offset[-2:] if offset else ""
        return f"{name} ({offset})"
    except Exception:  # noqa: BLE001
        return name
