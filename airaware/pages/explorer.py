"""Air Quality Explorer page: assessment headline, pollutant cards,
health guidance, methodology details and CSV import/compare.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

import airaware.charts as charts  # noqa: PLR0402
import airaware.ui as ui  # noqa: PLR0402
from airaware.aqi import (
    CATEGORIES,
    POLLUTANTS,
    category_color,
    is_outdoor_safe,
)

from ._common import (
    _flash,
    _manual_entry_form,
    _meas,
    _measurement_caption,
    _provenance_warning,
    import_csv_measurements,
)


def _pollutant_note(p: str) -> str:
    return {
        "pm25": "Fine particles; deep lung penetration, cardiovascular effects.",
        "pm10": "Coarse particles; irritates airways, aggravates asthma.",
        "no2": "Traffic/combustion gas; airway inflammation, smog component.",
        "so2": "Sulphur dioxide; respiratory irritant, acid deposition.",
        "co": "Carbon monoxide; reduces blood oxygen carriage.",
        "o3": "Ground-level ozone; lung irritant, peaks in afternoon sun.",
        "nh3": "Ammonia; agricultural/industrial source, particle precursor.",
    }.get(p, "")


def _sub_index_color(si: float) -> str:
    """AQI-band colour for a sub-index value (Good→Severe+)."""
    for cat in reversed(CATEGORIES):
        if si >= cat["min"]:
            return cat["color"]
    return "#1a9850"


def explorer_page():
    _flash()
    ui.page_header(
        "Air Quality",
        "Air Quality Explorer",
        "Your reading, explained. Built on the official CPCB AQI "
        "methodology - partial data is labelled honestly.")

    m = _meas()

    # ---------- guided entry ----------
    with st.expander("Enter or update measurements", expanded=m is None):
        _manual_entry_form(prefix="exp")

    # ---------- assessment ----------
    if m is None:
        st.markdown(
            '<div class="aw-card" style="text-align:center;padding:2.6rem">'
            '<div style="display:flex;justify-content:center;margin-bottom:.8rem">'
            + ui.scene("city") + '</div>'
            '<h3 style="margin:.2rem 0 .4rem">Your air story starts here</h3>'
            '<p style="color:var(--muted);max-width:52ch;margin:0 auto">'
            'Enter measurements above (or start a check on Home) to see '
            'your assessment.</p></div>', unsafe_allow_html=True)
        return

    _provenance_warning(m)
    st.caption(_measurement_caption(m))

    aqi = m.display_aqi
    if aqi is None:
        st.error("No computable AQI from the current measurement.")
        return

    completeness = (len(m.result.pollutant_results) / len(POLLUTANTS)
                    if m.result else 0)
    cat = m.result.category if m.result else None

    # ---------- headline assessment ----------
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.plotly_chart(charts.aqi_gauge(aqi, m.category_name or ""),
                        width="stretch")
    with col_b:
        dom = (m.result.dominant_pollutant.upper()
               if m.result and m.result.dominant_pollutant else "-")
        ui.kpi_row([
            (f"{aqi:.0f}", "Overall AQI"),
            (m.category_name or "-", "CPCB category"),
            (dom, "Dominant pollutant"),
            (f"{completeness*100:.0f}%", "Data completeness"),
        ])
        st.markdown(
            f'<div class="aw-card" style="border-left:5px solid '
            f'{category_color(m.category_name)}">'
            f'<h4>{html.escape(m.category_name or "-")}</h4>'
            f'<p>{html.escape(cat["summary"] if cat else "")}</p></div>',
            unsafe_allow_html=True)
        st.progress(min(completeness, 1.0),
                    text=f"{len(m.result.pollutant_results) if m.result else 0}"
                         f" of {len(POLLUTANTS)} pollutants measured")

    if completeness < 1:
        st.info(f"**Partial data:** {len(m.result.pollutant_results)} of "
                f"{len(POLLUTANTS)} pollutants measured. The AQI shown is "
                "the maximum of what was measured - the true AQI could be "
                "higher.")

    # ---------- pollutant indicator cards ----------
    if m.result and m.result.pollutant_results:
        st.markdown('<div class="aw-section-title" style="font-size:1.15rem;'
                    'margin-top:1.4rem">What is in your air</div>',
                    unsafe_allow_html=True)
        pcols = st.columns(len(m.result.pollutant_results))
        max_si = max(r.sub_index for r in m.result.pollutant_results)
        for col, r in zip(pcols, m.result.pollutant_results):
            info = POLLUTANTS[r.pollutant]
            c = _sub_index_color(r.sub_index)
            bar_pct = min(100, r.sub_index / 5)
            dom_mark = (' <span class="aw-tag-soft">main driver</span>'
                        if r.sub_index == max_si and len(
                            m.result.pollutant_results) > 1 else "")
            with col:
                st.markdown(
                    f'<div class="aw-card" style="text-align:center;'
                    f'padding:.95rem .7rem">'
                    f'<div style="font-size:.7rem;font-weight:800;'
                    f'letter-spacing:.08em;color:#5a6d5e;text-transform:'
                    f'uppercase">{html.escape(info["name"])}{dom_mark}</div>'
                    f'<div style="font-size:1.35rem;font-weight:800;'
                    f'color:{c};font-family:var(--serif);margin:.1rem 0">'
                    f'{r.sub_index:.0f}</div>'
                    f'<div style="height:6px;border-radius:3px;'
                    f'background:#eef1e6;overflow:hidden;margin:.3rem 0 .5rem">'
                    f'<div style="height:100%;width:{bar_pct:.0f}%;'
                    f'background:{c};border-radius:3px"></div></div>'
                    f'<div style="font-size:.74rem;color:#5a6d5e">'
                    f'{r.concentration:g} {r.unit} · {info["period"]}</div>'
                    f'</div>', unsafe_allow_html=True)

    # ---------- health guidance ----------
    safe, safe_msg = is_outdoor_safe(m.category_name or "Good", "moderate")
    guidance = ("Good conditions for normal outdoor activity."
                if safe else safe_msg)
    ui.card("Health guidance",
            body_html=f"<p>{guidance}</p>"
                     f"<p>Category summary: "
                     f"{cat['summary'] if cat else ''}</p>")

    if m.result and m.result.pollutant_results:
        st.plotly_chart(charts.pollutant_bar_chart(m.result),
                        width="stretch")

    # ---------- technical details (progressive disclosure) ----------
    with st.expander("Technical details & methodology"):
        if m.result and m.result.pollutant_results:
            st.markdown("**Your measurements**")
            rows = []
            for r in m.result.pollutant_results:
                info = POLLUTANTS[r.pollutant]
                rows.append({
                    "Pollutant": info["name"],
                    "Your value": f"{r.concentration:g} {r.unit}",
                    "Averaging": info["period"],
                    "Sub-index": f"{r.sub_index:.0f}",
                    "What it means": _pollutant_note(r.pollutant),
                })
            st.dataframe(pd.DataFrame(rows), width="stretch",
                         hide_index=True)
        for n in (m.result.notes if m.result else []):
            st.info(n)
        st.markdown(
            "**AQI vs pollutant concentrations** — AQI is a unitless index "
            "from CPCB breakpoints; pollutants keep their own units. "
            "Overall AQI is the **maximum** sub-index, so one bad "
            "pollutant can dominate.")

    # ---------- CSV comparison ----------
    with st.expander("Import a CSV to compare multiple observations"):
        up = st.file_uploader("CSV with pollutant columns", type=["csv"],
                              key="exp_csv")
        if up is not None and st.button("Parse CSV", key="exp_parse"):
            import_csv_measurements(up, "Parsed {count} measurement(s).")
        csv_list = st.session_state.get("csv_measurements")
        if csv_list:
            st.dataframe(pd.DataFrame([{
                "location": mm.location,
                "AQI": mm.display_aqi,
                "category": mm.category_name,
                "timestamp": mm.timestamp.strftime("%Y-%m-%d %H:%M"),
            } for mm in csv_list]), width="stretch", hide_index=True)
            if len(csv_list) > 1:
                st.plotly_chart(charts.comparison_bar(csv_list),
                                width="stretch")
