import pandas as pd
import plotly.express as go
import plotly.graph_objects as pgo
import streamlit as st
import yfinance as yf

from utils import market_data as md

st.set_page_config(page_title="ETF Explorer", page_icon="🧺", layout="wide")
st.title("🧺 ETF Explorer")

ticker = st.text_input("ETF ticker symbol", value="SPY").strip().upper()

if not ticker:
    st.stop()

with st.spinner(f"Loading {ticker}..."):
    hist = md.get_history(ticker, period="1y")
    info = md.get_info(ticker)
    tk = yf.Ticker(ticker)

if hist is None or hist.empty:
    st.error(f"No data found for '{ticker}'. Check the ticker symbol.")
    st.stop()

name = info.get("longName") or info.get("shortName") or ticker
st.subheader(f"{name} ({ticker})")

col1, col2, col3, col4 = st.columns(4)
last_close = hist["Close"].iloc[-1]
col1.metric("Last Close", f"${last_close:,.2f}")
col2.metric("Total Assets (AUM)", f"${info.get('totalAssets'):,}" if info.get("totalAssets") else "N/A")
col3.metric("Expense Ratio", f"{info.get('annualReportExpenseRatio', 0) * 100:.2f}%" if info.get("annualReportExpenseRatio") else "N/A")
col4.metric("Yield", f"{info.get('yield', 0) * 100:.2f}%" if info.get("yield") else "N/A")

price_fig = pgo.Figure(pgo.Scatter(x=hist.index, y=hist["Close"], mode="lines"))
price_fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10), title="1-Year Price")
st.plotly_chart(price_fig, use_container_width=True)

tabs = st.tabs(["Sector Weights", "Top Holdings", "Fund Details"])

with tabs[0]:
    try:
        sector_weights = tk.funds_data.sector_weightings if hasattr(tk, "funds_data") else None
    except Exception:
        sector_weights = None
    if sector_weights:
        df_sector = pd.DataFrame(
            {"Sector": list(sector_weights.keys()), "Weight": list(sector_weights.values())}
        ).sort_values("Weight", ascending=False)
        pie = go.pie(df_sector, names="Sector", values="Weight", title="Sector Allocation")
        st.plotly_chart(pie, use_container_width=True)
        st.dataframe(df_sector, use_container_width=True, hide_index=True)
    else:
        st.info("Sector weighting data not available for this ETF from the data provider.")

with tabs[1]:
    try:
        top_holdings = tk.funds_data.top_holdings if hasattr(tk, "funds_data") else None
    except Exception:
        top_holdings = None
    if top_holdings is not None and not top_holdings.empty:
        st.dataframe(top_holdings, use_container_width=True)
    else:
        st.info("Top holdings data not available for this ETF from the data provider.")

with tabs[2]:
    details = {
        "Category": info.get("category"),
        "Fund Family": info.get("fundFamily"),
        "Inception Date": info.get("fundInceptionDate"),
        "Total Assets": info.get("totalAssets"),
        "Expense Ratio": info.get("annualReportExpenseRatio"),
        "NAV Price": info.get("navPrice"),
        "Beta (3Y)": info.get("beta3Year"),
        "YTD Return": info.get("ytdReturn"),
        "3Y Avg Return": info.get("threeYearAverageReturn"),
        "5Y Avg Return": info.get("fiveYearAverageReturn"),
    }
    df_details = pd.DataFrame({"Field": details.keys(), "Value": details.values()})
    st.dataframe(df_details, use_container_width=True, hide_index=True)
    if info.get("longBusinessSummary"):
        with st.expander("Fund Description"):
            st.write(info["longBusinessSummary"])
