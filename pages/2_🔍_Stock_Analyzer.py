import streamlit as st

from lib.charts import VIEWS, render_gauge, render_price_chart
from lib.claude_analyst import bull_bear_case, deep_analysis, get_client
from lib.config import missing_key_message, inject_base_style, render_disclosure
from lib.logos import render_logo_html
from lib.market_data import get_history, get_prev_close, get_stock_fundamentals
from lib.news import ticker_news, time_ago
from lib.signals import build_at_a_glance_chips, fundamental_score, technical_score

st.set_page_config(page_title="Stock Analyzer", page_icon="🔍", layout="wide")
inject_base_style()
st.title("🔍 Stock Analyzer")

c1, c2 = st.columns([3, 2])
ticker = c1.text_input("Ticker symbol", value="AAPL").strip().upper()
period = c2.segmented_control(
    "Period", ["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y", "10Y", "20Y", "30Y", "Max"], default="6M"
)
period = period or "6M"

if not ticker:
    st.stop()

with st.spinner(f"Loading {ticker}..."):
    fundamentals = get_stock_fundamentals(ticker)
    hist = get_history(ticker, period)
    baseline = get_prev_close(ticker) if period == "1D" else None

if hist is None or hist.empty:
    st.error(f"No price data found for '{ticker}'. Check the ticker symbol.")
    st.stop()

# --- Header -------------------------------------------------------------------

last_price = float(hist["Close"].iloc[-1])
header_cols = st.columns([1, 5])
with header_cols[0]:
    st.markdown(render_logo_html(ticker, size=64), unsafe_allow_html=True)
with header_cols[1]:
    st.subheader(f"{fundamentals['name']} ({ticker})")
    sub = " · ".join(x for x in [fundamentals.get("sector"), fundamentals.get("industry")] if x)
    if sub:
        st.caption(sub)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Price", f"${last_price:,.2f}")
mcap = fundamentals.get("market_cap")
m2.metric("Market Cap", f"${mcap:,}" if mcap else "N/A")
pe = fundamentals.get("trailing_pe")
m3.metric("Trailing P/E", f"{pe:.2f}" if pe else "N/A")
beta = fundamentals.get("beta")
m4.metric("Beta", f"{beta:.2f}" if beta else "N/A")

st.divider()

# --- Big chart ------------------------------------------------------------------

view = st.radio("View", VIEWS, horizontal=True, key="stock_view")
fig = render_price_chart(hist, view=view, baseline_price=baseline, height=480, show_volume=True)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Snapshot ---------------------------------------------------------------------

st.subheader("Snapshot")
st.caption(
    "A descriptive, factual summary of price and fundamental data. Not a recommendation "
    "to buy, sell, or hold."
)

tech = technical_score(hist)
fund = fundamental_score(fundamentals)
chips = build_at_a_glance_chips(hist, fundamentals)

snap_cols = st.columns(3)

with snap_cols[0]:
    st.markdown("**At a Glance**")
    with st.container(border=True):
        for chip in chips:
            st.markdown(f"**{chip['label']}:** {chip['value']}")

with snap_cols[1]:
    st.markdown("**Technical Strength**")
    st.caption("Trend, momentum, position vs averages")
    st.plotly_chart(render_gauge(tech["score"]), use_container_width=True, config={"displayModeBar": False})
    st.markdown(f"<div style='text-align:center;font-size:1.4em;font-weight:700;'>{tech['score']}/100</div>", unsafe_allow_html=True)
    for d in tech["drivers"]:
        st.markdown(f"- {d}")

with snap_cols[2]:
    st.markdown("**Fundamental Quality**")
    st.caption("Margins, returns, leverage, growth")
    st.plotly_chart(render_gauge(fund["score"]), use_container_width=True, config={"displayModeBar": False})
    st.markdown(f"<div style='text-align:center;font-size:1.4em;font-weight:700;'>{fund['score']}/100</div>", unsafe_allow_html=True)
    for d in fund["drivers"]:
        st.markdown(f"- {d}")

st.divider()

# --- Key statistics grid -----------------------------------------------------------

st.subheader("Key Statistics")


def stat_card(title: str, rows: list[tuple[str, str]]):
    with st.container(border=True):
        st.markdown(f"**{title}**")
        for label, value in rows:
            st.markdown(f"<div style='display:flex;justify-content:space-between;'><span style='color:#999;'>{label}</span><span>{value}</span></div>", unsafe_allow_html=True)


def fmt(value, kind="num", suffix=""):
    if value is None:
        return "N/A"
    if kind == "pct":
        return f"{value * 100:.2f}%"
    if kind == "money":
        return f"${value:,.0f}"
    if kind == "num":
        return f"{value:,.2f}{suffix}"
    return str(value)


stat_cols = st.columns(3)
with stat_cols[0]:
    stat_card("Valuation", [
        ("Trailing P/E", fmt(fundamentals.get("trailing_pe"))),
        ("Forward P/E", fmt(fundamentals.get("forward_pe"))),
        ("PEG Ratio", fmt(fundamentals.get("peg_ratio"))),
        ("Price/Book", fmt(fundamentals.get("price_to_book"))),
    ])
    stat_card("Balance Sheet", [
        ("Debt/Equity", fmt(fundamentals.get("debt_to_equity"))),
        ("Free Cash Flow", fmt(fundamentals.get("free_cash_flow"), "money")),
    ])
with stat_cols[1]:
    stat_card("Profitability", [
        ("Profit Margin", fmt(fundamentals.get("profit_margin"), "pct")),
        ("Return on Equity", fmt(fundamentals.get("roe"), "pct")),
        ("Revenue Growth", fmt(fundamentals.get("revenue_growth"), "pct")),
        ("Earnings Growth", fmt(fundamentals.get("earnings_growth"), "pct")),
    ])
    stat_card("Income", [
        ("EPS (TTM)", fmt(fundamentals.get("eps_ttm"))),
        ("Revenue (TTM)", fmt(fundamentals.get("revenue_ttm"), "money")),
        ("Dividend Yield", fmt(fundamentals.get("dividend_yield"), "pct")),
    ])
with stat_cols[2]:
    stat_card("Trading", [
        ("Beta", fmt(fundamentals.get("beta"))),
        ("Avg Volume", fmt(fundamentals.get("avg_volume"), "money")),
        ("52W Range", f"${fmt(fundamentals.get('fifty_two_wk_low'))} - ${fmt(fundamentals.get('fifty_two_wk_high'))}"),
    ])
    st.caption("Analyst figures below are third-party data shown for informational context — not this app's recommendation.")
    stat_card("Analyst (Third-Party Data)", [
        ("Mean Target Price", fmt(fundamentals.get("target_mean_price"))),
        ("Recommendation Mean", fmt(fundamentals.get("recommendation_mean"))),
        ("# Analysts", str(fundamentals.get("number_of_analysts") or "N/A")),
    ])

if fundamentals.get("business_summary"):
    with st.expander("Business Summary"):
        st.write(fundamentals["business_summary"])

st.divider()

# --- AI analysis tabs -----------------------------------------------------------

st.subheader("AI Analysis")
tabs = st.tabs(["Bull/Bear Case", "Deep Analysis", "Recent Headlines"])

with tabs[0]:
    if get_client() is None:
        st.info(missing_key_message("anthropic"))
    else:
        st.caption("A summary of arguments each side of the market might make — not a recommendation.")
        if st.button("Generate Bull/Bear Case", key="bull_bear_btn"):
            with st.spinner("Thinking..."):
                st.markdown(bull_bear_case(ticker, fundamentals["name"], fundamentals, tech))

with tabs[1]:
    if get_client() is None:
        st.info(missing_key_message("anthropic"))
    else:
        if st.button("Generate Deep Analysis", key="deep_analysis_btn"):
            with st.spinner("Analyzing..."):
                headlines = [h["title"] for h in ticker_news(ticker, limit=5)]
                st.markdown(deep_analysis(ticker, fundamentals["name"], fundamentals, tech, headlines))

with tabs[2]:
    news_items = ticker_news(ticker, limit=10)
    if not news_items:
        st.info("No recent news found.")
    else:
        for item in news_items:
            st.markdown(f"**[{item['title']}]({item['link']})**")
            meta = item["publisher"]
            ago = time_ago(item["published"])
            if ago:
                meta += f" · {ago}"
            st.caption(meta)
            st.divider()

render_disclosure()
