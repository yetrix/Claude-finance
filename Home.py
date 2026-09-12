import streamlit as st

st.set_page_config(page_title="Stock Market Analyst", page_icon="📈", layout="wide")

st.title("📈 Stock Market Analyst")

st.warning(
    "**Educational & personal-research use only.** This dashboard does not give "
    "buy/sell/hold recommendations. All data and any AI commentary are for "
    "informational purposes and should not be treated as financial advice.",
    icon="⚠️",
)

st.markdown(
    """
Welcome to your personal stock market dashboard. Use the sidebar to navigate:

- **📊 Stock Explorer** — price charts, fundamentals, financials, and news for any ticker
- **🧺 ETF Explorer** — ETF holdings, sector weights, and metadata
- **🌐 Macro Dashboard** — inflation, rates, unemployment, and other FRED indicators
- **💼 My Portfolio** — track a personal watchlist stored locally on this machine
- **🤖 AI Analysis** — ask Claude to explain and summarize data you've pulled up

### Setup
This app reads API keys from a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_key_here
FRED_API_KEY=your_key_here
```

`yfinance` requires no API key. If a key is missing, the relevant page will show a
friendly notice instead of an error.
"""
)
