"""Descriptive technical/fundamental scoring for the Stock Analyzer Snapshot panel.

IMPORTANT: these are 0-100 composite scores and neutral factual buckets, never
buy/sell/hold signals. Language must stay descriptive ("Firm momentum", "Higher
than market") — never prescriptive ("Buy", "Sell", "Should").
"""
from __future__ import annotations

import pandas as pd


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _rsi_bucket(rsi_value: float) -> str:
    if rsi_value < 30:
        return "Soft momentum"
    if rsi_value < 45:
        return "Cooling momentum"
    if rsi_value < 55:
        return "Neutral momentum"
    if rsi_value < 70:
        return "Firm momentum"
    return "Strong momentum"


def _range_bucket(position_pct: float) -> str:
    if position_pct < 20:
        return "Near 52-week low"
    if position_pct < 40:
        return "Lower range"
    if position_pct < 60:
        return "Mid-range"
    if position_pct < 80:
        return "Upper range"
    return "Near 52-week high"


def _beta_bucket(beta: float | None) -> str:
    if beta is None:
        return "Unknown"
    if beta < 0.8:
        return "Lower than market"
    if beta <= 1.2:
        return "In line with market"
    return "Higher than market"


def technical_score(hist: pd.DataFrame) -> dict:
    """Composite 0-100 technical strength score from trend, momentum, and 52-week
    range position. Returns score, bucket labels, and factual driver bullets."""
    empty = {
        "score": 50, "trend_bucket": "Unknown", "momentum_bucket": "Unknown",
        "range_bucket": "Unknown", "range_position_pct": None, "rsi": None, "drivers": [],
    }
    if hist is None or hist.empty or len(hist) < 5:
        return empty

    close = hist["Close"].dropna()
    if close.empty:
        return empty

    last_price = float(close.iloc[-1])
    drivers = []

    sma200 = close.rolling(200).mean()
    sma50 = close.rolling(50).mean()
    has_sma200 = not sma200.dropna().empty
    has_sma50 = not sma50.dropna().empty

    if has_sma200:
        above_200 = last_price > sma200.iloc[-1]
        above_50 = has_sma50 and last_price > sma50.iloc[-1]
        golden = has_sma50 and sma50.iloc[-1] > sma200.iloc[-1]
        if above_200 and golden:
            trend_component, trend_bucket = 90, "Above 200-day average"
        elif above_200:
            trend_component, trend_bucket = 70, "Above 200-day average"
        elif above_50:
            trend_component, trend_bucket = 40, "Below 200-day average"
        else:
            trend_component, trend_bucket = 15, "Below 200-day average"
        drivers.append(f"Price {'above' if above_200 else 'below'} 200-day moving average")
    else:
        trend_component, trend_bucket = 50, "Unknown"

    rsi_series = compute_rsi(close)
    rsi_value = float(rsi_series.iloc[-1])
    momentum_bucket = _rsi_bucket(rsi_value)
    momentum_component = rsi_value
    drivers.append(f"RSI(14) at {rsi_value:.0f} — {momentum_bucket.lower()}")

    period_high = float(close.max())
    period_low = float(close.min())
    if period_high > period_low:
        range_position_pct = (last_price - period_low) / (period_high - period_low) * 100
    else:
        range_position_pct = 50.0
    range_bucket = _range_bucket(range_position_pct)
    drivers.append(f"Trading in the {range_bucket.lower()} of its range ({range_position_pct:.0f}th percentile)")

    score = round(0.4 * trend_component + 0.3 * momentum_component + 0.3 * range_position_pct)
    score = max(0, min(100, score))

    return {
        "score": score,
        "trend_bucket": trend_bucket,
        "momentum_bucket": momentum_bucket,
        "range_bucket": range_bucket,
        "range_position_pct": round(range_position_pct, 1),
        "rsi": round(rsi_value, 1),
        "drivers": drivers,
    }


def _tier(value: float | None, thresholds: list[tuple[float, int, str]], default=(50, "Unknown")) -> tuple[int, str]:
    """thresholds: list of (min_value, score, label) sorted ascending; picks the
    highest threshold value does not exceed... actually picks last matching min."""
    if value is None:
        return default
    result = default
    for min_val, score, label in thresholds:
        if value >= min_val:
            result = (score, label)
    return result


def fundamental_score(fundamentals: dict) -> dict:
    """Composite 0-100 fundamental quality score from profitability, leverage,
    valuation, and growth. Returns score, bucket labels, and driver bullets."""
    roe = fundamentals.get("roe")
    margin = fundamentals.get("profit_margin")
    de = fundamentals.get("debt_to_equity")
    pe = fundamentals.get("trailing_pe")
    rev_growth = fundamentals.get("revenue_growth")
    earn_growth = fundamentals.get("earnings_growth")

    drivers = []

    roe_score, roe_label = _tier(
        roe * 100 if roe is not None else None,
        [(-1000, 10, "Negative returns"), (0, 35, "Low returns"), (8, 60, "Moderate returns"),
         (15, 80, "Strong returns"), (25, 95, "High returns")],
    )
    if roe is not None:
        drivers.append(f"Return on equity {roe * 100:.1f}% — {roe_label.lower()}")

    margin_score, margin_label = _tier(
        margin * 100 if margin is not None else None,
        [(-1000, 10, "Negative margin"), (0, 35, "Thin margin"), (10, 60, "Moderate margin"),
         (20, 80, "Healthy margin"), (30, 95, "High margin")],
    )
    if margin is not None:
        drivers.append(f"Profit margin {margin * 100:.1f}% — {margin_label.lower()}")

    leverage_score, leverage_label = _tier(
        de,
        [(0, 85, "Low leverage"), (50, 65, "Moderate leverage"), (100, 40, "Elevated leverage"), (200, 20, "High leverage")],
    )
    if de is not None:
        drivers.append(f"Debt/equity {de:.0f} — {leverage_label.lower()}")

    if pe is not None and pe > 0:
        valuation_score, valuation_label = _tier(
            pe, [(0, 80, "Low multiple"), (15, 60, "Moderate multiple"), (25, 40, "Higher multiple"), (40, 20, "High multiple")],
        )
        drivers.append(f"Trailing P/E {pe:.1f} — {valuation_label.lower()}")
    else:
        valuation_score, valuation_label = 50, "Not meaningful"

    growth_values = [g for g in (rev_growth, earn_growth) if g is not None]
    if growth_values:
        avg_growth_pct = sum(growth_values) / len(growth_values) * 100
        growth_score, growth_label = _tier(
            avg_growth_pct,
            [(-1000, 15, "Contracting"), (0, 40, "Flat"), (5, 60, "Growing"), (15, 80, "Fast-growing"), (30, 95, "Very fast-growing")],
        )
        drivers.append(f"Average growth {avg_growth_pct:.1f}% — {growth_label.lower()}")
    else:
        growth_score = 50

    score = round(0.25 * roe_score + 0.15 * margin_score + 0.2 * leverage_score + 0.2 * valuation_score + 0.2 * growth_score)
    score = max(0, min(100, score))

    return {
        "score": score,
        "profitability_bucket": roe_label,
        "leverage_bucket": leverage_label,
        "valuation_bucket": valuation_label,
        "drivers": drivers,
    }


def build_at_a_glance_chips(hist: pd.DataFrame, fundamentals: dict) -> list[dict]:
    """The 7 neutral-language chips for the 'At a glance' card."""
    tech = technical_score(hist)
    fund = fundamental_score(fundamentals)
    beta_bucket = _beta_bucket(fundamentals.get("beta"))
    return [
        {"label": "Trend", "value": tech["trend_bucket"]},
        {"label": "Momentum", "value": tech["momentum_bucket"]},
        {"label": "52-Week Range", "value": tech["range_bucket"]},
        {"label": "Profitability", "value": fund["profitability_bucket"]},
        {"label": "Leverage", "value": fund["leverage_bucket"]},
        {"label": "Volatility", "value": beta_bucket},
        {"label": "Valuation", "value": fund["valuation_bucket"]},
    ]
