"""Shared UI helpers: design system, CSS, cards, badges, navigation.

AirAware design system - refined environmental-wellness palette:
  forest #173E32 · evergreen #245B46 · sage #A8BCA3 · ivory #F8F7F0
  mint #E8F0E6 · charcoal #26352E
AQI category colours are used only where meaningful (badges, gauges).
"""

from __future__ import annotations

import html

import streamlit as st

from .aqi import category_color

_CSS = """
<style>
:root {
  --forest:#173E32; --forest-2:#1f5040; --evergreen:#245B46;
  --sage:#A8BCA3; --sage-soft:#d3dfc9; --ivory:#F8F7F0; --mint:#E8F0E6;
  --charcoal:#26352E; --muted:#6d7f72; --line:#e4e8dd;
  --card:#ffffff; --warn:#b45309; --bad:#b91c1c; --good:#15803d;
  --gold:#c9a24b; --sky:#7fa8b8;
  --shadow:0 1px 2px rgba(23,62,50,.05),0 8px 24px rgba(23,62,50,.07);
  --shadow-lg:0 14px 40px rgba(23,62,50,.16);
  --radius:18px;
  --serif:Georgia,'Iowan Old Style','Times New Roman',serif;
}
.stApp { background:var(--ivory); }
h1,h2,h3,h4,h5 { color:var(--forest); letter-spacing:-0.015em;
  font-family:var(--serif); }
p, li, .stMarkdown { color:var(--charcoal); }
a { color:var(--evergreen); }

/* ---------- typography ---------- */
.aw-eyebrow { display:inline-block; font-size:.7rem; font-weight:800;
  letter-spacing:.16em; text-transform:uppercase; color:var(--evergreen);
  background:var(--mint); border:1px solid var(--sage-soft);
  padding:.32rem .8rem; border-radius:999px; margin-bottom:.8rem; }
.aw-eyebrow--light { background:rgba(255,255,255,.12);
  border-color:rgba(255,255,255,.28); color:#eaf3ec; }
.aw-section-title { color:var(--forest); font-family:var(--serif);
  font-size:1.7rem; margin:2.6rem 0 .4rem; font-weight:600;
  letter-spacing:-0.01em; }
.aw-section-sub { color:var(--muted); font-size:.98rem; max-width:68ch;
  margin:-.15rem 0 1.1rem; line-height:1.55; }
.aw-lede { font-size:1.08rem; color:var(--charcoal); line-height:1.6;
  max-width:60ch; }

/* ---------- editorial hero ---------- */
.aw-hero { position:relative; overflow:hidden; border-radius:26px;
  background:var(--ivory); border:1px solid var(--line);
  padding:0; margin-bottom:1.8rem; box-shadow:var(--shadow); }
.aw-hero-grid { display:grid; grid-template-columns:1.05fr .95fr;
  gap:0; align-items:stretch; }
.aw-hero-left { padding:3rem 0 2.8rem 3rem; display:flex;
  flex-direction:column; justify-content:center; }
.aw-hero-right { position:relative; min-height:340px;
  background:var(--forest); overflow:hidden; }
.aw-hero-right svg.scene { position:absolute; inset:0; width:100%;
  height:100%; }
.aw-hero h1 { color:var(--forest); font-size:3.1rem; line-height:1.06;
  margin:.35rem 0 .9rem; font-weight:600; letter-spacing:-0.02em; }
.aw-hero .aw-sub { color:var(--muted); font-size:1.1rem;
  max-width:48ch; margin:0 0 1.4rem; line-height:1.6; }
.aw-hero .aw-tag { display:inline-block; background:var(--mint);
  border:1px solid var(--sage-soft); color:var(--evergreen);
  padding:.32rem .85rem; border-radius:999px; font-size:.8rem;
  font-weight:600; margin-top:.4rem; }
.aw-trust { display:flex; gap:1.2rem; flex-wrap:wrap; margin-top:1.5rem; }
.aw-trust span { font-size:.82rem; color:var(--muted); display:flex;
  align-items:center; gap:.45rem; font-weight:500; }
.aw-trust svg { color:var(--evergreen); }
.aw-hero-cta-row { display:flex; gap:.8rem; flex-wrap:wrap;
  margin-top:1.6rem; }
.aw-hero-cta { display:inline-block; background:var(--forest);
  color:#fff; font-weight:700; font-size:.95rem; padding:.78rem 1.6rem;
  border-radius:999px; text-decoration:none;
  box-shadow:0 6px 18px rgba(23,62,50,.25); }
.aw-hero-cta:hover { background:var(--evergreen); }
.aw-hero-cta--ghost { background:transparent; color:var(--forest);
  border:1.5px solid var(--sage-soft); box-shadow:none; }
.aw-hero-cta--ghost:hover { background:var(--mint); }
@media (max-width:980px){
  .aw-hero-grid{grid-template-columns:1fr}
  .aw-hero-left{padding:2.2rem 1.6rem}
  .aw-hero-right{min-height:230px}
  .aw-hero h1{font-size:2.1rem}
}
@media (max-width:560px){
  .aw-hero-left{padding:1.8rem 1.2rem}
  .aw-hero h1{font-size:1.85rem}
}

/* ---------- cards ---------- */
.aw-card { background:var(--card); border:1px solid var(--line);
  border-radius:var(--radius); padding:1.35rem 1.5rem; margin-bottom:1rem;
  box-shadow:var(--shadow); }
.aw-card h4 { margin:0 0 .4rem; color:var(--forest); font-size:1.05rem;
  font-weight:700; }
.aw-card p { margin:.25rem 0; color:var(--muted); font-size:.93rem;
  line-height:1.55; }
.aw-card--feature { border-top:3px solid var(--sage); }
.aw-card--cta { border:1.5px dashed var(--sage-soft); background:#fbfcf7;
  transition:box-shadow .15s ease, transform .15s ease,
  border-color .15s ease; }
.aw-card--cta:hover { box-shadow:var(--shadow-lg);
  border-color:var(--sage); }
.aw-card--flat { box-shadow:none; }
.aw-card--forest { background:var(--forest); border-color:var(--forest);
  color:#eef4ee; }
.aw-card--forest h4 { color:#fff; }
.aw-card--forest p { color:#cfe0d4; }
.aw-card--mint { background:var(--mint); border-color:var(--sage-soft);
  box-shadow:none; }

/* image-led nav card */
.aw-navcard { display:flex; flex-direction:column; height:100%;
  background:#fff; border:1px solid var(--line); border-radius:var(--radius);
  overflow:hidden; box-shadow:var(--shadow); transition:transform .15s ease,
  box-shadow .15s ease; }
.aw-navcard:hover { transform:translateY(-3px); box-shadow:var(--shadow-lg); }
.aw-navcard .art { height:132px; overflow:hidden; position:relative;
  display:flex; align-items:flex-end; }
.aw-navcard .art svg.scene { width:100%; height:100%; display:block; }
.aw-navcard .body { padding:1rem 1.2rem 1.15rem; display:flex;
  flex-direction:column; flex:1; }
.aw-navcard h4 { margin:0 0 .3rem; font-size:1.02rem; }
.aw-navcard p { font-size:.87rem; flex:1; }
.aw-navcard .go { display:inline-flex; align-items:center; gap:.35rem;
  font-size:.83rem; font-weight:700; color:var(--evergreen); margin-top:.6rem; }
.aw-navcard .go svg { transition:transform .15s ease; }
.aw-navcard:hover .go svg { transform:translateX(3px); }

/* feature tile: icon + title + copy + action */
.aw-feat { display:flex; flex-direction:column; height:100%;
  min-height:228px; }
.aw-feat-ico { width:46px; height:46px; border-radius:13px;
  background:var(--mint); color:var(--evergreen);
  display:flex; align-items:center; justify-content:center;
  margin-bottom:.75rem; flex:none; }
.aw-feat-ico--lg { width:58px; height:58px; border-radius:16px; }
.aw-feat p { flex:1; }
.aw-feat .aw-feat-link { font-size:.85rem; font-weight:600;
  color:var(--evergreen); margin-top:.5rem; }

/* showcase row (image-led, alternating) */
.aw-show { display:grid; grid-template-columns:1fr 1fr; gap:2.4rem;
  align-items:center; margin:3rem 0; }
.aw-show .art { border-radius:22px; overflow:hidden; border:1px solid
  var(--line); box-shadow:var(--shadow); background:var(--mint); }
.aw-show .art svg.scene { display:block; width:100%; height:auto; }
.aw-show h3 { font-size:1.55rem; margin:.2rem 0 .6rem; }
.aw-show .aw-show-points { list-style:none; padding:0; margin:.8rem 0 1.1rem; }
.aw-show .aw-show-points li { display:flex; gap:.55rem; align-items:flex-start;
  padding:.3rem 0; font-size:.92rem; color:var(--charcoal); }
.aw-show .aw-show-points svg { flex:none; margin-top:.2rem; color:var(--evergreen); }
.aw-show--flip .art { order:2; }
@media (max-width:860px){
  .aw-show{grid-template-columns:1fr;gap:1.2rem}
  .aw-show--flip .art{order:0}
}

/* ---------- badges / meta ---------- */
.aw-badge { display:inline-block; padding:.22rem .75rem; border-radius:999px;
  font-size:.76rem; font-weight:700; color:#fff; letter-spacing:.03em; }
.aw-badge--soft { background:var(--mint); color:var(--forest);
  border:1px solid var(--sage-soft); }
.aw-meta { font-size:.78rem; color:var(--muted); }
.aw-hero .aw-meta, .aw-hero .aw-reason { color:#cfe0d4; }
.aw-reason { font-size:.85rem; color:var(--muted); font-style:italic;
  background:var(--mint); border-radius:12px; padding:.55rem .8rem;
  margin-top:.55rem; }
.aw-pill { display:inline-block; background:var(--sage-soft); color:var(--forest);
  padding:.2rem .65rem; border-radius:999px; font-size:.76rem; font-weight:600; }
.aw-chip { display:inline-flex; align-items:center; gap:.35rem;
  background:var(--mint); color:var(--forest); border:1px solid var(--sage-soft);
  padding:.28rem .75rem; border-radius:999px; font-size:.78rem; font-weight:600; }
.aw-tag-soft { display:inline-block; background:#fdf3e0; color:#8a5a00;
  border:1px solid #ecd9ae; padding:.22rem .7rem; border-radius:999px;
  font-size:.74rem; font-weight:700; letter-spacing:.05em; }

/* ---------- KPI / grid ---------- */
.aw-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:.9rem; }
.aw-kpi { background:#fff; border:1px solid var(--line); border-radius:14px;
  padding:1rem 1.1rem; text-align:center; box-shadow:var(--shadow); }
.aw-kpi .v { font-size:1.55rem; font-weight:700; color:var(--forest);
  font-family:var(--serif); }
.aw-kpi .l { font-size:.7rem; color:var(--muted); text-transform:uppercase;
  letter-spacing:.07em; margin-top:.2rem; }
.aw-kpi--accent { border-top:3px solid var(--sage); }
.aw-kpi--accent2 { border-top:3px solid var(--evergreen); }
.aw-kpi--accent3 { border-top:3px solid var(--gold); }

/* ---------- AQI ring ---------- */
.aw-aqi-wrap { display:flex; align-items:center; gap:1.4rem; flex-wrap:wrap; }
.aw-aqi-ring { position:relative; width:150px; height:150px; flex:none; }
.aw-aqi-ring svg { transform:rotate(-90deg); }
.aw-aqi-ring .val { position:absolute; inset:0; display:flex;
  flex-direction:column; align-items:center; justify-content:center; }
.aw-aqi-ring .num { font-family:var(--serif); font-size:2.6rem; font-weight:700;
  line-height:1; }
.aw-aqi-ring .cat { font-size:.72rem; font-weight:800; letter-spacing:.1em;
  text-transform:uppercase; margin-top:.2rem; }
.aw-aqi-side .big { font-size:1.05rem; font-weight:600; color:var(--forest);
  font-family:var(--serif); }

/* ---------- journey / stepper ---------- */
.aw-journey { display:grid; grid-template-columns:repeat(4,1fr); gap:0;
  margin:1.4rem 0 1.6rem; }
.aw-jstep { position:relative; text-align:center; padding:1.4rem .7rem;
  background:#fff; border:1px solid var(--line); }
.aw-jstep:first-child { border-radius:18px 0 0 18px; }
.aw-jstep:last-child { border-radius:0 18px 18px 0; }
.aw-jstep + .aw-jstep { border-left:none; }
.aw-jstep .aw-jico { width:54px; height:54px; margin:0 auto .65rem;
  border-radius:50%; background:var(--mint); color:var(--evergreen);
  display:flex; align-items:center; justify-content:center; }
.aw-jstep .t { font-weight:700; color:var(--forest); font-size:.95rem;
  font-family:var(--serif); }
.aw-jstep .d { font-size:.78rem; color:var(--muted); margin-top:.3rem;
  line-height:1.45; }
.aw-jarrow { position:absolute; right:-9px; top:44px; z-index:2;
  color:var(--sage); }
@media (max-width:860px){
  .aw-journey{grid-template-columns:1fr 1fr}
  .aw-jstep{border-radius:0!important;border-left:none!important;
    border-top:none!important}
  .aw-jarrow{display:none}
}

/* vertical timeline */
.aw-timeline { position:relative; margin:1.2rem 0 1.4rem; padding-left:2.2rem; }
.aw-timeline::before { content:""; position:absolute; left:26px; top:8px;
  bottom:8px; width:2px; background:var(--sage-soft); border-radius:2px; }
/* timeline node (self-contained; works without a shared wrapper) */
.aw-tstep { position:relative; margin:0 0 1.15rem; padding-left:1.35rem;
  border-left:2px solid var(--sage-soft); }
.aw-tstep::before { content:""; position:absolute; left:-7px; top:.3rem;
  width:12px; height:12px; border-radius:50%; background:var(--mint);
  border:3px solid var(--evergreen); }
.aw-tstep .when { font-size:.72rem; font-weight:800; letter-spacing:.12em;
  text-transform:uppercase; color:var(--evergreen); }
.aw-tstep h4 { margin:.15rem 0 .25rem; font-size:1rem; }
.aw-tstep p { margin:0; font-size:.9rem; }

/* ---------- recommendation cards ---------- */
.aw-rec { border-radius:16px; padding:1.1rem 1.3rem; margin-bottom:.85rem;
  background:#fff; border:1px solid var(--line); border-left:5px solid var(--sage);
  box-shadow:var(--shadow); }
.aw-rec .aw-rec-head { display:flex; justify-content:space-between;
  align-items:baseline; gap:.6rem; flex-wrap:wrap; }
.aw-rec h4 { margin:0; font-size:1.02rem; }
.aw-rec .what { margin:.45rem 0 .2rem; font-size:.93rem; color:var(--charcoal); }
.aw-rec .fld { font-size:.86rem; color:var(--muted); margin:.18rem 0; }
.aw-rec .fld b { color:var(--forest-2); }

/* ---------- checklist ---------- */
.aw-checklist { display:grid; gap:.55rem; }
.aw-check { display:flex; align-items:flex-start; gap:.8rem;
  background:#fff; border:1px solid var(--line); border-radius:14px;
  padding:.85rem 1rem; transition:border-color .15s ease, background .15s; }
.aw-check:hover { border-color:var(--sage); }
.aw-check input[type="checkbox"] { margin-top:.2rem; width:17px; height:17px;
  accent-color:var(--evergreen); flex:none; }
.aw-check .txt { font-size:.92rem; color:var(--charcoal); line-height:1.5; }

/* ---------- speech bubble (companion) ---------- */
.aw-bubble { position:relative; background:#fff; border:1px solid var(--line);
  border-radius:18px; padding:1.1rem 1.3rem; box-shadow:var(--shadow); }
.aw-bubble::before { content:""; position:absolute; left:-9px; top:26px;
  width:16px; height:16px; background:#fff; border-left:1px solid var(--line);
  border-bottom:1px solid var(--line); transform:rotate(45deg); }
.aw-avatar { width:44px; height:44px; border-radius:50%; flex:none;
  background:var(--forest); color:var(--sage); display:flex; align-items:center;
  justify-content:center; }

/* ---------- misc ---------- */
.aw-warn-box { border-left:4px solid var(--warn); }
.aw-bad-box { border-left:4px solid var(--bad); }
.aw-good-box { border-left:4px solid var(--good); }
.aw-info-box { border-left:4px solid #2563eb; }
.aw-divider { border:none; border-top:1px solid var(--line); margin:2rem 0; }
.aw-leaf { color:var(--evergreen); }
.aw-field-label { font-size:.85rem; font-weight:600; color:var(--forest);
  margin-bottom:.15rem; }
.aw-hint { font-size:.78rem; color:var(--muted); }
.aw-cta-band { border-radius:26px; background:var(--forest); color:#eef4ee;
  padding:3rem 2.4rem; text-align:center; box-shadow:var(--shadow-lg);
  margin:2.6rem 0 .8rem; position:relative; overflow:hidden; }
.aw-cta-band::before { content:""; position:absolute; top:-70px; right:-70px;
  width:240px; height:240px; border-radius:50%; background:var(--evergreen);
  opacity:.55; }
.aw-cta-band h2 { color:#fff; font-size:1.9rem; margin:0 0 .6rem;
  position:relative; }
.aw-cta-band p { color:#cfe0d4; max-width:56ch; margin:0 auto 1.4rem;
  position:relative; }
svg.scene { display:block; width:100%; height:auto; }
.aw-hero-right svg.scene { position:absolute; inset:0; width:100%;
  height:100%; }
.block-container { padding-top:1.2rem; padding-bottom:2.6rem; }
[data-testid="stSidebar"] { background:#f0f3ec; border-right:1px solid var(--line); }
[data-testid="stSidebar"] .block-container { padding-top:1.1rem; }
.aw-nav-group { display:flex; align-items:center; gap:.45rem;
  font-size:.68rem; font-weight:800; letter-spacing:.13em;
  color:#5f7263; margin:1.1rem 0 .4rem .2rem; }
.aw-nav-group svg { color:var(--sage); }
.aw-nav-item { display:flex; align-items:center; gap:.6rem; width:100%;
  padding:.55rem .8rem; border-radius:11px; font-size:.9rem;
  font-weight:600; color:var(--forest); text-align:left;
  background:transparent; border:1px solid transparent;
  cursor:pointer; transition:background .12s ease, border-color .12s ease;
  margin-bottom:.15rem; }
.aw-nav-item:hover { background:#e4ecdf; }
.aw-nav-item.aw-nav-active { background:var(--forest); color:#fff;
  box-shadow:0 4px 12px rgba(23,62,50,.25); }
.aw-nav-item.aw-nav-active svg { color:var(--sage); }
.aw-nav-item svg { flex:none; opacity:.9; }
[data-testid="stSidebar"] hr { margin:.9rem 0; border-color:var(--line); }
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
.stButton > button { border-radius:12px; font-weight:600; }
.stButton > button[kind="primary"] { background:var(--evergreen);
  border-color:var(--evergreen); }
.stButton > button[kind="primary"]:hover { background:var(--forest);
  border-color:var(--forest); }
.stTabs [data-baseweb="tab-list"] { gap:.4rem; }
.stTabs [data-baseweb="tab"] { border-radius:10px 10px 0 0; }
details summary { cursor:pointer; font-weight:600; color:var(--forest-2);
  padding:.3rem 0; }
details[open] summary { margin-bottom:.4rem; }
.aw-stat-strip { display:flex; flex-wrap:wrap; gap:.6rem 1.4rem;
  font-size:.82rem; color:var(--muted); }
.aw-stat-strip b { color:var(--forest); font-weight:700; }
/* responsive helpers */
.aw-chk-grid { display:grid; grid-template-columns:1fr 1fr; gap:.5rem;
  margin-top:1rem; }
.aw-band-grid { display:grid; grid-template-columns:1.2fr .8fr;
  gap:2rem; align-items:center; }
.aw-bl-grid { display:grid; grid-template-columns:1fr 1fr; gap:.6rem;
  margin-top:.5rem; }
@media (max-width:860px){
  .aw-band-grid{grid-template-columns:1fr}
  .aw-chk-grid{grid-template-columns:1fr}
}
@media (max-width:560px){
  .aw-bl-grid{grid-template-columns:1fr}
}
/* Streamlit columns never stack on their own; below tablet width we
   stack every horizontal block so cards and inputs stay readable. */
@media (max-width:820px){
  [data-testid="stHorizontalBlock"]{flex-direction:column !important;
    gap:.7rem}
  [data-testid="stHorizontalBlock"] > div{width:100% !important;
    min-width:0 !important}
}
@media (max-width:640px){
  .aw-card{padding:1rem 1.05rem} .aw-kpi .v{font-size:1.2rem}
  .stButton > button{min-height:42px}
  .aw-cta-band{padding:2rem 1.3rem}
  .aw-hero-left{padding:1.8rem 1.2rem}
  .aw-hero-right{min-height:200px}
}
</style>
"""


def apply_css():
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Icons - consistent stroke SVG family (Lucide-style, 24x24 viewBox)
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
    "bike": '<circle cx="5.5" cy="17.5" r="3.5"/><circle cx="18.5" cy="17.5" r="3.5"/><path d="M15 6a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm-3 11.5V14l-3-3 4-3 2 5h2"/>',
    "train": '<rect x="4" y="3" width="16" height="14" rx="2"/><path d="M4 10h16"/><path d="M8 21l-2 3"/><path d="M16 21l2 3"/><path d="M8 13.5h.01"/><path d="M16 13.5h.01"/>',
    "factory": '<path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M17 18h1"/><path d="M12 18h1"/><path d="M7 18h1"/>',
    "mask": '<path d="M4 7c0-2.2 3.6-4 8-4s8 1.8 8 4-3.6 4-8 4-8-1.8-8-4Z"/><path d="M4 7v4c0 2.2 3.6 4 8 4s8-1.8 8-4V7"/><path d="M9 12v3c0 1.7 1.3 3 3 3s3-1.3 3-3v-3"/>',
    "trash": '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "tree": '<path d="M12 22v-8"/><path d="M12 14c0-4-3-6-7-6 0 4 3 6 7 6Z"/><path d="M12 12c0-4 3-6 7-6 0 4-3 6-7 6Z"/><path d="M12 22c0-3-2-5-5-6"/><path d="M12 22c0-3 2-5 5-6"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "message": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "play": '<polygon points="6 3 20 12 6 21 6 3"/>',
    "minus": '<path d="M5 12h14"/>',
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
# Illustration library - original flat-style SVG scenes in the brand palette
# ---------------------------------------------------------------------------

_SCENES: dict[str, str] = {}


def _scene(name: str, inner: str, w: int = 480, h: int = 320) -> str:
    _SCENES[name] = inner
    return inner


def scene(name: str) -> str:
    """Return a full <svg class="scene"> illustration by name."""
    inner = _SCENES.get(name, _SCENES.get("city", ""))
    return inner


# Shared defs injected per-scene (ids are unique per scene via prefix).
def _defs(p: str) -> str:
    return (
        f'<defs>'
        f'<linearGradient id="{p}sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#e6f0e4"/>'
        f'<stop offset="1" stop-color="#f6f5ec"/></linearGradient>'
        f'<linearGradient id="{p}hill1" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#b9cfae"/><stop offset="1" stop-color="#8fae85"/>'
        f'</linearGradient>'
        f'<linearGradient id="{p}hill2" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#7fa27c"/><stop offset="1" stop-color="#5c8262"/>'
        f'</linearGradient>'
        f'</defs>')


_scene("city", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a green city skyline with trees and birds">
{_defs("c")}
<rect width="480" height="320" fill="url(#csky)"/>
<circle cx="392" cy="62" r="30" fill="#f0d9a0"/>
<circle cx="392" cy="62" r="44" fill="#f0d9a0" opacity=".3"/>
<g fill="#ffffff" opacity=".9">
<ellipse cx="96" cy="58" rx="42" ry="14"/><ellipse cx="128" cy="48" rx="30" ry="12"/>
<ellipse cx="300" cy="110" rx="36" ry="11"/><ellipse cx="326" cy="103" rx="24" ry="9"/>
</g>
<g stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".8" fill="none">
<path d="M70 130 q7 -9 0 -18 q-7 -9 0 -18"/><path d="M108 108 q6 -8 0 -16 q-6 -8 0 -16"/>
</g>
<path d="M0 205 Q120 165 240 195 T480 188 V320 H0 Z" fill="url(#chill1)"/>
<path d="M0 255 Q140 220 260 248 T480 240 V320 H0 Z" fill="url(#chill2)"/>
<g>
<rect x="52" y="212" width="9" height="46" rx="3" fill="#173E32"/>
<circle cx="56" cy="200" r="26" fill="#173E32"/>
<circle cx="40" cy="212" r="15" fill="#245B46"/>
<circle cx="72" cy="212" r="15" fill="#245B46"/>
<rect x="410" y="222" width="8" height="36" rx="3" fill="#173E32"/>
<circle cx="414" cy="212" r="20" fill="#173E32"/>
<circle cx="402" cy="221" r="11" fill="#245B46"/>
<circle cx="426" cy="221" r="11" fill="#245B46"/>
</g>
<g>
<rect x="180" y="196" width="34" height="58" rx="4" fill="#F8F7F0" stroke="#d8dccb"/>
<rect x="186" y="204" width="9" height="9" rx="1" fill="#A8BCA3"/>
<rect x="199" y="204" width="9" height="9" rx="1" fill="#cfe0cd"/>
<rect x="186" y="218" width="9" height="9" rx="1" fill="#cfe0cd"/>
<rect x="199" y="218" width="9" height="9" rx="1" fill="#A8BCA3"/>
<rect x="186" y="232" width="22" height="6" rx="2" fill="#245B46"/>
</g>
<path d="M0 320 V300 Q240 282 480 300 V320 Z" fill="#173E32" opacity=".16"/>
</svg>''')

_scene("home", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a cozy home with plants and clean indoor air">
{_defs("h")}
<rect width="480" height="320" fill="url(#hsky)"/>
<circle cx="80" cy="60" r="26" fill="#f0d9a0" opacity=".9"/>
<path d="M0 240 Q120 210 240 232 T480 226 V320 H0 Z" fill="url(#hhill1)"/>
<path d="M0 275 Q140 250 260 268 T480 262 V320 H0 Z" fill="url(#hhill2)"/>
<g>
<path d="M170 200 L250 140 L330 200 Z" fill="#245B46"/>
<rect x="185" y="200" width="130" height="80" rx="6" fill="#F8F7F0" stroke="#d8dccb"/>
<rect x="228" y="232" width="34" height="48" rx="4" fill="#245B46"/>
<circle cx="254" cy="256" r="3" fill="#F8F7F0"/>
<rect x="200" y="218" width="26" height="24" rx="3" fill="#cfe0cd" stroke="#d8dccb"/>
<rect x="284" y="218" width="26" height="24" rx="3" fill="#cfe0cd" stroke="#d8dccb"/>
<rect x="246" y="146" width="12" height="26" fill="#173E32"/>
<path d="M206 148 h88 v-12 a44 14 0 0 0 -88 0 Z" fill="#173E32"/>
</g>
<g>
<rect x="330" y="212" width="34" height="44" rx="6" fill="#E8F0E6" stroke="#A8BCA3"/>
<path d="M347 218 v-10 M338 222 l-6 -8 M356 222 l6 -8" stroke="#245B46" stroke-width="3" stroke-linecap="round" fill="none"/>
<path d="M342 240 c0-10 4-16 10-16 s10 6 10 16" stroke="#245B46" stroke-width="3" fill="none" stroke-linecap="round"/>
</g>
<g fill="#ffffff" opacity=".85">
<circle cx="120" cy="120" r="4"/><circle cx="150" cy="96" r="3"/><circle cx="420" cy="90" r="3.5"/>
</g>
</svg>''')

_scene("wellness", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a person breathing fresh air during a morning walk">
{_defs("w")}
<rect width="480" height="320" fill="url(#wsky)"/>
<circle cx="88" cy="70" r="34" fill="#f0d9a0"/>
<circle cx="88" cy="70" r="50" fill="#f0d9a0" opacity=".28"/>
<path d="M0 235 Q130 195 250 222 T480 214 V320 H0 Z" fill="url(#whill1)"/>
<path d="M0 268 Q150 240 270 258 T480 252 V320 H0 Z" fill="url(#whill2)"/>
<g stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" opacity=".85" fill="none">
<path d="M330 90 q8 -10 0 -20 q-8 -10 0 -20"/><path d="M365 120 q7 -9 0 -18 q-7 -9 0 -18"/>
<path d="M300 140 q6 -8 0 -16 q-6 -8 0 -16"/>
</g>
<g>
<circle cx="240" cy="128" r="20" fill="#E8B98F"/>
<path d="M214 122 a26 26 0 0 1 52 0 l-4 10 h-44 Z" fill="#3d2f26"/>
<path d="M206 205 q34 -26 68 0 l6 60 h-80 Z" fill="#245B46"/>
<path d="M226 205 v-14 M254 205 v-14" stroke="#E8B98F" stroke-width="9" stroke-linecap="round"/>
<path d="M212 250 l-16 34 M268 250 l16 34" stroke="#26352E" stroke-width="10" stroke-linecap="round"/>
<path d="M196 286 l-8 14 M284 286 l8 14" stroke="#26352E" stroke-width="8" stroke-linecap="round"/>
</g>
<g>
<rect x="52" y="252" width="8" height="44" rx="3" fill="#173E32"/>
<circle cx="56" cy="240" r="24" fill="#173E32"/>
<circle cx="38" cy="254" r="14" fill="#245B46"/>
<circle cx="74" cy="254" r="14" fill="#245B46"/>
</g>
</svg>''')

_scene("impact", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a growing plant beside a rising green chart">
{_defs("i")}
<rect width="480" height="320" fill="url(#isky)"/>
<circle cx="400" cy="66" r="28" fill="#f0d9a0" opacity=".9"/>
<path d="M0 250 Q120 215 250 240 T480 232 V320 H0 Z" fill="url(#ihill1)"/>
<path d="M0 285 Q150 258 280 276 T480 270 V320 H0 Z" fill="url(#ihill2)"/>
<g>
<rect x="70" y="150" width="120" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<rect x="70" y="178" width="86" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<rect x="70" y="206" width="52" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<path d="M84 148 L110 128 L136 112 L168 92 L196 74" stroke="#245B46" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="196" cy="74" r="9" fill="#A8BCA3"/>
<circle cx="168" cy="92" r="7" fill="#A8BCA3"/>
<circle cx="136" cy="112" r="6" fill="#A8BCA3"/>
</g>
<g>
<path d="M330 260 q-26 -34 -8 -66 q24 6 20 34 q18 -30 44 -22 q-8 40 -56 54z" fill="#245B46"/>
<path d="M340 258 q-4 -60 26 -86" stroke="#173E32" stroke-width="7" fill="none" stroke-linecap="round"/>
<circle cx="368" cy="166" r="14" fill="#A8BCA3"/>
<circle cx="352" cy="180" r="11" fill="#cfe0cd"/>
</g>
<g fill="#ffffff" opacity=".8">
<circle cx="180" cy="90" r="3.5"/><circle cx="220" cy="60" r="2.8"/><circle cx="120" cy="120" r="2.5"/>
</g>
</svg>''')

_scene("family", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a family walking together on a clean-air day">
{_defs("f")}
<rect width="480" height="320" fill="url(#fsky)"/>
<circle cx="400" cy="60" r="30" fill="#f0d9a0"/>
<circle cx="400" cy="60" r="46" fill="#f0d9a0" opacity=".25"/>
<g fill="#ffffff" opacity=".9">
<ellipse cx="90" cy="66" rx="40" ry="13"/><ellipse cx="122" cy="56" rx="28" ry="11"/>
<ellipse cx="260" cy="120" rx="34" ry="10"/>
</g>
<path d="M0 250 Q130 212 260 240 T480 232 V320 H0 Z" fill="url(#fhill1)"/>
<path d="M0 282 Q150 255 280 272 T480 266 V320 H0 Z" fill="url(#fhill2)"/>
<g>
<circle cx="190" cy="176" r="17" fill="#E8B98F"/>
<path d="M172 172 a18 18 0 0 1 36 0 l-3 9 h-30 Z" fill="#26352E"/>
<path d="M160 252 q30 -24 60 0 l5 46 h-70 Z" fill="#245B46"/>
<path d="M182 252 v-12 M208 252 v-12" stroke="#E8B98F" stroke-width="8" stroke-linecap="round"/>
<path d="M166 292 l-14 28 M224 292 l14 28" stroke="#26352E" stroke-width="9" stroke-linecap="round"/>
</g>
<g>
<circle cx="300" cy="196" r="13" fill="#E8B98F"/>
<path d="M287 193 a14 14 0 0 1 26 0 l-2 7 h-22 Z" fill="#6b4a2f"/>
<path d="M274 262 q26 -20 52 0 l4 36 h-60 Z" fill="#A8BCA3"/>
<path d="M292 262 v-10 M318 262 v-10" stroke="#E8B98F" stroke-width="7" stroke-linecap="round"/>
<path d="M276 294 l-12 22 M324 294 l12 22" stroke="#26352E" stroke-width="8" stroke-linecap="round"/>
</g>
<g>
<circle cx="110" cy="210" r="10" fill="#E8B98F"/>
<path d="M100 208 a11 11 0 0 1 20 0 l-2 6 h-16 Z" fill="#3d2f26"/>
<path d="M88 268 q22 -16 44 0 l3 28 h-50 Z" fill="#c9a24b"/>
<path d="M102 268 v-8 M118 268 v-8" stroke="#E8B98F" stroke-width="6" stroke-linecap="round"/>
<path d="M90 292 l-10 18 M130 292 l10 18" stroke="#26352E" stroke-width="7" stroke-linecap="round"/>
</g>
<g>
<rect x="60" y="240" width="7" height="40" rx="3" fill="#173E32"/>
<circle cx="63" cy="230" r="20" fill="#173E32"/>
<circle cx="48" cy="242" r="11" fill="#245B46"/>
<circle cx="78" cy="242" r="11" fill="#245B46"/>
</g>
</svg>''')

_scene("indoor", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a clean, well-ventilated living room">
<rect width="480" height="320" fill="#E8F0E6"/>
<rect x="0" y="0" width="480" height="210" fill="#F8F7F0"/>
<rect x="0" y="210" width="480" height="110" fill="#D8CBB2"/>
<g>
<rect x="60" y="50" width="120" height="120" rx="8" fill="#cfe0cd" stroke="#b9cfae" stroke-width="6"/>
<line x1="120" y1="50" x2="120" y2="170" stroke="#b9cfae" stroke-width="4"/>
<line x1="60" y1="110" x2="180" y2="110" stroke="#b9cfae" stroke-width="4"/>
<path d="M80 160 q20 -30 40 -12 q10 -22 30 -8" stroke="#fff" stroke-width="5" fill="none" opacity=".8" stroke-linecap="round"/>
</g>
<g>
<rect x="330" y="60" width="90" height="110" rx="8" fill="#fdf6e0" stroke="#e0d3a8" stroke-width="5"/>
<rect x="338" y="68" width="74" height="70" rx="4" fill="#f0d9a0" opacity=".5"/>
<circle cx="375" cy="112" r="16" fill="#f0d9a0"/>
</g>
<g>
<rect x="230" y="150" width="150" height="46" rx="12" fill="#245B46"/>
<rect x="222" y="138" width="34" height="56" rx="10" fill="#173E32"/>
<rect x="364" y="138" width="34" height="56" rx="10" fill="#173E32"/>
<rect x="240" y="130" width="52" height="26" rx="8" fill="#A8BCA3"/>
<rect x="292" y="130" width="52" height="26" rx="8" fill="#cfe0cd"/>
</g>
<g>
<rect x="120" y="238" width="26" height="34" rx="6" fill="#c96f4a"/>
<path d="M118 238 q15 -34 30 0" fill="#245B46"/>
<path d="M126 226 q8 -14 22 -12" stroke="#245B46" stroke-width="4" fill="none" stroke-linecap="round"/>
</g>
<rect x="0" y="272" width="480" height="48" fill="#C4B49A"/>
<rect x="330" y="196" width="10" height="76" fill="#8a7a5c"/>
<circle cx="335" cy="190" r="18" fill="#A8BCA3"/>
<circle cx="320" cy="200" r="11" fill="#cfe0cd"/>
<circle cx="350" cy="200" r="11" fill="#cfe0cd"/>
</svg>''')

_scene("transport", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration comparing car, bus and bicycle travel">
{_defs("t")}
<rect width="480" height="320" fill="url(#tsky)"/>
<circle cx="80" cy="58" r="26" fill="#f0d9a0" opacity=".9"/>
<path d="M0 250 Q140 215 280 240 T480 232 V320 H0 Z" fill="url(#thill1)"/>
<path d="M0 282 Q150 258 280 272 T480 266 V320 H0 Z" fill="url(#thill2)"/>
<g>
<rect x="52" y="196" width="86" height="40" rx="10" fill="#b7c9bd" stroke="#8fae85"/>
<rect x="60" y="188" width="56" height="20" rx="8" fill="#dfeee2"/>
<circle cx="76" cy="240" r="12" fill="#26352E"/><circle cx="76" cy="240" r="5" fill="#F8F7F0"/>
<circle cx="114" cy="240" r="12" fill="#26352E"/><circle cx="114" cy="240" r="5" fill="#F8F7F0"/>
<path d="M140 202 h22" stroke="#8fae85" stroke-width="4" stroke-linecap="round"/>
</g>
<g>
<rect x="210" y="172" width="110" height="66" rx="12" fill="#245B46"/>
<rect x="220" y="182" width="24" height="22" rx="4" fill="#cfe0cd"/>
<rect x="252" y="182" width="24" height="22" rx="4" fill="#cfe0cd"/>
<rect x="284" y="182" width="24" height="22" rx="4" fill="#cfe0cd"/>
<circle cx="238" cy="246" r="13" fill="#26352E"/><circle cx="238" cy="246" r="5" fill="#F8F7F0"/>
<circle cx="292" cy="246" r="13" fill="#26352E"/><circle cx="292" cy="246" r="5" fill="#F8F7F0"/>
</g>
<g>
<circle cx="392" cy="252" r="17" stroke="#173E32" stroke-width="5" fill="none"/>
<circle cx="392" cy="252" r="5" fill="#173E32"/>
<path d="M392 252 L408 226 M408 226 h18 M408 226 l10 4" stroke="#173E32" stroke-width="5" fill="none" stroke-linecap="round"/>
<circle cx="430" cy="222" r="9" fill="#E8B98F"/>
<path d="M418 218 a11 11 0 0 1 22 0 l-2 8 h-18 Z" fill="#3d2f26"/>
<path d="M408 246 q-6 -22 12 -30" stroke="#245B46" stroke-width="6" fill="none" stroke-linecap="round"/>
</g>
<path d="M0 310 H480" stroke="#173E32" stroke-width="4" opacity=".25"/>
</svg>''')

_scene("lab", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of air-quality measurement and CPCB methodology">
{_defs("l")}
<rect width="480" height="320" fill="url(#lsky)"/>
<path d="M0 250 Q140 215 280 240 T480 232 V320 H0 Z" fill="url(#lhill1)"/>
<path d="M0 285 Q150 260 280 275 T480 270 V320 H0 Z" fill="url(#lhill2)"/>
<g>
<path d="M190 110 h44 v60 l34 66 a10 10 0 0 1 -9 15 H165 a10 10 0 0 1 -9 -15 l34 -66 Z" fill="#F8F7F0" stroke="#A8BCA3" stroke-width="4"/>
<path d="M172 190 h70 l-14 -30 H186 Z" fill="#E8F0E6"/>
<path d="M180 178 h54 l-8 -18 h-38 Z" fill="#245B46" opacity=".85"/>
<circle cx="212" cy="160" r="6" fill="#A8BCA3"/><circle cx="224" cy="150" r="4" fill="#A8BCA3"/><circle cx="200" cy="146" r="4.5" fill="#A8BCA3"/>
<path d="M178 96 h68" stroke="#A8BCA3" stroke-width="5" stroke-linecap="round"/>
</g>
<g>
<rect x="300" y="150" width="90" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<rect x="300" y="176" width="64" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<rect x="300" y="202" width="40" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<path d="M310 148 L330 134 L350 122 L372 108 L392 96" stroke="#245B46" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="392" cy="96" r="8" fill="#A8BCA3"/>
</g>
<g fill="#ffffff" opacity=".8">
<circle cx="120" cy="100" r="4"/><circle cx="150" cy="76" r="3"/><circle cx="330" cy="60" r="3"/>
</g>
</svg>''')

_scene("checklist", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a household checklist and healthy habits">
{_defs("k")}
<rect width="480" height="320" fill="url(#ksky)"/>
<path d="M0 250 Q140 215 280 240 T480 232 V320 H0 Z" fill="url(#khill1)"/>
<path d="M0 285 Q150 260 280 275 T480 270 V320 H0 Z" fill="url(#khill2)"/>
<g>
<rect x="120" y="60" width="240" height="210" rx="16" fill="#F8F7F0" stroke="#d8dccb" stroke-width="3"/>
<rect x="142" y="88" width="110" height="14" rx="7" fill="#A8BCA3"/>
<g>
<rect x="142" y="118" width="22" height="22" rx="6" fill="#245B46"/>
<path d="M147 129 l4 4 8 -9" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="176" y="122" width="150" height="10" rx="5" fill="#e4e8dd"/>
</g>
<g>
<rect x="142" y="156" width="22" height="22" rx="6" fill="#fff" stroke="#A8BCA3" stroke-width="3"/>
<path d="M147 167 l4 4 8 -9" stroke="#245B46" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="176" y="160" width="120" height="10" rx="5" fill="#e4e8dd"/>
</g>
<g>
<rect x="142" y="194" width="22" height="22" rx="6" fill="#245B46"/>
<path d="M147 205 l4 4 8 -9" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="176" y="198" width="170" height="10" rx="5" fill="#e4e8dd"/>
</g>
<g>
<rect x="142" y="232" width="22" height="22" rx="6" fill="#fff" stroke="#A8BCA3" stroke-width="3"/>
<path d="M147 243 l4 4 8 -9" stroke="#245B46" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="176" y="236" width="95" height="10" rx="5" fill="#e4e8dd"/>
</g>
</g>
<g>
<circle cx="80" cy="240" r="26" fill="#173E32"/>
<path d="M66 236 q14 -22 28 0" fill="#245B46"/>
<path d="M74 226 q8 -16 20 -14" stroke="#245B46" stroke-width="4" fill="none" stroke-linecap="round"/>
<rect x="76" y="264" width="8" height="30" rx="3" fill="#173E32"/>
</g>
</svg>''')

_scene("plan", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a day planned around air quality">
{_defs("p")}
<rect width="480" height="320" fill="url(#psky)"/>
<circle cx="240" cy="150" r="60" fill="#f0d9a0" opacity=".9"/>
<circle cx="240" cy="150" r="86" fill="#f0d9a0" opacity=".22"/>
<path d="M0 262 Q140 228 280 252 T480 246 V320 H0 Z" fill="url(#phill1)"/>
<path d="M0 292 Q150 268 280 284 T480 278 V320 H0 Z" fill="url(#phill2)"/>
<g stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".85" fill="none">
<path d="M90 80 q8 -10 0 -20 q-8 -10 0 -20"/><path d="M130 110 q6 -8 0 -16 q-6 -8 0 -16"/>
</g>
<g>
<rect x="200" y="96" width="80" height="150" rx="14" fill="#F8F7F0" stroke="#d8dccb" stroke-width="3"/>
<rect x="212" y="112" width="56" height="8" rx="4" fill="#A8BCA3"/>
<rect x="212" y="132" width="40" height="8" rx="4" fill="#e4e8dd"/>
<rect x="212" y="152" width="48" height="8" rx="4" fill="#e4e8dd"/>
<rect x="212" y="172" width="34" height="8" rx="4" fill="#e4e8dd"/>
<circle cx="240" cy="220" r="20" fill="#245B46"/>
<path d="M228 220 l8 8 16 -16" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</g>
<g>
<rect x="330" y="120" width="60" height="60" rx="12" fill="#E8F0E6" stroke="#A8BCA3"/>
<path d="M344 156 l10 -20 10 14 12 -18" stroke="#245B46" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</g>
</svg>''')

_scene("companion", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a friendly AI air companion">
<rect width="480" height="320" fill="#F8F7F0"/>
<path d="M0 250 Q140 215 280 240 T480 232 V320 H0 Z" fill="url(#chill1)" opacity=".5"/>
<defs><linearGradient id="chill1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cfe0cd"/><stop offset="1" stop-color="#a8bca3"/></linearGradient></defs>
<g>
<rect x="150" y="80" width="180" height="150" rx="26" fill="#173E32"/>
<rect x="168" y="102" width="144" height="96" rx="16" fill="#1f5040"/>
<circle cx="212" cy="150" r="13" fill="#A8BCA3"/>
<circle cx="212" cy="150" r="6" fill="#F8F7F0"/>
<circle cx="268" cy="150" r="13" fill="#A8BCA3"/>
<circle cx="268" cy="150" r="6" fill="#F8F7F0"/>
<path d="M216 186 q24 16 48 0" stroke="#A8BCA3" stroke-width="6" fill="none" stroke-linecap="round"/>
<rect x="228" y="232" width="24" height="20" rx="6" fill="#173E32"/>
<rect x="196" y="252" width="88" height="14" rx="7" fill="#A8BCA3"/>
</g>
<g fill="#A8BCA3">
<path d="M120 120 l4 10 10 4 -10 4 -4 10 -4 -10 -10 -4 10 -4 Z"/>
<path d="M372 96 l3 8 8 3 -8 3 -3 8 -3 -8 -8 -3 8 -3 Z"/>
<circle cx="390" cy="170" r="5"/>
</g>
</svg>''')


# ---------------------------------------------------------------------------
# Page-level pieces
# ---------------------------------------------------------------------------

def page_header(eyebrow: str, title: str, subtitle: str = ""):
    """Consistent page intro: eyebrow chip + serif title + lede."""
    sub = f'<p class="aw-section-sub">{html.escape(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f'<div style="margin-bottom:.4rem"><span class="aw-eyebrow">'
        f'{html.escape(eyebrow)}</span></div>'
        f'<h1 style="font-size:2.1rem;margin:.1rem 0 .4rem">'
        f'{html.escape(title)}</h1>{sub}',
        unsafe_allow_html=True)


def hero(title: str, subtitle: str = "", extra: str = "", art: bool = False):
    """Compact in-page hero band. ``title``/``subtitle`` are escaped;
    ``extra`` is trusted internal markup only."""
    illustration = ""
    if art:
        illustration = (
            '<div class="aw-hero-right" style="min-height:200px">'
            + scene("city") + "</div>")
    st.markdown(
        f'<div class="aw-hero"><div class="aw-hero-grid">'
        f'<div class="aw-hero-left" style="padding:2rem">'
        f'<h1 style="font-size:2rem">{html.escape(title)}</h1>'
        f'<p class="aw-sub">{html.escape(subtitle)}</p>{extra}</div>'
        f'{illustration}</div></div>',
        unsafe_allow_html=True)


def hero_art() -> str:
    """Landing hero artwork (kept for backwards compatibility)."""
    return scene("city")


def floating_aqi_card(aqi: float, category: str, label: str = "Demo reading") -> str:
    """Small floating AQI chip rendered over hero artwork."""
    color = category_color(category) if category else "#748078"
    return (
        f'<div style="position:absolute;right:18px;bottom:18px;'
        f'background:#fff;border-radius:16px;padding:.9rem 1.1rem;'
        f'box-shadow:0 12px 34px rgba(21,61,50,.3);min-width:180px;'
        f'border:1px solid var(--line)">'
        f'<div style="font-size:.66rem;font-weight:800;letter-spacing:.1em;'
        f'text-transform:uppercase;color:#748078">{html.escape(label)}</div>'
        f'<div style="display:flex;align-items:baseline;gap:.4rem;margin-top:.2rem">'
        f'<span style="font-size:1.8rem;font-weight:800;color:{color};'
        f'font-family:var(--serif)">{aqi:.0f}</span>'
        f'<span style="font-size:.82rem;font-weight:700;color:{color}">'
        f'{html.escape(category)}</span></div>'
        f'<div style="font-size:.7rem;color:#748078;margin-top:.2rem">'
        'Illustrative sample · not a live reading</div></div>')


def aqi_ring(aqi: float, category: str, size: int = 150) -> str:
    """Circular AQI gauge rendered with pure CSS/SVG (no external assets)."""
    color = category_color(category) if category else "#748078"
    pct = max(0.0, min(aqi / 500.0, 1.0))
    r = 62
    c = 2 * 3.14159 * r
    return (
        f'<div class="aw-aqi-ring" style="width:{size}px;height:{size}px">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 140 140">'
        f'<circle cx="70" cy="70" r="{r}" fill="none" stroke="#e7ecdf" '
        f'stroke-width="11"/>'
        f'<circle cx="70" cy="70" r="{r}" fill="none" stroke="{color}" '
        f'stroke-width="11" stroke-linecap="round" '
        f'stroke-dasharray="{c*pct:.1f} {c:.1f}"/>'
        f'</svg>'
        f'<div class="val"><div class="num" style="color:{color}">'
        f'{aqi:.0f}</div>'
        f'<div class="cat" style="color:{color}">'
        f'{html.escape(category)}</div></div></div>')


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


def nav_card(title: str, description: str, scene_name: str, icon_name: str,
             action_label: str, action_key: str, target_page: str,
             badge: str = "") -> None:
    """Image-led navigation card: illustration strip + copy + action."""
    badge_html = (f' <span class="aw-tag-soft">{html.escape(badge)}</span>'
                  if badge else "")
    st.markdown(
        f'<div class="aw-navcard">'
        f'<div class="art">{scene(scene_name)}</div>'
        f'<div class="body"><h4>{html.escape(title)}{badge_html}</h4>'
        f'<p>{html.escape(description)}</p>'
        f'<span class="go">{html.escape(action_label)} '
        f'{icon("arrow", 15)}</span></div></div>',
        unsafe_allow_html=True)
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


def timeline(items: list[tuple[str, str, str, str]]):
    """Vertical timeline. items: list of (when_label, title, body, icon)."""
    cells = []
    for when, title, body, ic in items:
        cells.append(
            f'<div class="aw-tstep">'
            f'<div class="when">{html.escape(when)}</div>'
            f'<h4>{html.escape(title)} '
            f'<span style="color:var(--evergreen)">{icon(ic, 18)}</span></h4>'
            f'<p>{html.escape(body)}</p></div>')
    st.markdown(f'<div class="aw-timeline">{"".join(cells)}</div>',
                unsafe_allow_html=True)


def showcase(title: str, points: list[str], scene_name: str,
             flip: bool = False) -> None:
    """Image-led showcase block: illustration + title + bullet points."""
    lis = "".join(
        f'<li>{icon("check", 16)}<span>{html.escape(p)}</span></li>'
        for p in points)
    st.markdown(
        f'<div class="aw-show{" aw-show--flip" if flip else ""}">'
        f'<div class="art">{scene(scene_name)}</div>'
        f'<div><div class="aw-eyebrow">AirAware</div>'
        f'<h3>{html.escape(title)}</h3><ul class="aw-show-points">{lis}</ul>'
        f'</div></div>',
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


def empty_state(message: str, icon_name: str = "wind"):
    st.markdown(
        f'<div class="aw-card" style="text-align:center;padding:2.4rem 1.6rem">'
        f'<div style="display:flex;justify-content:center;margin-bottom:.7rem">'
        f'{icon(icon_name, 36, "#A8BCA3")}</div>'
        f'<p style="color:var(--muted);max-width:52ch;margin:0 auto;'
        f'font-size:.95rem">{html.escape(message)}</p></div>',
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
