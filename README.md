# Stock Market Analyst

A personal Streamlit dashboard for exploring stocks, ETFs, and macro
indicators, with optional AI-generated explanations via Claude.

**Educational and personal-research use only.** This app does not provide
buy/sell/hold recommendations or investment advice.

## Features

- **Stock Explorer** — price charts, fundamentals, financials, dividends, analyst
  rating history, and news via `yfinance` (no API key required)
- **ETF Explorer** — ETF metadata, sector weights, and top holdings
- **Macro Dashboard** — CPI, unemployment, Fed funds rate, Treasury yields, and
  more via FRED (requires a free FRED API key)
- **My Portfolio** — a local watchlist/holdings tracker stored in
  `data/portfolio.json` (never committed to git)
- **AI Analysis** — ask Claude to explain and summarize data in plain language
  (requires an Anthropic API key)

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
   If a key is missing, the relevant page shows a friendly notice instead of
   crashing.

3. Run the app:

   ```bash
   streamlit run Home.py
   ```

## Project Structure

```
Home.py                     # Landing page
pages/                      # Streamlit multipage app pages
utils/
  config.py                 # Env/key loading
  market_data.py            # Cached yfinance wrappers
  macro_data.py             # FRED series helpers
  ai_analysis.py            # Claude client + prompt guardrails
  portfolio.py              # Local JSON portfolio storage
data/portfolio.json         # Local holdings (git-ignored)
```
