"""AirAware AI - Streamlit entry point.

Run locally:  streamlit run app.py
Deploy:       Streamlit Community Cloud (see README.md)
"""

from __future__ import annotations

import html

import streamlit as st

from airaware import pages, ui
from airaware.aqi import category_color

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

# Navigation groups keep the sidebar scannable as the app grows.
NAV_GROUPS = [
    ("Begin", "leaf", ["Home", "Air Quality Explorer"]),
    ("Your wellbeing", "heart", ["Personal AI Assistant", "My Daily Air Plan"]),
    ("Your surroundings", "home", ["Indoor Air Guardian", "Green Lifestyle Planner"]),
    ("Impact & community", "users", ["Environmental Impact", "Family & Community"]),
    ("About", "info", ["About & Data Sources"]),
]


def _brand():
    st.sidebar.markdown(
        '<div style="display:flex;align-items:center;gap:.6rem;'
        'padding:.4rem .2rem 1rem">'
        '<div style="width:38px;height:38px;border-radius:11px;flex:none;'
        'background:#153D32;color:#A8BCA3;display:flex;align-items:center;'
        'justify-content:center">' + ui.icon("leaf", 22) + '</div>'
        '<div><div style="font-family:Georgia,serif;font-size:1.25rem;'
        'font-weight:700;color:#153D32;line-height:1">AirAware</div>'
        '<div style="font-size:.72rem;color:#748078;margin-top:.15rem">'
        'Breathe smarter. Live better.</div></div></div>',
        unsafe_allow_html=True)


def _sidebar():
    _brand()

    current = st.session_state.get("nav_page", "Home")
    for group, gicon, items in NAV_GROUPS:
        st.sidebar.markdown(
            f'<div class="aw-nav-group">{ui.icon(gicon, 13)}'
            f'<span>{html.escape(group.upper())}</span></div>',
            unsafe_allow_html=True)
        for label in items:
            if st.sidebar.button(
                    label, key=f"navbtn_{label}",
                    type="primary" if label == current else "secondary",
                    width="stretch"):
                st.session_state["nav_page"] = label
                st.rerun()
        st.sidebar.markdown('<div style="height:.55rem"></div>',
                            unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Your current reading**")
    m = st.session_state.get("measurement")
    if m and m.display_aqi is not None:
        st.sidebar.markdown(
            '<div class="aw-card" style="padding:.85rem 1rem;margin-bottom:.6rem">'
            '<div style="display:flex;align-items:baseline;gap:.4rem">'
            f'<span style="font-size:1.5rem;font-weight:800;'
            f'color:{category_color(m.category_name)};'
            f'font-family:Georgia,serif">{m.display_aqi:.0f}</span>'
            f'<span style="font-size:.78rem;font-weight:700">'
            f'{html.escape(m.category_name or "")}</span></div>'
            f'<div style="font-size:.75rem;color:#748078;margin-top:.15rem">'
            f'{html.escape(m.location or "")} · '
            f'{m.timestamp.strftime("%Y-%m-%d %H:%M UTC")} · '
            f'{html.escape(m.source_label)}</div></div>',
            unsafe_allow_html=True)
        if m.is_sample:
            st.sidebar.caption("Sample data — not a live reading.")
    else:
        st.sidebar.caption("No reading yet — start a check on Home.")
        if st.sidebar.button("Start air-quality check", key="sb_start",
                             width="stretch"):
            st.session_state["nav_page"] = "Home"
            st.session_state["home_entry"] = "manual"
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("AirAware AI · CPCB AQI methodology · offline-first")


def main():
    st.set_page_config(page_title="AirAware AI", page_icon="🌿",
                       layout="wide", initial_sidebar_state="auto")
    ui.apply_css()
    _sidebar()
    nav = st.session_state.get("nav_page", "Home")
    PAGE_FN[nav]()


if __name__ == "__main__":
    main()
