"""Treasury yield curve helpers, built on the same FRED client as lib.macro."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib.macro import get_raw_series

# (maturity label, FRED series id, sort order in years for the x-axis)
YIELD_CURVE_SERIES = [
    ("1M", "DGS1MO", 1 / 12),
    ("3M", "DGS3MO", 3 / 12),
    ("6M", "DGS6MO", 6 / 12),
    ("1Y", "DGS1", 1),
    ("2Y", "DGS2", 2),
    ("3Y", "DGS3", 3),
    ("5Y", "DGS5", 5),
    ("7Y", "DGS7", 7),
    ("10Y", "DGS10", 10),
    ("20Y", "DGS20", 20),
    ("30Y", "DGS30", 30),
]


@st.cache_data(ttl=3600, show_spinner=False)
def get_yield_curve_snapshot() -> pd.DataFrame:
    """Latest available yield for each maturity on the curve."""
    rows = []
    for label, series_id, years in YIELD_CURVE_SERIES:
        s = get_raw_series(series_id).dropna()
        if s.empty:
            continue
        rows.append({"Maturity": label, "Years": years, "Yield": float(s.iloc[-1]), "Date": s.index[-1]})
    return pd.DataFrame(rows).sort_values("Years") if rows else pd.DataFrame(columns=["Maturity", "Years", "Yield", "Date"])


@st.cache_data(ttl=3600, show_spinner=False)
def get_yield_curve_snapshot_years_ago(years_ago: int = 1) -> pd.DataFrame:
    """Same curve as of ~N years ago, for a comparison overlay."""
    import pandas as pd

    rows = []
    for label, series_id, years in YIELD_CURVE_SERIES:
        s = get_raw_series(series_id).dropna()
        if s.empty:
            continue
        cutoff = s.index[-1] - pd.DateOffset(years=years_ago)
        past = s[s.index <= cutoff]
        if past.empty:
            continue
        rows.append({"Maturity": label, "Years": years, "Yield": float(past.iloc[-1]), "Date": past.index[-1]})
    return pd.DataFrame(rows).sort_values("Years") if rows else pd.DataFrame(columns=["Maturity", "Years", "Yield", "Date"])
