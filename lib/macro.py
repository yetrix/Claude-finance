"""FRED macro indicator helpers."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib.config import get_fred_key

# label -> {series_id, transform, unit}
INDICATORS: dict[str, dict] = {
    "GDP": {"series_id": "GDP", "transform": None, "unit": "$B"},
    "Unemployment Rate": {"series_id": "UNRATE", "transform": None, "unit": "%"},
    "CPI YoY": {"series_id": "CPIAUCSL", "transform": "yoy_pct", "unit": "%"},
    "Core CPI YoY": {"series_id": "CPILFESL", "transform": "yoy_pct", "unit": "%"},
    "Fed Funds Rate": {"series_id": "FEDFUNDS", "transform": None, "unit": "%"},
    "10Y-2Y Spread": {"series_id": "T10Y2Y", "transform": None, "unit": "%"},
    "Retail Sales": {"series_id": "RSAFS", "transform": None, "unit": "$M"},
    "Industrial Production": {"series_id": "INDPRO", "transform": None, "unit": "Index"},
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
def get_raw_series(series_id: str) -> pd.Series:
    key = get_fred_key()
    if not key:
        return pd.Series(dtype=float)
    from fredapi import Fred

    try:
        fred = Fred(api_key=key)
        return fred.get_series(series_id)
    except Exception:
        return pd.Series(dtype=float)


def _apply_transform(series: pd.Series, transform: str | None) -> pd.Series:
    if series is None or series.empty or transform is None:
        return series
    if transform == "yoy_pct":
        return series.pct_change(periods=12) * 100
    return series


@st.cache_data(ttl=3600, show_spinner=False)
def get_indicator_series(label: str) -> pd.Series:
    spec = INDICATORS.get(label)
    if not spec:
        return pd.Series(dtype=float)
    raw = get_raw_series(spec["series_id"])
    return _apply_transform(raw, spec["transform"]).dropna()


def get_indicator_latest(label: str) -> dict:
    series = get_indicator_series(label)
    if series is None or series.empty:
        return {"value": None, "date": None, "unit": INDICATORS.get(label, {}).get("unit", "")}
    return {
        "value": float(series.iloc[-1]),
        "date": series.index[-1],
        "unit": INDICATORS.get(label, {}).get("unit", ""),
    }
