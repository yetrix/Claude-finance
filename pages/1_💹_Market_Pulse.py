import streamlit as st

from lib.charts import VIEWS, render_price_chart, render_sparkline
from lib.config import APP_ICON, inject_base_style, render_disclosure
from lib.logos import render_logo_html
from lib.market_data import (
    INDEX_TICKERS,
    SECTOR_ETFS,
    get_history,
    get_history_bulk,
    get_movers_universe,
    get_prev_close,
    get_quotes_bulk,
)
from lib.news import market_news, time_ago

st.set_page_config(page_title="Market Pulse", page_icon="💹", layout="wide")
inject_base_style()
st.title("💹 Market Pulse")

PERIOD_LABELS = ["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y", "10Y", "20Y", "30Y", "Max"]
period = st.segmented_control("Period", PERIOD_LABELS, default="1D")
period = period or "1D"

# --- Index/asset cards -------------------------------------------------------

index_symbols = tuple(t["symbol"] for t in INDEX_TICKERS)
with st.spinner("Loading market data..."):
    quotes = get_quotes_bulk(index_symbols)
    hist_map = get_history_bulk(index_symbols, period)

cols = st.columns(5)
for i, t in enumerate(INDEX_TICKERS):
    symbol = t["symbol"]
    q = quotes.get(symbol, {})
    hist = hist_map.get(symbol)
    baseline = get_prev_close(symbol) if period == "1D" else None
    with cols[i % 5]:
        with st.container(border=True):
            price = q.get("price")
            pct = q.get("pct_change")
            st.caption(t["label"])
            st.markdown(f"**{price:,.2f}**" if price is not None else "**N/A**")
            if pct is not None:
                color = "green" if pct >= 0 else "red"
                st.markdown(f":{color}[{pct:+.2f}%]")
            fig = render_sparkline(hist, baseline_price=baseline, height=60)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"spark_{symbol}")

st.divider()

# --- Big S&P 500 chart --------------------------------------------------------

st.subheader("S&P 500")
view = st.radio("View", VIEWS, horizontal=True, key="spx_view")
spx_hist = get_history("^GSPC", period)
spx_baseline = get_prev_close("^GSPC") if period == "1D" else None
fig = render_price_chart(spx_hist, view=view, baseline_price=spx_baseline, height=450, show_volume=True)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Sector heatmap -----------------------------------------------------------

st.subheader("Sector Performance")
sector_symbols = tuple(s["symbol"] for s in SECTOR_ETFS)
with st.spinner("Loading sectors..."):
    sector_quotes = get_quotes_bulk(sector_symbols)

import plotly.graph_objects as go

sector_rows = sorted(
    ({"label": s["label"], "symbol": s["symbol"], "pct": sector_quotes.get(s["symbol"], {}).get("pct_change") or 0.0} for s in SECTOR_ETFS),
    key=lambda r: r["pct"],
)
heat_fig = go.Figure(
    go.Bar(
        x=[r["pct"] for r in sector_rows],
        y=[r["label"] for r in sector_rows],
        orientation="h",
        marker_color=["#2ecc71" if r["pct"] >= 0 else "#e74c3c" for r in sector_rows],
        text=[f"{r['pct']:+.2f}%" for r in sector_rows],
        textposition="outside",
    )
)
heat_fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=40, t=10, b=10), xaxis_title="% Change")
st.plotly_chart(heat_fig, use_container_width=True)

st.divider()

# --- Gainers / Losers / Most Active -------------------------------------------

st.subheader("Movers")
universe = get_movers_universe()
with st.spinner("Scanning movers..."):
    mover_quotes = get_quotes_bulk(tuple(universe))

rows = [
    {"symbol": sym, **q} for sym, q in mover_quotes.items()
    if q.get("pct_change") is not None
]
gainers = sorted(rows, key=lambda r: r["pct_change"], reverse=True)[:8]
losers = sorted(rows, key=lambda r: r["pct_change"])[:8]
most_active = sorted([r for r in rows if r.get("volume")], key=lambda r: r["volume"], reverse=True)[:8]


def render_mover_list(items: list[dict]):
    for r in items:
        logo_html = render_logo_html(r["symbol"], size=28)
        color = "#2ecc71" if r["pct_change"] >= 0 else "#e74c3c"
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:6px 0;">'
            f'{logo_html}'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="font-weight:600;">{r["symbol"]}</div>'
            f'<div style="font-size:0.8em;color:#999;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{r["name"]}</div>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<div>${r["price"]:.2f}</div>'
            f'<div style="color:{color};">{r["pct_change"]:+.2f}%</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )


c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**📈 Top Gainers**")
    render_mover_list(gainers)
with c2:
    st.markdown("**📉 Top Losers**")
    render_mover_list(losers)
with c3:
    st.markdown("**🔥 Most Active**")
    render_mover_list(most_active)

st.divider()

# --- Headlines -----------------------------------------------------------------

st.subheader("Top Headlines")
with st.spinner("Loading news..."):
    headlines = market_news(limit=3)

if not headlines:
    st.info("No recent headlines available.")
else:
    for h in headlines:
        st.markdown(f"**[{h['title']}]({h['link']})**")
        meta = h["publisher"]
        ago = time_ago(h["published"])
        if ago:
            meta += f" · {ago}"
        st.caption(meta)
        if h.get("summary"):
            summary = h["summary"]
            st.write(summary[:220] + ("..." if len(summary) > 220 else ""))
        st.divider()

render_disclosure()
