import streamlit as st

from utils import market_data as md
from utils.ai_analysis import ask_claude, get_client
from utils.config import missing_key_message

st.set_page_config(page_title="AI Analysis", page_icon="🤖", layout="wide")
st.title("🤖 AI Analysis")

st.info(
    "Claude explains and summarizes data here for educational purposes only. "
    "It will not provide buy/sell/hold recommendations or price targets.",
    icon="ℹ️",
)

if get_client() is None:
    st.warning(missing_key_message("anthropic"))
    st.stop()

ticker = st.text_input("Ticker to analyze (optional)", value="").strip().upper()
question = st.text_area(
    "What would you like Claude to explain?",
    value="Explain the recent performance and key fundamentals of this stock in plain language.",
    height=120,
)

if st.button("Ask Claude", type="primary"):
    context = ""
    if ticker:
        with st.spinner(f"Fetching {ticker} data..."):
            info = md.get_info(ticker)
            hist = md.get_history(ticker, period="6mo")
        if info:
            last_close = hist["Close"].iloc[-1] if hist is not None and not hist.empty else None
            context = (
                f"Ticker: {ticker} ({info.get('longName', ticker)})\n"
                f"Sector: {info.get('sector')}, Industry: {info.get('industry')}\n"
                f"Last close: {last_close}\n"
                f"Market cap: {info.get('marketCap')}\n"
                f"P/E: {info.get('trailingPE')}, Forward P/E: {info.get('forwardPE')}\n"
                f"Dividend yield: {info.get('dividendYield')}\n"
                f"52-week range: {info.get('fiftyTwoWeekLow')} - {info.get('fiftyTwoWeekHigh')}\n\n"
            )
        else:
            st.warning(f"Couldn't find data for '{ticker}', asking without it.")

    with st.spinner("Thinking..."):
        answer = ask_claude(context + f"User question: {question}")
    st.markdown(answer)
