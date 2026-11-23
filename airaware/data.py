"""Measurement data model, sample data and CSV import.

Every measurement set carries provenance: source ('user', 'import',
'sample', 'external'), location, timestamp and per-pollutant values.
Sample data is always flagged and never presented as live.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from .aqi import MAX_REASONABLE, POLLUTANTS, calculate_aqi, AqiResult

MAX_CSV_BYTES = 2 * 1024 * 1024  # 2 MB upload limit
MAX_CSV_ROWS = 5000

SOURCE_LABELS = {
    "user": "User-provided measurement",
    "import": "Imported from CSV",
    "sample": "Sample demonstration data (NOT live)",
    "external": "Verified external source",
}


@dataclass
class MeasurementSet:
    """A single air-quality observation with full provenance."""

    location: str
    pollutants: dict[str, float] = field(default_factory=dict)
    aqi: Optional[float] = None  # user-supplied AQI, used only if no pollutants
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "user"
    notes: str = ""
    result: Optional[AqiResult] = field(default=None, repr=False)

    def finalize(self) -> "MeasurementSet":
        """Compute AQI from pollutants (preferred) or use supplied AQI."""
        if self.pollutants:
            self.result = calculate_aqi(self.pollutants)
        elif self.aqi is not None:
            import math
            from .aqi import category_for
            if not math.isfinite(float(self.aqi)) or float(self.aqi) < 0:
                self.aqi = None
                self.result = calculate_aqi({})
                return self
            cat = category_for(float(self.aqi))
            self.result = AqiResult(aqi=round(float(self.aqi), 1),
                                    category=cat, dominant_pollutant=None,
                                    pollutant_results=[],
                                    notes=["AQI supplied directly; pollutant "
                                           "breakdown unavailable."])
        else:
            self.result = calculate_aqi({})
        return self

    @property
    def display_aqi(self) -> Optional[float]:
        if self.result and self.result.aqi is not None:
            return self.result.aqi
        return self.aqi

    @property
    def category_name(self) -> Optional[str]:
        if self.result and self.result.category:
            return self.result.category["name"]
        return None

    @property
    def source_label(self) -> str:
        return SOURCE_LABELS.get(self.source, self.source)

    @property
    def is_sample(self) -> bool:
        return self.source == "sample"


# ---------------------------------------------------------------------------
# Sample demonstration data (clearly labelled, not live readings)
# ---------------------------------------------------------------------------

SAMPLE_MEASUREMENTS: list[MeasurementSet] = [
    MeasurementSet(
        location="New Delhi (Connaught Place)",
        pollutants={"pm25": 142, "pm10": 287, "no2": 95, "so2": 18},
        timestamp=datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc),
        source="sample",
        notes="Illustrative winter-morning values typical of Delhi NCR.",
    ),
    MeasurementSet(
        location="Mumbai (Bandra)",
        pollutants={"pm25": 48, "pm10": 92, "no2": 42, "co": 1.4},
        timestamp=datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc),
        source="sample",
        notes="Illustrative coastal-city values; sea breeze disperses pollutants.",
    ),
    MeasurementSet(
        location="Bengaluru (Indiranagar)",
        pollutants={"pm25": 61, "pm10": 118, "no2": 55, "o3": 88},
        timestamp=datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc),
        source="sample",
        notes="Illustrative moderate readings with photochemical ozone contribution.",
    ),
    MeasurementSet(
        location="Chennai (T Nagar)",
        pollutants={"pm25": 34, "pm10": 71, "no2": 38, "so2": 12, "co": 0.9},
        timestamp=datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc),
        source="sample",
        notes="Illustrative satisfactory readings for demonstration.",
    ),
]

for _m in SAMPLE_MEASUREMENTS:
    _m.finalize()

INDIAN_CITIES = [
    "New Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata", "Hyderabad",
    "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Kanpur", "Nagpur",
    "Surat", "Indore", "Bhopal", "Patna", "Varanasi", "Agra", "Meerut",
    "Ludhiana", "Custom / other location",
]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_pollutant_value(pollutant: str, value: float) -> Optional[str]:
    """Return an error string if invalid, else None."""
    if pollutant not in POLLUTANTS:
        return f"Unknown pollutant '{pollutant}'."
    if value is None:
        return "Value is required."
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "Value must be a number."
    if v < 0:
        return "Value cannot be negative."
    if v > MAX_REASONABLE.get(pollutant, 1e9):
        return (f"Value {v:g} {POLLUTANTS[pollutant]['unit']} is implausibly "
                f"high (max expected ~{MAX_REASONABLE[pollutant]:g}). Check units.")
    return None


def validate_aqi_value(aqi: float) -> Optional[str]:
    if aqi is None:
        return "AQI value is required."
    try:
        a = float(aqi)
    except (TypeError, ValueError):
        return "AQI must be a number."
    if a < 0:
        return "AQI cannot be negative."
    if a > 999:
        return "AQI above 999 is not supported by the CPCB scale."
    return None


# ---------------------------------------------------------------------------
# CSV import
# ---------------------------------------------------------------------------

# Accepted column-name aliases (case-insensitive, punctuation-insensitive)
_COLUMN_ALIASES: dict[str, str] = {
    "pm25": "pm25", "pm2.5": "pm25", "pm2_5": "pm25", "pm25_ugm3": "pm25",
    "pm25ugm3": "pm25", "pm25 (ug/m3)": "pm25",
    "pm10": "pm10", "pm10_ugm3": "pm10", "pm10ugm3": "pm10",
    "no2": "no2", "no2_ugm3": "no2", "nitrogen dioxide": "no2",
    "so2": "so2", "so2_ugm3": "so2", "sulphur dioxide": "so2", "sulfur dioxide": "so2",
    "co": "co", "co_mgm3": "co", "co (mg/m3)": "co", "carbon monoxide": "co",
    "o3": "o3", "o3_ugm3": "o3", "ozone": "o3",
    "nh3": "nh3", "nh3_ugm3": "nh3", "ammonia": "nh3",
    "aqi": "aqi", "air quality index": "aqi", "naqi": "aqi",
    "location": "location", "city": "location", "station": "location",
    "timestamp": "timestamp", "datetime": "timestamp", "date": "timestamp",
    "time": "timestamp",
}


def _normalise_header(name: str) -> str:
    return str(name).strip().lower()


def parse_measurements_csv(file_bytes: bytes, filename: str = "upload.csv"
                            ) -> tuple[list[MeasurementSet], list[str]]:
    """Parse uploaded CSV bytes into MeasurementSet objects.

    Returns (measurements, warnings). Raises ValueError on unusable files.
    Expected columns: pollutant names (aliases accepted), optional 'aqi',
    optional 'location', optional 'timestamp'. One row = one observation.
    """
    if len(file_bytes) > MAX_CSV_BYTES:
        raise ValueError("File exceeds the 2 MB size limit.")
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), on_bad_lines="skip")
    except Exception as exc:  # noqa: BLE001 - surface a friendly message
        raise ValueError(f"Could not parse CSV: {exc}") from exc

    if df.empty:
        raise ValueError("CSV contains no data rows.")
    if len(df) > MAX_CSV_ROWS:
        raise ValueError(f"CSV has {len(df)} rows; limit is {MAX_CSV_ROWS}.")

    # Map headers to canonical field names
    rename: dict[str, str] = {}
    for col in df.columns:
        key = _normalise_header(col)
        if key in _COLUMN_ALIASES:
            rename[col] = _COLUMN_ALIASES[key]
    df = df.rename(columns=rename)

    pollutant_cols = [c for c in POLLUTANTS if c in df.columns]
    has_aqi = "aqi" in df.columns
    if not pollutant_cols and not has_aqi:
        raise ValueError(
            "CSV must contain at least one recognised pollutant column "
            "(pm25, pm10, no2, so2, co, o3, nh3) or an 'aqi' column. "
            f"Found columns: {', '.join(df.columns)}"
        )

    measurements: list[MeasurementSet] = []
    warnings: list[str] = []

    for idx, row in df.iterrows():
        pollutants: dict[str, float] = {}
        invalid: list[str] = []
        for p in pollutant_cols:
            raw = row.get(p)
            if pd.isna(raw):
                continue
            try:
                v = float(raw)
            except (TypeError, ValueError):
                invalid.append(f"{POLLUTANTS[p]['name']} row {idx + 2}")
                continue
            err = validate_pollutant_value(p, v)
            if err:
                invalid.append(f"{POLLUTANTS[p]['name']} row {idx + 2}: {err}")
                continue
            pollutants[p] = v
        if invalid:
            warnings.extend(invalid[:3])

        aqi_val: Optional[float] = None
        if has_aqi and not pollutants and not pd.isna(row.get("aqi")):
            try:
                aqi_val = float(row["aqi"])
            except (TypeError, ValueError):
                warnings.append(f"aqi row {idx + 2}: not a number, skipped")
                aqi_val = None
            else:
                err = validate_aqi_value(aqi_val)
                if err:
                    warnings.append(f"aqi row {idx + 2}: {err}, skipped")
                    aqi_val = None

        location = str(row["location"]) if "location" in df.columns and not pd.isna(row.get("location")) else "Imported location"

        ts = datetime.now(timezone.utc)
        if "timestamp" in df.columns and not pd.isna(row.get("timestamp")):
            try:
                ts = pd.to_datetime(row["timestamp"], errors="raise").to_pydatetime()
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:  # noqa: BLE001
                warnings.append(f"timestamp row {idx + 2}: unparseable, using import time")

        m = MeasurementSet(location=location, pollutants=pollutants,
                          aqi=aqi_val, timestamp=ts, source="import",
                          notes=f"Row {idx + 2} of {filename}")
        m.finalize()
        if m.display_aqi is not None:
            measurements.append(m)

    if not measurements:
        raise ValueError("No usable measurement rows found in the CSV.")

    return measurements, warnings[:10]
