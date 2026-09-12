"""Claude-powered descriptive analysis. Bull/bear "case" prompts are framed as
opposing scenarios/arguments for educational purposes, never as a recommendation
to act on either one."""
from __future__ import annotations

from lib.config import get_anthropic_key

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "You are a financial data explainer embedded in a personal, educational stock "
    "market dashboard. Your job is to explain and contextualize data the user "
    "already has in front of them: trends, what metrics mean, and factors other "
    "market participants weigh. You must NEVER give investment advice, price "
    "targets, or buy/sell/hold recommendations, and never tell the user what "
    "they should do. When asked for a 'bull case' or 'bear case', present it "
    "explicitly as a summary of arguments each side of the market might make — "
    "not your own endorsement or recommendation, and always include both sides. "
    "Use neutral, descriptive language. If asked directly for a recommendation, "
    "explain that this tool is educational only and does not provide one. Keep "
    "responses concise and well-structured with short paragraphs or bullets."
)


def get_client():
    key = get_anthropic_key()
    if not key:
        return None
    import anthropic

    return anthropic.Anthropic(api_key=key)


def _ask(prompt: str, max_tokens: int = 1200) -> str:
    client = get_client()
    if client is None:
        return ""
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
    except Exception as e:
        return f"⚠️ AI analysis unavailable: {e}"


def bull_bear_case(ticker: str, name: str, fundamentals: dict, technical: dict) -> str:
    prompt = (
        f"Ticker: {ticker} ({name})\n"
        f"Sector: {fundamentals.get('sector')}, Industry: {fundamentals.get('industry')}\n"
        f"Trailing P/E: {fundamentals.get('trailing_pe')}, Forward P/E: {fundamentals.get('forward_pe')}\n"
        f"ROE: {fundamentals.get('roe')}, Profit margin: {fundamentals.get('profit_margin')}\n"
        f"Debt/Equity: {fundamentals.get('debt_to_equity')}, Beta: {fundamentals.get('beta')}\n"
        f"Revenue growth: {fundamentals.get('revenue_growth')}, Earnings growth: {fundamentals.get('earnings_growth')}\n"
        f"Technical strength score (0-100): {technical.get('score')}, "
        f"Trend: {technical.get('trend_bucket')}, Momentum: {technical.get('momentum_bucket')}\n\n"
        "Summarize the bull case (arguments optimistic observers might make) and the "
        "bear case (arguments skeptical observers might make) for this company based "
        "on the data above. Two clearly labeled sections, 3-4 bullets each. This is "
        "not a recommendation for either side."
    )
    return _ask(prompt)


def deep_analysis(ticker: str, name: str, fundamentals: dict, technical: dict, headlines: list[str]) -> str:
    headline_block = "\n".join(f"- {h}" for h in headlines[:5]) if headlines else "None available"
    prompt = (
        f"Ticker: {ticker} ({name})\n"
        f"Sector: {fundamentals.get('sector')}, Industry: {fundamentals.get('industry')}\n"
        f"Market cap: {fundamentals.get('market_cap')}\n"
        f"Valuation: P/E {fundamentals.get('trailing_pe')}, Forward P/E {fundamentals.get('forward_pe')}, "
        f"PEG {fundamentals.get('peg_ratio')}, P/B {fundamentals.get('price_to_book')}\n"
        f"Profitability: ROE {fundamentals.get('roe')}, Margin {fundamentals.get('profit_margin')}\n"
        f"Balance sheet: Debt/Equity {fundamentals.get('debt_to_equity')}, FCF {fundamentals.get('free_cash_flow')}\n"
        f"Technicals: Score {technical.get('score')}/100, Trend {technical.get('trend_bucket')}, "
        f"Momentum {technical.get('momentum_bucket')}, Range position {technical.get('range_bucket')}\n"
        f"Recent headlines:\n{headline_block}\n\n"
        "Write a structured, educational deep-dive covering: (1) business/valuation "
        "context, (2) profitability and balance-sheet quality, (3) technical/price "
        "context, (4) what the recent headlines add. Plain language, factual tone, "
        "no recommendation."
    )
    return _ask(prompt, max_tokens=1600)


def macro_pulse_check(indicators: dict) -> str:
    lines = []
    for label, data in indicators.items():
        if data.get("value") is not None:
            lines.append(f"{label}: {data['value']:.2f}{data.get('unit', '')} (as of {data.get('date')})")
    prompt = (
        "Current macro indicator readings:\n" + "\n".join(lines) + "\n\n"
        "Explain what these readings suggest about the current phase of the "
        "economic cycle, inflation trajectory, and monetary policy stance, in "
        "plain language. Educational context only, not investment advice."
    )
    return _ask(prompt)


def portfolio_deep_analysis(holdings_summary: str) -> str:
    prompt = (
        f"Portfolio holdings:\n{holdings_summary}\n\n"
        "Explain this portfolio's composition: sector/asset concentration, "
        "apparent diversification level, and general risk characteristics implied "
        "by the mix. Educational context only — do not suggest changes to the "
        "portfolio or recommend buying/selling/rebalancing anything."
    )
    return _ask(prompt, max_tokens=1400)
