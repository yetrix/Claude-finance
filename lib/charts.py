"""Shared plotly chart rendering: performance/price/candlestick/area views with
green/red baseline splitting, optional volume overlay, and dark theme throughout."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

POSITIVE_COLOR = "#2ecc71"
NEGATIVE_COLOR = "#e74c3c"
NEUTRAL_COLOR = "#3498db"

VIEWS = ["Performance", "Price", "Candlestick", "Area"]


def _interpolate_crossing(x0, y0, x1, y1, baseline):
    if y1 == y0:
        return x0, baseline
    t = (baseline - y0) / (y1 - y0)
    if isinstance(x0, pd.Timestamp):
        x_cross = pd.Timestamp(int(x0.value + t * (x1.value - x0.value)))
    else:
        x_cross = x0 + t * (x1 - x0)
    return x_cross, baseline


def split_traces(x, y, baseline: float = 0.0) -> list[dict]:
    """Split a line into contiguous segments above/below `baseline`, inserting
    linearly-interpolated crossing points so segments join with no visual gap.
    Returns a list of {"x": [...], "y": [...], "positive": bool}."""
    x = list(x)
    y = list(y)
    n = len(x)
    if n == 0:
        return []
    segments = []
    cur_x, cur_y = [x[0]], [y[0]]
    cur_sign = y[0] >= baseline
    for i in range(1, n):
        prev_sign = y[i - 1] >= baseline
        this_sign = y[i] >= baseline
        if this_sign != prev_sign:
            xc, yc = _interpolate_crossing(x[i - 1], y[i - 1], x[i], y[i], baseline)
            cur_x.append(xc)
            cur_y.append(yc)
            segments.append({"x": cur_x, "y": cur_y, "positive": prev_sign})
            cur_x, cur_y = [xc, x[i]], [yc, y[i]]
            cur_sign = this_sign
        else:
            cur_x.append(x[i])
            cur_y.append(y[i])
    segments.append({"x": cur_x, "y": cur_y, "positive": cur_sign})
    return segments


def render_sparkline(hist: pd.DataFrame, baseline_price: float | None = None, height: int = 60) -> go.Figure:
    """Minimal axis-free line for card grids. Splits green/red at `baseline_price`
    (or the period's first close if not given) exactly like the main chart."""
    fig = go.Figure()
    if hist is None or hist.empty or "Close" not in hist:
        fig.update_layout(template="plotly_dark", height=height, margin=dict(l=0, r=0, t=0, b=0),
                           xaxis_visible=False, yaxis_visible=False)
        return fig

    close = hist["Close"]
    start_price = float(baseline_price) if baseline_price is not None else float(close.iloc[0])
    for seg in split_traces(hist.index, close.tolist(), baseline=start_price):
        color = POSITIVE_COLOR if seg["positive"] else NEGATIVE_COLOR
        fig.add_trace(
            go.Scatter(x=seg["x"], y=seg["y"], mode="lines", line=dict(color=color, width=1.5),
                       showlegend=False, hoverinfo="skip")
        )
    fig.update_layout(
        template="plotly_dark", height=height, margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False,
    )
    return fig


def render_gauge(score: float | None, height: int = 220) -> go.Figure:
    """0-100 needle-style gauge with a red-to-green band, shared by the Stock
    Analyzer's technical/fundamental scores and the ETF risk score."""
    display_value = score if score is not None else 0
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=display_value,
            number={"suffix": "" if score is not None else " (N/A)", "font": {"size": 34}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.5)"},
                "bar": {"color": "rgba(0,0,0,0)"},
                "bgcolor": "rgba(0,0,0,0)",
                "steps": [
                    {"range": [0, 20], "color": "#e74c3c"},
                    {"range": [20, 40], "color": "#e67e22"},
                    {"range": [40, 60], "color": "#f1c40f"},
                    {"range": [60, 80], "color": "#9acd32"},
                    {"range": [80, 100], "color": "#2ecc71"},
                ],
                "threshold": {"line": {"color": "white", "width": 4}, "thickness": 0.9, "value": display_value},
            },
        )
    )
    fig.update_layout(template="plotly_dark", height=height, margin=dict(l=20, r=20, t=30, b=10))
    return fig


def _empty_figure(height: int, message: str = "No data available") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=14, color="#888"))
    fig.update_layout(template="plotly_dark", height=height, xaxis_visible=False, yaxis_visible=False)
    return fig


def render_price_chart(
    hist: pd.DataFrame,
    view: str = "Performance",
    baseline_price: float | None = None,
    title: str | None = None,
    height: int = 480,
    show_volume: bool = False,
) -> go.Figure:
    """Render one of the 4 chart views for a single ticker's OHLCV history.

    baseline_price: for 1D charts, pass yesterday's close so overnight gaps
    don't distort the green/red split or % return badge.
    """
    if hist is None or hist.empty or "Close" not in hist:
        return _empty_figure(height)

    x = hist.index
    close = hist["Close"]
    start_price = float(baseline_price) if baseline_price is not None else float(close.iloc[0])
    last_price = float(close.iloc[-1])
    pct_return = (last_price / start_price - 1) * 100 if start_price else 0.0
    badge_color = POSITIVE_COLOR if pct_return >= 0 else NEGATIVE_COLOR

    price_traces = []
    badge_y = last_price
    yaxis_title = "Price"

    if view == "Performance":
        y_pct = ((close / start_price) - 1) * 100
        for seg in split_traces(x, y_pct.tolist(), baseline=0.0):
            color = POSITIVE_COLOR if seg["positive"] else NEGATIVE_COLOR
            price_traces.append(
                go.Scatter(x=seg["x"], y=seg["y"], mode="lines", line=dict(color=color, width=2), showlegend=False)
            )
        badge_y = float(y_pct.iloc[-1])
        yaxis_title = "% Change"

    elif view == "Area":
        for seg in split_traces(x, close.tolist(), baseline=start_price):
            color = POSITIVE_COLOR if seg["positive"] else NEGATIVE_COLOR
            fillcolor = "rgba(46,204,113,0.15)" if seg["positive"] else "rgba(231,76,60,0.15)"
            price_traces.append(
                go.Scatter(
                    x=seg["x"], y=[start_price] * len(seg["x"]),
                    mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
                )
            )
            price_traces.append(
                go.Scatter(
                    x=seg["x"], y=seg["y"], mode="lines", line=dict(color=color, width=2),
                    fill="tonexty", fillcolor=fillcolor, showlegend=False,
                )
            )

    elif view == "Candlestick":
        price_traces.append(
            go.Candlestick(
                x=x, open=hist["Open"], high=hist["High"], low=hist["Low"], close=hist["Close"],
                increasing_line_color=POSITIVE_COLOR, decreasing_line_color=NEGATIVE_COLOR, showlegend=False,
            )
        )

    else:  # Price
        price_traces.append(go.Scatter(x=x, y=close, mode="lines", line=dict(color=NEUTRAL_COLOR, width=2), showlegend=False))

    if show_volume and "Volume" in hist:
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03,
        )
        for tr in price_traces:
            fig.add_trace(tr, row=1, col=1)
        vol_colors = [POSITIVE_COLOR if c >= o else NEGATIVE_COLOR for o, c in zip(hist["Open"], hist["Close"])]
        fig.add_trace(
            go.Bar(x=x, y=hist["Volume"], marker_color=vol_colors, showlegend=False, opacity=0.6),
            row=2, col=1,
        )
        fig.update_yaxes(title_text=yaxis_title, row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
    else:
        fig = go.Figure(data=price_traces)
        fig.update_yaxes(title_text=yaxis_title)
        fig.update_xaxes(rangeslider_visible=False)

    if view == "Performance":
        fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)", row=1 if show_volume else None,
                       col=1 if show_volume else None)

    fig.add_annotation(
        x=x[-1], y=badge_y, text=f" {pct_return:+.2f}% ", showarrow=False, xanchor="left", xshift=8,
        font=dict(color="#0b0f19", size=12, family="Arial Black"), bgcolor=badge_color, bordercolor=badge_color,
        borderwidth=1, borderpad=3, row=1 if show_volume else None, col=1 if show_volume else None,
    )

    fig.update_layout(
        template="plotly_dark",
        height=height,
        title=title,
        margin=dict(l=10, r=60, t=40 if title else 20, b=10),
        hovermode="x unified",
    )
    return fig
