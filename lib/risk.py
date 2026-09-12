"""ETF risk score (0-100): volatility + max drawdown + holdings concentration."""
from __future__ import annotations

import pandas as pd

RISK_BANDS = [
    (0, "Conservative"), (20, "Moderate"), (40, "Balanced"), (60, "Aggressive"), (80, "Very Aggressive"),
]


def _band(score: int) -> str:
    label = RISK_BANDS[0][1]
    for threshold, name in RISK_BANDS:
        if score >= threshold:
            label = name
    return label


def _linear_map(value: float, low: float, high: float) -> float:
    if high == low:
        return 0.0
    pct = (value - low) / (high - low) * 100
    return max(0.0, min(100.0, pct))


def compute_etf_risk_score(hist: pd.DataFrame, top_holdings: pd.DataFrame | None = None) -> dict:
    if hist is None or hist.empty or "Close" not in hist or len(hist) < 10:
        return {"score": None, "band": "Unknown", "volatility_pct": None, "max_drawdown_pct": None, "concentration_pct": None}

    close = hist["Close"].dropna()
    daily_returns = close.pct_change().dropna()
    ann_volatility_pct = float(daily_returns.std() * (252 ** 0.5) * 100) if not daily_returns.empty else 0.0

    running_max = close.cummax()
    drawdown = (close / running_max - 1) * 100
    max_drawdown_pct = float(abs(drawdown.min()))

    concentration_pct = None
    if top_holdings is not None and not top_holdings.empty:
        weight_col = None
        for candidate in ("Holding Percent", "holdingPercent", "% Assets", "weight"):
            if candidate in top_holdings.columns:
                weight_col = candidate
                break
        if weight_col:
            weights = top_holdings[weight_col].dropna()
            values = weights.values
            if len(values) and values.max() <= 1.5:
                values = values * 100
            concentration_pct = float(sum(values))

    vol_score = _linear_map(ann_volatility_pct, 10, 45)
    dd_score = _linear_map(max_drawdown_pct, 8, 55)
    conc_score = _linear_map(concentration_pct, 15, 75) if concentration_pct is not None else 50.0

    score = round(0.4 * vol_score + 0.3 * dd_score + 0.3 * conc_score)
    score = max(0, min(100, score))

    return {
        "score": score,
        "band": _band(score),
        "volatility_pct": round(ann_volatility_pct, 1),
        "max_drawdown_pct": round(max_drawdown_pct, 1),
        "concentration_pct": round(concentration_pct, 1) if concentration_pct is not None else None,
    }


def compute_portfolio_risk_score(value_series: pd.Series, weights: dict[str, float]) -> dict:
    """Same volatility/drawdown/concentration methodology as compute_etf_risk_score,
    applied to a blended portfolio value series and its per-holding weight mix."""
    if value_series is None or value_series.empty:
        return {"score": None, "band": "Unknown", "volatility_pct": None, "max_drawdown_pct": None, "concentration_pct": None}
    hist = pd.DataFrame({"Close": value_series})
    top_holdings = None
    if weights:
        top_holdings = pd.DataFrame({"Holding Percent": list(weights.values())}, index=list(weights.keys()))
    return compute_etf_risk_score(hist, top_holdings)
