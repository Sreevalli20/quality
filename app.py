"""AirAware AI - Streamlit entry point.

Run locally:  streamlit run app.py
Deploy:       Streamlit Community Cloud (see README.md)
"""

from __future__ import annotations

import streamlit as st

from airaware import pages, ui
from airaware.aqi import POLLUTANTS
from airaware.data import (INDIAN_CITIES, SAMPLE_MEASUREMENTS,
                           MeasurementSet, parse_measurements_csv)

NAV = [
    "Home",
    "Air Quality Explorer",
    "Personal AI Assistant",
    "My Daily Air Plan",
    "Indoor Air Guardian",
    "Green Lifestyle Planner",
    "Environmental Impact",
    "Family & Community",
    "About & Data Sources",
]

PAGE_FN = {
    "Home": pages.home_page,
    "Air Quality Explorer": pages.explorer_page,
    "Personal AI Assistant": pages.assistant_page,
    "My Daily Air Plan": pages.planner_page,
    "Indoor Air Guardian": pages.indoor_page,
    "Green Lifestyle Planner": pages.lifestyle_page,
    "Environmental Impact": pages.impact_page,
    "Family & Community": pages.community_page,
    "About & Data Sources": pages.about_page,
}


def _sidebar_data_loader():
    """Sidebar panel: choose data source, enter/import measurements."""
    st.sidebar.markdown("### Air quality data")
    st.sidebar.caption("Every reading records value, unit, source and "
                       "timestamp. Sample data is always labelled.")

    mode = st.sidebar.radio(
        "Data source",
        ["Enter manually", "Upload CSV", "Sample demonstration data"],
        key="data_mode", label_visibility="collapsed")

    if mode == "Enter manually":
        location = st.sidebar.selectbox("Location", INDIAN_CITIES, key="loc")
        st.sidebar.markdown("**Pollutant concentrations**")
        pollutants = {}
        cols = st.sidebar.columns(2)
        for i, p in enumerate(POLLUTANTS):
            with cols[i % 2]:
                v = st.sidebar.number_input(
                    f"{POLLUTANTS[p]['name']} ({POLLUTANTS[p]['unit']})",
                    min_value=0.0, value=0.0, step=1.0,
                    key=f"man_{p}")
                if v > 0:
                    pollutants[p] = v
        st.sidebar.markdown("**Or AQI directly** (used only if no pollutants)")
        aqi_val = st.sidebar.number_input("AQI", min_value=0.0, value=0.0,
                                          step=1.0, key="man_aqi")
        if st.sidebar.button("Apply measurement", key="man_apply",
                             width="stretch"):
            ms = MeasurementSet(
                location=location, pollutants=pollutants,
                aqi=aqi_val if aqi_val > 0 and not pollutants else None,
                source="user")
            ms.finalize()
            st.session_state["measurement"] = ms
            st.sidebar.success("Measurement applied.")

    elif mode == "Upload CSV":
        up = st.sidebar.file_uploader(
            "CSV file (pollutant columns + optional location/timestamp)",
            type=["csv"], key="csv_up")
        if up is not None and st.sidebar.button("Import CSV",
                                                key="csv_go",
                                                width="stretch"):
            try:
                ms_list, warns = parse_measurements_csv(up.getvalue(), up.name)
                st.session_state["csv_imports"] = ms_list
                for w in warns:
                    st.sidebar.warning(w)
                st.sidebar.success(f"Imported {len(ms_list)} observation(s).")
            except ValueError as e:
                st.sidebar.error(str(e))
        imports = st.session_state.get("csv_imports")
        if imports:
            labels = [f"{m.location} · AQI {m.display_aqi:.0f} · "
                      f"{m.timestamp.strftime('%Y-%m-%d %H:%M')}"
                      if m.display_aqi is not None else m.location
                      for m in imports]
            pick = st.sidebar.selectbox("Select observation", range(len(imports)),
                                        format_func=lambda i: labels[i],
                                        key="csv_pick")
            st.session_state["measurement"] = imports[pick]

    else:  # sample data
        picks = [f"{m.location} · AQI {m.display_aqi:.0f} · SAMPLE"
                 if m.display_aqi is not None else m.location
                 for m in SAMPLE_MEASUREMENTS]
        pick = st.sidebar.selectbox("Sample city", range(len(SAMPLE_MEASUREMENTS)),
                                    format_func=lambda i: picks[i], key="sample_pick")
        st.session_state["measurement"] = SAMPLE_MEASUREMENTS[pick]
        st.sidebar.warning("Sample data is for demonstration only - it is "
                           "not a live reading.")

    # Current measurement summary
    m = st.session_state.get("measurement")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Active measurement**")
    if m and m.display_aqi is not None:
        st.sidebar.markdown(
            f"**AQI {m.display_aqi:.0f}** · {m.category_name or ''}<br>"
            f"{m.location}<br>"
            f"<span style='font-size:.78rem;color:#5a6b60'>"
            f"{m.timestamp.strftime('%Y-%m-%d %H:%M UTC')} · {m.source_label}</span>",
            unsafe_allow_html=True)
    else:
        st.sidebar.caption("No active measurement.")


def main():
    st.set_page_config(page_title="AirAware AI", page_icon="🌿",
                       layout="wide", initial_sidebar_state="expanded")
    ui.apply_css()

    _sidebar_data_loader()

    nav = st.sidebar.radio("Navigate", NAV, label_visibility="collapsed",
                           key="nav")
    PAGE_FN[nav]()

    st.sidebar.markdown("---")
    st.sidebar.caption("AirAware AI · PromptWars Challenge 06 · "
                       "CPCB AQI methodology · offline rule engine")


if __name__ == "__main__":
    main()
