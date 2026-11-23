"""Page renderers for each AirAware AI module."""

from __future__ import annotations

import io
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from . import charts, ui
from .aqi import POLLUTANTS, calculate_aqi, category_color, is_outdoor_safe
from .alerts import SEVERITY_META, evaluate_alerts
from .data import (INDIAN_CITIES, SAMPLE_MEASUREMENTS, MeasurementSet,
                   parse_measurements_csv)
from .indoor import BUDGET_TIERS, ROOMS, ventilation_advice
from .impact import (INDIAN_GRID_KG_CO2_PER_KWH, VEHICLE_FACTORS,
                     actions_to_csv, estimate_ac_savings,
                     estimate_trip_savings, summarise_actions, ImpactAction)
from .lifestyle import options_by_area, personalised_options
from .planner import build_daily_plan
from .recommendations import UserProfile, generate_recommendations

GROUP_LABELS = {
    "understanding": "A. Understanding the situation",
    "today": "B. What to do today",
    "avoid": "C. What to avoid",
    "alternatives": "D. Lower-emission alternatives",
    "indoor": "E. Indoor protection",
    "next_steps": "F/G. Why it matters & next steps",
}


def _meas() -> MeasurementSet | None:
    return st.session_state.get("measurement")


def _require_measurement() -> bool:
    if _meas() is None:
        ui.empty_state("No air-quality data loaded yet. Use the **Data source** "
                       "panel in the sidebar to enter measurements, upload a "
                       "CSV, or load the labelled sample set.")
        return False
    return True


def _measurement_caption(m: MeasurementSet) -> str:
    return (f"Location: {m.location or 'unspecified'} · "
            f"Timestamp: {m.timestamp.strftime('%Y-%m-%d %H:%M UTC')} · "
            f"Source: {m.source_label}")


def _provenance_warning(m: MeasurementSet):
    if m.is_sample:
        st.warning("**Sample demonstration data** - these values are "
                   "illustrative, not live readings.")
    elif m.source == "user":
        st.caption("Source: user-provided measurement.")
    elif m.source == "import":
        st.caption(f"Source: imported from {m.notes}.")


# ===========================================================================
# HOME
# ===========================================================================

def home_page():
    ui.hero(
        "AirAware AI",
        "Your intelligent urban air-quality companion - turning pollution data into everyday decisions.",
        "CPCB AQI methodology · rule-based recommendations · works fully offline",
    )

    m = _meas()
    col1, col2 = st.columns([1, 1])
    with col1:
        ui.section_header("How it works")
        st.markdown(
            "1. **Load air-quality data** - enter PM2.5/PM10/AQI manually, "
            "import a CSV, or try the labelled sample set.\n\n"
            "2. **Get a CPCB AQI assessment** - pollutant sub-indices are "
            "calculated with official breakpoints; overall AQI is the maximum.\n\n"
            "3. **Receive practical guidance** - what to do today, what to "
            "avoid, indoor protection, greener travel choices and tracked impact."
        )
    with col2:
        ui.section_header("Current reading")
        if m and m.display_aqi is not None:
            ui.kpi_row([
                (f"{m.display_aqi:.0f}", "AQI"),
                (m.category_name or "-", "Category"),
                (m.location or "-", "Location"),
                (m.source_label.split(" (")[0], "Source"),
            ])
            _provenance_warning(m)
        else:
            ui.empty_state("No measurement loaded. Use the sidebar to add one.")

    ui.hr()
    ui.section_header("Alerts")
    for a in evaluate_alerts(m):
        meta = SEVERITY_META[a.severity]
        st.markdown(
            f'<div class="aw-card" style="border-left:4px solid {meta["color"]}">'
            f'<h4>{meta["label"]}: {a.title}</h4><p>{a.detail}</p></div>',
            unsafe_allow_html=True)

    ui.hr()
    ui.section_header("Quick access")
    cols = st.columns(3)
    pages = [
        ("Air Quality Explorer", "Sub-indices, charts, CSV import"),
        ("Personal AI Assistant", "Context-aware recommendations"),
        ("My Daily Air Plan", "Hour-by-hour guidance"),
        ("Indoor Air Guardian", "Room-by-room, budget tiers"),
        ("Green Lifestyle Planner", "Low-emission alternatives"),
        ("Environmental Impact", "Track CO2e savings"),
        ("Family & Community", "Checklists & education"),
        ("About & Data Sources", "Methodology & limitations"),
    ]
    for i, (name, desc) in enumerate(pages):
        with cols[i % 3]:
            ui.card(name, body_text=desc)

    ui.hr()
    ui.section_header("Environmental awareness")
    st.markdown(
        "- **PM2.5** (particles ≤2.5 µm) penetrates deep into lungs and "
        "bloodstream; it is the pollutant most linked to cardiorespiratory harm.\n"
        "- **AQI is a maximum, not an average** - one bad pollutant sets the "
        "whole index under the CPCB method.\n"
        "- **Your smallest trip still counts** - short cold-start trips emit "
        "more per km than highway cruising.\n"
        "- **Indoor air is controllable** - filtration, ventilation timing and "
        "cooking habits often matter more than outdoor levels overnight."
    )


# ===========================================================================
# AIR QUALITY EXPLORER
# ===========================================================================

def explorer_page():
    ui.hero("Air Quality Explorer",
            "Assess air quality using CPCB AQI methodology.")

    # --- manual quick-entry override within the page ---
    with st.expander("Enter measurements for this analysis only"):
        st.caption("These inputs are used for the explorer below and stored "
                   "as your active measurement if applied.")
        loc = st.text_input("Location", value=INDIAN_CITIES[0], key="exp_loc")
        pcols = st.columns(4)
        vals = {}
        pkeys = ["pm25", "pm10", "no2", "so2", "co", "o3", "nh3"]
        for i, p in enumerate(pkeys):
            with pcols[i % 4]:
                vals[p] = st.number_input(
                    f"{POLLUTANTS[p]['name']} ({POLLUTANTS[p]['unit']})",
                    min_value=0.0, value=0.0, step=1.0,
                    key=f"exp_{p}") or None
        aqi_direct = st.number_input("AQI (only if pollutant data unavailable)",
                                     min_value=0.0, value=0.0, step=1.0,
                                     key="exp_aqi") or None
        if st.button("Use these values", key="exp_apply"):
            pollutants = {k: v for k, v in vals.items() if v}
            ms = MeasurementSet(location=loc, pollutants=pollutants,
                                aqi=aqi_direct if not pollutants else None,
                                source="user")
            ms.finalize()
            st.session_state["measurement"] = ms
            st.success("Measurement applied - charts updated below.")

    # --- CSV import for comparison set ---
    with st.expander("Import measurements from CSV for comparison"):
        up = st.file_uploader("CSV with pollutant columns (pm25, pm10, no2, so2, "
                              "co, o3, nh3) and optional 'aqi', 'location', "
                              "'timestamp' columns", type=["csv"], key="exp_csv")
        if up is not None:
            if st.button("Parse CSV", key="exp_parse"):
                try:
                    ms_list, warns = parse_measurements_csv(up.getvalue(), up.name)
                    st.session_state["csv_measurements"] = ms_list
                    for w in warns:
                        st.warning(w)
                    st.success(f"Parsed {len(ms_list)} measurement(s).")
                except ValueError as e:
                    st.error(str(e))
        csv_list = st.session_state.get("csv_measurements")
        if csv_list:
            st.dataframe(pd.DataFrame([{
                "location": m.location,
                "AQI": m.display_aqi,
                "category": m.category_name,
                "source": m.source_label,
                "timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M"),
            } for m in csv_list]), width="stretch")
            if len(csv_list) > 1:
                st.plotly_chart(charts.comparison_bar(csv_list),
                                width="stretch")

    # --- main assessment ---
    m = _meas()
    if m is None:
        ui.empty_state("Load a measurement from the sidebar or use the entry "
                       "form above.")
        return

    _provenance_warning(m)
    st.caption(_measurement_caption(m))

    aqi = m.display_aqi
    if aqi is None:
        st.error("No computable AQI from the current measurement.")
        return

    ui.kpi_row([
        (f"{aqi:.0f}", "Overall AQI"),
        (m.category_name or "-", "CPCB category"),
        (f"{m.result.dominant_pollutant.upper()}" if m.result and m.result.dominant_pollutant else "-", "Dominant pollutant"),
        (f"{len(m.result.pollutant_results)}/{len(POLLUTANTS)}", "Pollutants measured"),
    ])

    cat = m.result.category if m.result else None
    if cat:
        st.markdown(
            f'<div class="aw-card" style="border-left:4px solid {cat["color"]}">'
            f'<h4>{cat["name"]}</h4><p>{cat["summary"]}</p></div>',
            unsafe_allow_html=True)

    if m.result and m.result.pollutant_results:
        st.plotly_chart(charts.pollutant_bar_chart(m.result),
                        width="stretch")
        st.plotly_chart(charts.aqi_gauge(aqi, m.category_name or ""),
                        width="stretch")

        st.markdown("**What each pollutant means**")
        rows = []
        for r in m.result.pollutant_results:
            info = POLLUTANTS[r.pollutant]
            rows.append({
                "Pollutant": info["name"],
                "Concentration": f"{r.concentration:g} {r.unit}",
                "Averaging": info["period"],
                "Sub-index": f"{r.sub_index:.0f}",
                "Health relevance": _pollutant_note(r.pollutant),
            })
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    for n in (m.result.notes if m.result else []):
        st.info(n)

    st.markdown("---")
    st.markdown("**AQI vs pollutant concentrations**")
    st.markdown(
        "AQI is a *unitless index* derived from pollutant concentrations via "
        "CPCB breakpoints - higher is worse. Individual pollutants are "
        "reported in their own units (µg/m³ or mg/m³). The overall AQI is "
        "the **maximum** sub-index, so a single bad pollutant can dominate "
        "the reading even when others are low. When only some pollutants "
        "are measured, the result is a *partial* assessment - the true AQI "
        "could be higher."
    )


def _pollutant_note(p: str) -> str:
    return {
        "pm25": "Fine particles; deep lung penetration, cardiovascular effects.",
        "pm10": "Coarse particles; irritates airways, aggravates asthma.",
        "no2": "Traffic/combustion gas; airway inflammation, smog component.",
        "so2": "Sulphur dioxide; respiratory irritant, acid deposition.",
        "co": "Carbon monoxide; reduces blood oxygen carriage.",
        "o3": "Ground-level ozone; lung irritant, peaks in afternoon sun.",
        "nh3": "Ammonia; agricultural/industrial source, precursor to particles.",
    }.get(p, "")


# ===========================================================================
# PERSONAL AI ASSISTANT
# ===========================================================================

def assistant_page():
    ui.hero("Personal AI Assistant",
            "Context-aware guidance powered by a transparent rule engine - "
            "no external AI service is used or claimed.")

    with st.form("profile_form"):
        st.markdown("**About you**")
        c1, c2 = st.columns(2)
        city = c1.text_input("City / locality", value="")
        lifestyle = c1.selectbox("Lifestyle", [
            "Office worker", "Student", "Runner / fitness enthusiast",
            "Parent", "Shift worker", "Retired / home mostly"],
            key="as_life")
        transport = c2.selectbox("Main transport", [
            "Car", "Bike / scooter", "Bus", "Metro / train",
            "Cycle", "Walk", "Mixed"], key="as_trans")
        household = c2.selectbox("Household", [
            "Living alone", "With family", "With children",
            "With elderly members"], key="as_hh")
        outdoor = st.selectbox("Typical outdoor activity level", [
            "Light (short walks)", "Moderate (jogging, cycling)",
            "Heavy (intense exercise, sports)"], key="as_out")
        concerns = st.multiselect("Daily concerns", [
            "Health conditions (asthma/COPD/heart)", "Long commute",
            "Children's health", "Budget / cost", "Staying active outdoors",
            "Reducing environmental impact"], key="as_conc")
        budget = st.selectbox("Budget for improvements", [
            "Free only", "Low (under ~Rs 5,000)", "Moderate (Rs 5-25k)",
            "Higher investments OK"], key="as_budget")
        priority = st.selectbox("Top priority", [
            "Health protection", "Saving money", "Convenience",
            "Environmental impact"], key="as_pri")
        submitted = st.form_submit_button("Generate my plan")

    life_map = {"Office worker": "office", "Student": "student",
                "Runner / fitness enthusiast": "runner", "Parent": "parent",
                "Shift worker": "shift_worker", "Retired / home mostly": "retired"}
    trans_map = {"Car": "car", "Bike / scooter": "bike", "Bus": "bus",
                 "Metro / train": "metro", "Cycle": "cycle", "Walk": "walk",
                 "Mixed": "mixed"}
    hh_map = {"Living alone": "alone", "With family": "family",
              "With children": "children", "With elderly members": "elderly"}
    out_map = {"Light (short walks)": "light",
               "Moderate (jogging, cycling)": "moderate",
               "Heavy (intense exercise, sports)": "heavy"}
    bud_map = {"Free only": "free", "Low (under ~Rs 5,000)": "low",
               "Moderate (Rs 5-25k)": "moderate",
               "Higher investments OK": "high"}
    pri_map = {"Health protection": "health", "Saving money": "cost",
               "Convenience": "convenience", "Environmental impact": "environment"}
    con_map = {"Health conditions (asthma/COPD/heart)": "health",
               "Long commute": "commute", "Children's health": "kids",
               "Budget / cost": "cost",
               "Staying active outdoors": "exercise",
               "Reducing environmental impact": "environment"}

    if submitted or st.session_state.get("profile"):
        if submitted:
            st.session_state["profile"] = UserProfile(
                city=city, lifestyle=life_map[lifestyle],
                transport=trans_map[transport], household=hh_map[household],
                outdoor_pref=out_map[outdoor],
                concerns=[con_map[c] for c in concerns],
                budget=bud_map[budget], priority=pri_map[priority])
        profile: UserProfile = st.session_state["profile"]

        if not _require_measurement():
            return
        m = _meas()
        recs = generate_recommendations(m, profile)

        ui.card("Your situation",
                body_html=f"<p>{profile.summary()}</p>"
                         f"<p>Outdoor activity: {outdoor} · Budget: {budget} · "
                         f"Priority: {priority}</p>")

        for group, label in GROUP_LABELS.items():
            items = recs.get(group, [])
            if not items:
                continue
            st.markdown(f"**{label}**")
            for r in sorted(items, key=lambda x: x.priority):
                pri = {1: "High", 2: "Medium", 3: "Low"}[r.priority]
                st.markdown(
                    f'<div class="aw-card" style="border-left:4px solid '
                    + ("#dc2626" if r.priority == 1 else
                       "#d97706" if r.priority == 2 else "#2563eb") + '">'
                    f'<h4>{r.title} <span class="aw-meta">· {pri} priority</span></h4>'
                    f'<p>{r.detail}</p><div class="aw-reason">Why: {r.reason}</div>'
                    f'</div>', unsafe_allow_html=True)
            ui.hr()

        st.caption("Recommendations are generated by deterministic Python "
                   "rules from your profile and the CPCB AQI category. No "
                   "external AI model is used.")


# ===========================================================================
# DAILY AIR PLAN
# ===========================================================================

def planner_page():
    ui.hero("My Daily Air Plan",
            "A personalised hour-by-hour plan based on the current reading. "
            "Guidance reflects current conditions - it does not predict "
            "future hourly pollution.")
    m = _meas()
    if not _require_measurement():
        return
    profile = st.session_state.get("profile")
    has_kids = profile and profile.household == "children"
    outdoor = profile.outdoor_pref if profile else "moderate"

    plan = build_daily_plan(m, outdoor_pref=outdoor,
                            has_children=bool(has_kids))
    indoor_n, total_n = sum(1 for p in plan if p.indoor_friendly), len(plan)
    ui.kpi_row([
        (f"{m.category_name}", "Current AQI category"),
        (f"{indoor_n}/{total_n}", "Indoor-friendly slots"),
        (m.location or "-", "Location"),
    ])
    st.caption(_measurement_caption(m))

    # editable plan storage
    key = "daily_plan"
    if key not in st.session_state:
        st.session_state[key] = {p.slot_key: p.guidance for p in plan}

    if st.button("Reset plan to current recommendations"):
        st.session_state[key] = {p.slot_key: p.guidance for p in plan}
        st.rerun()

    for p in plan:
        edited = st.text_area(
            f"{p.slot_label} - {p.focus}",
            value=st.session_state[key].get(p.slot_key, p.guidance),
            key=f"plan_{p.slot_key}", height=68)
        st.session_state[key][p.slot_key] = edited

    st.download_button(
        "Download my plan (CSV)",
        data=pd.DataFrame([{
            "slot": p.slot_label, "focus": p.focus,
            "guidance": st.session_state[key].get(p.slot_key, p.guidance),
        } for p in plan]).to_csv(index=False),
        file_name="airaware_daily_plan.csv", mime="text/csv")


# ===========================================================================
# INDOOR AIR GUARDIAN
# ===========================================================================

def indoor_page():
    ui.hero("Indoor Air Guardian",
            "Practical, room-by-room guidance for healthier indoor air.")
    m = _meas()
    cat = m.category_name if m else None

    head, detail = ventilation_advice(cat)
    st.markdown(
        f'<div class="aw-card" style="border-left:4px solid #0f5132">'
        f'<h4>{head}</h4><p>{detail}</p></div>', unsafe_allow_html=True)
    if m:
        st.caption(_measurement_caption(m))

    st.markdown("**Choose a room**")
    room_names = [r.name for r in ROOMS]
    sel = st.selectbox("Room", room_names, key="indoor_room")
    room = next(r for r in ROOMS if r.name == sel)
    ui.card(room.name,
            body_html="<br>".join(f"• {x}" for x in room.priorities) +
            f'<p class="aw-meta" style="margin-top:.5rem">{room.notes}</p>')

    ui.hr()
    st.markdown("**Improvements by budget**")
    st.caption("Indicative Indian-rupee ranges - prices vary widely by brand "
               "and city; treat them as planning estimates, not quotes.")
    tier = st.selectbox("Budget tier", list(BUDGET_TIERS.keys()),
                        format_func=lambda k: BUDGET_TIERS[k]["label"],
                        key="indoor_budget")
    t = BUDGET_TIERS[tier]
    ui.card(f"{t['label']} · {t['range']}",
            body_html="<br>".join(f"• {x}" for x in t["items"]))

    ui.hr()
    st.markdown("**Common indoor pollution sources to control**")
    st.markdown(
        "- **Cooking** - frying and biomass fuels are the biggest indoor PM2.5 sources.\n"
        "- **Tobacco smoke & incense** - no safe level indoors; eliminate.\n"
        "- **Dust** - resuspends with activity; damp-clean and use doormaps.\n"
        "- **Cleaning products & air fresheners** - many emit VOCs; choose fragrance-free.\n"
        "- **Outdoor infiltration** - depends on AQI; seal windows on bad days.\n"
        "- **Mould & damp** - worsens with poor ventilation; fix leaks promptly."
    )
    st.caption("Note: houseplants improve wellbeing but are not a substitute "
               "for filtration - their effect on PM2.5 is negligible.")


# ===========================================================================
# GREEN LIFESTYLE PLANNER
# ===========================================================================

def lifestyle_page():
    ui.hero("Green Lifestyle Planner",
            "Practical sustainable-living options, personalised to your "
            "situation. Every option states its limits honestly.")

    profile = st.session_state.get("profile")
    if profile is None:
        st.info("Fill in the **Personal AI Assistant** form first for "
                "personalised ranking - or browse all options below.")
        scored = [(0, o) for o in _all_opts()]
    else:
        scored = personalised_options(profile)

    area_filter = st.selectbox("Filter by area",
                               ["All"] + list(options_by_area().keys()))

    current_area = None
    for score, opt in scored:
        if area_filter != "All" and opt.area != area_filter:
            continue
        if opt.area != current_area:
            st.markdown(f"**{opt.area}**")
            current_area = opt.area
        badge = f" · match score {score}" if profile and score > 0 else ""
        body = (f"<p>{opt.detail}</p>"
                f"<p><b>Benefit:</b> {opt.benefit}</p>"
                f"<p><b>Limitation:</b> {opt.limitation}</p>")
        if opt.conditions:
            body += "<p><b>Applies when:</b> " + "; ".join(opt.conditions) + "</p>"
        ui.card(f"{opt.title}{badge}", body_html=body)


def _all_opts():
    from .lifestyle import all_options
    return all_options()


# ===========================================================================
# ENVIRONMENTAL IMPACT
# ===========================================================================

def impact_page():
    ui.hero("Environmental Impact Tracker",
            "Estimate the CO2e benefit of your sustainable choices. All "
            "figures are transparent estimates, not measured reductions.")

    st.markdown(
        '<div class="aw-card"><h4>Important distinction</h4>'
        '<p>CO₂e savings from transport and energy are <b>climate</b> '
        'benefits. They are not the same as PM2.5 or local air-pollution '
        'reductions, though cleaner transport usually helps both.</p></div>',
        unsafe_allow_html=True)

    # --- Trip calculator ---
    st.markdown("**Trip-mode comparison**")
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
    ui.kpi_row([
        (f"{est['co2e_saved_kg']:.1f} kg", "CO₂e saved / trip"),
        (f"{est['fuel_saved_litres']} L" if est['fuel_saved_litres'] is not None else "-",
         "Fuel saved"),
        (f"₹{est['fuel_cost_saved_inr']:.0f}" if est['fuel_cost_saved_inr'] is not None else "-",
         "Fuel cost saved"),
    ])
    with st.expander("Assumptions used"):
        st.json(est["assumptions"])

    if st.button("Log this as a completed action"):
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
    st.markdown("**Air-conditioning savings estimate**")
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
        if st.button("Log AC savings for today"):
            acts = st.session_state.setdefault("impact_actions", [])
            acts.append(ImpactAction(
                action_type="energy",
                description=f"Avoided {hrs} h/day of AC use",
                kwh_saved=ac["kwh_saved_per_day"],
                cost_saved_inr=ac["indicative_cost_saved_inr_per_year"] / 365,
                date=datetime.now(timezone.utc).strftime("%Y-%m-%d")))
            st.success("Logged.")

    # --- Log ---
    st.markdown("**Your logged actions**")
    acts: list[ImpactAction] = st.session_state.get("impact_actions", [])
    if not acts:
        st.caption("Nothing logged yet - use the calculators above.")
    else:
        summ = summarise_actions(acts)
        ui.kpi_row([
            (f"{summ['total_actions']}", "Actions logged"),
            (f"{summ['total_co2e_saved_kg']:.1f} kg", "Est. CO₂e saved"),
            (f"{summ['trip_km']:.0f} km", "Green km"),
            (f"₹{summ['indicative_cost_saved_inr']:.0f}", "Indicative ₹ saved"),
        ])
        st.dataframe(pd.DataFrame([a.as_dict() for a in acts]),
                     width="stretch")
        c1, c2 = st.columns(2)
        c1.download_button("Download impact report (CSV)",
                           data=actions_to_csv(acts),
                           file_name="airaware_impact_report.csv",
                           mime="text/csv")
        if c2.button("Clear log"):
            st.session_state["impact_actions"] = []
            st.rerun()

    st.caption(f"Grid factor used for electricity: "
               f"{INDIAN_GRID_KG_CO2_PER_KWH} kg CO₂/kWh (Indian average "
               "estimate). Vehicle factors are generic; real results depend "
               "on your vehicle and driving.")


# ===========================================================================
# FAMILY & COMMUNITY
# ===========================================================================

def community_page():
    ui.hero("Family & Community",
            "Household checklists, kids' education and neighbourhood action.")

    st.markdown("**Household air-quality checklist**")
    checklist_items = [
        "Keep windows closed on Poor-or-worse days; ventilate on clean days",
        "Run kitchen exhaust fan for every cooking session",
        "No smoking, incense or mosquito coils indoors",
        "Damp-dust and wet-mop weekly",
        "Shoes off at the door",
        "HEPA purifier in the room used most (bedroom priority)",
        "AC filters cleaned monthly",
        "Vehicle idling minimised near home",
        "School commute planned to avoid peak traffic where possible",
    ]
    done = st.session_state.setdefault("community_checklist", {})
    for i, item in enumerate(checklist_items):
        done[i] = st.checkbox(item, value=done.get(i, False), key=f"chk_{i}")
    pct = sum(done.values()) / len(checklist_items) * 100
    st.progress(pct / 100, text=f"{pct:.0f}% complete")

    ui.hr()
    st.markdown("**For children - simple explanation**")
    st.markdown(
        "Air pollution is like tiny invisible dust floating in the air. "
        "Some days there is more of it - we can see it as haze. When the "
        "air is bad, our lungs work harder, just like running up stairs. "
        "We can help by **walking or cycling** to nearby places (cleaner "
        "than cars), **closing windows** on smoky days, and **saving "
        "electricity** so power plants burn less fuel.")

    st.markdown("**Community action ideas**")
    st.markdown(
        "- **Car-free day** - pick one day a week where your household uses "
        "only walking, cycling or transit.\n"
        "- **Neighbourhood clean-up** - collect roadside waste that would "
        "otherwise be burned.\n"
        "- **Tree-drive** - coordinate with your RWAs/school for native "
        "saplings.\n"
        "- **School awareness** - share the kids' explainer above with "
        "teachers; many schools run 'clean commute' weeks.\n"
        "- **Report violations** - dusty construction without sprinkling, "
        "open garbage burning; log them on your municipal app.")

    ui.hr()
    m = _meas()
    if m and m.display_aqi is not None:
        st.markdown("**Family plan for today's air**")
        profile = st.session_state.get("profile")
        has_kids = profile and profile.household == "children"
        plan = build_daily_plan(m, profile.outdoor_pref if profile else "moderate",
                                has_children=bool(has_kids))
        for p in plan:
            st.markdown(f"- **{p.slot_label}:** {st.session_state.get('daily_plan', {}).get(p.slot_key, p.guidance)}")


# ===========================================================================
# ABOUT & DATA SOURCES
# ===========================================================================

def about_page():
    ui.hero("About & Data Sources",
            "Methodology, assumptions and honest limitations.")

    st.markdown("**How AQI is calculated**")
    st.markdown(
        "AirAware AI implements the **CPCB National Air Quality Index "
        "(NAQI)** method: each measured pollutant (PM2.5, PM10, NO₂, SO₂, "
        "CO, O₃, NH₃) is converted to a sub-index via published "
        "concentration breakpoints using piecewise-linear interpolation. "
        "The overall AQI is the **maximum** sub-index, and that pollutant "
        "is reported as dominant. If only some pollutants are measured, "
        "the result is explicitly labelled *partial* - the true AQI could "
        "be higher.\n\n"
        "Averaging periods follow CPCB: 24-hour for most pollutants, "
        "8-hour for O₃.")

    st.markdown("**Data sources**")
    st.markdown(
        "- **User-entered measurements** - whatever you type; treated as "
        "user-provided, unverified.\n"
        "- **CSV imports** - parsed and validated locally; nothing is "
        "uploaded anywhere.\n"
        "- **Sample demonstration data** - illustrative values included for "
        "demo purposes, always labelled as non-live.\n"
        "- **No live feed is bundled** - the app works fully offline and "
        "does not fabricate readings. To use live data, import official "
        "CPCB/state-board AQI tables or OpenAQ exports as CSV.\n\n"
        "Every measurement records value, unit, source and timestamp.")

    st.markdown("**Recommendation methodology**")
    st.markdown(
        "Recommendations come from a deterministic Python rule engine "
        "mapping AQI category + dominant pollutant + your profile to "
        "actionable guidance. **No generative AI service is integrated** - "
        "all 'AI' output is these auditable rules.")

    st.markdown("**Impact calculation assumptions**")
    st.markdown(
        "Vehicle CO₂e factors are generic estimates (petrol car ≈0.19 "
        "kg/km, electric car ≈0.10 kg/km on the Indian grid, metro ≈0.02 "
        "kg/passenger-km). Grid intensity ≈0.82 kg CO₂/kWh. Fuel prices "
        "and economy are defaults you can override. Figures are estimates "
        "of climate benefit, not measured reductions.")

    st.markdown("**Technology**")
    st.markdown("Python 3.14 · Streamlit · pandas · plotly. No database, "
                "no API keys, no paid services. All state is kept in the "
                "browser session; you can download CSV reports.")

    st.markdown("**Limitations & future work**")
    st.markdown(
        "- No live monitoring feed is included (deliberately, to avoid "
        "fabricated data); CSV import covers official exports.\n"
        "- Recommendations are rule-based, not personalised ML.\n"
        "- Indoor guidance is qualitative; a real PM2.5 sensor would enable "
        "quantitative indoor tracking.\n"
        "- Future: CPCB/OpenAQ live fetch, multi-day personal exposure "
        "logging, family accounts.")
