"""Environmental Impact page: trip/AC savings calculators, action log,
cumulative dashboard and CSV report download.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

import airaware.ui as ui
from airaware.impact import (
    VEHICLE_FACTORS,
    ImpactAction,
    actions_to_csv,
    estimate_ac_savings,
    estimate_trip_savings,
    summarise_actions,
)


def impact_page():
    ui.page_header(
        "Environmental Impact",
        "See the difference you make",
        "Estimate the climate benefit of your greener choices. All "
        "figures are transparent estimates - not measured reductions.")

    ui.card("CO₂e vs air pollution",
            body_html="<p>CO₂e savings from transport and energy are "
                      "<b>climate</b> benefits. They are not the same as PM2.5 "
                      "or local air-pollution reductions - though cleaner "
                      "transport usually helps both.</p>")

    # --- Trip calculator ---
    with st.container(border=True):
        st.markdown('<div class="aw-section-title" '
                    'style="font-size:1.2rem;margin:.2rem 0 .8rem;display:flex;'
                    'align-items:center;gap:.5rem">'
                    + ui.icon("route", 22) + ' Compare a trip</div>',
                    unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        avoided = c1.selectbox("Instead of taking...", list(VEHICLE_FACTORS.keys()),
                               format_func=lambda k: VEHICLE_FACTORS[k]["label"],
                               key="imp_avoided")
        new_mode = c2.selectbox("...I now use...", list(VEHICLE_FACTORS.keys()),
                                format_func=lambda k: VEHICLE_FACTORS[k]["label"],
                                index=list(VEHICLE_FACTORS).index("metro"),
                                key="imp_new")
        km = c3.number_input("One-way distance (km)", min_value=0.1, value=5.0,
                             step=0.5, key="imp_km")

        est = estimate_trip_savings(new_mode, avoided, km)
        if est["co2e_saved_kg"] < 0:
            st.warning("This switch would **increase** emissions versus the "
                       "avoided mode - the estimate is shown honestly below, but "
                       "it is not a saving.")
        ui.kpi_row([
            (f"{est['co2e_saved_kg']:.1f} kg", "CO₂e saved / trip"),
            (f"{est['fuel_saved_litres']} L" if est['fuel_saved_litres'] is not None else "-",
             "Fuel saved"),
            (f"₹{est['fuel_cost_saved_inr']:.0f}" if est['fuel_cost_saved_inr'] is not None else "-",
             "Fuel cost saved"),
        ])
        with st.expander("Assumptions used for this estimate"):
            st.json(est["assumptions"])

        if st.button("Log this as a completed action", key="imp_log_trip"):
            acts = st.session_state.setdefault("impact_actions", [])
            acts.append(ImpactAction(
                action_type="trip",
                description=f"{VEHICLE_FACTORS[new_mode]['label']} instead of "
                            f"{VEHICLE_FACTORS[avoided]['label']} for {km} km",
                vehicle=new_mode, avoided_vehicle=avoided, distance_km=km,
                cost_saved_inr=est['fuel_cost_saved_inr'],
                date=datetime.now(timezone.utc).strftime("%Y-%m-%d")))
            st.success("Action logged.")

    # --- AC savings ---
    with st.container(border=True):
        st.markdown('<div class="aw-section-title" '
                    'style="font-size:1.2rem;margin:.2rem 0 .8rem;display:flex;'
                    'align-items:center;gap:.5rem">'
                    + ui.icon("bolt", 22) + ' Air-conditioning savings '
                    'estimate</div>', unsafe_allow_html=True)
        hrs = st.number_input("Hours of AC avoided per day (e.g. fan instead, "
                              "higher setpoint)", min_value=0.0, value=2.0, step=0.5,
                              key="imp_ac")
        if hrs > 0:
            ac = estimate_ac_savings(hrs)
            ui.kpi_row([
                (f"{ac['kwh_saved_per_year']:.0f} kWh", "Saved / year"),
                (f"{ac['co2e_saved_kg_per_year']:.0f} kg", "CO₂e / year"),
                (f"₹{ac['indicative_cost_saved_inr_per_year']:.0f}", "Cost / year (indicative)"),
            ])
            if st.button("Log AC savings for today", key="imp_log_ac"):
                acts = st.session_state.setdefault("impact_actions", [])
                acts.append(ImpactAction(
                    action_type="energy",
                    description=f"Avoided {hrs} h/day of AC use",
                    kwh_saved=ac["kwh_saved_per_day"],
                    cost_saved_inr=ac["indicative_cost_saved_inr_per_year"] / 365,
                    date=datetime.now(timezone.utc).strftime("%Y-%m-%d")))
                st.success("Logged.")

    # --- Log ---
    with st.container(border=True):
        st.markdown('<div class="aw-section-title" '
                    'style="font-size:1.2rem;margin:.2rem 0 .8rem;display:flex;'
                    'align-items:center;gap:.5rem">'
                    + ui.icon("chart", 22) + ' Your impact dashboard</div>',
                    unsafe_allow_html=True)
        acts: list[ImpactAction] = st.session_state.get("impact_actions", [])
        if not acts:
            ui.empty_state("Nothing logged yet - use the calculators above "
                           "to start your impact story.", icon_name="chart")
        else:
            summ = summarise_actions(acts)
            ui.kpi_row([
                (f"{summ['total_actions']}", "Actions logged"),
                (f"{summ['total_co2e_saved_kg']:.1f} kg", "Est. CO₂e saved"),
                (f"{summ['trip_km']:.0f} km", "Green km"),
                (f"₹{summ['indicative_cost_saved_inr']:.0f}", "Indicative ₹ saved"),
            ])
            # simple cumulative chart
            daily: dict[str, float] = {}
            for a in acts:
                daily[a.date or "undated"] = daily.get(a.date or "undated", 0) + a.co2e_kg()
            if len(daily) > 1:
                chart_df = pd.DataFrame(
                    sorted(daily.items()), columns=["date", "co2e_kg"])
                st.bar_chart(chart_df.set_index("date"), height=220)
            st.dataframe(pd.DataFrame([a.as_dict() for a in acts]),
                         width="stretch")
            c1, c2 = st.columns(2)
            c1.download_button("Download impact report (CSV)",
                               data=actions_to_csv(acts),
                               file_name="airaware_impact_report.csv",
                               mime="text/csv", key="imp_dl")
            if c2.button("Clear log", key="imp_clear"):
                st.session_state["impact_actions"] = []
                st.rerun()

    # tree-equivalent flourish for logged CO2e
    acts = st.session_state.get("impact_actions", [])
    if acts:
        total = sum(a.co2e_kg() for a in acts)
        trees = total / 21.0  # ~21 kg CO2 absorbed per tree per year
        st.markdown(
            f'<div class="aw-card aw-card--mint" style="display:flex;'
            f'gap:.8rem;align-items:center">'
            f'<div class="aw-feat-ico">{ui.icon("tree", 24)}</div>'
            f'<div><b>That\'s roughly {trees:.0f} tree'
            f'{"s" if trees != 1 else ""} worth of CO₂e</b> '
            f'<span class="aw-meta">(one tree absorbs ~21 kg CO₂e/year '
            f'- a simple visual comparison, not a precise offset).</span>'
            f'</div></div>', unsafe_allow_html=True)

    st.caption("Vehicle factors are generic estimates; real savings depend "
               "on your vehicle, driving style and occupancy. Grid factor: "
               "0.82 kg CO₂/kWh (Indian average).")
