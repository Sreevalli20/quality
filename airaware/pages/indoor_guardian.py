"""Indoor Air Guardian page: ventilation advice, room picker, budget
tiers and indoor pollution sources.
"""

from __future__ import annotations

import html

import streamlit as st

import airaware.ui as ui
from airaware.indoor import BUDGET_TIERS, ROOMS, ventilation_advice

from ._common import _meas, _measurement_caption


def indoor_page():
    ui.page_header(
        "Indoor Air Guardian",
        "A healthier home, one room at a time",
        "Your home is where you spend most of your time - make the air "
        "inside it healthier.")
    st.markdown(
        '<div class="aw-show" style="margin-top:.4rem">'
        '<div class="art">' + ui.scene("indoor") + '</div>'
        '<div><div class="aw-eyebrow">Indoor first</div>'
        '<h3>You control this air</h3>'
        '<ul class="aw-show-points">'
        '<li>' + ui.icon("check", 16) + '<span>Outdoor pollution seeps '
        'in through windows, doors and walls - timing matters more than '
        ' gadgets.</span></li>'
        '<li>' + ui.icon("check", 16) + '<span>Cooking, cleaning and '
        'smoke are the biggest indoor sources you can remove today.</span></li>'
        '<li>' + ui.icon("check", 16) + '<span>Filtration helps most in '
        'the room you sleep in - roughly a third of your life.</span></li>'
        '</ul></div></div>', unsafe_allow_html=True)
    m = _meas()
    cat = m.category_name if m else None

    head, detail = ventilation_advice(cat)
    vent_icon = "check" if "helpful" in head.lower() or "selectively" in head.lower() else "shield"
    ui.card(head,
            body_html=(f'<p style="display:flex;gap:.5rem;align-items:flex-start">'
                       f'<span style="color:var(--evergreen);flex:none">'
                       f'{ui.icon(vent_icon, 18)}</span>'
                       f'<span>{detail}</span></p>'))
    if m:
        st.caption(_measurement_caption(m))

    # ---------- illustrated room picker ----------
    st.markdown('<div class="aw-section-title" style="font-size:1.25rem;'
                'margin-top:1.2rem">Pick a room</div>',
                unsafe_allow_html=True)
    sel = st.session_state.get("indoor_room", ROOMS[0].name)
    room_cols = st.columns(len(ROOMS))
    for i, r in enumerate(ROOMS):
        active = r.name == sel
        border = 'border:2px solid var(--evergreen);' if active else ''
        bg = 'background:var(--mint);' if active else ''
        with room_cols[i]:
            st.markdown(
                f'<div class="aw-card" style="text-align:center;'
                f'padding:1rem .7rem;{border}{bg}">'
                f'<div class="aw-feat-ico" style="margin:0 auto .6rem">'
                f'{ui.icon(r.icon if ui.has_icon(r.icon) else "home", 24)}'
                f'</div>'
                f'<div style="font-weight:700;color:var(--forest);'
                f'font-size:.92rem">{html.escape(r.name)}</div></div>',
                unsafe_allow_html=True)
            if st.button(("✓ " if active else "") + "Tips",
                         key=f"room_{r.name}", width="stretch"):
                st.session_state["indoor_room"] = r.name
                st.rerun()
    room = next(r for r in ROOMS if r.name == sel)
    st.markdown(
        f'<div class="aw-card" style="border-left:5px solid var(--evergreen)">'
        f'<div style="display:flex;align-items:center;gap:.7rem;'
        f'margin-bottom:.5rem"><div class="aw-feat-ico">'
        f'{ui.icon(room.icon if ui.has_icon(room.icon) else "home", 22)}'
        f'</div><h4 style="margin:0">{html.escape(room.name)}</h4></div>'
        + "".join(
            f'<p style="display:flex;gap:.55rem;align-items:flex-start;'
            f'margin:.4rem 0">'
            f'<span style="color:var(--evergreen);flex:none;margin-top:.15rem">'
            f'{ui.icon("check", 15)}</span>'
            f'<span>{html.escape(x)}</span></p>' for x in room.priorities)
        + f'<p class="aw-meta" style="margin-top:.6rem;border-top:1px solid '
        f'var(--line);padding-top:.6rem">{html.escape(room.notes)}</p></div>',
        unsafe_allow_html=True)

    ui.section_title("Improvements by budget")
    st.caption("Indicative Indian-rupee ranges - prices vary by brand and "
               "city; planning estimates, not quotes.")
    # Short tab labels keep the tab bar inside narrow viewports; the full
    # tier name and range are shown inside each tab.
    tier_short = {"free": "Free", "low": "Low-cost", "moderate": "Moderate",
                  "high": "Higher-cost"}
    tabs = st.tabs([tier_short.get(k, k) for k in BUDGET_TIERS])
    for tab, key in zip(tabs, BUDGET_TIERS.keys()):
        with tab:
            t = BUDGET_TIERS[key]
            st.markdown(f'<div class="aw-eyebrow" style="margin-bottom:.6rem">'
                        f'{html.escape(t["label"])} · '
                        f'{html.escape(t["range"])}</div>',
                        unsafe_allow_html=True)
            for item in t["items"]:
                st.markdown(
                    f'<div class="aw-card" style="padding:.7rem 1rem;'
                    f'margin-bottom:.5rem"><p style="margin:0">'
                    f'{html.escape(item)}</p></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="aw-card" style="border-left:4px solid var(--gold)">'
        '<h4 style="display:flex;align-items:center;gap:.5rem">'
        + ui.icon("alert", 20, "#b45309") + ' Sources worth controlling'
        '</h4></div>', unsafe_allow_html=True)
    sources = [
        ("Cooking", "flask", "Frying and biomass fuels are the biggest "
         "indoor PM2.5 sources."),
        ("Smoke & incense", "alert", "No safe level indoors - eliminate."),
        ("Dust", "droplets", "Resuspends with activity; damp-clean and "
         "use doormats."),
        ("Cleaning products", "sprout", "Many emit VOCs; choose "
         "fragrance-free."),
        ("Outdoor infiltration", "wind", "Depends on today's AQI; seal "
         "windows on bad days."),
        ("Mould & damp", "droplets", "Worsens without ventilation; fix "
         "leaks promptly."),
    ]
    for i in range(0, len(sources), 3):
        cols = st.columns(3)
        for j, (name, ic, txt) in enumerate(sources[i:i + 3]):
            with cols[j]:
                st.markdown(
                    f'<div class="aw-card" style="height:100%;'
                    f'padding:1rem 1.1rem">'
                    f'<div class="aw-feat-ico">{ui.icon(ic, 20)}</div>'
                    f'<h4 style="font-size:.92rem">{html.escape(name)}</h4>'
                    f'<p>{html.escape(txt)}</p></div>', unsafe_allow_html=True)
    st.caption("Honest note: houseplants improve wellbeing but are **not** "
               "air purifiers - their effect on PM2.5 is negligible.")
