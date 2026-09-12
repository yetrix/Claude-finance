"""Financial Modeling Prep REST client. Additive fallback only — yfinance stays
the zero-key primary source everywhere; every function here returns None/[]
(never raises) when FMP_API_KEY is unset or a request fails, so callers can
unconditionally try FMP and fall back cleanly.

Auth: FMP's `apikey` is sent as a request header (not a query param), per FMP's
own current guidance for this key.
"""
from __future__ import annotations

from datetime import datetime

import requests
import streamlit as st

from lib.config import get_fmp_key

BASE_URL = "https://financialmodelingprep.com/stable"
TIMEOUT = 6


def _get(endpoint: str, params: dict | None = None) -> list | dict | None:
    key = get_fmp_key()
    if not key:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/{endpoint}",
            params=params or {},
            headers={"apikey": key},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except (requests.RequestException, ValueError):
        return None


def _parse_range(range_str: str | None) -> tuple[float | None, float | None]:
    if not range_str or "-" not in range_str:
        return None, None
    try:
        low, high = range_str.split("-")
        return float(low), float(high)
    except (ValueError, TypeError):
        return None, None


def _parse_published(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def get_quote(ticker: str) -> dict | None:
    """Normalized quote dict matching lib.market_data.get_quote's shape, or None
    if FMP is unavailable/unconfigured."""
    data = _get("quote", {"symbol": ticker})
    if not data:
        return None
    q = data[0]
    return {
        "symbol": q.get("symbol", ticker),
        "name": q.get("name") or ticker,
        "price": q.get("price"),
        "change": q.get("change"),
        "pct_change": q.get("changePercentage"),
        "previous_close": q.get("previousClose"),
        "volume": q.get("volume"),
    }


@st.cache_data(ttl=1800, show_spinner=False)
def get_profile(ticker: str) -> dict | None:
    data = _get("profile", {"symbol": ticker})
    if not data:
        return None
    return data[0]


@st.cache_data(ttl=1800, show_spinner=False)
def get_key_metrics_ttm(ticker: str) -> dict | None:
    data = _get("key-metrics-ttm", {"symbol": ticker})
    if not data:
        return None
    return data[0]


@st.cache_data(ttl=1800, show_spinner=False)
def get_ratios_ttm(ticker: str) -> dict | None:
    data = _get("ratios-ttm", {"symbol": ticker})
    if not data:
        return None
    return data[0]


@st.cache_data(ttl=1800, show_spinner=False)
def get_fundamentals(ticker: str) -> dict:
    """Best-effort fundamentals in the same field shape as
    lib.market_data.get_stock_fundamentals, built from FMP's profile + TTM
    metrics/ratios. Fields FMP doesn't expose (forward P/E, growth rates,
    analyst targets) are left None — callers merge this in only to fill gaps
    left by yfinance, never to overwrite it."""
    profile = get_profile(ticker) or {}
    metrics = get_key_metrics_ttm(ticker) or {}
    ratios = get_ratios_ttm(ticker) or {}
    low, high = _parse_range(profile.get("range"))

    debt_to_equity = ratios.get("debtToEquityRatioTTM")
    if debt_to_equity is not None:
        debt_to_equity *= 100  # normalize to the same percentage scale as yfinance's debtToEquity

    return {
        "name": profile.get("companyName"),
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
        "market_cap": profile.get("marketCap"),
        "trailing_pe": ratios.get("priceToEarningsRatioTTM"),
        "forward_pe": None,
        "peg_ratio": ratios.get("priceToEarningsGrowthRatioTTM"),
        "price_to_book": ratios.get("priceToBookRatioTTM"),
        "beta": profile.get("beta"),
        "dividend_yield": ratios.get("dividendYieldTTM"),
        "eps_ttm": ratios.get("netIncomePerShareTTM"),
        "revenue_ttm": None,
        "profit_margin": ratios.get("netProfitMarginTTM"),
        "roe": metrics.get("returnOnEquityTTM"),
        "debt_to_equity": debt_to_equity,
        "free_cash_flow": None,
        "fifty_two_wk_low": low,
        "fifty_two_wk_high": high,
        "avg_volume": profile.get("averageVolume"),
        "shares_outstanding": None,
        "revenue_growth": None,
        "earnings_growth": None,
        "target_mean_price": None,
        "recommendation_mean": None,
        "number_of_analysts": None,
        "business_summary": profile.get("description"),
    }


def _normalize_news_item(item: dict) -> dict:
    return {
        "title": item.get("title"),
        "link": item.get("url"),
        "publisher": item.get("publisher") or item.get("site") or "Unknown",
        "summary": item.get("text") or "",
        "published": _parse_published(item.get("publishedDate")),
    }


@st.cache_data(ttl=600, show_spinner=False)
def get_stock_news(ticker: str, limit: int = 10) -> list[dict]:
    data = _get("news/stock", {"symbols": ticker, "limit": limit})
    if not data:
        return []
    return [_normalize_news_item(item) for item in data if item.get("title")]


@st.cache_data(ttl=600, show_spinner=False)
def get_general_news(limit: int = 10) -> list[dict]:
    data = _get("news/general-latest", {"limit": limit})
    if not data:
        return []
    return [_normalize_news_item(item) for item in data if item.get("title")]
