"""AirAware AI - Streamlit entry point.

Run locally:  streamlit run app.py
Deploy:       Streamlit Community Cloud (see README.md)
"""

from __future__ import annotations

import html

import streamlit as st

# Explicit submodule imports: `import pkg.sub as sub` binds through
# sys.modules and raises a clear ModuleNotFoundError if the file is
# missing, unlike `from pkg import sub` which can surface a bare
# KeyError during partial/stale deployments.
import airaware.pages as pages  # noqa: PLR0402
import airaware.tzutil as tzutil  # noqa: PLR0402
import airaware.ui as ui  # noqa: PLR0402
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

# Navigation groups keep the sidebar scannable and purposeful.
NAV_GROUPS = [
    ("Discover", "compass", ["Home", "Air Quality Explorer"]),
    ("Understand your air", "eye", ["Personal AI Assistant", "My Daily Air Plan"]),
    ("Improve your environment", "sprout",
     ["Indoor Air Guardian", "Green Lifestyle Planner"]),
    ("Track your impact", "chart",
     ["Environmental Impact", "Family & Community"]),
    ("About", "info", ["About & Data Sources"]),
]

# Emoji icons keep the nav icon family consistent and dependency-free.
NAV_ICONS = {
    "Home": "🌿",
    "Air Quality Explorer": "🌫️",
    "Personal AI Assistant": "✨",
    "My Daily Air Plan": "📅",
    "Indoor Air Guardian": "🏠",
    "Green Lifestyle Planner": "♻️",
    "Environmental Impact": "🌍",
    "Family & Community": "👨‍👩‍👧",
    "About & Data Sources": "📖",
}


def _brand():
    st.sidebar.markdown(
        '<div style="display:flex;align-items:center;gap:.65rem;'
        'padding:.3rem .2rem 1.1rem">'
        '<div style="width:40px;height:40px;border-radius:12px;flex:none;'
        'background:#173E32;color:#A8BCA3;display:flex;align-items:center;'
        'justify-content:center">' + ui.icon("leaf", 23) + '</div>'
        '<div><div style="font-family:Georgia,serif;font-size:1.3rem;'
        'font-weight:700;color:#173E32;line-height:1">AirAware</div>'
        '<div style="font-size:.72rem;color:#5a6d5e;margin-top:.18rem">'
        'Breathe smarter. Live better.</div></div></div>',
        unsafe_allow_html=True)


def _aqi_summary():
    """Compact reading card pinned near the top of the nav flow."""
    m = st.session_state.get("measurement")
    if m and m.display_aqi is not None:
        cat_color = category_color(m.category_name)
        st.sidebar.markdown(
            '<div style="background:#fff;border:1px solid var(--line);'
            'border-radius:14px;padding:.85rem 1rem;margin-bottom:.4rem;'
            'box-shadow:var(--shadow)">'
            '<div style="display:flex;align-items:center;justify-content:'
            'space-between">'
            f'<span style="font-family:Georgia,serif;font-size:1.6rem;'
            f'font-weight:700;color:{cat_color}">{m.display_aqi:.0f}</span>'
            f'<span class="aw-badge" style="background:{cat_color}">'
            f'{html.escape(m.category_name or "")}</span></div>'
            f'<div class="aw-meta" style="margin-top:.3rem">'
            f'{html.escape(m.location or "")} · '
            f'{m.timestamp.strftime("%d %b %H:%M UTC")}</div></div>',
            unsafe_allow_html=True)
        if m.is_sample:
            st.sidebar.caption("Sample data — not a live reading.")
        elif m.source == "user":
            st.sidebar.caption("Your own entry.")
        else:
            st.sidebar.caption(m.source_label)
    else:
        st.sidebar.markdown(
            '<div style="background:var(--mint);border:1px dashed '
            'var(--sage-soft);border-radius:14px;padding:.8rem 1rem;'
            'margin-bottom:.4rem;font-size:.82rem;color:var(--muted)">'
            'No reading yet — takes under a minute to check.</div>',
            unsafe_allow_html=True)
        if st.sidebar.button("Start air-quality check", key="sb_start",
                             width="stretch"):
            st.session_state["nav_page"] = "Home"
            st.session_state["home_entry"] = "manual"
            st.rerun()


def _sidebar():
    _brand()
    _aqi_summary()

    current = st.session_state.get("nav_page", "Home")
    for group, gicon, items in NAV_GROUPS:
        st.sidebar.markdown(
            f'<div class="aw-nav-group">{ui.icon(gicon, 13)}'
            f'<span>{html.escape(group.upper())}</span></div>',
            unsafe_allow_html=True)
        for label in items:
            # Buttons keep the existing navbtn_* keys and behaviour; the
            # active item is styled via the primary button kind.
            if st.sidebar.button(
                    label, key=f"navbtn_{label}",
                    type="primary" if label == current else "secondary",
                    width="stretch", icon=NAV_ICONS.get(label)):
                st.session_state["nav_page"] = label
                st.rerun()
        st.sidebar.markdown('<div style="height:.5rem"></div>',
                            unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.selectbox(
        "Your timezone", tzutil.TZ_OPTIONS,
        index=tzutil.TZ_OPTIONS.index(tzutil.user_timezone_name())
        if tzutil.user_timezone_name() in tzutil.TZ_OPTIONS else 0,
        key="user_tz",
        help="Used for the daily plan's 'now' marker and the 24-hour "
             "planning outlook windows.")
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
