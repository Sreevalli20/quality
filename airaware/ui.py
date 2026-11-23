"""Shared UI helpers: CSS, cards, badges, section headers."""

from __future__ import annotations

import streamlit as st

from .aqi import category_color

_CSS = """
<style>
:root { --ink:#1c2b21; --muted:#5a6b60; --line:#e3e0d5; --card:#ffffff;
        --accent:#0f5132; --accent2:#147a55; }
.stApp { background:#f7f6f1; }
h1,h2,h3 { color:var(--ink); letter-spacing:-0.01em; }
.aw-card { background:var(--card); border:1px solid var(--line);
           border-radius:14px; padding:1.1rem 1.25rem; margin-bottom:1rem;
           box-shadow:0 1px 2px rgba(20,40,30,.04); }
.aw-card h4 { margin:0 0 .4rem 0; color:var(--accent); font-size:1.05rem; }
.aw-card p { margin:.15rem 0; color:var(--muted); font-size:.92rem; }
.aw-badge { display:inline-block; padding:.18rem .6rem; border-radius:999px;
            font-size:.78rem; font-weight:600; color:#fff; }
.aw-meta { font-size:.78rem; color:var(--muted); }
.aw-hero { background:linear-gradient(135deg,#0f5132 0%,#147a55 60%,#1b8a5a 100%);
           color:#fff; border-radius:16px; padding:1.6rem 1.8rem; margin-bottom:1.2rem; }
.aw-hero h1 { color:#fff; margin:0 0 .3rem 0; }
.aw-hero p { color:#dff0e6; margin:.2rem 0; }
.aw-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
           gap:.9rem; }
.aw-kpi { background:#fff; border:1px solid var(--line); border-radius:12px;
          padding:.9rem 1rem; text-align:center; }
.aw-kpi .v { font-size:1.5rem; font-weight:700; color:var(--accent); }
.aw-kpi .l { font-size:.75rem; color:var(--muted); text-transform:uppercase;
             letter-spacing:.05em; }
.aw-reason { font-size:.8rem; color:var(--muted); font-style:italic; }
hr.aw-hr { border:none; border-top:1px solid var(--line); margin:1.2rem 0; }
.block-container { padding-top:1.6rem; }
@media (max-width:640px){ .aw-hero{padding:1.2rem} }
</style>
"""


def apply_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str = "", extra: str = ""):
    inner = f"<h1>{title}</h1><p>{subtitle}</p>"
    if extra:
        inner += f"<p>{extra}</p>"
    st.markdown(f'<div class="aw-hero">{inner}</div>', unsafe_allow_html=True)


def section_header(title: str, caption: str = ""):
    st.markdown(f"### {title}")
    if caption:
        st.caption(caption)


def card(title: str, body_html: str = "", body_text: str = ""):
    html = f'<div class="aw-card"><h4>{title}</h4>'
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
    st.markdown('<hr class="aw-hr">', unsafe_allow_html=True)


def empty_state(message: str):
    st.info(message)
