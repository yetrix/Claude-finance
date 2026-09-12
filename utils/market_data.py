"""Thin caching wrappers around yfinance."""
import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=300, show_spinner=False)
def get_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    tk = yf.Ticker(ticker)
    hist = tk.history(period=period, interval=interval)
    return hist


@st.cache_data(ttl=900, show_spinner=False)
def get_info(ticker: str) -> dict:
    tk = yf.Ticker(ticker)
    try:
        return tk.info or {}
    except Exception:
        return {}


@st.cache_data(ttl=900, show_spinner=False)
def get_fast_info(ticker: str) -> dict:
    tk = yf.Ticker(ticker)
    try:
        fi = tk.fast_info
        return dict(fi) if fi else {}
    except Exception:
        return {}


@st.cache_data(ttl=1800, show_spinner=False)
def get_financials(ticker: str) -> dict:
    tk = yf.Ticker(ticker)
    out = {}
    for name, attr in (
        ("income_stmt", "income_stmt"),
        ("balance_sheet", "balance_sheet"),
        ("cashflow", "cashflow"),
    ):
        try:
            out[name] = getattr(tk, attr)
        except Exception:
            out[name] = pd.DataFrame()
    return out


@st.cache_data(ttl=1800, show_spinner=False)
def get_dividends(ticker: str) -> pd.Series:
    tk = yf.Ticker(ticker)
    try:
        return tk.dividends
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=600, show_spinner=False)
def get_news(ticker: str) -> list:
    tk = yf.Ticker(ticker)
    try:
        return tk.news or []
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def get_recommendations(ticker: str) -> pd.DataFrame:
    """Analyst rating history from yfinance (informational only, not our own recommendation)."""
    tk = yf.Ticker(ticker)
    try:
        return tk.recommendations if tk.recommendations is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def get_major_holders(ticker: str) -> pd.DataFrame:
    tk = yf.Ticker(ticker)
    try:
        return tk.major_holders if tk.major_holders is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def is_valid_ticker(ticker: str) -> bool:
    if not ticker:
        return False
    hist = get_history(ticker, period="5d")
    return hist is not None and not hist.empty
