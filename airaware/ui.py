"""Shared UI helpers: design system, CSS, cards, badges, navigation."""

from __future__ import annotations

import streamlit as st

from .aqi import category_color

_CSS = """
<style>
:root {
  --forest:#0b3d2e; --forest2:#0f5132; --emerald:#147a55; --emerald2:#1b9a6b;
  --sage:#dce8d8; --sage2:#a8c3a0; --ivory:#faf7ef; --ivory2:#f3eee1;
  --ink:#1d2b22; --muted:#66756a; --line:#e4dfd0; --card:#ffffff;
  --warn:#b45309; --bad:#b91c1c; --good:#15803d;
}
.stApp { background:var(--ivory); }
h1,h2,h3,h4 { color:var(--forest); letter-spacing:-0.01em; }
p, li { color:var(--ink); }
.aw-hero {
  position:relative; overflow:hidden; border-radius:20px;
  background:
    radial-gradient(1200px 400px at 85% -10%, rgba(52,168,112,.35), transparent 60%),
    linear-gradient(120deg,#0b3d2e 0%,#0f5132 55%,#17795a 100%);
  color:#fff; padding:2.4rem 2.2rem 2.2rem; margin-bottom:1.4rem;
  box-shadow:0 10px 30px rgba(11,61,46,.18);
}
.aw-hero h1 { color:#fff; font-family:Georgia,'Times New Roman',serif;
              font-size:2.5rem; line-height:1.12; margin:0 0 .5rem; }
.aw-hero .aw-sub { color:#cfe8d9; font-size:1.05rem; max-width:56ch; margin:0 0 .4rem; }
.aw-hero .aw-tag { display:inline-block; background:rgba(255,255,255,.12);
  border:1px solid rgba(255,255,255,.25); color:#eaf6ee;
  padding:.28rem .8rem; border-radius:999px; font-size:.8rem; margin-top:.9rem; }
.aw-hero-grid { display:grid; grid-template-columns:1.2fr .8fr; gap:1.5rem; align-items:center; }
@media (max-width:860px){ .aw-hero-grid{grid-template-columns:1fr} .aw-hero h1{font-size:1.9rem} }
.aw-card { background:var(--card); border:1px solid var(--line);
  border-radius:14px; padding:1.15rem 1.3rem; margin-bottom:.9rem;
  box-shadow:0 1px 3px rgba(27,61,46,.05); }
.aw-card h4 { margin:0 0 .45rem; color:var(--forest2); font-size:1.02rem; }
.aw-card p { margin:.2rem 0; color:var(--muted); font-size:.92rem; }
.aw-card--feature { border-top:3px solid var(--emerald); }
.aw-card--cta { border:1px dashed var(--sage2); background:#fbfdf8;
  transition:box-shadow .15s ease; }
.aw-card--cta:hover { box-shadow:0 4px 14px rgba(20,122,85,.15); }
.aw-badge { display:inline-block; padding:.18rem .65rem; border-radius:999px;
  font-size:.78rem; font-weight:600; color:#fff; letter-spacing:.02em; }
.aw-meta { font-size:.78rem; color:var(--muted); }
.aw-hero .aw-meta, .aw-hero .aw-reason { color:#cfe8d9; }
.aw-reason { font-size:.8rem; color:var(--muted); font-style:italic; }
.aw-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
  gap:.9rem; }
.aw-kpi { background:#fff; border:1px solid var(--line); border-radius:12px;
  padding:.95rem 1rem; text-align:center; }
.aw-kpi .v { font-size:1.45rem; font-weight:700; color:var(--forest2); }
.aw-kpi .l { font-size:.72rem; color:var(--muted); text-transform:uppercase;
  letter-spacing:.06em; }
.aw-step { display:flex; gap:.8rem; align-items:flex-start; margin-bottom:.7rem; }
.aw-step .n { flex:0 0 30px; height:30px; border-radius:50%;
  background:var(--sage); color:var(--forest); font-weight:700;
  display:flex; align-items:center; justify-content:center; font-size:.85rem; }
.aw-pill { display:inline-block; background:var(--sage); color:var(--forest);
  padding:.22rem .7rem; border-radius:999px; font-size:.8rem; font-weight:600; }
.aw-warn-box { border-left:4px solid var(--warn); }
.aw-bad-box { border-left:4px solid var(--bad); }
.aw-good-box { border-left:4px solid var(--good); }
.aw-info-box { border-left:4px solid #2563eb; }
.aw-divider { border:none; border-top:1px solid var(--line); margin:1.4rem 0; }
.aw-section-title { color:var(--forest); font-family:Georgia,serif;
  font-size:1.5rem; margin:1.6rem 0 .4rem; }
.aw-leaf { color:var(--emerald); }
.aw-field-label { font-size:.85rem; font-weight:600; color:var(--forest);
  margin-bottom:.15rem; }
.aw-hint { font-size:.78rem; color:var(--muted); }
.block-container { padding-top:1.4rem; padding-bottom:2rem; }
[data-testid="stSidebar"] { background:#f4f1e6; border-right:1px solid var(--line); }
@media (max-width:640px){
  .aw-hero{padding:1.5rem 1.2rem} .aw-card{padding:1rem}
}
</style>
"""


def apply_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str = "", extra: str = "", art: bool = False):
    """Premium hero block. art=True adds a decorative SVG landscape."""
    illustration = ""
    if art:
        illustration = _HERO_ART
    st.markdown(
        f'<div class="aw-hero"><div class="aw-hero-grid">'
        f'<div><h1>{title}</h1><p class="aw-sub">{subtitle}</p>{extra}</div>'
        f'{illustration}</div></div>',
        unsafe_allow_html=True)


_HERO_ART = """
<svg viewBox="0 0 320 190" width="100%" aria-hidden="true"
     style="max-width:320px;justify-self:end">
  <circle cx="250" cy="45" r="26" fill="#f4d58d" opacity=".9"/>
  <path d="M0 120 Q80 70 160 105 T320 95 V190 H0 Z" fill="#1d6b4a" opacity=".85"/>
  <path d="M0 145 Q90 105 180 135 T320 125 V190 H0 Z" fill="#0f5132"/>
  <path d="M40 150 q10 -30 30 -38 q-4 26 -18 40 q-8 6 -12 -2z" fill="#a8c3a0"/>
  <path d="M250 140 q14 -26 34 -30 q-6 24 -22 36 q-8 5 -12 -6z" fill="#dce8d8"/>
  <circle cx="120" cy="60" r="3" fill="#fff" opacity=".7"/>
  <circle cx="160" cy="40" r="2.4" fill="#fff" opacity=".6"/>
  <circle cx="90" cy="85" r="2" fill="#fff" opacity=".5"/>
</svg>
"""


def section_title(title: str):
    st.markdown(f'<div class="aw-section-title">{title}</div>',
                unsafe_allow_html=True)


def card(title: str, body_html: str = "", body_text: str = "",
         variant: str = ""):
    cls = "aw-card"
    if variant:
        cls += f" aw-card--{variant}"
    html = f'<div class="{cls}"><h4>{title}</h4>'
    if body_html:
        html += body_html
    if body_text:
        html += f"<p>{body_text}</p>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def badge(text: str, aqi_category: str | None = None, color: str | None = None):
    c = color or (category_color(aqi_category) if aqi_category else "#475569")
    st.markdown(f'<span class="aw-badge" style="background:{c}">{text}</span>',
                unsafe_allow_html=True)


def meta(text: str):
    st.markdown(f'<div class="aw-meta">{text}</div>', unsafe_allow_html=True)


def kpi_row(items: list[tuple[str, str]]):
    """items: list of (big_value, small_label)."""
    cells = "".join(
        f'<div class="aw-kpi"><div class="v">{v}</div><div class="l">{l}</div></div>'
        for v, l in items)
    st.markdown(f'<div class="aw-grid">{cells}</div>', unsafe_allow_html=True)


def hr():
    st.markdown('<hr class="aw-divider">', unsafe_allow_html=True)


def empty_state(message: str):
    st.info(message)


def alert_box(severity: str, title: str, detail: str):
    """severity: info|caution|warning|critical"""
    colors = {"info": "#2563eb", "caution": "#b45309",
              "warning": "#ea580c", "critical": "#b91c1c"}
    labels = {"info": "Info", "caution": "Caution",
              "warning": "Warning", "critical": "Critical"}
    c = colors.get(severity, "#475569")
    st.markdown(
        f'<div class="aw-card" style="border-left:4px solid {c}">'
        f'<h4>{labels.get(severity, severity)}: {title}</h4>'
        f'<p>{detail}</p></div>', unsafe_allow_html=True)


def goto(page: str):
    """Navigate to another module by setting the sidebar nav state."""
    st.session_state["nav_page"] = page
    st.rerun()


def field_label(text: str, hint: str = ""):
    h = f'<div class="aw-hint">{hint}</div>' if hint else ""
    st.markdown(f'<div class="aw-field-label">{text}</div>{h}',
                unsafe_allow_html=True)


def cta_button(label: str, page: str, key: str):
    """Primary-action button that navigates to a module."""
    if st.button(label, key=key, type="primary"):
        goto(page)
