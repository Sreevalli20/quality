"""Page renderers for each AirAware AI module."""

from __future__ import annotations

import html
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from . import ai, charts, providers, report, ui
from .alerts import evaluate_alerts
from .aqi import POLLUTANTS, is_outdoor_safe
from .data import (
    INDIAN_CITIES,
    SAMPLE_MEASUREMENTS,
    MeasurementSet,
    measurement_fingerprint,
    parse_measurements_csv,
)
from .impact import (
    VEHICLE_FACTORS,
    ImpactAction,
    actions_to_csv,
    estimate_ac_savings,
    estimate_trip_savings,
    summarise_actions,
)
from .indoor import BUDGET_TIERS, ROOMS, ventilation_advice
from .lifestyle import all_options, options_by_area, personalised_options
from .planner import build_daily_plan, current_time_slot
from .recommendations import UserProfile, generate_recommendations

GROUP_LABELS = {
    "understanding": "A. Understanding the situation",
    "today": "B. What to do today",
    "avoid": "C. What to avoid",
    "alternatives": "D. Lower-emission alternatives",
    "indoor": "E. Indoor protection",
    "next_steps": "F/G. Why it matters & next steps",
}

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

GROUP_WHEN = {
    "understanding": "Now",
    "today": "Today",
    "avoid": "Whenever conditions apply",
    "alternatives": "For your next trips",
    "indoor": "At home, daily",
    "next_steps": "This week",
}


def _meas() -> MeasurementSet | None:
    return st.session_state.get("measurement")


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


# ===========================================================================
# HOME
# ===========================================================================

def home_page():
    _flash()
    ui.hero(
        "Breathe smarter. Live better.",
        "AirAware AI turns air-quality numbers into simple, personal "
        "decisions - what to do today, how to protect your home, and how "
        "to move cleaner, together.",
        '<span class="aw-tag">PromptWars Challenge 06 · CPCB AQI methodology · '
        'works offline, no sign-up</span>',
        art=True)

    m = _meas()

    # ---------- current reading strip ----------
    if m and m.display_aqi is not None:
        ui.section_title("Your current reading")
        cat = m.category_name or ""
        ui.kpi_row([
            (f"{m.display_aqi:.0f}", "AQI"),
            (cat, "Category"),
            (m.location or "-", "Location"),
            (m.source.split(" ")[0].title(), "Source"),
        ])
        _provenance_warning(m)
        for a in evaluate_alerts(m):
            ui.alert_box(a.severity, a.title, a.detail)
        c1, c2 = st.columns(2)
        c1.button("See full assessment", key="home_to_explorer",
                  on_click=lambda: st.session_state.update(nav_page="Air Quality Explorer"))
        c2.button("Get personalised advice", key="home_to_assistant",
                  on_click=lambda: st.session_state.update(nav_page="Personal AI Assistant"))
        ui.hr()

    # ---------- start your check ----------
    ui.section_title("Start your air-quality check")
    entry = st.session_state.get("home_entry")

    if entry is None:
        choices = [
            ("Enter my own measurements",
             "Type PM2.5, PM10 or AQI values you already have",
             "manual"),
            ("Upload my air-quality report",
             "Import a CSV exported from CPCB, a monitor or OpenAQ",
             "csv"),
            ("Explore demonstration data",
             "Try realistic sample readings - always labelled as samples",
             "sample"),
        ]
        if providers.available_providers():
            choices.append(
                ("Fetch live monitoring data",
                 "Pull the freshest reading from a configured provider "
                 "(timestamped and labelled with its source)",
                 "live"))
        cols = st.columns(len(choices))
        for col, (label, desc, val) in zip(cols, choices):
            with col:
                ui.card(label, body_html=f"<p>{desc}</p>", variant="cta")
                if st.button(f"Choose: {label}", key=f"entry_{val}",
                             width="stretch"):
                    st.session_state["home_entry"] = val
                    st.rerun()
    else:
        _entry_panel(entry)
        if st.button("← Back to all options", key="entry_back"):
            st.session_state.pop("home_entry", None)
            st.rerun()

    ui.hr()

    # ---------- what airaware can do ----------
    ui.section_title("What AirAware can do")
    feats = [
        ("Know your air", "CPCB-method AQI from real pollutant measurements, "
         "with honest labels for partial or sample data."),
        ("Get a daily plan", "Hour-by-hour guidance that adapts to today's "
         "reading - exercise indoors, travel smarter, sleep safer."),
        ("Protect your home", "Room-by-room indoor air tips for every budget, "
         "from free habits to HEPA filtration."),
        ("Move cleaner", "Compare transit, carpool, cycling and walking with "
         "clear benefits and honest limitations."),
        ("See your impact", "Estimate CO₂e saved by your greener choices and "
         "download a personal report."),
        ("Bring everyone along", "Family checklists and simple explanations "
         "kids can understand."),
    ]
    for i in range(0, len(feats), 3):
        cols = st.columns(3)
        for j, (title, desc) in enumerate(feats[i:i + 3]):
            with cols[j]:
                ui.card(title, body_html=f"<p>{desc}</p>", variant="feature")

    ui.hr()

    # ---------- module teasers ----------
    ui.section_title("Your personal daily guidance")
    t1, t2 = st.columns(2)
    with t1:
        ui.card("Personal AI Assistant",
                body_html="<p>Tell AirAware about your routine - work hours, "
                          "transport, family - and get prioritised advice "
                          "with reasons, costs and alternatives.</p>")
        ui.cta_button("Open the assistant", "Personal AI Assistant",
                      key="cta_assistant")
    with t2:
        ui.card("My Daily Air Plan",
                body_html="<p>Wake-up to bedtime guidance shaped by today's "
                          "AQI. Edit it, download it, share it with family.</p>")
        ui.cta_button("Plan my day", "My Daily Air Plan", key="cta_plan")

    ui.section_title("Protect your indoor spaces")
    t1, t2 = st.columns(2)
    with t1:
        ui.card("Indoor Air Guardian",
                body_html="<p>Bedroom, kitchen, study and kids' room - what "
                          "to change first, at free, low-cost and premium "
                          "budgets.</p>")
        ui.cta_button("Check my rooms", "Indoor Air Guardian", key="cta_indoor")
    with t2:
        ui.card("Green Lifestyle Planner",
                body_html="<p>Practical low-emission swaps for transport, "
                          "energy, waste and home - ranked for your situation.</p>")
        ui.cta_button("Explore options", "Green Lifestyle Planner",
                      key="cta_lifestyle")

    ui.section_title("Greener decisions, visible impact")
    t1, t2 = st.columns(2)
    with t1:
        ui.card("Environmental Impact",
                body_html="<p>Log avoided car trips, transit switches and AC "
                          "savings. See estimated CO₂e benefits grow.</p>")
        ui.cta_button("Track my impact", "Environmental Impact",
                      key="cta_impact")
    with t2:
        ui.card("Family & Community",
                body_html="<p>Household checklists, kids' explainers and "
                          "neighbourhood action ideas.</p>")
        ui.cta_button("Get family tips", "Family & Community",
                      key="cta_family")

    ui.hr()
    ui.section_title("Good to know")
    st.markdown(
        "- **AQI is a maximum, not an average** - one bad pollutant sets the "
        "whole index under the CPCB method.\n"
        "- **PM2.5 is the quiet risk** - particles small enough to enter the "
        "bloodstream; filtration and masks matter most here.\n"
        "- **Short trips pollute most per km** - cold engines and stop-go "
        "traffic multiply emissions; combine errands when you can.\n"
        "- **Windows are a two-way door** - open them on clean days, keep "
        "them shut (and filter) on polluted ones."
    )


# ---------------------------------------------------------------------------
# Home: data entry panels
# ---------------------------------------------------------------------------

def _entry_panel(entry: str):
    if entry == "manual":
        _manual_entry_form(prefix="home")
    elif entry == "csv":
        _csv_entry_panel()
    elif entry == "sample":
        _sample_entry_panel()
    elif entry == "live":
        _live_entry_panel()


def _manual_entry_form(prefix: str = "", apply_immediately: bool = True):
    """Guided pollutant entry. Empty fields stay empty (no fake zeros)."""
    ui.field_label("Where are you?", "Pick a city or describe your locality.")
    loc = st.selectbox("Location", INDIAN_CITIES, key=f"{prefix}loc_entry")

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
        st.session_state["measurement"] = ms
        st.session_state["flash_success"] = "Measurement saved - assessment updated."
        if apply_immediately:
            st.session_state["nav_page"] = "Air Quality Explorer"
        st.rerun()


def _csv_entry_panel():
    st.markdown("**Upload an air-quality CSV**")
    st.caption("Expected columns: pollutant names (pm25, pm10, no2, so2, "
               "co, o3, nh3) and optional `aqi`, `location`, `timestamp`. "
               "Max 2 MB / 5,000 rows. Files are parsed locally only.")
    up = st.file_uploader("Choose a CSV file", type=["csv"], key="home_csv_up")
    if up is not None and st.button("Import file", key="home_csv_go",
                                    type="primary"):
        try:
            ms_list, warns = parse_measurements_csv(up.getvalue(), up.name)
            st.session_state["csv_measurements"] = ms_list
            for w in warns:
                st.warning(w)
            st.success(f"Imported {len(ms_list)} observation(s) - "
                       "select one below.")
        except ValueError as e:
            st.error(str(e))
    csv_list = st.session_state.get("csv_measurements")
    if csv_list:
        labels = [f"{m.location} · AQI {m.display_aqi:.0f} · "
                  f"{m.timestamp.strftime('%Y-%m-%d %H:%M')}"
                  if m.display_aqi is not None else m.location
                  for m in csv_list]
        pick = st.selectbox("Observation", range(len(csv_list)),
                            format_func=lambda i: labels[i],
                            key="home_csv_pick")
        if st.button("Use this observation", key="home_csv_use"):
            st.session_state["measurement"] = csv_list[pick]
            st.session_state["flash_success"] = "Observation loaded."
            st.session_state["nav_page"] = "Air Quality Explorer"
            st.rerun()


def _live_entry_panel():
    """Fetch the freshest reading from a configured live provider."""
    st.markdown("**Fetch live monitoring data**")
    st.caption("Reads the newest real measurement from a configured "
               "provider (currently OpenAQ). The result keeps its own "
               "timestamp and station name - if the freshest available "
               "reading is old, that is stated plainly rather than "
               "presented as current.")
    hint = st.text_input(
        "City or station name (optional - blank uses the most recently "
        "updated station)", key="home_live_city",
        placeholder="e.g. Delhi")
    provs = providers.available_providers()
    st.caption("Active provider(s): "
               + ", ".join(p.name for p in provs))
    if st.button("Fetch latest reading", key="home_live_go",
                 type="primary"):
        with st.spinner("Querying provider..."):
            m = providers.fetch_latest(hint)
        if m is None:
            st.error("No provider returned usable data right now. Check "
                     "the provider status on the About page, or use manual "
                     "entry / CSV import instead.")
            return
        st.session_state["measurement"] = m
        st.session_state["flash_success"] = (
            f"Live reading loaded from {m.notes.split(';')[0]}.")
        st.session_state["nav_page"] = "Air Quality Explorer"
        st.rerun()


def _sample_entry_panel():
    st.markdown("**Explore demonstration data**")
    st.warning("These are **illustrative sample readings** created for "
               "demonstration - they are NOT live pollution data.")
    picks = [f"{m.location} · AQI {m.display_aqi:.0f}"
             for m in SAMPLE_MEASUREMENTS]
    pick = st.selectbox("Sample city", range(len(SAMPLE_MEASUREMENTS)),
                        format_func=lambda i: picks[i], key="home_sample_pick")
    st.caption(SAMPLE_MEASUREMENTS[pick].notes)
    if st.button("Load this sample", key="home_sample_use", type="primary"):
        st.session_state["measurement"] = SAMPLE_MEASUREMENTS[pick]
        st.session_state["flash_success"] = ("Sample demonstration data "
                                              "loaded - not a live reading.")
        st.session_state["nav_page"] = "Air Quality Explorer"
        st.rerun()


# ===========================================================================
# AIR QUALITY EXPLORER
# ===========================================================================

def explorer_page():
    _flash()
    ui.hero("Air Quality Explorer",
            "A guided assessment built on the official CPCB AQI methodology. "
            "Enter what you know - partial data is handled honestly.")

    m = _meas()

    # ---------- guided entry ----------
    with st.expander("Enter or update measurements", expanded=m is None):
        _manual_entry_form(prefix="exp")

    # ---------- assessment ----------
    if m is None:
        ui.empty_state("Enter measurements above (or start a check on Home) "
                       "to see your assessment.")
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

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.plotly_chart(charts.aqi_gauge(aqi, m.category_name or ""),
                        width="stretch")
    with col_b:
        ui.kpi_row([
            (f"{aqi:.0f}", "Overall AQI"),
            (m.category_name or "-", "CPCB category"),
            (m.result.dominant_pollutant.upper()
             if m.result and m.result.dominant_pollutant else "-",
             "Dominant pollutant"),
            (f"{completeness*100:.0f}%", "Data completeness"),
        ])
        if cat:
            ui.card(cat["name"],
                    body_html=f'<p>{cat["summary"]}</p>')

    if completeness < 1:
        st.info(f"**Partial data:** {len(m.result.pollutant_results)} of "
                f"{len(POLLUTANTS)} pollutants measured. The AQI shown is "
                "the maximum of what was measured - the true AQI could be "
                "higher.")

    if m.result and m.result.pollutant_results:
        st.plotly_chart(charts.pollutant_bar_chart(m.result), width="stretch")
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
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    # health guidance by category
    safe, safe_msg = is_outdoor_safe(m.category_name or "Good", "moderate")
    guidance = ("Good conditions for normal outdoor activity."
                if safe else safe_msg)
    ui.card("Health guidance",
            body_html=f"<p>{guidance}</p>"
                     f"<p>Category summary: "
                     f"{cat['summary'] if cat else ''}</p>")

    for n in (m.result.notes if m.result else []):
        st.info(n)

    # ---------- CSV comparison ----------
    with st.expander("Import a CSV to compare multiple observations"):
        up = st.file_uploader("CSV with pollutant columns", type=["csv"],
                              key="exp_csv")
        if up is not None and st.button("Parse CSV", key="exp_parse"):
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
                "location": mm.location,
                "AQI": mm.display_aqi,
                "category": mm.category_name,
                "timestamp": mm.timestamp.strftime("%Y-%m-%d %H:%M"),
            } for mm in csv_list]), width="stretch", hide_index=True)
            if len(csv_list) > 1:
                st.plotly_chart(charts.comparison_bar(csv_list),
                                width="stretch")

    ui.hr()
    st.markdown(
        "**AQI vs pollutant concentrations** — AQI is a unitless index from "
        "CPCB breakpoints; pollutants keep their own units. Overall AQI is "
        "the **maximum** sub-index, so one bad pollutant can dominate."
    )


# ===========================================================================
# PERSONAL AI ASSISTANT
# ===========================================================================

def assistant_page():
    ui.hero("Your Personal Air Companion",
            "Tell us about your routine and get clear, prioritised advice "
            "- with reasons, timing, costs and alternatives.",
            "Powered by a transparent rule engine"
            + (" + optional Gemini enhancement" if ai.gemini_configured()
               else " · no external AI required"))

    with st.form("profile_form"):
        st.markdown("**A little about you**")
        c1, c2 = st.columns(2)
        city = c1.text_input("City or locality (optional)",
                             placeholder="e.g. Pune, Kothrud",
                             key="as_city")
        lifestyle = c1.selectbox("Your day mostly looks like", [
            "Office job", "Student", "Runner / gym-goer",
            "Parent at home", "Shift worker", "Mostly at home"],
            key="as_life")
        transport = c2.selectbox("How you usually get around", [
            "Car", "Bike / scooter", "Bus", "Metro / train",
            "Bicycle", "On foot", "Depends on the day"], key="as_trans")
        household = c2.selectbox("Who you live with", [
            "Just me", "Family", "Children", "Elderly family members"],
            key="as_hh")
        st.markdown("**Your habits & priorities**")
        c3, c4 = st.columns(2)
        outdoor = c3.selectbox("Outdoor activity level", [
            "Light - short walks", "Moderate - jogging, cycling",
            "Heavy - sports, long runs"], key="as_out")
        budget = c4.selectbox("Budget for improvements", [
            "Free only", "Low - under ~₹5,000", "Moderate - ₹5,000-25,000",
            "Open to bigger investments"], key="as_budget")
        concerns = st.multiselect("What matters most to you", [
            "Health (asthma, heart, breathing)", "Long commute",
            "Children's wellbeing", "Saving money", "Staying active outdoors",
            "Reducing pollution I cause"], key="as_conc")
        priority = st.selectbox("Your top priority", [
            "Health protection", "Saving money", "Convenience",
            "Environmental impact"], key="as_pri")
        submitted = st.form_submit_button("Create my personalised plan",
                                          type="primary")

    life_map = {"Office job": "office", "Student": "student",
                "Runner / gym-goer": "runner", "Parent at home": "parent",
                "Shift worker": "shift_worker", "Mostly at home": "retired"}
    trans_map = {"Car": "car", "Bike / scooter": "bike", "Bus": "bus",
                 "Metro / train": "metro", "Bicycle": "cycle",
                 "On foot": "walk", "Depends on the day": "mixed"}
    hh_map = {"Just me": "alone", "Family": "family",
              "Children": "children", "Elderly family members": "elderly"}
    out_map = {"Light - short walks": "light",
               "Moderate - jogging, cycling": "moderate",
               "Heavy - sports, long runs": "heavy"}
    bud_map = {"Free only": "free", "Low - under ~₹5,000": "low",
               "Moderate - ₹5,000-25,000": "moderate",
               "Open to bigger investments": "high"}
    pri_map = {"Health protection": "health", "Saving money": "cost",
               "Convenience": "convenience",
               "Environmental impact": "environment"}
    con_map = {"Health (asthma, heart, breathing)": "health",
               "Long commute": "commute", "Children's wellbeing": "kids",
               "Saving money": "cost", "Staying active outdoors": "exercise",
               "Reducing pollution I cause": "environment"}

    if submitted:
        st.session_state["profile"] = UserProfile(
            city=city, lifestyle=life_map[lifestyle],
            transport=trans_map[transport], household=hh_map[household],
            outdoor_pref=out_map[outdoor],
            concerns=[con_map[c] for c in concerns],
            budget=bud_map[budget], priority=pri_map[priority])
        st.session_state.pop("ai_text", None)
        st.session_state.pop("ai_text_for", None)
        st.session_state.pop("ai_text_provider", None)

    profile: UserProfile | None = st.session_state.get("profile")
    if profile is None:
        ui.empty_state("Fill in the short form above to get your plan. "
                       "Your answers stay in this browser session only.")
        return

    if not _require_measurement():
        st.button("Start an air-quality check", key="as_go_home",
                  on_click=lambda: st.session_state.update(
                      nav_page="Home", home_entry="manual"))
        return
    m = _meas()
    recs = generate_recommendations(m, profile)

    ui.card("Your situation",
            body_html=f"<p>{html.escape(profile.summary())}</p>"
                     f"<p>Outdoor activity: {html.escape(outdoor)} · "
                     f"Budget: {html.escape(budget)} · "
                     f"Priority: {html.escape(priority)}</p>")

    for group, label in GROUP_LABELS.items():
        items = recs.get(group, [])
        if not items:
            continue
        st.markdown(f"**{label}**")
        for r in sorted(items, key=lambda x: x.priority):
            pri_color = {1: "#b91c1c", 2: "#b45309", 3: "#2563eb"}[r.priority]
            pri_label = {1: "Priority", 2: "Suggested", 3: "Optional"}[
                r.priority]
            extras = ""
            if r.when:
                extras += f'<p><b>When:</b> {r.when}</p>'
            if r.cost:
                extras += f'<p><b>Cost:</b> {r.cost}</p>'
            if r.alternative:
                extras += f'<p><b>Alternative:</b> {r.alternative}</p>'
            st.markdown(
                f'<div class="aw-card" style="border-left:4px solid {pri_color}">'
                f'<h4>{r.title} '
                f'<span class="aw-meta">· {pri_label}</span></h4>'
                f'<p><b>What:</b> {r.detail}</p>'
                f'{extras}'
                f'<div class="aw-reason"><b>Why it matters:</b> {r.reason}</div>'
                f'</div>', unsafe_allow_html=True)
        ui.hr()

    # ---------- optional AI enhancement ----------
    st.markdown("**A warmer explanation (optional)**")
    provider = ai.get_provider()
    if provider is not None:
        model_label = getattr(provider, "model", lambda: provider.name)()
        st.caption(f"AI provider detected ({provider.name}"
                   + (f", model {model_label}" if model_label else "")
                   + "). The button below sends your profile summary and "
                   "top recommendations to the provider's API for a "
                   "narrative briefing. Output is clearly labelled as "
                   "AI-generated and is HTML-escaped before display.")
        # Fingerprint of the inputs the briefing was generated from, so a
        # stale briefing is never shown for a different reading/profile.
        fp = (measurement_fingerprint(m), profile.summary())
        if st.button("Generate AI briefing", key="ai_gen"):
            top = [r.title + " - " + r.detail
                   for items in recs.values() for r in items[:3]]
            prompt = ai.build_assistant_prompt(
                f"AQI {m.display_aqi:.0f} ({m.category_name}) at {m.location}; "
                f"source: {m.source_label}; timestamp: "
                f"{m.timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
                profile.summary(), top)
            with st.spinner(f"Asking {provider.name}..."):
                text = provider.generate(prompt)
            if text:
                st.session_state["ai_text"] = text
                st.session_state["ai_text_for"] = fp
                st.session_state["ai_text_provider"] = provider.name
            else:
                st.warning(f"{provider.name} did not respond (network, "
                           "quota or configuration). Your rule-based plan "
                           "above is unaffected.")
        ai_text = st.session_state.get("ai_text")
        if ai_text and st.session_state.get("ai_text_for") == fp:
            st.markdown(
                '<div class="aw-card" style="border-left:4px solid #7c3aed">'
                f'<h4>AI-generated briefing · '
                f'{html.escape(st.session_state.get("ai_text_provider", provider.name))}</h4>'
                f'<p style="white-space:pre-wrap">'
                f'{html.escape(ai_text)}</p>'
                '<p class="aw-meta">Generated by an AI model from your '
                'profile and the rule-based recommendations. Verify health '
                'decisions with a professional.</p></div>',
                unsafe_allow_html=True)
        elif ai_text:
            st.info("A briefing was generated for different inputs (reading "
                    "or profile changed). Regenerate it to match the "
                    "current data.")
    else:
        st.caption("_Rule-based guidance only._ Add `GEMINI_API_KEY` to "
                   "`.streamlit/secrets.toml` to optionally enable an "
                   "AI-written narrative briefing. Everything above "
                   "works without it.")

    # ---------- personal report ----------
    ui.hr()
    st.markdown("**Take your plan with you**")
    plan_state = st.session_state.get("daily_plan", {})
    md = report.build_report(m, profile, recs,
                             plan_guidance=plan_state or None)
    st.download_button("Download my air plan (Markdown)",
                       data=md, file_name="airaware_my_plan.md",
                       mime="text/markdown",
                       key="report_dl")
    st.caption("The report contains your reading, profile and "
               "recommendations - stored only in this file, nowhere else.")


# ===========================================================================
# DAILY AIR PLAN
# ===========================================================================

def planner_page():
    ui.hero("My Daily Air Plan",
            "A personalised schedule shaped by today's reading. Guidance "
            "reflects current conditions - it does not predict future hours.")
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

    key = "daily_plan"
    # rebuild when there is no plan, an explicit regenerate was requested,
    # or the underlying measurement changed (fingerprint survives
    # session-state serialisation, unlike id(m))
    meas_fp = measurement_fingerprint(m)
    meas_changed = st.session_state.get("plan_meas_fp") != meas_fp
    if (key not in st.session_state or st.session_state.get("plan_regen")
            or meas_changed):
        st.session_state[key] = {p.slot_key: p.guidance for p in plan}
        st.session_state["plan_regen"] = False
        st.session_state["plan_meas_fp"] = meas_fp

    c1, c2 = st.columns([1, 4])
    c1.button("Regenerate from current reading", key="plan_reset",
              on_click=lambda: st.session_state.update(plan_regen=True))
    st.caption("“now” marks whichever time-of-day slot contains the current "
               "hour - guidance itself still reflects today's reading, "
               "not an hourly forecast.")

    slot_icons = {
        "morning": "MORNING", "commute_am": "AM TRAVEL",
        "midday": "MIDDAY", "commute_pm": "PM TRAVEL",
        "evening": "EVENING", "night": "NIGHT",
    }
    now_slot = current_time_slot()
    for p in plan:
        marker = " · now" if p.slot_key == now_slot else ""
        edited = st.text_area(
            f"{slot_icons.get(p.slot_key, p.slot_label)} — {p.focus}{marker}",
            value=st.session_state[key].get(p.slot_key, p.guidance),
            key=f"plan_{p.slot_key}", height=64)
        st.session_state[key][p.slot_key] = edited

    st.download_button(
        "Download my plan (CSV)",
        data=pd.DataFrame([{
            "slot": p.slot_label, "focus": p.focus,
            "guidance": st.session_state[key].get(p.slot_key, p.guidance),
        } for p in plan]).to_csv(index=False),
        file_name="airaware_daily_plan.csv", mime="text/csv",
        key="plan_dl")


# ===========================================================================
# INDOOR AIR GUARDIAN
# ===========================================================================

def indoor_page():
    ui.hero("Indoor Air Guardian",
            "Your home is where you spend most of your time - make the air "
            "inside it healthier, one room at a time.")
    m = _meas()
    cat = m.category_name if m else None

    head, detail = ventilation_advice(cat)
    ui.card(head, body_html=f"<p>{detail}</p>")
    if m:
        st.caption(_measurement_caption(m))

    ui.section_title("Pick a room")
    room_cols = st.columns(5)
    for i, r in enumerate(ROOMS):
        with room_cols[i]:
            if st.button(r.name, key=f"room_{r.name}",
                         width="stretch"):
                st.session_state["indoor_room"] = r.name
                st.rerun()
    sel = st.session_state.get("indoor_room", ROOMS[0].name)
    room = next(r for r in ROOMS if r.name == sel)
    ui.card(room.name,
            body_html="<br>".join(f"• {x}" for x in room.priorities) +
            f'<p class="aw-meta" style="margin-top:.5rem">{room.notes}</p>')

    ui.section_title("Improvements by budget")
    st.caption("Indicative Indian-rupee ranges - prices vary by brand and "
               "city; planning estimates, not quotes.")
    tab_labels = [f"{BUDGET_TIERS[k]['label']} · {BUDGET_TIERS[k]['range']}"
                  for k in BUDGET_TIERS]
    tabs = st.tabs(tab_labels)
    for tab, key in zip(tabs, BUDGET_TIERS.keys()):
        with tab:
            t = BUDGET_TIERS[key]
            for item in t["items"]:
                st.markdown(f"- {item}")

    ui.section_title("Indoor pollution sources to control")
    st.markdown(
        "- **Cooking** - frying and biomass fuels are the biggest indoor PM2.5 sources.\n"
        "- **Tobacco smoke & incense** - no safe level indoors; eliminate.\n"
        "- **Dust** - resuspends with activity; damp-clean and use doormats.\n"
        "- **Cleaning products** - many emit VOCs; choose fragrance-free.\n"
        "- **Outdoor infiltration** - depends on today's AQI; seal windows on bad days.\n"
        "- **Mould & damp** - worsens without ventilation; fix leaks promptly."
    )
    st.caption("Honest note: houseplants improve wellbeing but are **not** "
               "air purifiers - their effect on PM2.5 is negligible.")


# ===========================================================================
# GREEN LIFESTYLE PLANNER
# ===========================================================================

def lifestyle_page():
    ui.hero("Green Lifestyle Planner",
            "Practical low-emission swaps for transport, energy, waste and "
            "home - each with honest benefits and limitations.")

    profile = st.session_state.get("profile")
    if profile is None:
        st.info("Complete the **Personal AI Assistant** form to rank these "
                "options for your situation - or browse everything below.")
        scored = [(0, o) for o in all_options()]
    else:
        scored = personalised_options(profile)

    area_filter = st.selectbox("Focus area", ["All"] + list(options_by_area().keys()),
                               key="life_area")

    current_area = None
    for score, opt in scored:
        if area_filter != "All" and opt.area != area_filter:
            continue
        if opt.area != current_area:
            st.markdown(f"**{opt.area}**")
            current_area = opt.area
        badge = f" · match {score}" if profile and score > 0 else ""
        body = (f"<p>{opt.detail}</p>"
                f"<p><b>Benefit:</b> {opt.benefit}</p>"
                f"<p><b>Limitation:</b> {opt.limitation}</p>")
        if opt.conditions:
            body += "<p><b>Applies when:</b> " + "; ".join(opt.conditions) + "</p>"
        ui.card(f"{opt.title}{badge}", body_html=body)


# ===========================================================================
# ENVIRONMENTAL IMPACT
# ===========================================================================

def impact_page():
    ui.hero("Environmental Impact Tracker",
            "Estimate the climate benefit of your greener choices. All "
            "figures are transparent estimates - not measured reductions.")

    ui.card("CO₂e vs air pollution",
            body_html="<p>CO₂e savings from transport and energy are "
                      "<b>climate</b> benefits. They are not the same as PM2.5 "
                      "or local air-pollution reductions - though cleaner "
                      "transport usually helps both.</p>")

    # --- Trip calculator ---
    st.markdown("### Compare a trip")
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
    st.markdown("### Air-conditioning savings estimate")
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
    st.markdown("### Your logged actions")
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

    st.caption("Vehicle factors are generic estimates; real savings depend "
               "on your vehicle, driving style and occupancy. Grid factor: "
               "0.82 kg CO₂/kWh (Indian average).")


# ===========================================================================
# FAMILY & COMMUNITY
# ===========================================================================

def community_page():
    ui.hero("Family & Community",
            "Small household habits add up - checklists, kid-friendly "
            "explanations and ideas for your neighbourhood.")

    st.markdown("### Household air-quality checklist")
    checklist_items = [
        "Keep windows closed on Poor-or-worse days; ventilate on clean days",
        "Run the kitchen exhaust fan for every cooking session",
        "No smoking, incense or mosquito coils indoors",
        "Damp-dust and wet-mop weekly",
        "Shoes off at the door",
        "HEPA purifier in the most-used room (bedroom first)",
        "AC filters cleaned monthly",
        "Avoid vehicle idling near the home",
        "Plan school/office commutes around peak traffic where possible",
    ]
    done = st.session_state.setdefault("community_checklist", {})
    for i, item in enumerate(checklist_items):
        done[i] = st.checkbox(item, value=done.get(i, False), key=f"chk_{i}")
    pct = sum(done.values()) / len(checklist_items) * 100
    st.progress(pct / 100, text=f"{pct:.0f}% complete")

    ui.section_title("For children - a simple explanation")
    ui.card("Why the air matters",
            body_html="<p>Air pollution is like tiny invisible dust floating "
                      "in the air. Some days there is more of it - we can "
                      "see it as haze. When the air is bad, our lungs work "
                      "harder, just like running up stairs. We can help by "
                      "<b>walking or cycling</b> to nearby places (cleaner "
                      "than cars), <b>closing windows</b> on smoky days, and "
                      "<b>saving electricity</b> so power plants burn less "
                      "fuel.</p>")

    ui.section_title("Community action ideas")
    st.markdown(
        "- **Car-free day** - one day a week where the household uses only "
        "walking, cycling or transit.\n"
        "- **Neighbourhood clean-up** - collect roadside waste before it is "
        "burned.\n"
        "- **Tree drive** - coordinate with your RWAs or school for native "
        "saplings.\n"
        "- **School awareness** - share the kids' explainer with teachers; "
        "many schools run 'clean commute' weeks.\n"
        "- **Report violations** - dusty construction without sprinkling or "
        "open garbage burning; log them on your municipal app."
    )

    ui.section_title("Today's family plan")
    m = _meas()
    if m and m.display_aqi is not None:
        profile = st.session_state.get("profile")
        has_kids = profile and profile.household == "children"
        plan = build_daily_plan(
            m, profile.outdoor_pref if profile else "moderate",
            has_children=bool(has_kids))
        plan_state = st.session_state.get("daily_plan", {})
        for p in plan:
            st.markdown(f"- **{p.slot_label}:** "
                        f"{html.escape(plan_state.get(p.slot_key, p.guidance))}")
    else:
        st.caption("Load a reading on Home to see today's family plan.")


# ===========================================================================
# ABOUT & DATA SOURCES
# ===========================================================================

def about_page():
    ui.hero("About & Data Sources",
            "The methodology, assumptions and honest limitations behind "
            "every number AirAware shows you.")

    st.markdown("### How AQI is calculated")
    st.markdown(
        "AirAware AI implements the **CPCB National Air Quality Index "
        "(NAQI)** method: each measured pollutant (PM2.5, PM10, NO₂, SO₂, "
        "CO, O₃, NH₃) is converted to a sub-index via published "
        "concentration breakpoints using piecewise-linear interpolation. "
        "The overall AQI is the **maximum** sub-index and that pollutant is "
        "the dominant one. Averaging periods follow CPCB (24-hour, 8-hour "
        "for O₃). Partial measurements are labelled as partial - the true "
        "AQI could be higher.\n\n"
        "Categories: Good (0-50) · Satisfactory (51-100) · Moderate "
        "(101-200) · Poor (201-300) · Very Poor (301-400) · Severe "
        "(401-500) · Severe+ (>500).")

    st.markdown("### Live data providers")
    status = providers.provider_status()
    if status:
        for s in status:
            if s["configured"] and s["health"] and s["health"]["ok"]:
                st.caption(f"- **{s['name']}**: configured - "
                           f"{s['health']['detail']}")
            elif s["configured"]:
                st.warning(f"- **{s['name']}**: configured but unhealthy - "
                           f"{(s['health'] or {}).get('detail', 'unreachable')}")
            else:
                st.caption(f"- **{s['name']}**: not configured "
                           f"(set `{s['name'].upper()}_API_KEY` in secrets to enable)")
    else:
        st.caption("No live providers configured. Add `OPENAQ_API_KEY` to "
                   "`.streamlit/secrets.toml` to enable live fetches; "
                   "everything else works without it.")
    st.caption("Live fetches appear on Home under 'Fetch live monitoring "
               "data' and always carry the provider's own timestamp and "
               "station name. Stale readings are labelled, never passed "
               "off as current.")

    st.markdown("### Data sources & provenance")
    st.markdown(
        "- **Your entries** - treated as user-provided, unverified.\n"
        "- **CSV imports** - parsed and validated locally; nothing uploaded.\n"
        "- **Sample data** - illustrative demo values, always labelled.\n"
        "- **Live provider data** - fetched on demand from configured "
        "providers (OpenAQ), timestamped and station-attributed.\n\n"
        "Every measurement records value, unit, source and timestamp.")

    st.markdown("### Recommendation methodology")
    st.markdown(
        "Recommendations come from a deterministic Python rule engine "
        "mapping AQI category + dominant pollutant + your profile to "
        "actionable guidance. Every item shows what to do, why it matters, "
        "when, approximate cost and an alternative where meaningful.\n\n"
        "**Optional AI:** if `GEMINI_API_KEY` is configured in Streamlit "
        "secrets, an AI provider (Gemini) can rewrite the briefing in "
        "natural language. Output is always labelled *AI-generated*; without "
        "the key, the rule engine alone powers the app. No other AI service "
        "is used or claimed.")

    st.markdown("### Impact calculation assumptions")
    st.markdown(
        "Vehicle CO₂e factors are generic estimates (petrol car ≈0.19 "
        "kg/km, electric car ≈0.10 kg/km on the Indian grid, metro "
        "≈0.02 kg/passenger-km). Grid intensity ≈0.82 kg CO₂/kWh. Fuel "
        "prices and economy are defaults you can override. Figures are "
        "estimates of climate benefit, not measured reductions.")

    st.markdown("### Technology")
    st.markdown("Python 3.14 · Streamlit · pandas · plotly · optional "
                "Gemini API (stdlib urllib only). No database, no required "
                "API keys, no paid services. State lives in your browser "
                "session; reports are downloadable files.")

    st.markdown("### Limitations & future work")
    st.markdown(
        "- Live fetch requires a provider API key; without one the app "
        "relies on manual entry, CSV import or labelled samples.\n"
        "- Recommendations are rule-based, not ML-personalised.\n"
        "- Indoor guidance is qualitative; a real PM2.5 sensor would enable "
        "quantitative tracking.\n"
        "- Hourly pollution is not predicted; plans adapt to the current "
        "reading only.\n"
        "- Future: CPCB/OpenAQ live fetch, multi-day exposure logging, "
        "household sharing.")
