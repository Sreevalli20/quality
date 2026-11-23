"""Shared UI helpers: design system, CSS, cards, badges, navigation.

AirAware design system - premium environmental-wellness palette:
  forest #153D32 · evergreen #245B46 · sage #A8BCA3 · ivory #F8F7F0
  mint #E8F0E6 · charcoal #26352E · muted #748078
AQI category colours are used only where meaningful (badges, gauges).
"""

from __future__ import annotations

import html

import streamlit as st

from .aqi import category_color

_CSS = """
<style>
:root {
  --forest:#153D32; --forest-2:#1d4f40; --evergreen:#245B46;
  --sage:#A8BCA3; --sage-soft:#cfdcc6; --ivory:#F8F7F0; --mint:#E8F0E6;
  --charcoal:#26352E; --muted:#748078; --line:#e2e7dd;
  --card:#ffffff; --warn:#b45309; --bad:#b91c1c; --good:#15803d;
  --shadow:0 1px 2px rgba(21,61,50,.05),0 6px 18px rgba(21,61,50,.06);
  --shadow-lg:0 12px 34px rgba(21,61,50,.14);
  --radius:16px;
}
.stApp { background:var(--ivory); }
h1,h2,h3,h4,h5 { color:var(--forest); letter-spacing:-0.015em;
  font-family:Georgia,'Iowan Old Style','Times New Roman',serif; }
p, li, .stMarkdown { color:var(--charcoal); }
a { color:var(--evergreen); }

/* ---------- typography ---------- */
.aw-eyebrow { display:inline-block; font-size:.72rem; font-weight:700;
  letter-spacing:.14em; text-transform:uppercase; color:var(--evergreen);
  background:var(--mint); border:1px solid var(--sage-soft);
  padding:.28rem .75rem; border-radius:999px; margin-bottom:.7rem; }
.aw-section-title { color:var(--forest); font-family:Georgia,serif;
  font-size:1.55rem; margin:2.2rem 0 .5rem; font-weight:600; }
.aw-section-sub { color:var(--muted); font-size:.95rem; max-width:70ch;
  margin:-.2rem 0 .9rem; }

/* ---------- hero ---------- */
.aw-hero { position:relative; overflow:hidden; border-radius:22px;
  background:var(--forest); color:#f4f7f2;
  padding:0; margin-bottom:1.6rem; box-shadow:var(--shadow-lg); }
.aw-hero-grid { display:grid; grid-template-columns:1.15fr .85fr;
  gap:2rem; align-items:center; }
.aw-hero-left { padding:2.6rem 0 2.4rem 2.4rem; }
.aw-hero-right { position:relative; padding:1.2rem 1.4rem 1.2rem 0; }
.aw-hero h1 { color:#fff; font-size:2.6rem; line-height:1.12;
  margin:.4rem 0 .7rem; font-weight:600; }
.aw-hero .aw-sub { color:#cfe0d4; font-size:1.06rem; max-width:52ch;
  margin:0 0 1.2rem; line-height:1.55; }
.aw-hero .aw-tag { display:inline-block; background:rgba(255,255,255,.10);
  border:1px solid rgba(255,255,255,.22); color:#eaf4ec;
  padding:.3rem .8rem; border-radius:999px; font-size:.78rem;
  margin-top:.9rem; }
.aw-hero .aw-cta-row { display:flex; gap:.7rem; flex-wrap:wrap;
  margin-top:1.1rem; }
.aw-hero-cta { display:inline-block; background:#fff; color:var(--forest);
  font-weight:700; font-size:.95rem; padding:.7rem 1.4rem;
  border-radius:999px; text-decoration:none;
  box-shadow:0 4px 14px rgba(0,0,0,.18); }
.aw-hero-cta:hover { background:var(--mint); }
.aw-hero-cta--ghost { background:transparent; color:#fff;
  border:1.5px solid rgba(255,255,255,.45); box-shadow:none; }
.aw-hero-cta--ghost:hover { background:rgba(255,255,255,.1); }
.aw-trust { display:flex; gap:1.1rem; flex-wrap:wrap; margin-top:1.3rem; }
.aw-trust span { font-size:.8rem; color:#b9d2c2; display:flex;
  align-items:center; gap:.4rem; }
.aw-trust svg { opacity:.85; }
@media (max-width:900px){
  .aw-hero-grid{grid-template-columns:1fr}
  .aw-hero-left{padding:1.8rem 1.4rem}
  .aw-hero-right{padding:0 1.4rem 1.4rem}
  .aw-hero h1{font-size:1.95rem}
}

/* ---------- cards ---------- */
.aw-card { background:var(--card); border:1px solid var(--line);
  border-radius:var(--radius); padding:1.2rem 1.35rem; margin-bottom:.9rem;
  box-shadow:var(--shadow); }
.aw-card h4 { margin:0 0 .4rem; color:var(--forest-2); font-size:1.02rem;
  font-weight:700; }
.aw-card p { margin:.25rem 0; color:var(--muted); font-size:.92rem; }
.aw-card--feature { border-top:3px solid var(--sage); }
.aw-card--cta { border:1px dashed var(--sage-soft); background:#fbfdf8;
  transition:box-shadow .15s ease, transform .15s ease; }
.aw-card--cta:hover { box-shadow:var(--shadow-lg); }
.aw-card--flat { box-shadow:none; }

/* feature tile: icon + title + copy + action */
.aw-feat { display:flex; flex-direction:column; height:100%;
  min-height:228px; }
.aw-feat-ico { width:44px; height:44px; border-radius:12px;
  background:var(--mint); color:var(--evergreen);
  display:flex; align-items:center; justify-content:center;
  margin-bottom:.7rem; }
.aw-feat p { flex:1; }
.aw-feat .aw-feat-link { font-size:.85rem; font-weight:600;
  color:var(--evergreen); margin-top:.5rem; }

/* ---------- badges / meta ---------- */
.aw-badge { display:inline-block; padding:.2rem .7rem; border-radius:999px;
  font-size:.76rem; font-weight:700; color:#fff; letter-spacing:.03em; }
.aw-badge--soft { background:var(--mint); color:var(--forest);
  border:1px solid var(--sage-soft); }
.aw-meta { font-size:.78rem; color:var(--muted); }
.aw-hero .aw-meta, .aw-hero .aw-reason { color:#cfe0d4; }
.aw-reason { font-size:.82rem; color:var(--muted); font-style:italic;
  background:var(--mint); border-radius:10px; padding:.45rem .7rem;
  margin-top:.5rem; }
.aw-pill { display:inline-block; background:var(--sage-soft); color:var(--forest);
  padding:.2rem .65rem; border-radius:999px; font-size:.76rem; font-weight:600; }
.aw-chip { display:inline-flex; align-items:center; gap:.35rem;
  background:var(--mint); color:var(--forest); border:1px solid var(--sage-soft);
  padding:.25rem .7rem; border-radius:999px; font-size:.78rem; font-weight:600; }

/* ---------- KPI / grid ---------- */
.aw-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:.9rem; }
.aw-kpi { background:#fff; border:1px solid var(--line); border-radius:14px;
  padding:.95rem 1rem; text-align:center; box-shadow:var(--shadow); }
.aw-kpi .v { font-size:1.5rem; font-weight:700; color:var(--forest);
  font-family:Georgia,serif; }
.aw-kpi .l { font-size:.7rem; color:var(--muted); text-transform:uppercase;
  letter-spacing:.07em; margin-top:.15rem; }

/* ---------- journey ---------- */
.aw-journey { display:grid; grid-template-columns:repeat(4,1fr); gap:0;
  margin:1.2rem 0 1.6rem; }
.aw-jstep { position:relative; text-align:center; padding:1.2rem .6rem;
  background:#fff; border:1px solid var(--line); }
.aw-jstep:first-child { border-radius:16px 0 0 16px; }
.aw-jstep:last-child { border-radius:0 16px 16px 0; }
.aw-jstep + .aw-jstep { border-left:none; }
.aw-jstep .aw-jico { width:52px; height:52px; margin:0 auto .6rem;
  border-radius:50%; background:var(--mint); color:var(--evergreen);
  display:flex; align-items:center; justify-content:center; }
.aw-jstep .t { font-weight:700; color:var(--forest); font-size:.92rem;
  font-family:Georgia,serif; }
.aw-jstep .d { font-size:.76rem; color:var(--muted); margin-top:.25rem; }
.aw-jarrow { position:absolute; right:-9px; top:44px; z-index:2;
  color:var(--sage); }
@media (max-width:860px){
  .aw-journey{grid-template-columns:1fr 1fr}
  .aw-jstep{border-radius:0!important;border-left:none!important;
    border-top:none!important}
  .aw-jarrow{display:none}
}

/* ---------- recommendation cards ---------- */
.aw-rec { border-radius:14px; padding:1rem 1.15rem; margin-bottom:.8rem;
  background:#fff; border:1px solid var(--line); border-left:5px solid var(--sage);
  box-shadow:var(--shadow); }
.aw-rec .aw-rec-head { display:flex; justify-content:space-between;
  align-items:baseline; gap:.6rem; flex-wrap:wrap; }
.aw-rec h4 { margin:0; font-size:1rem; }
.aw-rec .what { margin:.4rem 0 .2rem; font-size:.92rem; color:var(--charcoal); }
.aw-rec .fld { font-size:.85rem; color:var(--muted); margin:.15rem 0; }
.aw-rec .fld b { color:var(--forest-2); }

/* ---------- misc ---------- */
.aw-warn-box { border-left:4px solid var(--warn); }
.aw-bad-box { border-left:4px solid var(--bad); }
.aw-good-box { border-left:4px solid var(--good); }
.aw-info-box { border-left:4px solid #2563eb; }
.aw-divider { border:none; border-top:1px solid var(--line); margin:1.6rem 0; }
.aw-leaf { color:var(--evergreen); }
.aw-field-label { font-size:.85rem; font-weight:600; color:var(--forest);
  margin-bottom:.15rem; }
.aw-hint { font-size:.78rem; color:var(--muted); }
.aw-cta-band { border-radius:22px; background:var(--forest); color:#f4f7f2;
  padding:2.2rem 2rem; text-align:center; box-shadow:var(--shadow-lg);
  margin:2.2rem 0 .6rem; }
.aw-cta-band h2 { color:#fff; font-size:1.7rem; margin:0 0 .5rem; }
.aw-cta-band p { color:#cfe0d4; max-width:56ch; margin:0 auto 1.1rem; }
.block-container { padding-top:1.2rem; padding-bottom:2.4rem; }
[data-testid="stSidebar"] { background:#eef3ec; border-right:1px solid var(--line); }
[data-testid="stSidebar"] .block-container { padding-top:1.1rem; }
.aw-nav-group { display:flex; align-items:center; gap:.4rem;
  font-size:.66rem; font-weight:800; letter-spacing:.12em;
  color:#5d7263; margin:.9rem 0 .35rem .2rem; }
.aw-nav-group svg { color:#A8BCA3; }
[data-testid="stSidebar"] .stButton > button { border-radius:10px;
  font-weight:600; font-size:.88rem; min-height:38px; text-align:left;
  justify-content:flex-start; }
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
  background:transparent; border:1px solid transparent; color:var(--forest); }
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
  background:#e2ecdf; border-color:#d4e0cf; }
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background:var(--evergreen); border-color:var(--evergreen); color:#fff; }
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
  background:var(--forest); border-color:var(--forest); }
[data-testid="stSidebar"] hr { margin:.8rem 0; border-color:var(--line); }
.stButton > button { border-radius:999px; font-weight:600; }
.stButton > button[kind="primary"] { background:var(--evergreen);
  border-color:var(--evergreen); }
.stButton > button[kind="primary"]:hover { background:var(--forest);
  border-color:var(--forest); }
details summary { cursor:pointer; font-weight:600; color:var(--forest-2);
  padding:.3rem 0; }
details[open] summary { margin-bottom:.4rem; }
@media (max-width:640px){
  .aw-card{padding:1rem} .aw-kpi .v{font-size:1.2rem}
  .stButton > button{min-height:40px}
}
</style>
"""


def apply_css():
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Icons - simple consistent stroke SVGs (Lucide-style, 24x24 viewBox)
# ---------------------------------------------------------------------------

_ICONS = {
    "leaf": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',
    "wind": '<path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>',
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    "car": '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/>',
    "bolt": '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
    "sparkles": '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>',
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "flask": '<path d="M10 2v7.5L4.5 19a2 2 0 0 0 1.8 3h11.4a2 2 0 0 0 1.8-3L14 9.5V2"/><line x1="8" x2="16" y1="2" y2="2"/><line x1="7" x2="17" y1="15" y2="15"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.7 9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    "coffee": '<path d="M17 8h1a4 4 0 1 1 0 8h-1"/><path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"/><line x1="6" x2="6" y1="2" y2="4"/><line x1="10" x2="10" y1="2" y2="4"/><line x1="14" x2="14" y1="2" y2="4"/>',
    "compass": '<circle cx="12" cy="12" r="10"/><polygon points="16.2 7.8 14.4 14.4 7.8 16.2 9.6 9.6 16.2 7.8"/>',
    "droplets": '<path d="M7 16.3c2.2 0 4-1.83 4-4.05 0-1.16-.57-2.26-1.71-3.19S7.29 6.75 7 5.3c-.29 1.45-1.14 2.84-2.29 3.76S3 11.1 3 12.25c0 2.22 1.8 4.05 4 4.05z"/><path d="M12.56 6.6A10.97 10.97 0 0 0 14 3.02c.5 2.5 2 4.9 4 6.5s3 3.5 3 5.5a6.98 6.98 0 0 1-11.91 4.97"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "bed": '<path d="M2 20v-8a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v8"/><path d="M4 10V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v4"/><path d="M2 17h20"/><path d="M12 4v6"/>',
    "recycle": '<path d="M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5"/><path d="M11 19h8.203a1.83 1.83 0 0 0 1.556-.89 1.784 1.784 0 0 0 0-1.775l-1.226-2.12"/><path d="m14 16-3 3 3 3"/><path d="M8.293 13.596 7.196 9.5 3.1 10.598"/><path d="m9.344 5.811 1.093-1.892A1.83 1.83 0 0 1 12.029 3a1.785 1.785 0 0 1 1.556.89l3.045 5.273"/><path d="m13.378 9.633 4.096 1.098 1.097-4.096"/>',
    "book": '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>',
    "sprout": '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    "route": '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
    "sofa": '<path d="M20 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3"/><path d="M2 16a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5a2 2 0 0 0-4 0v2H6v-2a2 2 0 0 0-4 0Z"/><path d="M4 18v2"/><path d="M20 18v2"/>',
    "pot": '<path d="M3 10h18"/><path d="M7 10V7a5 5 0 0 1 10 0v3"/><path d="M9 14v7"/><path d="M15 14v7"/>',
    "child": '<circle cx="12" cy="5" r="2"/><path d="M12 8v5"/><path d="m8 11 4 4 4-4"/><path d="M9 21h6"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "eye": '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
}


def icon(name: str, size: int = 22, color: str = "currentColor") -> str:
    """Inline SVG icon markup (trusted, internal). Returns a <svg> string."""
    path = _ICONS.get(name, _ICONS["leaf"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" '
        f'height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{path}</svg>')


def icon_html(name: str, size: int = 22, color: str = "currentColor",
              wrap: str | None = None) -> str:
    """icon() optionally wrapped in a div (e.g. .aw-feat-ico)."""
    svg = icon(name, size, color)
    if wrap:
        return f'<div class="{wrap}">{svg}</div>'
    return svg


# ---------------------------------------------------------------------------
# Page-level pieces
# ---------------------------------------------------------------------------

def page_header(eyebrow: str, title: str, subtitle: str = ""):
    """Consistent page intro: eyebrow chip + serif title + lede."""
    sub = f'<p class="aw-section-sub">{html.escape(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f'<div style="margin-bottom:.4rem"><span class="aw-eyebrow">'
        f'{html.escape(eyebrow)}</span></div>'
        f'<h1 style="font-size:2rem;margin:.1rem 0 .4rem">'
        f'{html.escape(title)}</h1>{sub}',
        unsafe_allow_html=True)


def hero(title: str, subtitle: str = "", extra: str = "", art: bool = False):
    """Compact in-page hero band. ``title``/``subtitle`` are escaped;
    ``extra`` is trusted internal markup only."""
    illustration = ""
    if art:
        illustration = (
            '<div class="aw-hero-right">'
            '<svg viewBox="0 0 320 190" width="100%" aria-hidden="true" '
            'style="max-width:320px;margin-left:auto;display:block">'
            '<circle cx="250" cy="45" r="26" fill="#cfe8d9" opacity=".9"/>'
            '<path d="M0 120 Q80 70 160 105 T320 95 V190 H0 Z" fill="#1d6b4a" opacity=".85"/>'
            '<path d="M0 145 Q90 105 180 135 T320 125 V190 H0 Z" fill="#0f5132"/>'
            '<path d="M40 150 q10 -30 30 -38 q-4 26 -18 40 q-8 6 -12 -2z" fill="#A8BCA3"/>'
            '<path d="M250 140 q14 -26 34 -30 q-6 24 -22 36 q-8 5 -12 -6z" fill="#E8F0E6"/>'
            '<circle cx="120" cy="60" r="3" fill="#fff" opacity=".7"/>'
            '<circle cx="160" cy="40" r="2.4" fill="#fff" opacity=".6"/>'
            '<circle cx="90" cy="85" r="2" fill="#fff" opacity=".5"/>'
            '</svg></div>')
    st.markdown(
        f'<div class="aw-hero"><div class="aw-hero-grid">'
        f'<div class="aw-hero-left"><h1>{html.escape(title)}</h1>'
        f'<p class="aw-sub">{html.escape(subtitle)}</p>{extra}</div>'
        f'{illustration}</div></div>',
        unsafe_allow_html=True)


_LANDSCAPE_ART = """
<svg viewBox="0 0 520 420" width="100%" aria-hidden="true"
     style="display:block;width:100%;height:auto">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#dfeee2"/><stop offset="1" stop-color="#f2f6ec"/>
    </linearGradient>
  </defs>
  <rect width="520" height="420" fill="url(#sky)" rx="18"/>
  <circle cx="415" cy="80" r="42" fill="#f4d58d" opacity=".95"/>
  <circle cx="415" cy="80" r="58" fill="#f4d58d" opacity=".25"/>
  <g fill="#ffffff" opacity=".85">
    <ellipse cx="110" cy="80" rx="46" ry="16"/><ellipse cx="145" cy="70" rx="34" ry="14"/>
    <ellipse cx="330" cy="140" rx="40" ry="13"/><ellipse cx="360" cy="132" rx="28" ry="11"/>
  </g>
  <path d="M0 250 Q140 190 300 235 T520 225 V420 H0 Z" fill="#cfe0cd"/>
  <path d="M0 300 Q160 250 330 290 T520 280 V420 H0 Z" fill="#9dbb96"/>
  <path d="M0 350 Q180 315 360 345 T520 340 V420 H0 Z" fill="#245B46"/>
  <g>
    <rect x="70" y="300" width="10" height="70" rx="4" fill="#153D32"/>
    <circle cx="75" cy="285" r="34" fill="#153D32"/>
    <circle cx="52" cy="300" r="20" fill="#1d4f40"/>
    <circle cx="98" cy="300" r="20" fill="#1d4f40"/>
    <rect x="430" y="315" width="9" height="55" rx="4" fill="#153D32"/>
    <circle cx="434" cy="303" r="26" fill="#153D32"/>
    <circle cx="415" cy="316" r="15" fill="#1d4f40"/>
    <circle cx="452" cy="316" r="15" fill="#1d4f40"/>
  </g>
  <g stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".9">
    <path d="M150 120 q6 -8 0 -16 q-6 -8 0 -16" fill="none"/>
    <path d="M185 95 q5 -7 0 -14 q-5 -7 0 -14" fill="none"/>
  </g>
</svg>
"""


def hero_art() -> str:
    """Custom environmental illustration used in the landing hero."""
    return _LANDSCAPE_ART


def floating_aqi_card(aqi: float, category: str, label: str = "Demo reading") -> str:
    """Small floating AQI chip rendered over the hero artwork."""
    color = category_color(category) if category else "#748078"
    return (
        f'<div style="position:absolute;right:18px;bottom:18px;'
        f'background:#fff;border-radius:14px;padding:.8rem 1rem;'
        f'box-shadow:0 10px 30px rgba(21,61,50,.25);min-width:170px">'
        f'<div style="font-size:.65rem;font-weight:700;letter-spacing:.1em;'
        f'text-transform:uppercase;color:#748078">{html.escape(label)}</div>'
        f'<div style="display:flex;align-items:baseline;gap:.4rem;margin-top:.15rem">'
        f'<span style="font-size:1.7rem;font-weight:800;color:{color};'
        f'font-family:Georgia,serif">{aqi:.0f}</span>'
        f'<span style="font-size:.8rem;font-weight:700;color:{color}">'
        f'{html.escape(category)}</span></div>'
        f'<div style="font-size:.7rem;color:#748078;margin-top:.2rem">'
        'PM2.5 · PM10 · live CPCB method</div></div>')


def feature_tile(title: str, description: str, icon_name: str,
                 action_label: str, action_key: str | None = None,
                 target_page: str | None = None) -> None:
    """A visual feature card. If action_key is given, renders a button that
    navigates to target_page via session state."""
    st.markdown(
        f'<div class="aw-card aw-feat"><div class="aw-feat-ico">'
        f'{icon(icon_name, 24)}</div>'
        f'<h4>{html.escape(title)}</h4>'
        f'<p>{html.escape(description)}</p></div>',
        unsafe_allow_html=True)
    if action_key and target_page:
        if st.button(action_label, key=action_key, width="stretch"):
            goto(target_page)


def journey(steps: list[tuple[str, str, str]]):
    """Visual journey strip. steps: list of (icon_name, title, desc)."""
    cells = []
    n = len(steps)
    for i, (ic, title, desc) in enumerate(steps):
        arrow = "" if i == n - 1 else (
            f'<div class="aw-jarrow">{icon("arrow", 16)}</div>')
        cells.append(
            f'<div class="aw-jstep">{arrow}'
            f'<div class="aw-jico">{icon(ic, 26)}</div>'
            f'<div class="t">{html.escape(title)}</div>'
            f'<div class="d">{html.escape(desc)}</div></div>')
    st.markdown(f'<div class="aw-journey">{"".join(cells)}</div>',
                unsafe_allow_html=True)


def cta_band(title: str, subtitle: str, button_label: str, page: str,
             key: str, secondary: bool = False):
    """Closing call-to-action band with a navigation button."""
    st.markdown(
        f'<div class="aw-cta-band"><h2>{html.escape(title)}</h2>'
        f'<p>{html.escape(subtitle)}</p></div>',
        unsafe_allow_html=True)
    st.button(button_label, key=key, type="primary"
              if not secondary else "secondary",
              on_click=lambda: st.session_state.update(nav_page=page))


def section_title(title: str):
    st.markdown(f'<div class="aw-section-title">{html.escape(title)}</div>',
                unsafe_allow_html=True)


def card(title: str, body_html: str = "", body_text: str = "",
         variant: str = ""):
    cls = "aw-card"
    if variant:
        cls += f" aw-card--{variant}"
    out = f'<div class="{cls}"><h4>{html.escape(title)}</h4>'
    if body_html:
        out += body_html
    if body_text:
        out += f"<p>{html.escape(body_text)}</p>"
    out += "</div>"
    st.markdown(out, unsafe_allow_html=True)


def badge(text: str, aqi_category: str | None = None, color: str | None = None):
    c = color or (category_color(aqi_category) if aqi_category else "#475569")
    st.markdown(
        f'<span class="aw-badge" style="background:{c}">'
        f'{html.escape(text)}</span>',
        unsafe_allow_html=True)


def meta(text: str):
    st.markdown(f'<div class="aw-meta">{html.escape(text)}</div>',
                unsafe_allow_html=True)


def kpi_row(items: list[tuple[str, str]]):
    """items: list of (big_value, small_label); both are HTML-escaped."""
    cells = "".join(
        f'<div class="aw-kpi"><div class="v">{html.escape(str(v))}</div>'
        f'<div class="l">{html.escape(str(l))}</div></div>'
        for v, l in items)
    st.markdown(f'<div class="aw-grid">{cells}</div>', unsafe_allow_html=True)


def hr():
    st.markdown('<hr class="aw-divider">', unsafe_allow_html=True)


def empty_state(message: str):
    st.markdown(
        f'<div class="aw-card" style="text-align:center;padding:2rem">'
        f'<div style="display:flex;justify-content:center;margin-bottom:.6rem">'
        f'{icon("wind", 34, "#A8BCA3")}</div>'
        f'<p style="color:var(--muted);max-width:52ch;margin:0 auto">'
        f'{html.escape(message)}</p></div>',
        unsafe_allow_html=True)


def alert_box(severity: str, title: str, detail: str):
    """severity: info|caution|warning|critical"""
    colors = {"info": "#2563eb", "caution": "#b45309",
              "warning": "#ea580c", "critical": "#b91c1c"}
    labels = {"info": "Info", "caution": "Caution",
              "warning": "Warning", "critical": "Critical"}
    c = colors.get(severity, "#475569")
    st.markdown(
        f'<div class="aw-card" style="border-left:4px solid {c}">'
        f'<h4>{labels.get(severity, severity)}: {html.escape(title)}</h4>'
        f'<p>{html.escape(detail)}</p></div>', unsafe_allow_html=True)


def goto(page: str):
    """Navigate to another module by setting the sidebar nav state."""
    st.session_state["nav_page"] = page
    st.rerun()


def field_label(text: str, hint: str = ""):
    h = f'<div class="aw-hint">{html.escape(hint)}</div>' if hint else ""
    st.markdown(f'<div class="aw-field-label">{html.escape(text)}</div>{h}',
                unsafe_allow_html=True)


def cta_button(label: str, page: str, key: str):
    """Primary-action button that navigates to a module."""
    if st.button(label, key=key, type="primary"):
        goto(page)
