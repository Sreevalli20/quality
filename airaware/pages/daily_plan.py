"""My Daily Air Plan page: editable slot guidance, progress tracking,
CSV download and the shared 24-hour planning-outlook renderer.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

import airaware.charts as charts  # noqa: PLR0402
import airaware.forecast as forecast  # noqa: PLR0402
import airaware.tzutil as tzutil  # noqa: PLR0402
import airaware.ui as ui  # noqa: PLR0402
from airaware.aqi import category_color
from airaware.data import MeasurementSet, measurement_fingerprint
from airaware.planner import build_daily_plan, current_time_slot

from ._common import _meas, _measurement_caption, _require_measurement

_VERDICT_STYLE = {
    "good": ("var(--good)", "OK"),
    "caution": ("var(--warn)", "Caution"),
    "avoid": ("var(--bad)", "Avoid"),
}


def _outlook_section(m: MeasurementSet,
                     history: list[MeasurementSet] | None = None):
    """Render the 24-hour planning outlook with honest labelling.

    The outlook is a labelled planning estimate (diurnal model, optionally
    adjusted by the session trend) - never presented as an official or
    measured hourly forecast.
    """
    hist = (history if history is not None
            else st.session_state.get("measurement_history") or [])
    outlook = forecast.build_outlook(m, history=hist)
    best = outlook.best_window

    st.markdown('<div class="aw-section-title" style="font-size:1.3rem">'
                '24-hour planning outlook</div>', unsafe_allow_html=True)
    conf_color = {"high": "var(--good)", "moderate": "var(--warn)",
                  "low": "var(--bad)"}[outlook.confidence]
    st.caption(
        f"Planning estimate · basis: {html.escape(outlook.basis)} · "
        f"confidence: <b style='color:{conf_color}'>{outlook.confidence}</b> · "
        f"times shown in your timezone ({html.escape(tzutil.tz_label())}). "
        "AQI categories per time window, not measured hourly readings.")
    for n in outlook.notes:
        st.info(n)

    if best is not None:
        st.markdown(
            '<div class="aw-card aw-card--mint" style="display:flex;gap:.7rem;'
            'align-items:flex-start;padding:.9rem 1.2rem">'
            + ui.icon("sun", 22) +
            '<div><b>Best window today: '
            + html.escape(best.label) + '.</b> '
            '<span class="aw-meta">Likely '
            + html.escape(best.cat_low if best.cat_low == best.cat_high
                          else f"{best.cat_low} to {best.cat_high}")
            + ' - the safest bet for outdoor time.</span></div></div>',
            unsafe_allow_html=True)

    st.plotly_chart(charts.outlook_chart(outlook), width="stretch")

    rows_html = ""
    for w in outlook.windows:
        acts = " · ".join(
            f"{a}: <b style='color:{_VERDICT_STYLE[v][0]}'>"
            f"{_VERDICT_STYLE[v][1]}</b>"
            for a, v in (("walk", w.activity["light"]),
                         ("exercise", w.activity["moderate"]),
                         ("sport", w.activity["heavy"])))
        cat_label = (w.cat_low if w.cat_low == w.cat_high
                     else f"{w.cat_low}–{w.cat_high}")
        cat_color = category_color(w.cat_high)
        vent_icon = {"open": "check", "brief": "alert", "closed": "shield"}[
            w.ventilation]
        rows_html += (
            f'<div style="display:flex;gap:.8rem;align-items:flex-start;'
            f'padding:.55rem 0;border-bottom:1px solid var(--line)">'
            f'<div style="min-width:150px;font-weight:700;color:var(--forest);'
            f'font-size:.88rem">{html.escape(w.label)}</div>'
            f'<div style="flex:1;font-size:.85rem;color:var(--muted)">'
            f'<span class="aw-chip" style="border-color:{cat_color};'
            f'color:{cat_color};margin-right:.4rem">{cat_label}</span>'
            f'{acts}<br><span style="font-size:.78rem">'
            f'{ui.icon(vent_icon, 13)} {html.escape(w.ventilation_note)}'
            f'</span></div></div>')
    st.markdown(
        '<div class="aw-card" style="padding:.4rem 1.2rem">'
        '<div class="aw-eyebrow" style="margin-bottom:.4rem">Window by '
        'window</div>' + rows_html + '</div>', unsafe_allow_html=True)

    with st.expander("How this outlook is produced - and its limits"):
        st.markdown(
            "- **Model:** a diurnal climatology for urban air (traffic "
            "peaks, midday mixing, overnight stability), shifted by the "
            "dominant pollutant - ozone-dominant days peak in the sunny "
            "afternoon instead of the morning.\n"
            "- **Session trend:** when several readings exist in this "
            "session, a least-squares AQI slope nudges every window "
            "(bounded to one AQI category).\n"
            "- **Uncertainty:** each window shows a *likely category "
            "range*, not a number. Bands widen for stale, partial or "
            "sample readings.\n"
            "- **Not a forecast:** CPCB publishes no public hourly "
            "forecast and no verified live forecast feed is connected. "
            "Treat this as planning guidance, not a prediction.")
        for lim in outlook.limitations:
            st.caption("• " + lim)


def planner_page():
    ui.page_header(
        "My Daily Air Plan",
        "Your day, hour by hour",
        "A personalised schedule shaped by today's reading and a "
        "24-hour planning outlook - guidance adapts as conditions change.")
    m = _meas()
    if not _require_measurement():
        return
    profile = st.session_state.get("profile")
    has_kids = profile and profile.household == "children"
    outdoor = profile.outdoor_pref if profile else "moderate"

    plan = build_daily_plan(m, outdoor_pref=outdoor,
                            has_children=bool(has_kids))
    indoor_n = sum(1 for p in plan if p.indoor_friendly)
    ui.kpi_row([
        (m.category_name or "-", "Today's category"),
        (f"{indoor_n}/{len(plan)}", "Indoor-friendly slots"),
        (m.location or "-", "Location"),
    ])
    st.caption(_measurement_caption(m))

    _outlook_section(m)

    key = "daily_plan"
    # rebuild when there is no plan, an explicit regenerate was requested,
    # or the underlying measurement changed (fingerprint survives
    # session-state serialisation, unlike id(m))
    meas_fp = measurement_fingerprint(m)
    meas_changed = st.session_state.get("plan_meas_fp") != meas_fp
    done_keys = [f"plan_done_{p.slot_key}" for p in plan]
    if (key not in st.session_state or st.session_state.get("plan_regen")
            or meas_changed):
        st.session_state[key] = {p.slot_key: p.guidance for p in plan}
        st.session_state["plan_regen"] = False
        st.session_state["plan_meas_fp"] = meas_fp
        for dk in done_keys:
            st.session_state.pop(dk, None)
    done_count = sum(1 for dk in done_keys
                     if st.session_state.get(dk))

    c1, _ = st.columns([1, 4])
    c1.button("Regenerate from current reading", key="plan_reset",
              on_click=lambda: st.session_state.update(plan_regen=True))
    st.caption("“now” marks whichever time-of-day slot contains the "
               "current hour; the outlook above estimates likely "
               "categories per window (a planning estimate, not an "
               "official forecast). Tick a slot off as you complete "
               "it - progress is kept for this reading.")

    # ---------- progress ----------
    pct = done_count / len(plan) * 100
    prog_col, chip_col = st.columns([3, 1])
    with prog_col:
        st.progress(pct / 100,
                    text=f"{done_count} of {len(plan)} slots completed")
    with chip_col:
        st.markdown(
            f'<div class="aw-chip" style="justify-content:center;'
            f'margin-top:.55rem">{pct:.0f}% done</div>',
            unsafe_allow_html=True)
    if done_count == len(plan):
        st.markdown(
            '<div class="aw-card aw-card--mint" style="display:flex;'
            'gap:.7rem;align-items:center;padding:.9rem 1.2rem">'
            + ui.icon("check", 22) +
            '<div><b>You\'ve worked through today\'s plan.</b> '
            '<span class="aw-meta">Nice work - small consistent choices '
            'add up to real exposure reduction.</span></div></div>',
            unsafe_allow_html=True)

    slot_icons = {
        "morning": ("sun", "MORNING"), "commute_am": ("car", "AM TRAVEL"),
        "midday": ("sun", "MIDDAY"), "commute_pm": ("car", "PM TRAVEL"),
        "evening": ("moon", "EVENING"), "night": ("moon", "NIGHT"),
    }
    now_slot = current_time_slot()
    with st.container(border=True):
        for p in plan:
            ic, label = slot_icons.get(p.slot_key, ("calendar", p.slot_label))
            is_done = bool(st.session_state.get(f"plan_done_{p.slot_key}"))
            now_pill = (' <span class="aw-pill" style="background:var(--evergreen);'
                        'color:#fff">NOW</span>'
                        if p.slot_key == now_slot else "")
            done_pill = (' <span class="aw-pill" style="background:var(--good);'
                         'color:#fff">DONE</span>' if is_done else "")
            focus_style = ('text-decoration:line-through;opacity:.65;'
                           if is_done else "")
            st.markdown(
                f'<div class="aw-tstep">'
                f'<div class="when" style="display:flex;align-items:center;'
                f'gap:.45rem"><span style="width:24px;height:24px;'
                f'border-radius:50%;background:var(--mint);color:var(--evergreen);'
                f'display:inline-flex;align-items:center;justify-content:center">'
                f'{ui.icon(ic, 13)}</span>{html.escape(label)}'
                f'{now_pill}{done_pill}</div>'
                f'<h4 style="margin:.25rem 0 .35rem;{focus_style}">'
                f'{html.escape(p.focus)}</h4>'
                f'</div>',
                unsafe_allow_html=True)
            edited = st.text_area(
                "Guidance (editable)",
                value=st.session_state[key].get(p.slot_key, p.guidance),
                key=f"plan_{p.slot_key}", height=64)
            st.session_state[key][p.slot_key] = edited
            st.checkbox("Mark this slot as done", key=f"plan_done_{p.slot_key}")

    st.download_button(
        "Download my plan (CSV)",
        data=pd.DataFrame([{
            "slot": p.slot_label, "focus": p.focus,
            "guidance": st.session_state[key].get(p.slot_key, p.guidance),
        } for p in plan]).to_csv(index=False),
        file_name="airaware_daily_plan.csv", mime="text/csv",
        key="plan_dl")
