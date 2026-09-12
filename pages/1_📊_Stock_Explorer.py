import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import market_data as md
from utils.ai_analysis import ask_claude, get_client
from utils.config import missing_key_message

st.set_page_config(page_title="Stock Explorer", page_icon="📊", layout="wide")
st.title("📊 Stock Explorer")

ticker = st.text_input("Ticker symbol", value="AAPL").strip().upper()
period = st.selectbox(
    "Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=2
)

if not ticker:
    st.stop()

with st.spinner(f"Loading {ticker}..."):
    hist = md.get_history(ticker, period=period)
    info = md.get_info(ticker)

if hist is None or hist.empty:
    st.error(f"No data found for '{ticker}'. Check the ticker symbol.")
    st.stop()

name = info.get("longName") or info.get("shortName") or ticker
st.subheader(f"{name} ({ticker})")

col1, col2, col3, col4 = st.columns(4)
last_close = hist["Close"].iloc[-1]
prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else last_close
change = last_close - prev_close
pct_change = (change / prev_close * 100) if prev_close else 0
col1.metric("Last Close", f"${last_close:,.2f}", f"{change:+.2f} ({pct_change:+.2f}%)")
col2.metric("Market Cap", f"${info.get('marketCap'):,}" if info.get("marketCap") else "N/A")
col3.metric("P/E (TTM)", f"{info.get('trailingPE'):.2f}" if info.get("trailingPE") else "N/A")
col4.metric("52W Range", f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}")

# Price chart
fig = go.Figure()
fig.add_trace(
    go.Candlestick(
        x=hist.index,
        open=hist["Open"],
        high=hist["High"],
        low=hist["Low"],
        close=hist["Close"],
        name=ticker,
    )
)
fig.update_layout(
    height=500,
    xaxis_rangeslider_visible=False,
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# Volume
vol_fig = go.Figure(go.Bar(x=hist.index, y=hist["Volume"], marker_color="steelblue"))
vol_fig.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10), title="Volume")
st.plotly_chart(vol_fig, use_container_width=True)

tabs = st.tabs(["Fundamentals", "Financials", "Dividends", "Analyst Ratings", "News", "AI Summary"])

with tabs[0]:
    fundamentals = {
        "Sector": info.get("sector"),
        "Industry": info.get("industry"),
        "Country": info.get("country"),
        "Full-Time Employees": info.get("fullTimeEmployees"),
        "Forward P/E": info.get("forwardPE"),
        "PEG Ratio": info.get("pegRatio"),
        "Price/Book": info.get("priceToBook"),
        "Dividend Yield": info.get("dividendYield"),
        "Beta": info.get("beta"),
        "EPS (TTM)": info.get("trailingEps"),
        "Revenue (TTM)": info.get("totalRevenue"),
        "Profit Margin": info.get("profitMargins"),
        "Return on Equity": info.get("returnOnEquity"),
        "Debt/Equity": info.get("debtToEquity"),
        "Free Cash Flow": info.get("freeCashflow"),
    }
    df_fund = pd.DataFrame(
        {"Metric": fundamentals.keys(), "Value": fundamentals.values()}
    )
    st.dataframe(df_fund, use_container_width=True, hide_index=True)
    if info.get("longBusinessSummary"):
        with st.expander("Business Summary"):
            st.write(info["longBusinessSummary"])

with tabs[1]:
    fin = md.get_financials(ticker)
    st.markdown("**Income Statement**")
    st.dataframe(fin["income_stmt"], use_container_width=True)
    st.markdown("**Balance Sheet**")
    st.dataframe(fin["balance_sheet"], use_container_width=True)
    st.markdown("**Cash Flow**")
    st.dataframe(fin["cashflow"], use_container_width=True)

with tabs[2]:
    divs = md.get_dividends(ticker)
    if divs is None or divs.empty:
        st.info("No dividend history for this ticker.")
    else:
        div_fig = go.Figure(go.Bar(x=divs.index, y=divs.values))
        div_fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(div_fig, use_container_width=True)
        st.dataframe(divs.sort_index(ascending=False), use_container_width=True)

with tabs[3]:
    st.caption(
        "Historical analyst ratings from data providers, shown for informational "
        "context only — not a recommendation from this app."
    )
    recs = md.get_recommendations(ticker)
    if recs is None or recs.empty:
        st.info("No analyst rating history available.")
    else:
        st.dataframe(recs, use_container_width=True)

with tabs[4]:
    news = md.get_news(ticker)
    if not news:
        st.info("No recent news found.")
    else:
        for item in news[:10]:
            content = item.get("content", item)
            title = content.get("title") or item.get("title")
            link = (content.get("canonicalUrl") or {}).get("url") or item.get("link")
            publisher = (content.get("provider") or {}).get("displayName") or item.get("publisher")
            if title:
                st.markdown(f"**[{title}]({link})**  \n*{publisher or ''}*")
                st.divider()

with tabs[5]:
    st.caption("Ask Claude to explain this data. Educational summaries only — no recommendations.")
    if get_client() is None:
        st.info(missing_key_message("anthropic"))
    else:
        default_q = f"Summarize {ticker}'s recent price action and key fundamentals in plain language."
        question = st.text_area("Question for Claude", value=default_q)
        if st.button("Ask Claude", type="primary"):
            with st.spinner("Thinking..."):
                snapshot = (
                    f"Ticker: {ticker} ({name})\n"
                    f"Last close: {last_close:.2f}, change: {pct_change:+.2f}%\n"
                    f"Sector: {info.get('sector')}, Industry: {info.get('industry')}\n"
                    f"P/E: {info.get('trailingPE')}, Forward P/E: {info.get('forwardPE')}\n"
                    f"Market cap: {info.get('marketCap')}\n"
                    f"52-week range: {info.get('fiftyTwoWeekLow')} - {info.get('fiftyTwoWeekHigh')}\n\n"
                    f"User question: {question}"
                )
                answer = ask_claude(snapshot)
                st.markdown(answer)
