"""Day-ahead air-quality planning outlook.

What this is
------------
A *planning estimate*, not an official forecast. AirAware does not have
access to a verified hourly forecast feed (CPCB publishes none publicly;
Google's Air Quality API forecast requires a separate paid key). Instead
this module combines:

1. **A diurnal climatology model** - typical urban Indian air-pollution
   patterns: morning and evening traffic peaks, a midday mixing dip, and
   overnight accumulation. Offsets are expressed in AQI *category* space
   (Good..Severe+), never as fabricated hourly AQI numbers.
2. **A session trend** - if the user has taken several readings during
   this browser session, a least-squares AQI slope nudges every window up
   or down. With fewer than 3 readings the trend is ignored.

Honesty rules enforced here:
- Output is always AQI *categories* and activity/ventilation guidance -
  never invented pollutant concentrations or hourly AQI values.
- Every result carries ``basis`` ("diurnal model" / "diurnal model +
  session trend"), ``confidence`` and explicit ``limitations`` that the
  UI must surface.
- Ozone-dominant readings shift the afternoon window UP (photochemical
  peak) instead of down - the model adapts to the dominant pollutant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from . import tzutil
from .aqi import CATEGORIES, is_outdoor_safe
from .data import MeasurementSet

# Canonical category order used for index arithmetic.
CAT_ORDER: list[str] = [c["name"] for c in CATEGORIES]
_CAT_INDEX = {name: i for i, name in enumerate(CAT_ORDER)}

# Time windows in LOCAL hours [start, end). Covers the full 24 h.
# Order matters: windows are sorted by start hour for display.
WINDOWS: list[tuple[str, str, int, int]] = [
    ("overnight", "Night (11 PM - 5 AM)", 23, 29),   # wraps past midnight
    ("early_morning", "Early morning (5-8 AM)", 5, 8),
    ("commute_am", "Morning commute (8-11 AM)", 8, 11),
    ("midday", "Midday (11 AM - 3 PM)", 11, 15),
    ("afternoon", "Afternoon (3-6 PM)", 15, 18),
    ("evening", "Evening (6-10 PM)", 18, 22),
    ("night", "Late night (10 PM - 11 PM)", 22, 23),
]

# Diurnal offsets in category-index units for a typical urban winter day
# driven by PM2.5/PM10/NO2 (traffic + inversion + biomass burning).
# Positive = worse than the daily mean, negative = better.
_DIURNAL_PM: dict[str, float] = {
    "overnight": -0.1,     # stable air but lower emissions
    "early_morning": +0.6, # rush hour + morning inversion
    "commute_am": +0.3,
    "midday": -0.7,        # boundary layer mixes highest
    "afternoon": -0.4,
    "evening": +0.6,       # evening rush + falling mixing height
    "night": +0.2,
}

# Ozone is photochemical: it builds through the sunny afternoon and is
# lowest overnight. When O3 dominates, the afternoon window is the risk.
_DIURNAL_O3: dict[str, float] = {
    "overnight": -0.5,
    "early_morning": -0.2,
    "commute_am": 0.0,
    "midday": +0.2,
    "afternoon": +0.7,     # peak photochemical production
    "evening": +0.4,       # persists after sunset briefly
    "night": -0.3,
}

UNCERTAINTY_BASE = 0.55      # category-index half-width of each band
UNCERTAINTY_PER_STALE_HOUR = 0.02
UNCERTAINTY_CAP = 1.6
TREND_MIN_POINTS = 3
TREND_MIN_SPAN_H = 3.0
TREND_MAX_SHIFT = 1.0        # category indices a trend may move windows
STALE_HOURS = 24.0

ACTIVITIES = ("light", "moderate", "heavy")


@dataclass
class OutlookWindow:
    """One time window of the planning outlook."""

    key: str
    label: str
    start_hour: float
    end_hour: float          # may exceed 24 for the overnight wrap
    cat_low: str             # best-case category name
    cat_high: str            # worst-case category name
    cat_mid_idx: float       # fractional category index for charting
    activity: dict[str, str]  # 'light'/'moderate'/'heavy' -> verdict
    ventilation: str         # 'open' | 'brief' | 'closed'
    ventilation_note: str


@dataclass
class DailyOutlook:
    """The full-day planning outlook plus provenance and caveats."""

    windows: list[OutlookWindow]
    basis: str               # what produced this outlook
    confidence: str          # 'low' | 'moderate' | 'high'
    dominant_pollutant: str | None
    generated_at: datetime
    measurement_age_hours: float | None
    trend_aqi_per_hour: float | None
    limitations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def best_window(self) -> OutlookWindow | None:
        """Window with the lowest (best) mid-band category index."""
        if not self.windows:
            return None
        return min(self.windows, key=lambda w: w.cat_mid_idx)

    @property
    def worst_window(self) -> OutlookWindow | None:
        if not self.windows:
            return None
        return max(self.windows, key=lambda w: w.cat_mid_idx)


def _cat_idx(name: str) -> float:
    try:
        return float(CAT_ORDER.index(name))
    except ValueError:
        return 0.0


def _cat_at(idx: float) -> str:
    i = round(idx)
    i = max(0, min(len(CAT_ORDER) - 1, i))
    return CAT_ORDER[i]


def _measurement_age_hours(m: MeasurementSet,
                           now: datetime) -> float | None:
    try:
        ts = m.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (now - ts).total_seconds() / 3600.0
        return max(0.0, age)
    except Exception:  # noqa: BLE001
        return None


def _aqi_slope(history: list[MeasurementSet]) -> tuple[float, int, float]:
    """Least-squares AQI slope (AQI/hour) over session history.

    Returns (slope, n_points, span_hours). slope is 0.0 with <3 usable
    points or a span under TREND_MIN_SPAN_H - callers treat that as
    'no reliable trend'.
    """
    pts = []
    for hm in history or []:
        aqi = hm.display_aqi
        if aqi is None:
            continue
        ts = hm.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        pts.append((ts.timestamp(), float(aqi)))
    pts = sorted(set(pts))
    if len(pts) < TREND_MIN_POINTS:
        return 0.0, len(pts), 0.0
    t0 = pts[0][0]
    span_h = (pts[-1][0] - t0) / 3600.0
    if span_h < TREND_MIN_SPAN_H:
        return 0.0, len(pts), span_h
    n = len(pts)
    sx = sum(p[0] - t0 for p in pts)
    sy = sum(p[1] for p in pts)
    sxx = sum((p[0] - t0) ** 2 for p in pts)
    sxy = sum((p[0] - t0) * p[1] for p in pts)
    denom = n * sxx - sx * sx
    if denom == 0:
        return 0.0, n, span_h
    # x is in seconds, y in AQI -> slope AQI/hour
    slope_h = (n * sxy - sx * sy) / denom * 3600.0
    return slope_h, n, span_h


def _activity_verdicts(cat_low_idx: float,
                       cat_high_idx: float) -> dict[str, str]:
    """Verdict per activity using the band edges.

    'good' if even the worst-case band allows it, 'caution' if only the
    best-case does, 'avoid' if even the best-case is too poor.
    """
    out: dict[str, str] = {}
    for act in ACTIVITIES:
        safe_lo, _ = is_outdoor_safe(_cat_at(cat_low_idx), act)
        safe_hi, _ = is_outdoor_safe(_cat_at(cat_high_idx), act)
        if safe_hi:
            out[act] = "good"
        elif safe_lo:
            out[act] = "caution"
        else:
            out[act] = "avoid"
    return out


def _ventilation(cat_low_idx: float,
                 cat_high_idx: float) -> tuple[str, str]:
    """Ventilation advice for the window's category band."""
    hi = _cat_at(cat_high_idx)
    lo = _cat_at(cat_low_idx)
    if hi in ("Good", "Satisfactory"):
        return ("open",
                "Air is clean enough to open windows and air out rooms.")
    if hi == "Moderate":
        if lo in ("Good", "Satisfactory"):
            return ("brief",
                    ("Brief ventilation (10-15 min) is reasonable; avoid "
                     "peak-traffic hours."))
        return ("brief",
                ("Ventilate briefly and only when outdoor activity "
                 "outside is low; use recirculated AC otherwise."))
    return ("closed",
            ("Keep windows closed; run AC/fans on recirculate or a "
             "purifier. Open windows only if indoor air feels stale."))


def build_outlook(m: MeasurementSet,
                  history: list[MeasurementSet] | None = None,
                  now: datetime | None = None,
                  tz: Optional[ZoneInfo] = None) -> DailyOutlook:
    """Build the day-ahead planning outlook for a measurement.

    ``history`` is an optional list of past MeasurementSets (e.g. the
    session history) used only for the AQI trend. ``now`` is injectable
    for tests; defaults to current UTC time. ``tz`` is the timezone the
    day windows are expressed in - defaults to the user's selected
    timezone (sidebar), never the server's.
    """
    now = now or datetime.now(timezone.utc)
    tz = tz or tzutil.user_tz()
    base_idx = _cat_idx(m.category_name or "Good")
    dominant = (m.result.dominant_pollutant
                if m.result else None) or (
                    next(iter(m.pollutants), None) if m.pollutants else None)
    diurnal = _DIURNAL_O3 if dominant == "o3" else _DIURNAL_PM

    age_h = _measurement_age_hours(m, now)
    slope, n_pts, span_h = _aqi_slope(history or [])

    # Trend contributes only a bounded category-index shift applied
    # uniformly to every window (conditions today move together more
    # than they diverge).
    trend_shift = 0.0
    trend_used = False
    if slope != 0.0 and n_pts >= TREND_MIN_POINTS:
        # AQI/hour -> rough category-index/hour: ~100 AQI per category.
        cat_slope = slope / 100.0
        # Project from measurement time to "now" so the outlook starts
        # near the observed level, not the session average.
        hours_since = age_h if age_h is not None else 0.0
        shift_now = cat_slope * hours_since
        trend_shift = max(-TREND_MAX_SHIFT,
                          min(TREND_MAX_SHIFT, shift_now))
        trend_used = abs(trend_shift) > 1e-6

    # Uncertainty grows with staleness; partial data adds a fixed amount.
    uncertainty = UNCERTAINTY_BASE
    if age_h is not None:
        uncertainty += min(UNCERTAINTY_CAP - UNCERTAINTY_BASE,
                           max(0.0, age_h - 6.0) * UNCERTAINTY_PER_STALE_HOUR)
    if m.result and m.result.is_partial:
        uncertainty += 0.25
    if m.is_sample:
        uncertainty += 0.4

    local_now = now.astimezone(tz)
    windows: list[OutlookWindow] = []
    for key, label, start, end in WINDOWS:
        # Centre of the window in local hours (handles the overnight wrap).
        if end > 24:
            centre = ((start + (end - 24)) / 2) % 24
        else:
            centre = (start + end) / 2
        # Hours from "now" to window centre, for trend projection.
        dh = (centre - local_now.hour - local_now.minute / 60.0) % 24
        if dh > 12:
            dh -= 24  # negative => window already passed today
        proj = trend_shift + (slope / 100.0) * dh if trend_used else 0.0
        proj = max(-TREND_MAX_SHIFT, min(TREND_MAX_SHIFT, proj))

        mid_idx = base_idx + diurnal[key] + proj
        half = uncertainty
        lo_idx = max(0.0, mid_idx - half)
        hi_idx = min(float(len(CAT_ORDER) - 1), mid_idx + half)
        activity = _activity_verdicts(lo_idx, hi_idx)
        vent, vent_note = _ventilation(lo_idx, hi_idx)
        windows.append(OutlookWindow(
            key=key, label=label,
            start_hour=float(start % 24), end_hour=float(end % 24),
            cat_low=_cat_at(lo_idx), cat_high=_cat_at(hi_idx),
            cat_mid_idx=mid_idx,
            activity=activity, ventilation=vent,
            ventilation_note=vent_note))

    # Confidence: high needs fresh, complete, non-sample data.
    if m.is_sample or (age_h is not None and age_h > STALE_HOURS):
        confidence = "low"
    elif (m.result and m.result.is_partial) or \
            (age_h is not None and age_h > 12):
        confidence = "moderate"
    else:
        confidence = "high"

    basis = "diurnal model"
    if trend_used:
        basis += " + session trend"

    limitations = [
        ("This is a planning estimate built from typical urban diurnal "
         "patterns - it is NOT an official or measured hourly forecast."),
        ("Real conditions can shift quickly with weather, wind, farm-fire "
         "smoke, dust storms or local sources; always check a live AQI "
         "source before important decisions."),
        ("Estimates describe likely AQI *categories*, not pollutant "
         "concentrations, and carry no medical certainty."),
    ]
    notes: list[str] = []
    if dominant == "o3":
        notes.append(("Ozone dominates today's reading - expect the "
                      "afternoon (sunny) window to be the riskiest, not "
                      "the morning."))
    if trend_used:
        direction = "rising" if slope > 0 else "falling"
        notes.append((f"Session readings show a {direction} trend "
                      f"(~{abs(slope):.0f} AQI/hour over {span_h:.0f} h); "
                      "windows are adjusted accordingly."))
    if age_h is not None and age_h > STALE_HOURS:
        notes.append((f"The reading is ~{age_h:.0f} h old - treat this "
                      "outlook as low-confidence."))

    return DailyOutlook(
        windows=windows, basis=basis, confidence=confidence,
        dominant_pollutant=dominant, generated_at=now,
        measurement_age_hours=age_h,
        trend_aqi_per_hour=slope if trend_used else None,
        limitations=limitations, notes=notes)
