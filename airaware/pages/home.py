"""Home page: editorial hero, reading band, daily intelligence card
and the data-entry panels (manual, CSV, sample, live).
"""

from __future__ import annotations

import html

import streamlit as st

import airaware.forecast as forecast  # noqa: PLR0402
import airaware.providers as providers  # noqa: PLR0402
import airaware.ui as ui  # noqa: PLR0402
from airaware.alerts import evaluate_alerts
from airaware.aqi import category_color, is_outdoor_safe
from airaware.data import SAMPLE_MEASUREMENTS, MeasurementSet

from ._common import (
    _flash,
    _manual_entry_form,
    _meas,
    _provenance_warning,
    _save_measurement,
    import_csv_measurements,
)


def _home_hero():
    """Editorial landing hero: story left, illustrated scene + clearly
    labelled sample AQI card right."""
    trust = "".join(
        f'<span>{ui.icon(ic, 14)}{html.escape(t)}</span>'
        for ic, t in [("shield", "CPCB methodology"),
                      ("eye", "Privacy-conscious"),
                      ("bolt", "Offline-ready")])
    art = (
        '<div style="position:absolute;inset:0">'
        + ui.hero_art()
        + ui.floating_aqi_card(64.0, "Good", "Sample reading · Pune")
        + '</div>')
    st.markdown(
        '<div class="aw-hero"><div class="aw-hero-grid">'
        '<div class="aw-hero-left">'
        '<span class="aw-eyebrow aw-eyebrow--light">AirAware AI</span>'
        '<h1>Breathe better.<br>Live well.</h1>'
        '<p class="aw-sub">Air quality shouldn\'t feel like a chemistry '
        'lesson. AirAware turns the numbers into simple, personal answers '
        '- what to do today, how to protect your home, and how to move '
        'cleaner together.</p>'
        '<div class="aw-trust">' + trust + '</div>'
        '<div class="aw-meta" style="margin-top:1.4rem">'
        'CPCB AQI methodology · works offline · no account needed</div>'
        '</div>'
        f'<div class="aw-hero-right">{art}</div>'
        '</div></div>',
        unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Check my air", key="hero_check",
                     type="primary", width="stretch"):
            st.session_state["home_entry"] = "manual"
            st.rerun()
    with c2:
        if st.button("Take the tour", key="hero_explore",
                     width="stretch"):
            st.session_state["nav_page"] = "Air Quality Explorer"
            st.rerun()


def _daily_intelligence(m: MeasurementSet):
    """Home 'daily intelligence' card: connects reading -> advice -> plan."""
    hist = st.session_state.get("measurement_history") or []
    outlook = forecast.build_outlook(m, history=hist)
    best = outlook.best_window
    dom = (m.result.dominant_pollutant.upper()
           if m.result and m.result.dominant_pollutant else "-")
    safe, safe_msg = is_outdoor_safe(m.category_name or "Good", "moderate")

    chips = (
        f'<span class="aw-chip" style="border-color:{category_color(m.category_name)};'
        f'color:{category_color(m.category_name)}">AQI {m.display_aqi:.0f} · '
        f'{html.escape(m.category_name or "-")}</span>'
        f'<span class="aw-chip">{ui.icon("activity", 14)} '
        f'{html.escape(dom)}</span>'
        + (f'<span class="aw-chip">{ui.icon("sun", 14)} Best outdoor '
           f'window: {html.escape(best.label.split(" (")[0]) if best else "-"}'
           f'</span>' if best else "")
        + f'<span class="aw-chip">{ui.icon("home", 14)} '
        f'{"Outdoor time OK" if safe else "Indoor-first day"}</span>')

    # Plan progress, if the daily plan exists for this reading.
    prog_html = ""
    plan = st.session_state.get("daily_plan")
    if plan:
        done_keys = [f"plan_done_{k}" for k in plan]
        done = sum(1 for k in done_keys if st.session_state.get(k))
        pct = done / len(done_keys) * 100 if done_keys else 0
        prog_html = (f'<div style="margin-top:.7rem;display:flex;'
                     f'align-items:center;gap:.6rem">'
                     f'<div style="flex:1;height:8px;border-radius:4px;'
                     f'background:var(--mint);overflow:hidden">'
                     f'<div style="height:100%;width:{pct:.0f}%;'
                     f'background:var(--evergreen)"></div></div>'
                     f'<span class="aw-meta">Daily plan {pct:.0f}% '
                     f'complete</span></div>')

    st.markdown(
        '<div class="aw-card" style="border-left:5px solid var(--evergreen);'
        'margin-top:1rem">'
        '<div class="aw-eyebrow" style="margin-bottom:.5rem">Today\'s '
        'intelligence</div>'
        f'<div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.6rem">'
        f'{chips}</div>'
        f'<p style="margin:.2rem 0">{html.escape(safe_msg)}</p>'
        f'{prog_html}</div>',
        unsafe_allow_html=True)


def _reading_band(m: MeasurementSet):
    """Today's-reading summary with a visual AQI ring + provenance."""
    cat_color = category_color(m.category_name)
    if m.display_aqi is not None:
        st.markdown(
            '<div class="aw-card"><div class="aw-aqi-wrap">'
            + ui.aqi_ring(m.display_aqi, m.category_name or "", size=132)
            + '<div class="aw-aqi-side" style="flex:1;min-width:220px">'
            + '<div class="aw-eyebrow">Your current reading</div>'
            + f'<div class="big">{html.escape(m.location or "-")} · '
            + f'{m.timestamp.strftime("%d %b %Y, %H:%M UTC")}</div>'
            + '<div class="aw-meta" style="margin:.35rem 0 .8rem">'
            + f'{html.escape(m.source_label)}</div>'
            + '<div style="display:flex;gap:.6rem;flex-wrap:wrap">'
            + f'<span class="aw-chip" style="border-color:{cat_color};'
            + f'color:{cat_color}">{ui.icon("gauge", 14)} AQI '
            + f'{m.display_aqi:.0f}</span>'
            + f'<span class="aw-chip">{ui.icon("activity", 14)} '
            + f'{html.escape(m.category_name or "-")}</span></div>'
            + '</div></div></div>',
            unsafe_allow_html=True)
    for a in evaluate_alerts(m):
        ui.alert_box(a.severity, a.title, a.detail)
    _provenance_warning(m)
    c1, c2 = st.columns(2)
    c1.button("See full assessment", key="home_to_explorer",
              on_click=lambda: st.session_state.update(
                  nav_page="Air Quality Explorer"))
    c2.button("Get personalised advice", key="home_to_assistant",
              on_click=lambda: st.session_state.update(
                  nav_page="Personal AI Assistant"))

    _daily_intelligence(m)


def _entry_card(icon_name: str, title: str, desc: str, btn_label: str,
                key: str, value: str, pill: str = "",
                extra_html: str = "") -> None:
    pill_html = (f' <span class="aw-tag-soft">{html.escape(pill)}</span>'
                 if pill else "")
    st.markdown(
        f'<div class="aw-card aw-card--cta" style="height:100%;'
        f'display:flex;flex-direction:column">'
        f'<div class="aw-feat-ico aw-feat-ico--lg">{ui.icon(icon_name, 26)}</div>'
        f'<h4>{html.escape(title)}{pill_html}</h4>'
        f'<p style="flex:1">{html.escape(desc)}</p>{extra_html}</div>',
        unsafe_allow_html=True)
    if st.button(btn_label, key=key, width="stretch"):
        st.session_state["home_entry"] = value
        st.rerun()


def _sample_preview() -> str:
    """Mini list of sample cities with their demo AQIs (accurately labelled)."""
    rows = "".join(
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:center;padding:.28rem 0;font-size:.8rem">'
        f'<span>{html.escape(m.location.split(" (")[0])}</span>'
        f'<b style="color:{category_color(m.category_name)}">'
        f'{m.display_aqi:.0f}</b></div>'
        for m in SAMPLE_MEASUREMENTS)
    return ('<div style="background:var(--mint);border-radius:12px;'
            'padding:.6rem .9rem;margin-top:.7rem;border:1px solid '
            'var(--sage-soft)">'
            '<div style="font-size:.68rem;font-weight:800;letter-spacing:'
            '.1em;text-transform:uppercase;color:var(--evergreen)">'
            'Sample cities</div>' + rows + '</div>')


def home_page():
    _flash()
    m = _meas()

    _home_hero()

    # ---------- current reading ----------
    if m and m.display_aqi is not None:
        _reading_band(m)

    # ---------- start your journey ----------
    ui.section_title("Start with a reading")
    entry = st.session_state.get("home_entry")

    if entry is None:
        choices = [
            ("gauge", "Measure my air",
             "Type PM2.5, PM10 or AQI values you already have",
             "Enter my own numbers", "manual", ""),
            ("upload", "Upload my report",
             "Import a CSV exported from CPCB, a monitor or OpenAQ",
             "Upload a CSV", "csv", ""),
            ("eye", "Explore sample data",
             "Try realistic sample readings - always labelled as samples",
             "Browse samples", "sample", "SAMPLE"),
        ]
        if providers.available_providers():
            choices.append(
                ("activity", "Fetch live data",
                 "Pull the freshest reading from a configured provider",
                 "Fetch live reading", "live", "LIVE"))
        cols = st.columns(len(choices))
        for col, (ic, title, desc, btn, val, pill) in zip(cols, choices):
            with col:
                extra = (_sample_preview() if val == "sample" else "")
                _entry_card(ic, title, desc, btn, f"entry_{val}", val,
                            pill=pill, extra_html=extra)
    else:
        _entry_panel(entry)
        if st.button("← Back to all options", key="entry_back"):
            st.session_state.pop("home_entry", None)
            st.rerun()

    # ---------- image-led feature showcase ----------
    ui.hr()
    ui.section_title("What AirAware can do for you")

    st.markdown(
        '<div class="aw-show">'
        '<div class="art">' + ui.scene("city") + '</div>'
        '<div><div class="aw-eyebrow">Understand</div>'
        '<h3>See your air clearly</h3>'
        '<ul class="aw-show-points">'
        '<li>' + ui.icon("check", 16) + '<span>CPCB-method AQI from real '
        'pollutant measurements</span></li>'
        '<li>' + ui.icon("check", 16) + '<span>Honest labels for partial '
        'or sample data</span></li>'
        '<li>' + ui.icon("check", 16) + '<span>Pollutant-by-pollutant '
        'breakdown with plain-language notes</span></li>'
        '</ul></div></div>', unsafe_allow_html=True)
    if st.button("Explore the data", key="feat_explorer",
                 type="primary"):
        st.session_state["nav_page"] = "Air Quality Explorer"
        st.rerun()

    st.markdown(
        '<div class="aw-show aw-show--flip">'
        '<div class="art">' + ui.scene("companion") + '</div>'
        '<div><div class="aw-eyebrow">Get guidance</div>'
        '<h3>A companion that knows your routine</h3>'
        '<ul class="aw-show-points">'
        '<li>' + ui.icon("check", 16) + '<span>Prioritised advice with '
        'reasons, timing and costs</span></li>'
        '<li>' + ui.icon("check", 16) + '<span>A day plan that adapts to '
        'today\'s reading</span></li>'
        '<li>' + ui.icon("check", 16) + '<span>Optional AI briefing - '
        'everything works without it</span></li>'
        '</ul></div></div>', unsafe_allow_html=True)
    if st.button("Meet your assistant", key="feat_assistant"):
        st.session_state["nav_page"] = "Personal AI Assistant"
        st.rerun()

    st.markdown(
        '<div class="aw-show">'
        '<div class="art">' + ui.scene("indoor") + '</div>'
        '<div><div class="aw-eyebrow">Protect</div>'
        '<h3>A healthier home, room by room</h3>'
        '<ul class="aw-show-points">'
        '<li>' + ui.icon("check", 16) + '<span>Room-by-room indoor air '
        'tips for every budget</span></li>'
        '<li>' + ui.icon("check", 16) + '<span>Smart ventilation guidance '
        'based on today\'s AQI</span></li>'
        '<li>' + ui.icon("check", 16) + '<span>Household checklists the '
        'whole family can use</span></li>'
        '</ul></div></div>', unsafe_allow_html=True)
    if st.button("Check my rooms", key="feat_indoor"):
        st.session_state["nav_page"] = "Indoor Air Guardian"
        st.rerun()

    # secondary destinations as compact cards
    ui.section_title("More ways to make a difference")
    c1, c2, c3 = st.columns(3)
    with c1:
        ui.feature_tile("Greener everyday choices", "Compare transit, "
                        "carpool, cycling and walking with honest "
                        "trade-offs.", "recycle", "Explore options",
                        "feat_lifestyle", "Green Lifestyle Planner")
    with c2:
        ui.feature_tile("Track your impact", "See the climate benefit of "
                        "your greener choices, in numbers.", "globe",
                        "See my impact", "feat_impact",
                        "Environmental Impact")
    with c3:
        ui.feature_tile("Family & community", "Simple explanations kids "
                        "understand, plus ideas for your neighbourhood.",
                        "users", "Get family tips", "feat_family",
                        "Family & Community")

    # ---------- journey ----------
    ui.hr()
    ui.section_title("How it works")
    ui.journey([
        ("gauge", "Measure", ("Enter what you know, upload a report, or "
         "explore labelled samples.")),
        ("eye", "Understand", "Plain-language answers, not raw indices."),
        ("sparkles", "Act", ("Prioritised steps for today, your home and "
         "your trips.")),
    ])

    # ---------- personal wellness ----------
    ui.section_title("Small changes, easier breathing")
    w1, w2, w3 = st.columns(3)
    with w1:
        ui.card("Time your outdoor time",
                body_html='<p>On poor-air days, exercise early morning or '
                'after rain. AirAware\'s daily plan tells you which slots '
                'are safest.</p>')
    with w2:
        ui.card("Protect the vulnerable",
                body_html='<p>Children, older adults and anyone with '
                'asthma feel poor air sooner. Keep their spaces filtered '
                'and ventilate on clean days.</p>')
    with w3:
        ui.card("Sleep with cleaner air",
                body_html='<p>You spend a third of life asleep. A bedroom '
                'purifier and closed windows on bad days add up to real '
                'exposure reduction.</p>')

    # ---------- environmental impact ----------
    st.markdown(
        '<div class="aw-cta-band" style="text-align:left">'
        '<div class="aw-band-grid">'
        '<div><div class="aw-eyebrow aw-eyebrow--light">Your impact</div>'
        '<h2 style="text-align:left">Every clean choice adds up.</h2>'
        '<p style="text-align:left;margin-left:0">Swap one car trip for a '
        'metro ride or cycle and you can cut kilograms of CO₂e a week. '
        'Track what you save - the planet notices.</p></div>'
        '<div style="border-radius:18px;overflow:hidden">'
        + ui.scene("impact") + '</div></div></div>',
        unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Start tracking my impact", key="home_impact",
                     type="primary", width="stretch"):
            st.session_state["nav_page"] = "Environmental Impact"
            st.rerun()
    with c2:
        if st.button("See greener swaps", key="home_lifestyle",
                     width="stretch"):
            st.session_state["nav_page"] = "Green Lifestyle Planner"
            st.rerun()

    # ---------- closing CTA ----------
    st.markdown(
        '<div class="aw-cta-band"><h2>A healthier day starts with '
        'knowing your air.</h2><p>It takes under a minute - enter what '
        'you know, or explore realistic sample readings first.</p></div>',
        unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Start an air-quality check", key="cta_final",
                     type="primary", width="stretch"):
            st.session_state["home_entry"] = "manual"
            st.rerun()
    with c2:
        if st.button("Explore sample data", key="cta_sample",
                     width="stretch"):
            st.session_state["home_entry"] = "sample"
            st.rerun()

    with st.expander("Good to know"):
        st.markdown(
            "- **AQI is a maximum, not an average** - one bad pollutant "
            "sets the whole index under the CPCB method.\n"
            "- **PM2.5 is the quiet risk** - particles small enough to "
            "enter the bloodstream; filtration and masks matter most "
            "here.\n"
            "- **Short trips pollute most per km** - cold engines and "
            "stop-go traffic multiply emissions; combine errands when "
            "you can.\n"
            "- **Windows are a two-way door** - open them on clean days, "
            "keep them shut (and filter) on polluted ones."
        )


def _entry_panel(entry: str):
    if entry == "manual":
        _manual_entry_form(prefix="home")
    elif entry == "csv":
        _csv_entry_panel()
    elif entry == "sample":
        _sample_entry_panel()
    elif entry == "live":
        _live_entry_panel()


def _csv_entry_panel():
    st.markdown("**Upload an air-quality CSV**")
    st.caption("Expected columns: pollutant names (pm25, pm10, no2, so2, "
               "co, o3, nh3) and optional `aqi`, `location`, `timestamp`. "
               "Max 2 MB / 5,000 rows. Files are parsed locally only.")
    up = st.file_uploader("Choose a CSV file", type=["csv"], key="home_csv_up")
    if up is not None and st.button("Import file", key="home_csv_go",
                                    type="primary"):
        import_csv_measurements(
            up, "Imported {count} observation(s) - select one below.")
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
            _save_measurement(csv_list[pick])
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
        _save_measurement(m)
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
        _save_measurement(SAMPLE_MEASUREMENTS[pick])
        st.session_state["flash_success"] = ("Sample demonstration data "
                                              "loaded - not a live reading.")
        st.session_state["nav_page"] = "Air Quality Explorer"
        st.rerun()
