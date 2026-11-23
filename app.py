"""AirAware AI - Streamlit entry point.

Run locally:  streamlit run app.py
Deploy:       Streamlit Community Cloud (see README.md)
"""

from __future__ import annotations

import html

import streamlit as st

from airaware import pages, ui

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

BRAND = """
<div style="padding:.4rem .2rem 1rem">
  <div style="font-family:Georgia,serif;font-size:1.5rem;font-weight:700;
       color:#0b3d2e;line-height:1">AirAware</div>
  <div style="font-size:.78rem;color:#66756a;margin-top:.2rem">
    Breathe smarter. Live better.</div>
</div>
"""


def _sidebar():
    st.sidebar.markdown(BRAND, unsafe_allow_html=True)

    current = st.session_state.get("nav_page", "Home")
    for label in NAV:
        if st.sidebar.button(
                label, key=f"navbtn_{label}",
                type="primary" if label == current else "secondary",
                width="stretch"):
            st.session_state["nav_page"] = label
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Your current reading**")
    m = st.session_state.get("measurement")
    if m and m.display_aqi is not None:
        st.sidebar.markdown(
            f"**AQI {m.display_aqi:.0f}** · "
            f"{html.escape(m.category_name or '')}<br>"
            f"{html.escape(m.location or '')}<br>"
            f"<span style='font-size:.75rem;color:#66756a'>"
            f"{m.timestamp.strftime('%Y-%m-%d %H:%M UTC')} · "
            f"{html.escape(m.source_label)}</span>",
            unsafe_allow_html=True)
        if m.is_sample:
            st.sidebar.caption("Sample data — not a live reading.")
    else:
        st.sidebar.caption("No reading yet — start a check on the Home page.")
        if st.sidebar.button("Start air-quality check", key="sb_start",
                             width="stretch"):
            st.session_state["nav_page"] = "Home"
            st.session_state["home_entry"] = "manual"
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("AirAware AI · PromptWars Challenge 06 · "
                       "CPCB AQI methodology · offline-first")


def main():
    st.set_page_config(page_title="AirAware AI", page_icon="🌿",
                       layout="wide", initial_sidebar_state="expanded")
    ui.apply_css()
    _sidebar()
    nav = st.session_state.get("nav_page", "Home")
    PAGE_FN[nav]()


if __name__ == "__main__":
    main()
