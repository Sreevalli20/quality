"""Small text-normalisation helpers shared across AirAware modules."""

from __future__ import annotations

_TRANSLATION = str.maketrans({
    "µ": "u", "μ": "u", "³": "3", "²": "2", "°": "",
})


def normalise_token(value: object) -> str:
    """Reduce a header, field name or unit to lowercase ASCII alphanumerics.

    This makes matching insensitive to case, whitespace, punctuation and
    common unit spellings, e.g. "PM2.5", "PM 2.5" and "PM2.5 (µg/m3)".
    """
    s = str(value or "").strip().lower().translate(_TRANSLATION)
    return "".join(ch for ch in s if ch.isascii() and ch.isalnum())
