# Stock Market Analyst

A personal Streamlit dashboard for exploring stocks, ETFs, and macro
indicators, with optional AI-generated explanations via Claude.

**Educational and personal-research use only.** This app does not provide
buy/sell/hold recommendations or investment advice. Its "Technical strength"
and "Fundamental quality" scores are descriptive composites, not signals.

## Features

- **Market Pulse** — indices/assets with sparklines, a big S&P 500 chart,
  sector heatmap, gainers/losers/most-active, and top headlines
- **Stock Analyzer** — price charts, a factual "Snapshot" panel (technical/
  fundamental gauges + neutral-language chips), key statistics, and
  Claude-generated bull/bear case and deep-dive summaries
- **ETF Analyzer** — holdings, sector weights, a risk gauge, and a peer cost
  comparison with a cheaper-alternative callout
- **Macro** — CPI, unemployment, Fed funds rate, the Treasury yield curve,
  and more via FRED, plus a Claude macro pulse-check
- **Portfolio** — a local holdings tracker with allocation, sector mix, and
  a risk score
- **News** — aggregated market headlines and by-ticker search

`yfinance` requires no API key. FRED and Claude features need your own free
keys (see Setup) and degrade to a friendly on-page notice when missing.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your own keys:

   ```bash
   cp .env.example .env
   ```

   ```
   ANTHROPIC_API_KEY=your_key_here
   FRED_API_KEY=your_key_here
   ```

   - Get a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html
   - Get an Anthropic API key at https://console.anthropic.com

   Never commit your `.env` file or paste real keys into chat, issues, or code.

3. (Optional) Download company/ETF logos for a nicer UI:

   ```bash
   python scripts/fetch_logos.py
   ```

   Best-effort — tries several free icon sources per ticker and skips any
   that fail. Pages fall back to a text-initial placeholder when a logo
   isn't available. Safe to re-run; it skips tickers that already succeeded.

4. Run the app:

   ```bash
   streamlit run app.py
   ```

## Project Structure

```
app.py                       # Landing page with a quick market snapshot
pages/
  1_💹_Market_Pulse.py
  2_🔍_Stock_Analyzer.py
  3_🧺_ETF_Analyzer.py
  4_🌍_Macro.py
  5_💼_Portfolio.py
  6_📰_News.py
lib/
  config.py                  # Env/key loading, DISCLOSURE, shared style
  market_data.py             # Cached yfinance wrappers, index/sector/period constants
  charts.py                  # render_price_chart, render_sparkline, render_gauge
  logos.py                   # Ticker->domain map + base64 logo loader
  news.py                    # yfinance news + Yahoo RSS fallback
  macro.py / rates.py        # FRED indicators and yield curve
  signals.py                 # Descriptive technical/fundamental scoring
  risk.py                    # ETF and portfolio risk scoring
  etf_peers.py                # Curated ETF peer groups
  portfolio.py                # Local JSON portfolio storage
  claude_analyst.py          # Claude client + compliance-safe prompts
scripts/
  fetch_logos.py              # Best-effort logo downloader
assets/logos/                 # Downloaded logos (ticker.ext)
data/portfolio.json           # Local holdings (git-ignored)
```
