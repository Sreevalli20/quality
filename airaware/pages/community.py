"""Family & Community page: household checklist, kid-friendly explainer,
community action ideas and today's family plan.
"""

from __future__ import annotations

import html

import streamlit as st

import airaware.ui as ui
from airaware.planner import build_daily_plan

from ._common import _meas


def community_page():
    ui.page_header(
        "Family & Community",
        "Small habits, bigger air",
        "Household habits add up - checklists, kid-friendly explanations "
        "and ideas for your neighbourhood.")

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
    pct = sum(done.get(i, False) for i in range(len(checklist_items))) \
        / len(checklist_items) * 100
    st.markdown(
        '<div class="aw-card" style="display:flex;justify-content:'
        'space-between;align-items:center;flex-wrap:wrap;gap:.6rem">'
        '<div><h4 style="margin:0">Household air-quality checklist</h4>'
        '<p class="aw-meta" style="margin:.2rem 0 0">Tick what your '
        'household already does - every item makes a difference.</p></div>'
        f'<div class="aw-chip" style="font-size:.9rem">{pct:.0f}% done</div>'
        '</div>', unsafe_allow_html=True)
    with st.container(border=True):
        for i, item in enumerate(checklist_items):
            done[i] = st.checkbox(item, value=done.get(i, False),
                                  key=f"chk_{i}")
    st.progress(pct / 100, text=f"{pct:.0f}% of the checklist complete")

    ui.section_title("For children - a simple explanation")
    st.markdown(
        '<div style="display:flex;gap:.9rem;align-items:flex-start">'
        '<div class="aw-avatar">' + ui.icon("child", 22, "#A8BCA3") + '</div>'
        '<div class="aw-bubble" style="flex:1;margin:0">'
        '<b>Hey! Want to know why we check the air?</b>'
        '<p style="margin:.4rem 0 0">Air pollution is like tiny invisible '
        'dust floating in the air. Some days there is more of it - we can '
        'see it as haze. When the air is bad, our lungs work harder, just '
        'like running up stairs. We can help by <b>walking or cycling</b> '
        'to nearby places (cleaner than cars), <b>closing windows</b> on '
        'smoky days, and <b>saving electricity</b> so power plants burn '
        'less fuel.</p></div></div>',
        unsafe_allow_html=True)

    ui.section_title("Community action ideas")
    ideas = [
        ("Car-free day", "route", "One day a week where the household uses "
         "only walking, cycling or transit."),
        ("Neighbourhood clean-up", "trash", "Collect roadside waste before "
         "it is burned."),
        ("Tree drive", "tree", "Coordinate with your RWAs or school for "
         "native saplings."),
        ("School awareness", "book", "Share the kids' explainer with "
         "teachers; many schools run 'clean commute' weeks."),
        ("Report violations", "alert", "Dusty construction without "
         "sprinkling or open garbage burning; log them on your municipal "
         "app."),
    ]
    for i in range(0, len(ideas), 3):
        cols = st.columns(3)
        for j, (name, ic, txt) in enumerate(ideas[i:i + 3]):
            with cols[j]:
                st.markdown(
                    f'<div class="aw-card" style="height:100%">'
                    f'<div class="aw-feat-ico">{ui.icon(ic, 20)}</div>'
                    f'<h4 style="font-size:.92rem">{html.escape(name)}</h4>'
                    f'<p>{html.escape(txt)}</p></div>', unsafe_allow_html=True)

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
