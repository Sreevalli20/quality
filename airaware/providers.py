"""Live air-quality data providers (optional, credential-gated).

Architecture
------------
- ``AirQualityProvider`` is the provider contract: ``configured()``,
  ``health_check()`` and ``latest(location_hint)``.
- ``OpenAQProvider`` talks to the OpenAQ v3 API and activates only when
  ``OPENAQ_API_KEY`` is present in Streamlit secrets. Additional providers
  can be added to ``_PROVIDER_CLASSES`` without touching the UI.
- ``fetch_latest()`` tries configured providers in order (failover) and
  returns the first real measurement. ``None`` means "no live data" -
  callers must fall back to manual entry / CSV / labelled samples and must
  never fabricate a reading.

Honesty rules enforced here:
- Every result carries ``source="external"`` plus the provider and station
  name in ``notes``.
- The measurement timestamp comes from the API, not from "now".
- Readings older than ``STALE_AFTER_HOURS`` are still returned (they are
  real data) but flagged in ``notes``; the alerts layer already warns on
  stale data. Old readings are never relabelled as current.
"""

from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Protocol

try:
    import streamlit as st
except Exception:  # noqa: BLE001 # pragma: no cover - unit tests without runtime
    st = None  # type: ignore[assignment]

import airaware.secretsutil as secretsutil  # noqa: PLR0402

from .aqi import POLLUTANTS
from .data import MeasurementSet, validate_pollutant_value
from .textutil import normalise_token

_API_BASE = "https://api.openaq.org/v3"
_TIMEOUT_S = 15
STALE_AFTER_HOURS = 24.0

# OpenAQ parameter names (normalised) -> our pollutant keys.
_PARAM_MAP = {"pm25": "pm25", "pm10": "pm10", "no2": "no2", "so2": "so2",
              "co": "co", "o3": "o3", "nh3": "nh3"}

# Expected units per pollutant in canonical CPCB units.
_EXPECTED_UNIT = {"pm25": "ugm3", "pm10": "ugm3", "no2": "ugm3",
                  "so2": "ugm3", "o3": "ugm3", "nh3": "ugm3", "co": "mgm3"}


def _secrets_get(key: str, default=None):
    """Safely read a secret; returns default outside Streamlit runtime.

    Thin wrapper kept as a module-level name so tests can monkeypatch
    ``providers._secrets_get``; the implementation lives in secretsutil.
    """
    return secretsutil.secrets_get(key, default)


class ProviderError(Exception):
    """A provider failed in a way the UI should surface honestly."""


class AirQualityProvider(Protocol):
    """Contract every live-data provider must satisfy."""

    name: str

    def configured(self) -> bool:
        """True when credentials/config make this provider usable."""
        ...

    def health_check(self) -> dict:
        """Return {'ok': bool, 'detail': str} - never raises."""
        ...

    def latest(self, location_hint: str = "") -> MeasurementSet | None:
        """Return the freshest real measurement, or None on any failure."""
        ...


def _http_json(url: str, params: dict, api_key: str) -> dict:
    """GET JSON from the provider API. Raises ProviderError on failure."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"X-API-Key": api_key, "Accept": "application/json"},
        method="GET")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # normalise every failure
        raise ProviderError(f"{type(exc).__name__}: request failed") from exc


class OpenAQProvider:
    """OpenAQ v3 provider. Requires OPENAQ_API_KEY in Streamlit secrets."""

    name = "OpenAQ"

    def configured(self) -> bool:
        return bool(_secrets_get("OPENAQ_API_KEY"))

    def _get(self, path: str, params: dict | None = None) -> dict:
        key = _secrets_get("OPENAQ_API_KEY")
        if not key:
            raise ProviderError("OPENAQ_API_KEY not configured")
        return _http_json(f"{_API_BASE}{path}", params or {}, str(key))

    def health_check(self) -> dict:
        if not self.configured():
            return {"ok": False, "detail": "OPENAQ_API_KEY not configured"}
        try:
            data = self._get("/parameters", {"limit": 1})
            n = len(data.get("results") or [])
            return {"ok": n > 0,
                    "detail": f"API reachable ({n} parameter(s) visible)"}
        except ProviderError as exc:
            return {"ok": False, "detail": str(exc)}

    def latest(self, location_hint: str = "") -> MeasurementSet | None:
        """Fetch the freshest multi-pollutant reading for a location.

        ``location_hint`` is matched against OpenAQ's ``city`` field;
        when empty the most recently updated station worldwide is used.
        Returns None on ANY failure - never raises to the UI.
        """
        try:
            # Fetch the most recently updated stations, then match the
            # optional hint client-side - this does not depend on which
            # query filters the provider API happens to support.
            params = {"limit": 100, "order_by": "lastUpdated", "sort": "desc"}
            locs = self._get("/locations", params).get("results") or []
            if not locs:
                return None
            hint = (location_hint or "").strip().lower()
            loc = locs[0]
            if hint:
                for cand in locs:
                    hay = " ".join(str(cand.get(k) or "")
                                   for k in ("name", "city", "country")).lower()
                    if hint in hay:
                        loc = cand
                        break
            loc_id = loc.get("id")
            if loc_id is None:
                return None

            latest = self._get(f"/locations/{loc_id}/latest").get("results") or []
            pollutants: dict[str, float] = {}
            seen_params: set[str] = set()
            newest_ts: datetime | None = None
            skipped: list[str] = []

            for item in latest:
                pname = normalise_token((item.get("parameter") or {}).get("name"))
                key = _PARAM_MAP.get(pname)
                if key is None or key in seen_params:
                    continue
                seen_params.add(key)
                unit = normalise_token(item.get("unit"))
                if unit != _EXPECTED_UNIT[key]:
                    skipped.append(f"{POLLUTANTS[key]['name']} ({unit or 'unknown unit'})")
                    continue
                try:
                    value = float(item.get("value"))
                except (TypeError, ValueError):
                    continue
                if not math.isfinite(value):
                    continue
                if validate_pollutant_value(key, value) is not None:
                    continue
                pollutants[key] = value
                raw_ts = item.get("datetime")
                try:
                    t = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
                    if t.tzinfo is None:
                        t = t.replace(tzinfo=timezone.utc)
                    newest_ts = t if newest_ts is None or t > newest_ts else newest_ts
                except (TypeError, ValueError):
                    pass

            if not pollutants:
                return None

            station = str(loc.get("name") or loc.get("city") or hint or "unknown station")
            ts = newest_ts or datetime.now(timezone.utc)
            notes = [(f"Live data from OpenAQ station '{station}' "
                      f"(location id {loc_id}); provider: OpenAQ v3 API.")]
            if skipped:
                notes.append("Skipped pollutant(s) with unexpected units: "
                             + ", ".join(skipped) + ".")
            if newest_ts is None:
                notes.append("Provider did not return a measurement "
                             "timestamp; fetch time recorded instead.")
            else:
                age_h = (datetime.now(timezone.utc) - newest_ts).total_seconds() / 3600
                if age_h > STALE_AFTER_HOURS:
                    notes.append(
                        f"WARNING: newest provider reading is ~{age_h:.0f} "
                        "hours old - this is the freshest available, "
                        "not a current measurement.")

            return MeasurementSet(
                location=station, pollutants=pollutants, timestamp=ts,
                source="external",
                notes="; ".join(notes),
                synthetic_timestamp=newest_ts is None).finalize()
        except Exception:  # noqa: BLE001 - provider failure -> None, honestly
            return None


_PROVIDER_CLASSES = (OpenAQProvider,)


def available_providers() -> list[AirQualityProvider]:
    """Configured providers in failover order."""
    out: list[AirQualityProvider] = []
    for cls in _PROVIDER_CLASSES:
        p = cls()
        if p.configured():
            out.append(p)
    return out


# A provider health check is a real network call. The About page reruns on
# every widget interaction, so results are cached briefly - 5 minutes is
# fresh enough for a status display and avoids hammering the API. The cache
# key is the provider *class* (provider instances are not hashable by
# st.cache_data); all current providers are stateless, so checking a fresh
# instance is equivalent.
_HEALTH_CHECK_TTL_S = 300


def _provider_health(provider_cls: type) -> dict:
    return provider_cls().health_check()


if st is not None:
    _provider_health_cached = st.cache_data(
        ttl=_HEALTH_CHECK_TTL_S, show_spinner=False)(_provider_health)
else:  # pragma: no cover - unit tests without runtime
    _provider_health_cached = _provider_health


def provider_status() -> list[dict]:
    """Status of every known provider, for the About page."""
    out = []
    for cls in _PROVIDER_CLASSES:
        p = cls()
        out.append({"name": p.name, "configured": p.configured(),
                    "health": _provider_health_cached(cls)
                    if p.configured() else None})
    return out


def fetch_latest(location_hint: str = "") -> MeasurementSet | None:
    """Try each configured provider in order; return first real result."""
    for provider in available_providers():
        m = provider.latest(location_hint)
        if m is not None and m.display_aqi is not None:
            return m
    return None
