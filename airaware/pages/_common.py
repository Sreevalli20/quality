"""Shared helpers for the AirAware page renderers.

Measurement access, provenance labelling, the guided pollutant entry
form (used by Home and the Explorer) and the shared CSV-import flow.
"""

from __future__ import annotations

import streamlit as st

import airaware.ui as ui
from airaware.aqi import POLLUTANTS
from airaware.data import (
    INDIAN_CITIES,
    MeasurementSet,
    parse_measurements_csv,
    record_measurement_history,
)

POLLUTANT_HELP = {
    "pm25": "Fine particles - reach deep into lungs",
    "pm10": "Coarse dust - irritates airways",
    "no2": "Traffic gas - smog component",
    "so2": "Sulphur dioxide - respiratory irritant",
    "co": "Carbon monoxide - reduces oxygen carriage",
    "o3": "Ground-level ozone - peaks in afternoon sun",
    "nh3": "Ammonia - agricultural/industrial",
}

POLLUTANT_PLACEHOLDER = {
    "pm25": "e.g. 45", "pm10": "e.g. 120", "no2": "e.g. 60",
    "so2": "e.g. 15", "co": "e.g. 1.2", "o3": "e.g. 90",
    "nh3": "e.g. 300",
}


def _meas() -> MeasurementSet | None:
    return st.session_state.get("measurement")


def _save_measurement(ms: MeasurementSet) -> None:
    """Store the active reading and append it to session history.

    The history feeds the day-ahead planning outlook's trend detection;
    it lives only in this browser session and is capped in size.
    """
    st.session_state["measurement"] = ms
    hist = st.session_state.get("measurement_history") or []
    st.session_state["measurement_history"] = record_measurement_history(
        hist, ms)


def _flash():
    """Show and clear a one-shot success message set before st.rerun()."""
    msg = st.session_state.pop("flash_success", None)
    if msg:
        st.success(msg)


def _require_measurement() -> bool:
    if _meas() is None:
        ui.empty_state("No air-quality reading yet. Head to **Home** and "
                       "start an air-quality check - it takes under a minute.")
        return False
    return True


def _measurement_caption(m: MeasurementSet) -> str:
    return (f"{m.location or 'unspecified location'} · "
            f"{m.timestamp.strftime('%Y-%m-%d %H:%M UTC')} · "
            f"{m.source_label}")


def _provenance_warning(m: MeasurementSet):
    if m.is_sample:
        st.warning("**Sample demonstration data** - illustrative values for "
                   "exploration only, not a live reading.")
    elif m.source == "user":
        st.caption("Source: measurement you entered.")
    elif m.source == "import":
        st.caption(f"Source: {m.notes}.")
    elif m.source == "external":
        st.caption(f"Source: {m.source_label}. {m.notes}")


def _manual_entry_form(prefix: str = "", apply_immediately: bool = True):
    """Guided pollutant entry. Empty fields stay empty (no fake zeros)."""
    ui.field_label("Where are you?", "Pick a city or describe your locality.")
    loc = st.selectbox("Location", INDIAN_CITIES, key=f"{prefix}loc_entry")
    if loc == "Custom / other location":
        custom = st.text_input(
            "Your location", key=f"{prefix}loc_custom",
            placeholder="e.g. Kothrud, Pune")
        loc = custom.strip() or "Custom location"

    st.markdown("**What do you know about today's air?**")
    st.caption("Leave fields empty if unknown - AirAware works with partial "
               "data and tells you what is missing.")
    pollutants = {}
    cols = st.columns(4)
    pkeys = list(POLLUTANTS.keys())
    for i, p in enumerate(pkeys):
        with cols[i % 4]:
            info = POLLUTANTS[p]
            val = st.number_input(
                f"{info['name']} ({info['unit']})",
                min_value=0.0, value=None, step=1.0,
                placeholder=POLLUTANT_PLACEHOLDER[p],
                help=POLLUTANT_HELP[p], key=f"{prefix}p_{p}")
            if val is not None:
                pollutants[p] = float(val)

    aqi_val = st.number_input(
        "Overall AQI (optional - only used if no pollutant values entered)",
        min_value=0.0, value=None, step=1.0, placeholder="e.g. 185",
        key=f"{prefix}aqi_entry")

    if st.button("Assess my air quality", key=f"{prefix}apply",
                 type="primary"):
        if not pollutants and aqi_val is None:
            st.error("Please enter at least one pollutant value or an AQI.")
            return
        ms = MeasurementSet(
            location=loc, pollutants=pollutants,
            aqi=float(aqi_val) if (aqi_val is not None and not pollutants)
            else None,
            source="user")
        ms.finalize()
        _save_measurement(ms)
        st.session_state["flash_success"] = "Measurement saved - assessment updated."
        if apply_immediately:
            st.session_state["nav_page"] = "Air Quality Explorer"
        st.rerun()


def import_csv_measurements(upload, success_message: str):
    """Parse an uploaded CSV into ``session_state["csv_measurements"]``.

    Shared by the Home CSV panel and the Explorer comparison importer so
    validation, warnings and error surfacing behave identically.
    ``success_message`` is a format string receiving ``count``.
    Returns the parsed list, or None when the file was rejected.
    """
    try:
        ms_list, warns = parse_measurements_csv(upload.getvalue(), upload.name)
    except ValueError as e:
        st.error(str(e))
        return None
    st.session_state["csv_measurements"] = ms_list
    for w in warns:
        st.warning(w)
    st.success(success_message.format(count=len(ms_list)))
    return ms_list
