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

from .aqi import MAX_REASONABLE, POLLUTANTS, AqiResult, calculate_aqi

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
    # True when the timestamp was synthesised (e.g. CSV row had none) rather
    # than read from the data - used for dedupe and honest provenance.
    synthetic_timestamp: bool = False
    result: Optional[AqiResult] = field(default=None, repr=False)

    def finalize(self) -> MeasurementSet:
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

# Header normalisation: lowercase, unify micro/mu and superscripts, then
# drop every character that is not a-z/0-9. This makes matching insensitive
# to case, whitespace, punctuation and common unit spellings, e.g.
# "PM2.5", "PM 2.5", "PM2.5 (µg/m3)", "pm2_5_ugm3" all reduce consistently.
_HEADER_TRANS = str.maketrans({
    "µ": "u", "μ": "u", "³": "3", "²": "2", "°": "",
})


def _normalise_header(name: str) -> str:
    s = str(name).strip().lower().translate(_HEADER_TRANS)
    return "".join(ch for ch in s if ch.isascii() and ch.isalnum())


# Canonical pollutant columns. Keys are _normalise_header() output.
# Values: canonical field name ('pm25', 'location', 'timestamp', ...).
_COLUMN_ALIASES_RAW: dict[str, str] = {
    # PM2.5
    "pm25": "pm25", "pm25ugm3": "pm25", "pm25mgm3": "pm25",
    "pm25ug": "pm25",
    # PM10
    "pm10": "pm10", "pm10ugm3": "pm10", "pm10mgm3": "pm10",
    # NO2
    "no2": "no2", "no2ugm3": "no2", "no2mgm3": "no2",
    "nitrogendioxide": "no2",
    # SO2
    "so2": "so2", "so2ugm3": "so2", "so2mgm3": "so2",
    "sulphurdioxide": "so2", "sulfurdioxide": "so2",
    # CO (canonical unit mg/m3)
    "co": "co", "comgm3": "co", "cougm3": "co", "coug": "co",
    "carbonmonoxide": "co",
    # O3
    "o3": "o3", "o3ugm3": "o3", "o3mgm3": "o3", "ozone": "o3",
    # NH3
    "nh3": "nh3", "nh3ugm3": "nh3", "nh3mgm3": "nh3", "ammonia": "nh3",
    # AQI
    "aqi": "aqi", "airqualityindex": "aqi", "naqi": "aqi",
    # provenance columns
    "location": "location", "city": "location", "station": "location",
    "stationname": "location", "areaname": "location",
    "timestamp": "timestamp", "datetime": "timestamp", "date": "timestamp",
    "time": "timestamp", "lastupdated": "timestamp", "updated": "timestamp",
    "utcts": "timestamp", "utcts_epoch": "timestamp_epoch",
}

# Columns whose values are in a NON-canonical unit and must be converted.
# Maps normalised header -> (pollutant, multiplier to canonical unit).
# CPCB canonical units: PM2.5/PM10/NO2/SO2/O3/NH3 in ug/m3, CO in mg/m3.
_UNIT_CONVERSIONS_RAW: dict[str, tuple[str, float]] = {
    "pm25mgm3": ("pm25", 1000.0), "pm10mgm3": ("pm10", 1000.0),
    "no2mgm3": ("no2", 1000.0), "so2mgm3": ("so2", 1000.0),
    "o3mgm3": ("o3", 1000.0), "nh3mgm3": ("nh3", 1000.0),
    "cougm3": ("co", 0.001), "coug": ("co", 0.001),
    "no2ppm": ("no2", None), "coppm": ("co", None),  # placeholder, handled below
}

# ppm -> ug/m3 conversion needs temperature/pressure; CPCB breakpoints are
# mass-based, so ppm columns are rejected with a clear warning instead of
# being silently misconverted.

_COLUMN_ALIASES: dict[str, str] = {
    _normalise_header(k): v for k, v in _COLUMN_ALIASES_RAW.items()}
_UNIT_CONVERSIONS: dict[str, tuple[str, float]] = {
    k: v for k, v in _UNIT_CONVERSIONS_RAW.items() if v[1] is not None}
_REJECTED_UNIT_HEADERS = {k for k, v in _UNIT_CONVERSIONS_RAW.items()
                          if v[1] is None}

# A row fingerprint for duplicate detection.
def _row_key(location: str, ts, pollutants: dict) -> tuple:
    return (location.strip().lower(), ts,
            tuple(sorted((k, round(v, 4)) for k, v in pollutants.items())))


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

    bad_rows: list[list[str]] = []
    try:
        # python engine lets us COUNT malformed rows instead of silently
        # dropping them; the row cap keeps the slower engine cheap enough.
        df = pd.read_csv(io.BytesIO(file_bytes), engine="python",
                         on_bad_lines=bad_rows.append)
    except Exception as exc:  # surface a friendly message
        raise ValueError(f"Could not parse CSV: {exc}") from exc

    if df.empty:
        raise ValueError("CSV contains no data rows.")
    if len(df) > MAX_CSV_ROWS:
        raise ValueError(f"CSV has {len(df)} rows; limit is {MAX_CSV_ROWS}.")

    # Duplicate column labels would make positional lookups ambiguous;
    # keep only the first occurrence of each label.
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    # Map columns to canonical fields, keeping POSITIONS so duplicate or
    # oddly-cased labels can never be confused. Two passes: standard-unit
    # columns first, then unit-variant columns only for pollutants not
    # already covered (a real "pm25" column beats "pm25_mgm3").
    pollutant_cols: dict[str, tuple[int, float]] = {}
    simple_cols: dict[str, int] = {}
    ignored_unit_cols: set[str] = set()

    def _scan(unit_variants: bool):
        for pos, col in enumerate(df.columns):
            key = _normalise_header(col)
            if key in _REJECTED_UNIT_HEADERS:
                ignored_unit_cols.add(str(col))
                continue
            conv = _UNIT_CONVERSIONS.get(key)
            if conv and unit_variants:
                p, factor = conv
                pollutant_cols.setdefault(p, (pos, factor))
                continue
            canon = _COLUMN_ALIASES.get(key)
            if canon is None or (conv and not unit_variants):
                continue
            if canon in POLLUTANTS:
                if unit_variants:
                    continue  # unit variants handled above
                pollutant_cols.setdefault(canon, (pos, 1.0))
            else:
                simple_cols.setdefault(canon, pos)

    _scan(unit_variants=False)
    _scan(unit_variants=True)

    aqi_col = simple_cols.get("aqi")
    location_col = simple_cols.get("location")
    ts_col = simple_cols.get("timestamp")

    if not pollutant_cols and aqi_col is None:
        extra = ""
        if ignored_unit_cols:
            extra = (" Ignored non-mass-unit column(s): "
                     f"{', '.join(sorted(ignored_unit_cols))} - CPCB AQI "
                     "requires ug/m3 (CO: mg/m3).")
        raise ValueError(
            "CSV must contain at least one recognised pollutant column "
            "(pm25, pm10, no2, so2, co, o3, nh3) or an 'aqi' column. "
            f"Found columns: {', '.join(str(c) for c in df.columns)}.{extra}"
        )

    measurements: list[MeasurementSet] = []
    warnings: list[str] = []
    if bad_rows:
        warnings.append(f"{len(bad_rows)} malformed line(s) skipped "
                        "(wrong number of fields).")
    if ignored_unit_cols:
        warnings.append(
            f"Ignored column(s) with non-mass units that cannot be "
            f"converted safely: {', '.join(sorted(ignored_unit_cols))}. "
            "CPCB AQI requires ug/m3 (CO: mg/m3).")

    missing_ts = naive_ts = 0
    for idx, row in df.iterrows():
        pollutants: dict[str, float] = {}
        invalid: list[str] = []
        for p, (pos, factor) in pollutant_cols.items():
            raw = row.iloc[pos]
            if pd.isna(raw):
                continue
            try:
                v = round(float(raw) * factor, 6)
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
        if aqi_col is not None and not pollutants and not pd.isna(row.iloc[aqi_col]):
            try:
                aqi_val = float(row.iloc[aqi_col])
            except (TypeError, ValueError):
                warnings.append(f"aqi row {idx + 2}: not a number, skipped")
                aqi_val = None
            else:
                err = validate_aqi_value(aqi_val)
                if err:
                    warnings.append(f"aqi row {idx + 2}: {err}, skipped")
                    aqi_val = None

        location = "Imported location"
        if location_col is not None and not pd.isna(row.iloc[location_col]):
            loc = str(row.iloc[location_col]).strip()
            if loc:
                location = loc

        ts = None
        ts_explicit = False
        if ts_col is not None and not pd.isna(row.iloc[ts_col]):
            try:
                t = pd.to_datetime(row.iloc[ts_col], errors="raise")
                ts = t.to_pydatetime()
                ts_explicit = True
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                    naive_ts += 1
            except Exception:  # noqa: BLE001
                warnings.append(
                    f"timestamp row {idx + 2}: unparseable, using import time")
        if ts is None:
            ts = datetime.now(timezone.utc)
            missing_ts += 1

        m = MeasurementSet(location=location, pollutants=pollutants,
                          aqi=aqi_val, timestamp=ts, source="import",
                          notes=f"Row {idx + 2} of {filename}",
                          synthetic_timestamp=not ts_explicit)
        m.finalize()
        if m.display_aqi is not None:
            measurements.append(m)

    if not measurements:
        raise ValueError("No usable measurement rows found in the CSV.")

    # De-duplicate identical observations. Rows without a real timestamp
    # are keyed without one, otherwise every row would look unique.
    seen: set = set()
    deduped: list[MeasurementSet] = []
    dupes = 0
    for m in measurements:
        ts_key = None if m.synthetic_timestamp else m.timestamp
        key = _row_key(m.location, ts_key, m.pollutants) + (m.aqi,)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        deduped.append(m)
    if dupes:
        warnings.append(f"{dupes} duplicate row(s) skipped "
                        "(identical location, time and values).")

    if missing_ts:
        warnings.append(f"{missing_ts} row(s) had no timestamp; "
                        "the import time was used instead.")
    if naive_ts:
        warnings.append(f"{naive_ts} timestamp(s) had no timezone; "
                        "assumed UTC.")

    return deduped, warnings[:10]


def measurement_fingerprint(m: MeasurementSet) -> tuple:
    """Stable identity for a measurement, used for staleness checks.

    Unlike ``id(m)`` this survives session-state serialisation and object
    recreation, so cached results are invalidated exactly when the
    underlying reading changes.
    """
    return (m.location, m.timestamp.isoformat(), m.display_aqi, m.source,
            tuple(sorted(m.pollutants.items())))
