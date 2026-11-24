"""About & Data Sources page: methodology, provider and AI status,
data provenance, assumptions, limitations and build information.
"""

from __future__ import annotations

import html

import streamlit as st

import airaware.ai as ai  # noqa: PLR0402
import airaware.build_info as build_info  # noqa: PLR0402
import airaware.providers as providers  # noqa: PLR0402
import airaware.ui as ui  # noqa: PLR0402


def about_page():
    ui.page_header(
        "About & Data Sources",
        "How AirAware works",
        "The methodology, assumptions and honest limitations behind "
        "every number AirAware shows you.")

    # ---------- editorial methodology ----------
    st.markdown(
        '<div class="aw-card" style="border-left:5px solid var(--evergreen)">'
        '<h4>Our promise: honest numbers</h4>'
        '<p>Every reading shows where it came from, how old it is, and '
        'how complete it is. Sample data is always labelled. Estimates '
        'are labelled as estimates. If we don\'t know, we say so.</p></div>',
        unsafe_allow_html=True)

    st.markdown('<div class="aw-section-title" style="font-size:1.3rem">'
                'How your AQI is calculated</div>', unsafe_allow_html=True)
    steps = [
        ("1", "Measure", ("You provide pollutant concentrations "
         "(PM2.5, PM10, NO₂, SO₂, CO, O₃, NH₃) - by typing them in, "
         "uploading a CSV, or fetching a live station reading.")),
        ("2", "Convert", ("Each pollutant is mapped to a sub-index using "
         "published CPCB concentration breakpoints, with piecewise-linear "
         "interpolation.")),
        ("3", "Combine", ("The overall AQI is the <b>maximum</b> "
         "sub-index - one bad pollutant sets the whole index. That "
         "pollutant is flagged as the dominant one.")),
        ("4", "Explain", ("The number becomes guidance: what to do today, "
         "how to protect your home, and which swaps help most.")),
    ]
    cells = "".join(
        f'<div class="aw-kpi" style="text-align:left;padding:1rem 1.1rem">'
        f'<div class="aw-feat-ico" style="width:34px;height:34px;'
        f'border-radius:10px;font-weight:800;font-family:var(--serif);'
        f'font-size:1rem">{n}</div>'
        f'<div style="font-weight:700;color:var(--forest);font-size:.9rem;'
        f'margin:.3rem 0 .15rem">{t}</div>'
        f'<div style="font-size:.82rem;color:var(--muted);line-height:1.5">'
        f'{d}</div></div>' for n, t, d in steps)
    st.markdown(f'<div class="aw-grid" style="grid-template-columns:'
                f'repeat(auto-fit,minmax(210px,1fr))">{cells}</div>',
                unsafe_allow_html=True)

    with st.expander("Technical details: CPCB breakpoints & categories"):
        st.markdown(
            "AirAware AI implements the **CPCB National Air Quality Index "
            "(NAQI)** method: each measured pollutant (PM2.5, PM10, NO₂, "
            "SO₂, CO, O₃, NH₃) is converted to a sub-index via published "
            "concentration breakpoints using piecewise-linear "
            "interpolation. The overall AQI is the **maximum** sub-index "
            "and that pollutant is the dominant one. Averaging periods "
            "follow CPCB (24-hour, 8-hour for O₃). Partial measurements "
            "are labelled as partial - the true AQI could be higher.\n\n"
            "Categories: Good (0-50) · Satisfactory (51-100) · Moderate "
            "(101-200) · Poor (201-300) · Very Poor (301-400) · Severe "
            "(401-500) · Severe+ (>500).")

    # ---------- live providers ----------
    st.markdown('<div class="aw-section-title" style="font-size:1.3rem">'
                'Live data providers</div>', unsafe_allow_html=True)
    status = providers.provider_status()
    if status:
        for s in status:
            ok = s["configured"] and s["health"] and s["health"]["ok"]
            icon_name = "check" if ok else ("alert" if s["configured"]
                                             else "minus")
            color = "var(--good)" if ok else ("var(--warn)"
                                              if s["configured"]
                                              else "var(--muted)")
            detail = (s["health"] or {}).get("detail", "") if s["health"] \
                else ""
            st.markdown(
                f'<div class="aw-card" style="display:flex;gap:.7rem;'
                f'align-items:flex-start;padding:.9rem 1.2rem">'
                f'<span style="color:{color};flex:none;margin-top:.15rem">'
                f'{ui.icon(icon_name, 20)}</span>'
                f'<div><b>{html.escape(s["name"])}</b> — '
                f'<span style="color:var(--muted)">'
                f'{html.escape(detail or ("configured" if s["configured"] else "not configured"))}</span>'
                f'</div></div>', unsafe_allow_html=True)
    else:
        st.caption("No live providers configured. Add `OPENAQ_API_KEY` to "
                   "`.streamlit/secrets.toml` to enable live fetches; "
                   "everything else works without it.")
    st.caption("Live fetches appear on Home under 'Fetch live monitoring "
               "data' and always carry the provider's own timestamp and "
               "station name. Stale readings are labelled, never passed "
               "off as current.")

    # ---------- AI engine status ----------
    ai_provider = ai.get_provider()
    if ai_provider is not None:
        model_label = getattr(ai_provider, "model", lambda: "")()
        ai_detail = (f"{ai_provider.name}"
                     + (f" · model {model_label}" if model_label else ""))
    else:
        ai_detail = ("not configured - rule engine only "
                     "(add GEMINI_API_KEY to enable optional AI text)")
    st.markdown(
        '<div class="aw-card" style="display:flex;gap:.7rem;align-items:'
        'flex-start;padding:.9rem 1.2rem">'
        '<span style="color:var(--evergreen);flex:none;margin-top:.15rem">'
        + ui.icon("sparkles", 20) + '</span>'
        '<div><b>Generative AI engine</b> — '
        '<span style="color:var(--muted)">' + html.escape(ai_detail) +
        '</span><br><span class="aw-meta">AI output is always labelled '
        'and every feature works without it; the rule engine is the '
        'foundation, never replaced by model output.</span></div></div>',
        unsafe_allow_html=True)

    # ---------- provenance ----------
    st.markdown('<div class="aw-section-title" style="font-size:1.3rem">'
                'Where your data comes from</div>', unsafe_allow_html=True)
    prov = [
        ("Your entries", "user", ("What you type is treated as "
         "user-provided and unverified.")),
        ("CSV imports", "upload", ("Parsed and validated locally; "
         "nothing is uploaded anywhere.")),
        ("Sample data", "eye", ("Illustrative demo values, always "
         "labelled as samples.")),
        ("Live providers", "activity", ("Fetched on demand (e.g. OpenAQ), "
         "timestamped and station-attributed.")),
    ]
    pcols = st.columns(2)
    for i, (name, ic, txt) in enumerate(prov):
        with pcols[i % 2]:
            st.markdown(
                f'<div class="aw-card" style="display:flex;gap:.7rem;'
                f'align-items:flex-start;padding:.9rem 1.1rem">'
                f'<div class="aw-feat-ico" style="width:38px;height:38px;'
                f'border-radius:11px">{ui.icon(ic, 19)}</div>'
                f'<div><b style="color:var(--forest)">{html.escape(name)}'
                f'</b><p style="margin:.15rem 0 0">{html.escape(txt)}</p>'
                f'</div></div>', unsafe_allow_html=True)
    st.caption("Every measurement records value, unit, source and "
               "timestamp.")

    # ---------- remaining methodology (expandable) ----------
    st.markdown('<div class="aw-section-title" style="font-size:1.3rem">'
                'Deeper details</div>', unsafe_allow_html=True)
    with st.expander("Recommendation methodology"):
        st.markdown(
            "Recommendations come from a deterministic Python rule "
            "engine mapping AQI category + dominant pollutant + your "
            "profile to actionable guidance. Every item shows what to "
            "do, why it matters, when, approximate cost and an "
            "alternative where meaningful.\n\n"
            "**Optional AI:** if `GEMINI_API_KEY` is configured in "
            "Streamlit secrets, an AI provider (Gemini) can rewrite the "
            "briefing in natural language. Output is always labelled "
            "*AI-generated*; without the key, the rule engine alone "
            "powers the app. No other AI service is used or claimed.")
    with st.expander("Day-ahead outlook methodology"):
        st.markdown(
            "The 24-hour planning outlook combines a **diurnal "
            "climatology** (typical urban patterns: morning/evening "
            "traffic peaks, a midday mixing-layer dip, overnight "
            "stability) with a **bounded session trend** when the user "
            "has taken several readings in one session (least-squares "
            "AQI slope, capped at one AQI category of shift). Ozone-"
            "dominant readings shift risk to the sunny afternoon.\n\n"
            "Output is AQI **categories per time window** with an "
            "uncertainty band - never hourly AQI values or pollutant "
            "concentrations. CPCB publishes no public hourly forecast "
            "and no verified live forecast feed is connected; the "
            "outlook is labelled a planning estimate everywhere it "
            "appears, with confidence graded by data freshness, "
            "completeness and provenance.")
    with st.expander("Impact calculation assumptions"):
        st.markdown(
            "Vehicle CO₂e factors are generic estimates (petrol car "
            "≈0.19 kg/km, electric car ≈0.10 kg/km on the Indian grid, "
            "metro ≈0.02 kg/passenger-km). Grid intensity ≈0.82 kg "
            "CO₂/kWh. Fuel prices and economy are defaults you can "
            "override. Figures are estimates of climate benefit, not "
            "measured reductions.")
    with st.expander("Build information"):
        st.markdown(
            f"- **Version:** {html.escape(build_info.APP_VERSION)}\n"
            f"- **Git commit:** `{html.escape(build_info.GIT_SHA)}`\n"
            f"- **Build ID:** `{html.escape(build_info.BUILD_ID)}` "
            f"({html.escape(build_info.BUILT_AT)})\n"
            f"- **Source fingerprint:** `{html.escape(build_info.SOURCE_HASH)}`")
        st.caption("The source fingerprint is a hash of the shipped "
                   "files; compare it against the repository to confirm "
                   "which commit this deployment is serving.")
    with st.expander("Technology"):
        st.markdown("Python 3.14 · Streamlit · pandas · plotly · "
                    "optional Gemini API (stdlib urllib only). No "
                    "database, no required API keys, no paid services. "
                    "State lives in your browser session; reports are "
                    "downloadable files.")
    with st.expander("Limitations & future work"):
        st.markdown(
            "- Live fetch requires a provider API key; without one the "
            "app relies on manual entry, CSV import or labelled "
            "samples.\n"
            "- Recommendations are rule-based, not ML-personalised.\n"
            "- Indoor guidance is qualitative; a real PM2.5 sensor "
            "would enable quantitative tracking.\n"
            "- The day-ahead outlook is a labelled planning estimate "
            "(diurnal model + session trend), not an official hourly "
            "forecast; a verified live forecast feed could replace it.\n"
            "- Future: CPCB/OpenAQ live fetch, official forecast feed, "
            "multi-day exposure logging, household sharing.")
