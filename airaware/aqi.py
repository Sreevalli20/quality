"""CPCB (India) Air Quality Index calculation.

Implements the documented CPCB / NAMP methodology:
- Pollutant-specific 24-hour (or 8-hour for O3) breakpoints are mapped to
  AQI sub-index ranges via piecewise-linear interpolation.
- The overall AQI is the maximum of the available sub-indices, and the
  corresponding pollutant is reported as the dominant pollutant.
- The overall AQI is only computed when at least one valid pollutant
  measurement is supplied; incomplete measurements never produce an
  "official" AQI - they produce partial sub-indices only.

Reference: CPCB National Air Quality Index (NAQI) methodology.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Optional

# CPCB pollutant definitions: (display name, unit, averaging period)
POLLUTANTS: dict[str, dict[str, str]] = {
    "pm25": {"name": "PM2.5", "unit": "ug/m3", "period": "24-hour"},
    "pm10": {"name": "PM10", "unit": "ug/m3", "period": "24-hour"},
    "no2": {"name": "NO2", "unit": "ug/m3", "period": "24-hour"},
    "so2": {"name": "SO2", "unit": "ug/m3", "period": "24-hour"},
    "co": {"name": "CO", "unit": "mg/m3", "period": "24-hour"},
    "o3": {"name": "O3", "unit": "ug/m3", "period": "8-hour"},
    "nh3": {"name": "NH3", "unit": "ug/m3", "period": "24-hour"},
}

# CPCB breakpoints: for each pollutant, lists of (concentration_low,
# concentration_high, aqi_low, aqi_high). Index i covers breakpoint
# range i; concentrations above the last high cap at AQI 500+.
_BREAKPOINTS: dict[str, list[tuple[float, float, float, float]]] = {
    "pm25": [
        (0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200),
        (91, 120, 201, 300), (121, 250, 301, 400), (251, 500, 401, 500),
    ],
    "pm10": [
        (0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200),
        (251, 350, 201, 300), (351, 430, 301, 400), (431, 510, 401, 500),
    ],
    "no2": [
        (0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200),
        (181, 280, 201, 300), (281, 400, 301, 400), (401, 800, 401, 500),
    ],
    "so2": [
        (0, 40, 0, 50), (41, 80, 51, 100), (81, 380, 101, 200),
        (381, 800, 201, 300), (801, 1600, 301, 400), (1601, 2000, 401, 500),
    ],
    "co": [
        (0, 1, 0, 50), (1.1, 2, 51, 100), (2.1, 5, 101, 200),
        (5.1, 10, 201, 300), (10.1, 20, 301, 400), (20.1, 40, 401, 500),
    ],
    "o3": [
        (0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200),
        (169, 208, 201, 300), (209, 748, 301, 400), (749, 1800, 401, 500),
    ],
    "nh3": [
        (0, 200, 0, 50), (201, 400, 51, 100), (401, 800, 101, 200),
        (801, 1200, 201, 300), (1201, 1800, 301, 400), (1801, 2400, 401, 500),
    ],
}

# Pollutant-specific acceptable upper bounds for input validation
# (values beyond the worst breakpoint are flagged, not silently accepted).
MAX_REASONABLE: dict[str, float] = {
    "pm25": 1000.0, "pm10": 2000.0, "no2": 4000.0, "so2": 5000.0,
    "co": 100.0, "o3": 3000.0, "nh3": 5000.0,
}

AQI_MAX = 500.0
AQI_EXTREME_THRESHOLD = 500.0

CATEGORIES: list[dict] = [
    {"name": "Good", "min": 0, "max": 50, "color": "#1a9850",
     "hex": "#1a9850",
     "summary": "Air quality is satisfactory and poses little or no risk."},
    {"name": "Satisfactory", "min": 51, "max": 100, "color": "#91cf60",
     "hex": "#66a61e",
     "summary": "Air quality is acceptable; minor breathing discomfort possible for very sensitive people."},
    {"name": "Moderate", "min": 101, "max": 200, "color": "#fee08b",
     "hex": "#d9a400",
     "summary": "Air quality is acceptable for most people; sensitive groups may experience health effects."},
    {"name": "Poor", "min": 201, "max": 300, "color": "#fc8d59",
     "hex": "#e66101",
     "summary": "Breathing discomfort for most people on prolonged exposure."},
    {"name": "Very Poor", "min": 301, "max": 400, "color": "#d73027",
     "hex": "#d73027",
     "summary": "Respiratory illness on prolonged exposure; serious health impact for vulnerable groups."},
    {"name": "Severe", "min": 401, "max": 500, "color": "#a50026",
     "hex": "#7f0000",
     "summary": "Health impacts severe even during short exposure; immediate action advised."},
    {"name": "Severe+", "min": 501, "max": float("inf"), "color": "#7f0000",
     "hex": "#4d0000",
     "summary": "Air quality is hazardous. Avoid all outdoor exertion."},
]


def pollutant_sub_index(pollutant: str, concentration: float) -> Optional[float]:
    """Return the AQI sub-index for one pollutant concentration.

    Returns None for unknown pollutants or invalid (negative/NaN) values.
    Concentrations above the worst breakpoint extrapolate the final segment
    uncapped; values beyond AQI 500 display in the "Severe+" category.
    """
    if pollutant not in _BREAKPOINTS:
        return None
    if concentration is None:
        return None
    try:
        c = float(concentration)
    except (TypeError, ValueError):
        return None
    if c < 0 or math.isnan(c) or math.isinf(c):
        return None

    # Piecewise-linear curve through every breakpoint corner point.
    # CPCB bands are declared as integer ranges (e.g. 0-30, 31-60) leaving
    # 1-unit gaps; interpolating continuously across the corners avoids the
    # artificial AQI jumps a band-wise lookup would produce (e.g. PM2.5
    # 30.0 -> 50 but 30.01 -> 51).
    pts: list[tuple[float, float]] = []
    for bp_lo, bp_hi, aqi_lo, aqi_hi in _BREAKPOINTS[pollutant]:
        pts.append((float(bp_lo), float(aqi_lo)))
        pts.append((float(bp_hi), float(aqi_hi)))
    if c <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in pairwise(pts):
        if c <= x1:
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (c - x0) / (x1 - x0)
    # Above the worst CPCB breakpoint: extrapolate the final segment, uncapped.
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    return y1 + (y1 - y0) / (x1 - x0) * (c - x1)


def category_for(aqi: float) -> dict:
    """Return the CPCB category dict for an AQI value.

    Category bounds are integers but interpolated/user-supplied AQI can be
    fractional (e.g. 50.5); the first category whose upper bound is >= the
    value wins, so gap values map sensibly instead of falling through.
    """
    if aqi is None or not math.isfinite(float(aqi)):
        return CATEGORIES[0]
    value = float(aqi)
    for cat in CATEGORIES:
        if value <= cat["max"]:
            return cat
    return CATEGORIES[-1]


def category_color(name: str | None) -> str:
    """Hex colour for a CPCB category name."""
    for cat in CATEGORIES:
        if cat["name"] == name:
            return cat["color"]
    return "#999999"


@dataclass
class PollutantResult:
    pollutant: str
    concentration: float
    unit: str
    sub_index: float

    @property
    def label(self) -> str:
        info = POLLUTANTS[self.pollutant]
        return f"{info['name']} ({info['period']})"


@dataclass
class AqiResult:
    """Result of an AQI calculation from pollutant measurements."""

    aqi: Optional[float]
    category: Optional[dict]
    dominant_pollutant: Optional[str]
    pollutant_results: list[PollutantResult] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def is_partial(self) -> bool:
        """True when only some pollutants were measured."""
        return len(self.pollutant_results) < len(POLLUTANTS)


def calculate_aqi(pollutants: dict[str, Optional[float]]) -> AqiResult:
    """Calculate AQI and sub-indices from a pollutant -> concentration map.

    Only keys present with valid numeric values are used. The overall AQI
    is the maximum sub-index (CPCB method). If no valid pollutant exists,
    aqi is None.
    """
    results: list[PollutantResult] = []
    rejected: list[str] = []
    for key, raw in pollutants.items():
        if raw is None:
            continue
        sub = pollutant_sub_index(key, raw)
        if sub is None:
            rejected.append(key)
            continue
        info = POLLUTANTS[key]
        results.append(PollutantResult(
            pollutant=key, concentration=float(raw),
            unit=info["unit"], sub_index=sub,
        ))

    notes: list[str] = []
    if rejected:
        names = ", ".join(POLLUTANTS[k]["name"] for k in rejected)
        notes.append(f"Ignored invalid value(s) for: {names}.")

    if not results:
        notes.append("No valid pollutant measurements supplied.")
        return AqiResult(aqi=None, category=None, dominant_pollutant=None,
                         pollutant_results=[], notes=notes)

    best = max(results, key=lambda r: r.sub_index)
    # CPCB reports AQI rounded to integer; keep one decimal for transparency.
    aqi_rounded = round(best.sub_index, 1)
    cat = category_for(aqi_rounded)
    if len(results) < len(POLLUTANTS):
        notes.append(
            "Partial measurement set: AQI shown is the maximum of measured "
            "pollutant sub-indices only. The true AQI could be higher if "
            "unmeasured pollutants are elevated."
        )
    return AqiResult(
        aqi=aqi_rounded,
        category=cat,
        dominant_pollutant=best.pollutant,
        pollutant_results=results,
        notes=notes,
    )


def aqi_description(aqi: float, category: dict) -> str:
    """One-line plain-language summary of an AQI reading."""
    return f"AQI {aqi:.0f} - {category['name']}: {category['summary']}"


def is_outdoor_safe(category_name: str, activity: str = "moderate") -> tuple[bool, str]:
    """Return (safe, explanation) for outdoor activity given AQI category.

    activity: 'light' (walking), 'moderate' (jogging, cycling),
    'heavy' (intense exercise, sports).
    """
    order = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe", "Severe+"]
    try:
        idx = order.index(category_name)
    except ValueError:
        return False, "Unknown air quality category."

    if activity == "heavy":
        safe_idx = 1   # only Good/Satisfactory
    elif activity == "moderate":
        safe_idx = 2   # up to Moderate
    else:
        safe_idx = 3   # light activity ok up to Poor with caution

    safe = idx <= safe_idx
    if safe:
        return True, f"{category_name} conditions are acceptable for {activity} outdoor activity."
    limit = order[safe_idx]
    return False, (f"{category_name} air is not recommended for {activity} outdoor "
                   f"activity (safe up to {limit}).")
