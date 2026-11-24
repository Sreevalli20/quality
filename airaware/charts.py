"""Plotly chart helpers for air quality visualisation."""

from __future__ import annotations

import plotly.graph_objects as go

from .aqi import AqiResult, category_color

__all__ = ["category_color"]


def pollutant_bar_chart(result: AqiResult) -> go.Figure:
    """Bar chart of pollutant sub-indices with CPCB category bands."""
    fig = go.Figure()
    labels, values, colors = [], [], []
    max_si = max(r.sub_index for r in result.pollutant_results)
    for r in result.pollutant_results:
        labels.append(f"{r.pollutant.upper()}<br>{r.concentration:g} {r.unit}")
        values.append(r.sub_index)
        colors.append(category_color(result.category["name"]) if r.sub_index == max_si else "#7fb3a3")

    fig.add_trace(go.Bar(
        x=labels, y=values, marker_color=colors,
        text=[f"{v:.0f}" for v in values], textposition="outside",
        hovertemplate="%{x}<br>Sub-index: %{y:.0f}<extra></extra>",
    ))
    # Category band lines
    for bound, name in [(50, "Good"), (100, "Satisfactory"), (200, "Moderate"),
                        (300, "Poor"), (400, "Very Poor"), (500, "Severe")]:
        fig.add_hline(y=bound, line_dash="dot", line_color="#bbbbbb",
                      annotation_text=f"{name} ≤{bound}", annotation_position="bottom right")
    fig.update_layout(
        title="Pollutant sub-indices (CPCB method)",
        yaxis_title="Sub-index (AQI scale)",
        yaxis_range=[0, max(550, max(values) * 1.15 if values else 100)],
        height=380, margin=dict(t=50, b=80),
        plot_bgcolor="#fafaf7", paper_bgcolor="#ffffff",
        font=dict(color="#1c2b21"),
    )
    return fig


def aqi_gauge(aqi: float, category_name: str) -> go.Figure:
    """Semi-gauge showing the current AQI position on the CPCB scale."""
    color = category_color(category_name)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=aqi,
        number={"suffix": "", "font": {"size": 48}},
        title={"text": f"AQI - {category_name}", "font": {"size": 18}},
        gauge={
            "axis": {"range": [0, 500], "tickwidth": 1},
            "bar": {"color": color, "thickness": 0.35},
            "bgcolor": "#efede6",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "#dff0d8"},
                {"range": [50, 100], "color": "#f0f7d8"},
                {"range": [100, 200], "color": "#fdf6d8"},
                {"range": [200, 300], "color": "#fde8d4"},
                {"range": [300, 400], "color": "#fbd3d3"},
                {"range": [400, 500], "color": "#f3c4c4"},
            ],
            "threshold": {
                "line": {"color": "#7f0000", "width": 3},
                "thickness": 0.8, "value": min(aqi, 500),
            },
        },
    ))
    fig.update_layout(height=280, margin=dict(t=60, b=20, l=40, r=40),
                      paper_bgcolor="#ffffff")
    return fig


def outlook_chart(outlook) -> go.Figure:
    """Band chart of the day-ahead planning outlook.

    Shows estimated AQI *category* positions per time window with an
    uncertainty band - deliberately NOT hourly AQI values, because the
    outlook is a labelled planning estimate, not a measured forecast.
    """
    from .forecast import CAT_ORDER
    cat_pos = {name: i for i, name in enumerate(CAT_ORDER)}

    labels = [w.label for w in outlook.windows]
    mids = [w.cat_mid_idx for w in outlook.windows]
    los = [cat_pos[w.cat_low] for w in outlook.windows]
    his = [cat_pos[w.cat_high] for w in outlook.windows]
    colors = [category_color(CAT_ORDER[min(max(round(m), 0),
                        len(CAT_ORDER) - 1)]) for m in mids]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels + labels[::-1],
        y=his + los[::-1],
        fill="toself", fillcolor="rgba(36,91,70,0.10)",
        line=dict(color="rgba(36,91,70,0.25)"),
        hoverinfo="skip", showlegend=False, name="likely range"))
    fig.add_trace(go.Scatter(
        x=labels, y=mids, mode="lines+markers+text",
        text=[w.cat_high if w.cat_low != w.cat_high
              else w.cat_low for w in outlook.windows],
        textposition="top center", textfont=dict(size=11),
        marker=dict(color=colors, size=11, line=dict(color="#fff", width=2)),
        line=dict(color="#245B46", width=2),
        hovertemplate="%{x}<br>likely %{text}<extra></extra>",
        name="planning estimate"))
    # Category boundary gridlines (integer indices = category edges).
    for i, name in enumerate(CAT_ORDER):
        fig.add_hline(y=i - 0.5, line_dash="dot",
                      line_color="#d8dcd0" if i else "#c9cfc0",
                      annotation_text=name, annotation_position="left",
                      annotation_font=dict(size=10, color="#6d7f72"))
    fig.update_layout(
        title="Planning outlook - likely AQI category by time window",
        yaxis=dict(range=[-0.6, len(CAT_ORDER) - 0.4],
                   tickvals=list(range(len(CAT_ORDER))),
                   ticktext=CAT_ORDER, showgrid=False),
        xaxis=dict(tickangle=-25),
        height=360, margin=dict(t=60, b=90, l=90, r=30),
        plot_bgcolor="#fafaf7", paper_bgcolor="#ffffff",
        font=dict(color="#1c2b21"),
        showlegend=False)
    return fig


def comparison_bar(measurements: list) -> go.Figure:
    """Bar chart comparing AQI across a set of measurements."""
    labels = [m.location if len(m.location) <= 22 else m.location[:20] + "..."
              for m in measurements]
    values = [m.display_aqi or 0 for m in measurements]
    colors = [category_color(m.category_name) for m in measurements]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors,
                           text=[f"{v:.0f}" for v in values], textposition="outside"))
    fig.update_layout(title="AQI comparison", yaxis_title="AQI",
                      height=320, margin=dict(t=50, b=100),
                      plot_bgcolor="#fafaf7", paper_bgcolor="#ffffff",
                      font=dict(color="#1c2b21"))
    return fig
