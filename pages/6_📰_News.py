import streamlit as st

from lib.config import inject_base_style, render_disclosure
from lib.news import market_news, ticker_news, time_ago

st.set_page_config(page_title="News", page_icon="📰", layout="wide")
inject_base_style()
st.title("📰 News")

tabs = st.tabs(["Market Headlines", "By Ticker"])


def render_news_list(items: list[dict]):
    if not items:
        st.info("No news found.")
        return
    for item in items:
        st.markdown(f"**[{item['title']}]({item['link']})**")
        meta = item["publisher"]
        ago = time_ago(item["published"])
        if ago:
            meta += f" · {ago}"
        st.caption(meta)
        if item.get("summary"):
            summary = item["summary"]
            st.write(summary[:280] + ("..." if len(summary) > 280 else ""))
        st.divider()


with tabs[0]:
    with st.spinner("Loading market headlines..."):
        headlines = market_news(limit=20)
    render_news_list(headlines)

with tabs[1]:
    ticker = st.text_input("Ticker symbol", value="AAPL").strip().upper()
    if ticker:
        with st.spinner(f"Loading news for {ticker}..."):
            items = ticker_news(ticker, limit=20)
        render_news_list(items)

render_disclosure()
