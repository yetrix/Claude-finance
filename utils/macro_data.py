"""FRED macro indicator helpers."""
import pandas as pd
import streamlit as st

from utils.config import get_fred_key

# label -> FRED series id
MACRO_SERIES = {
    "CPI (Inflation)": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Fed Funds Rate": "FEDFUNDS",
    "10-Year Treasury Yield": "DGS10",
    "GDP": "GDP",
    "Real GDP": "GDPC1",
    "Consumer Sentiment": "UMCSENT",
    "Retail Sales": "RSAFS",
    "Industrial Production": "INDPRO",
    "10Y-2Y Treasury Spread": "T10Y2Y",
}


def get_fred_client():
    key = get_fred_key()
    if not key:
        return None
    from fredapi import Fred

    try:
        return Fred(api_key=key)
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_series(series_id: str) -> pd.Series:
    key = get_fred_key()
    if not key:
        return pd.Series(dtype=float)
    from fredapi import Fred

    try:
        fred = Fred(api_key=key)
        return fred.get_series(series_id)
    except Exception:
        return pd.Series(dtype=float)
