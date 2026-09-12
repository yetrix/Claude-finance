"""yfinance wrappers: quotes, history, ETF/stock metadata. All calls cached with @st.cache_data."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf

from lib import fmp

# --- Reference data -------------------------------------------------------

INDEX_TICKERS = [
    {"symbol": "^GSPC", "label": "S&P 500"},
    {"symbol": "^NDX", "label": "Nasdaq 100"},
    {"symbol": "^DJI", "label": "Dow Jones"},
    {"symbol": "^RUT", "label": "Russell 2000"},
    {"symbol": "^VIX", "label": "VIX"},
    {"symbol": "^TNX", "label": "10Y Yield"},
    {"symbol": "GC=F", "label": "Gold"},
    {"symbol": "CL=F", "label": "Crude WTI"},
    {"symbol": "BTC-USD", "label": "Bitcoin"},
    {"symbol": "DX-Y.NYB", "label": "US Dollar Index"},
]

SECTOR_ETFS = [
    {"symbol": "XLK", "label": "Technology"},
    {"symbol": "XLF", "label": "Financials"},
    {"symbol": "XLV", "label": "Health Care"},
    {"symbol": "XLE", "label": "Energy"},
    {"symbol": "XLI", "label": "Industrials"},
    {"symbol": "XLY", "label": "Consumer Discretionary"},
    {"symbol": "XLP", "label": "Consumer Staples"},
    {"symbol": "XLU", "label": "Utilities"},
    {"symbol": "XLRE", "label": "Real Estate"},
    {"symbol": "XLB", "label": "Materials"},
    {"symbol": "XLC", "label": "Communication Services"},
]

# label -> {interval, and one of days / ytd / max}
PERIOD_MAP = {
    "1D": {"days": 1, "interval": "5m"},
    "5D": {"days": 5, "interval": "15m"},
    "1M": {"days": 30, "interval": "1d"},
    "3M": {"days": 90, "interval": "1d"},
    "6M": {"days": 182, "interval": "1d"},
    "YTD": {"ytd": True, "interval": "1d"},
    "1Y": {"days": 365, "interval": "1d"},
    "3Y": {"days": 365 * 3, "interval": "1wk"},
    "5Y": {"days": 365 * 5, "interval": "1wk"},
    "10Y": {"days": 365 * 10, "interval": "1mo"},
    "20Y": {"days": 365 * 20, "interval": "1mo"},
    "30Y": {"days": 365 * 30, "interval": "1mo"},
    "Max": {"max": True, "interval": "1mo"},
}


# --- History ---------------------------------------------------------------


@st.cache_data(ttl=300, show_spinner=False)
def get_history(ticker: str, period_label: str = "6M") -> pd.DataFrame:
    """Fetch OHLCV history for a single ticker over one of the PERIOD_MAP windows.
    Falls back to FMP (if a key is configured) when yfinance comes back empty —
    e.g. on cloud hosts where Yahoo Finance blocks shared data-center IPs."""
    cfg = PERIOD_MAP.get(period_label, PERIOD_MAP["6M"])
    interval = cfg["interval"]
    hist = pd.DataFrame()
    try:
        tk = yf.Ticker(ticker)
        if cfg.get("max"):
            hist = tk.history(period="max", interval=interval)
        elif cfg.get("ytd"):
            hist = tk.history(start=date(date.today().year, 1, 1), interval=interval)
        else:
            start = date.today() - timedelta(days=cfg["days"])
            hist = tk.history(start=start, interval=interval)
        hist = hist if hist is not None else pd.DataFrame()
    except Exception:
        hist = pd.DataFrame()

    if hist.empty:
        hist = fmp.get_history(ticker, period_label)

    return hist


@st.cache_data(ttl=300, show_spinner=False)
def get_prev_close(ticker: str) -> float | None:
    """Yesterday's close, used as the 1D chart baseline (not today's first bar)."""
    daily = pd.DataFrame()
    try:
        daily = yf.Ticker(ticker).history(period="5d", interval="1d")
        daily = daily if daily is not None else pd.DataFrame()
    except Exception:
        daily = pd.DataFrame()

    if len(daily) < 2:
        daily = fmp.get_daily_history(ticker, days=5)

    if daily is None or daily.empty or len(daily) < 2:
        return None
    try:
        return float(daily["Close"].iloc[-2])
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def get_history_bulk(tickers: tuple[str, ...], period_label: str = "6M") -> dict[str, pd.DataFrame]:
    return {t: get_history(t, period_label) for t in tickers}


# --- Quotes ------------------------------------------------------------------


def _safe_fi_get(fi, *keys):
    """fast_info is a lazy proxy — reading a property can itself raise (e.g. on a
    delisted ticker or incomplete Yahoo metadata), not just accessing fast_info
    itself. Never let a single bad field take down the whole quote."""
    for key in keys:
        try:
            value = fi.get(key)
        except Exception:
            value = None
        if value is not None:
            return value
    return None


@st.cache_data(ttl=60, show_spinner=False)
def get_quote(ticker: str) -> dict:
    """Lightweight current quote: price, change, pct_change, previous_close, name.
    Never raises — degrades to None fields so one bad ticker can't break a page."""
    try:
        tk = yf.Ticker(ticker)
        try:
            fi = tk.fast_info or {}
        except Exception:
            fi = {}
        price = _safe_fi_get(fi, "lastPrice", "last_price")
        prev_close = _safe_fi_get(fi, "previousClose", "previous_close")
        volume = _safe_fi_get(fi, "lastVolume", "last_volume")
        if price is None or prev_close is None:
            hist = get_history(ticker, "5D")
            if hist is not None and not hist.empty:
                price = price if price is not None else float(hist["Close"].iloc[-1])
                prev_close = prev_close if prev_close is not None else (
                    float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
                )
        name = None
        try:
            name = tk.info.get("shortName") or tk.info.get("longName")
        except Exception:
            pass

        if price is None:
            # yfinance came up empty (rate-limited, delisted, network hiccup) —
            # fall back to FMP if the user has configured a key. fmp.get_quote
            # returns None on any failure, so this is always safe to try.
            fmp_quote = fmp.get_quote(ticker)
            if fmp_quote:
                return {**fmp_quote, "symbol": ticker, "name": fmp_quote.get("name") or name or ticker}

        change = (price - prev_close) if (price is not None and prev_close is not None) else None
        pct_change = (change / prev_close * 100) if (change is not None and prev_close) else None
        return {
            "symbol": ticker,
            "name": name or ticker,
            "price": price,
            "change": change,
            "pct_change": pct_change,
            "previous_close": prev_close,
            "volume": volume,
        }
    except Exception:
        fmp_quote = fmp.get_quote(ticker)
        if fmp_quote:
            return {**fmp_quote, "symbol": ticker}
        return {
            "symbol": ticker, "name": ticker, "price": None, "change": None,
            "pct_change": None, "previous_close": None, "volume": None,
        }


@st.cache_data(ttl=60, show_spinner=False)
def get_quotes_bulk(tickers: tuple[str, ...]) -> dict[str, dict]:
    result = {}
    for t in tickers:
        try:
            result[t] = get_quote(t)
        except Exception:
            result[t] = {
                "symbol": t, "name": t, "price": None, "change": None,
                "pct_change": None, "previous_close": None, "volume": None,
            }
    return result


# --- Fundamentals / ETF metadata --------------------------------------------


@st.cache_data(ttl=900, show_spinner=False)
def get_info(ticker: str) -> dict:
    tk = yf.Ticker(ticker)
    try:
        return tk.info or {}
    except Exception:
        return {}


def is_etf(ticker: str) -> bool:
    info = get_info(ticker)
    qtype = (info.get("quoteType") or "").upper()
    return qtype == "ETF"


@st.cache_data(ttl=900, show_spinner=False)
def get_stock_fundamentals(ticker: str) -> dict:
    info = get_info(ticker)
    fundamentals = {
        "name": info.get("longName") or info.get("shortName") or ticker,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "price_to_book": info.get("priceToBook"),
        "beta": info.get("beta"),
        "dividend_yield": info.get("dividendYield"),
        "eps_ttm": info.get("trailingEps"),
        "revenue_ttm": info.get("totalRevenue"),
        "profit_margin": info.get("profitMargins"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "free_cash_flow": info.get("freeCashflow"),
        "fifty_two_wk_low": info.get("fiftyTwoWeekLow"),
        "fifty_two_wk_high": info.get("fiftyTwoWeekHigh"),
        "avg_volume": info.get("averageVolume"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "target_mean_price": info.get("targetMeanPrice"),
        "recommendation_mean": info.get("recommendationMean"),
        "number_of_analysts": info.get("numberOfAnalystOpinions"),
        "business_summary": info.get("longBusinessSummary"),
    }

    # Fill gaps (never overwrite) from FMP if a key is configured. yfinance
    # remains authoritative — FMP just patches holes (e.g. yfinance's .info
    # missing fields, or empty entirely on a bad fetch).
    if any(v is None for v in fundamentals.values()):
        fmp_fundamentals = fmp.get_fundamentals(ticker)
        for key, value in fmp_fundamentals.items():
            if fundamentals.get(key) is None and value is not None:
                fundamentals[key] = value

    return fundamentals


@st.cache_data(ttl=1800, show_spinner=False)
def get_etf_details(ticker: str) -> dict:
    info = get_info(ticker)
    tk = yf.Ticker(ticker)
    sector_weights, top_holdings = None, None
    try:
        fd = tk.funds_data
        sector_weights = fd.sector_weightings
        top_holdings = fd.top_holdings
    except Exception:
        pass
    return {
        "name": info.get("longName") or info.get("shortName") or ticker,
        "category": info.get("category"),
        "fund_family": info.get("fundFamily"),
        "total_assets": info.get("totalAssets"),
        "expense_ratio": info.get("annualReportExpenseRatio") or info.get("netExpenseRatio"),
        "nav_price": info.get("navPrice"),
        "beta_3y": info.get("beta3Year"),
        "ytd_return": info.get("ytdReturn"),
        "three_year_avg_return": info.get("threeYearAverageReturn"),
        "five_year_avg_return": info.get("fiveYearAverageReturn"),
        "business_summary": info.get("longBusinessSummary"),
        "sector_weights": sector_weights,
        "top_holdings": top_holdings,
    }


@st.cache_data(ttl=600, show_spinner=False)
def get_movers_universe() -> list[str]:
    """A fixed, reasonably liquid universe used to derive gainers/losers/most-active
    since yfinance has no live screener endpoint."""
    return [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "BRK-B", "LLY",
        "JPM", "V", "XOM", "UNH", "MA", "COST", "HD", "PG", "NFLX", "JNJ",
        "ABBV", "CRM", "BAC", "ORCL", "MRK", "CVX", "KO", "AMD", "PEP", "ADBE",
        "WMT", "TMO", "MCD", "CSCO", "ABT", "LIN", "ACN", "GE", "IBM", "PM",
        "TXN", "INTU", "QCOM", "CAT", "AMGN", "DHR", "NOW", "ISRG", "VZ", "NEE",
    ]
