"""Green Lifestyle Planner page: scored, filterable sustainable-swap
options with honest benefits and limitations.
"""

from __future__ import annotations

import hashlib
import html

import streamlit as st

import airaware.ui as ui
from airaware.lifestyle import all_options, options_by_area, personalised_options


def lifestyle_page():
    ui.page_header(
        "Green Lifestyle Planner",
        "Greener everyday choices",
        "Practical low-emission swaps for transport, energy, waste and "
        "home - each with honest benefits and limitations.")

    # visual intro strip
    st.markdown(
        '<div class="aw-card" style="display:flex;gap:1rem;align-items:'
        'center;padding:1rem 1.4rem">'
        '<div style="width:64px;height:48px;flex:none;border-radius:12px;'
        'overflow:hidden">' + ui.scene("transport") + '</div>'
        '<div><b>Small swaps, measurable difference.</b> '
        '<span class="aw-meta">Every option shows what it saves, what it '
        'costs you, and where it works best.</span></div></div>',
        unsafe_allow_html=True)

    profile = st.session_state.get("profile")
    if profile is None:
        st.markdown(
            '<div class="aw-card" style="border-left:4px solid var(--sage)">'
            '<p style="margin:0">Complete the <b>Personal AI Assistant</b> '
            'form to rank these options for your situation - or browse '
            'everything below.</p></div>', unsafe_allow_html=True)
        scored = [(0, o) for o in all_options()]
    else:
        scored = personalised_options(profile)

    area_filter = st.selectbox("Focus area", ["All"] + list(options_by_area().keys()),
                               key="life_area")

    # shortlist state: keys are created lazily by the checkboxes below
    picked = [k for k in st.session_state
              if k.startswith("life_pick_") and st.session_state[k]]
    if picked:
        st.markdown(
            '<div class="aw-card aw-card--mint" style="display:flex;'
            'gap:.6rem;align-items:center;padding:.7rem 1.1rem">'
            + ui.icon("check", 18) +
            f'<span><b>{len(picked)} swap{"s" if len(picked) != 1 else ""}'
            ' on your list.</b> <span class="aw-meta">Tick "I\'ll try '
            'this" on any option to shortlist it - your picks stay for '
            'this session.</span></span></div>',
            unsafe_allow_html=True)

    area_icons = {"Transport": "car", "Energy": "bolt", "Waste": "recycle",
                  "Household": "home"}
    current_area = None
    for score, opt in scored:
        if area_filter != "All" and opt.area != area_filter:
            continue
        if opt.area != current_area:
            st.markdown(
                f'<div class="aw-section-title" style="font-size:1.2rem;'
                f'display:flex;align-items:center;gap:.5rem">'
                f'{ui.icon(area_icons.get(opt.area, "leaf"), 20)}'
                f'{html.escape(opt.area)}</div>', unsafe_allow_html=True)
            current_area = opt.area
        badge = f' <span class="aw-pill">match {score}</span>' \
            if profile and score > 0 else ""
        body = (f"<p>{html.escape(opt.detail)}</p>"
                f'<div class="aw-bl-grid">'
                f'<div style="background:var(--mint);border-radius:10px;'
                f'padding:.5rem .7rem"><div style="font-size:.68rem;'
                f'font-weight:800;letter-spacing:.08em;color:var(--evergreen);'
                f'text-transform:uppercase">Benefit</div>'
                f'<div style="font-size:.85rem">{html.escape(opt.benefit)}'
                f'</div></div>'
                f'<div style="background:#fdf6ec;border:1px solid #ecd9ae;'
                f'border-radius:10px;padding:.5rem .7rem">'
                f'<div style="font-size:.68rem;font-weight:800;'
                f'letter-spacing:.08em;color:#8a5a00;text-transform:uppercase">'
                f'Watch out</div>'
                f'<div style="font-size:.85rem">{html.escape(opt.limitation)}'
                f'</div></div></div>')
        if opt.conditions:
            body += ("<p class='aw-meta' style='margin-top:.5rem'><b>Applies "
                     "when:</b> " + html.escape("; ".join(opt.conditions))
                     + "</p>")
        ui.card(f"{opt.title}{badge}", body_html=body)
        pick_key = "life_pick_" + hashlib.md5(
            (opt.area + "|" + opt.title).encode("utf-8")).hexdigest()[:12]
        st.checkbox("I'll try this", key=pick_key)

    st.markdown(
        '<div class="aw-cta-band"><h2>Turn swaps into measured impact.</h2>'
        '<p>Your shortlisted choices and trip estimates feed the '
        'Environmental Impact tracker - see the CO₂e and rupee savings '
        'add up.</p></div>', unsafe_allow_html=True)
    if st.button("Track my impact", key="life_to_impact",
                 type="primary"):
        st.session_state["nav_page"] = "Environmental Impact"
        st.rerun()
