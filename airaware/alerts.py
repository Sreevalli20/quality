"""Rule-based smart alerts from available measurements.

Alerts are generated only from actual measurement data - no fabricated
trends, no background push notifications. Severity labels are plain
language.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .data import MeasurementSet


@dataclass
class Alert:
    severity: str   # info | caution | warning | critical
    title: str
    detail: str


SEVERITY_META = {
    "info": {"label": "Info", "color": "#2563eb"},
    "caution": {"label": "Caution", "color": "#d97706"},
    "warning": {"label": "Warning", "color": "#ea580c"},
    "critical": {"label": "Critical", "color": "#dc2626"},
}


def evaluate_alerts(m: MeasurementSet | None,
                    stale_hours: float = 24.0) -> list[Alert]:
    """Generate alerts for the active measurement."""
    alerts: list[Alert] = []
    if m is None or m.display_aqi is None:
        alerts.append(Alert(
            severity="info",
            title="No air quality data loaded",
            detail=("Load a measurement (manual entry, CSV import or the "
                    "labelled sample set) to enable alerts and guidance.")))
        return alerts

    cat = m.category_name or "Good"

    # Staleness check - normalise naive timestamps to UTC first so a
    # naive reading can never crash the subtraction below.
    ts = m.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
    if age_h > stale_hours:
        alerts.append(Alert(
            severity="caution",
            title="Data may be outdated",
            detail=(f"This reading is ~{age_h:.0f} hours old. Pollution "
                    "changes quickly; refresh with a current measurement "
                    "before making outdoor plans.")))

    # Category-based alerts
    if cat in ("Very Poor", "Severe", "Severe+"):
        alerts.append(Alert(
            severity="critical" if cat != "Very Poor" else "warning",
            title=f"{cat} air quality - minimise all outdoor exposure",
            detail=("Sensitive groups should stay indoors; everyone should "
                    "avoid exertion outdoors and keep windows closed.")))
    elif cat == "Poor":
        alerts.append(Alert(
            severity="warning",
            title="Poor air quality",
            detail=("Outdoor exercise is not recommended. Use masks for "
                    "necessary trips and ventilate homes only with filtration.")))
    elif cat == "Moderate":
        alerts.append(Alert(
            severity="caution",
            title="Moderate air quality",
            detail=("Generally OK for most people; sensitive individuals "
                    "should reduce prolonged outdoor exertion.")))
    elif m.is_sample:
        alerts.append(Alert(
            severity="info",
            title="Showing sample demonstration data",
            detail="These are illustrative values, not live readings."))

    # Pollutant-specific notes
    if m.result:
        for r in m.result.pollutant_results:
            if r.pollutant == "pm25" and r.sub_index >= 300:
                alerts.append(Alert(
                    severity="warning",
                    title="PM2.5 is the dominant pollutant",
                    detail=(f"PM2.5 at {r.concentration:g} {r.unit} drives the "
                            "AQI. Fine particles penetrate deep into lungs - "
                            "filtration and masks matter most here.")))
            if r.pollutant == "o3" and r.sub_index >= 200:
                alerts.append(Alert(
                    severity="caution",
                    title="Elevated ozone (O3)",
                    detail=("Ozone peaks in afternoon sunlight. Limit midday "
                            "outdoor exertion; prefer early morning or evening.")))

    return alerts
