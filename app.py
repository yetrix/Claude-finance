import streamlit as st

from lib.charts import render_price_chart
from lib.config import APP_ICON, APP_NAME, inject_base_style, render_disclosure
from lib.market_data import INDEX_TICKERS, get_history, get_prev_close, get_quotes_bulk

st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide")
inject_base_style()

st.title(f"{APP_ICON} {APP_NAME}")

st.warning(
    "**Educational & personal-research use only.** This dashboard does not give "
    "buy/sell/hold recommendations. All data and any AI commentary are for "
    "informational purposes only.",
    icon="⚠️",
)

st.subheader("Quick Market Snapshot")

symbols = tuple(t["symbol"] for t in INDEX_TICKERS)
with st.spinner("Loading quotes..."):
    quotes = get_quotes_bulk(symbols)

cols = st.columns(5)
for i, t in enumerate(INDEX_TICKERS):
    q = quotes.get(t["symbol"], {})
    price = q.get("price")
    pct = q.get("pct_change")
    with cols[i % 5]:
        if price is None:
            st.metric(t["label"], "N/A")
        else:
            st.metric(t["label"], f"{price:,.2f}", f"{pct:+.2f}%" if pct is not None else None)

st.divider()
st.subheader("S&P 500")
with st.spinner("Loading chart..."):
    spx_hist = get_history("^GSPC", "1D")
    baseline = get_prev_close("^GSPC")
fig = render_price_chart(spx_hist, view="Area", baseline_price=baseline, height=400)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.markdown(
    """
Use the sidebar to navigate:

- **💹 Market Pulse** — indices, sector heatmap, movers, and headlines
- **🔍 Stock Analyzer** — price charts, fundamentals, and AI-generated summaries for any ticker
- **🧺 ETF Analyzer** — holdings, sector weights, risk, and cost comparisons
- **🌍 Macro** — inflation, rates, unemployment, and the yield curve (FRED)
- **💼 Portfolio** — track a personal watchlist stored locally on this machine
- **📰 News** — aggregated market headlines and by-ticker search

### Setup
This app reads API keys from a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_key_here
FRED_API_KEY=your_key_here
```

`yfinance` requires no API key. If a key is missing, the relevant page shows a
friendly notice instead of an error.
"""
)

render_disclosure()
