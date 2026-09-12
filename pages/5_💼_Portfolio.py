import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.claude_analyst import get_client, portfolio_deep_analysis
from lib.config import inject_base_style, missing_key_message, render_disclosure
from lib.market_data import get_history, get_quote, get_stock_fundamentals, is_etf
from lib.portfolio import add_holding, load_portfolio, remove_holding
from lib.risk import compute_portfolio_risk_score

st.set_page_config(page_title="Portfolio", page_icon="💼", layout="wide")
inject_base_style()
st.title("💼 Portfolio")

st.caption(
    "Holdings are stored locally in `data/portfolio.json` on this machine only "
    "(git-ignored). This is a personal tracker, not brokerage-connected."
)

with st.form("add_holding"):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    new_ticker = c1.text_input("Ticker").strip().upper()
    new_shares = c2.number_input("Shares", min_value=0.0, step=1.0, format="%.4f")
    new_cost = c3.number_input("Cost basis / share", min_value=0.0, step=0.01, format="%.2f")
    submitted = c4.form_submit_button("Add", type="primary")
    if submitted and new_ticker and new_shares > 0:
        add_holding(new_ticker, new_shares, new_cost)
        st.rerun()

portfolio = load_portfolio()
holdings = portfolio.get("holdings", [])

if not holdings:
    st.info("No holdings yet. Add one above.")
    render_disclosure()
    st.stop()

rows = []
sector_totals: dict[str, float] = {}
hist_by_ticker = {}
with st.spinner("Loading portfolio data..."):
    for h in holdings:
        t = h["ticker"]
        quote = get_quote(t)
        price = quote.get("price")
        value = (price or 0) * h["shares"]
        cost = h["cost_basis"] * h["shares"]
        gain = value - cost
        gain_pct = (gain / cost * 100) if cost else 0
        rows.append({
            "Ticker": t, "Shares": h["shares"], "Cost Basis": h["cost_basis"],
            "Last Price": price, "Market Value": value, "Gain/Loss": gain, "Gain/Loss %": gain_pct,
        })
        sector = None
        if not is_etf(t):
            fundamentals = get_stock_fundamentals(t)
            sector = fundamentals.get("sector")
        sector_key = sector or ("ETF/Fund" if is_etf(t) else "Other")
        sector_totals[sector_key] = sector_totals.get(sector_key, 0) + value
        hist_by_ticker[t] = get_history(t, "6M")

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

total_value = df["Market Value"].sum()
total_cost = (df["Cost Basis"] * df["Shares"]).sum()
total_gain = total_value - total_cost

col1, col2, col3 = st.columns(3)
col1.metric("Total Value", f"${total_value:,.2f}")
col2.metric("Total Cost Basis", f"${total_cost:,.2f}")
col3.metric("Total Gain/Loss", f"${total_gain:,.2f}", f"{(total_gain / total_cost * 100) if total_cost else 0:+.2f}%")

st.divider()

alloc_col, sector_col = st.columns(2)
with alloc_col:
    st.subheader("Allocation")
    if total_value > 0:
        pie = go.Figure(go.Pie(labels=df["Ticker"], values=df["Market Value"], hole=0.4))
        pie.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(pie, use_container_width=True)

with sector_col:
    st.subheader("Sector Breakdown")
    if sector_totals:
        sector_pie = go.Figure(go.Pie(labels=list(sector_totals.keys()), values=list(sector_totals.values()), hole=0.4))
        sector_pie.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(sector_pie, use_container_width=True)

st.divider()

st.subheader("Portfolio Risk Score")
value_frames = []
weights = {}
for h in holdings:
    t = h["ticker"]
    hist = hist_by_ticker.get(t)
    if hist is not None and not hist.empty:
        value_frames.append((t, hist["Close"] * h["shares"]))
        row = df[df["Ticker"] == t].iloc[0]
        weights[t] = row["Market Value"]

if value_frames:
    combined = pd.concat({t: s for t, s in value_frames}, axis=1).dropna()
    portfolio_value_series = combined.sum(axis=1)
    weight_sum = sum(weights.values()) or 1
    weights_pct = {t: v / weight_sum for t, v in weights.items()}
    risk = compute_portfolio_risk_score(portfolio_value_series, weights_pct)
    if risk["score"] is not None:
        from lib.charts import render_gauge

        rc1, rc2 = st.columns([1, 2])
        with rc1:
            st.plotly_chart(render_gauge(risk["score"]), use_container_width=True, config={"displayModeBar": False})
        with rc2:
            st.markdown(f"**{risk['band']}**")
            st.markdown(f"- Annualized volatility: {risk['volatility_pct']}%")
            st.markdown(f"- Max drawdown (6-month): {risk['max_drawdown_pct']}%")
            if risk["concentration_pct"] is not None:
                st.markdown(f"- Top-holding concentration: {risk['concentration_pct']}%")
    else:
        st.info("Not enough shared price history across holdings to compute a risk score.")
else:
    st.info("Not enough price history to compute a risk score.")

st.divider()

st.subheader("🤖 AI Deep Analysis")
if get_client() is None:
    st.info(missing_key_message("anthropic"))
else:
    st.caption("Educational commentary on composition and risk — not a recommendation to change holdings.")
    if st.button("Generate Deep Analysis", type="primary"):
        with st.spinner("Analyzing..."):
            summary_lines = [f"{r['Ticker']}: {r['Shares']} shares, ${r['Market Value']:,.0f} value ({r['Market Value'] / total_value * 100:.1f}% of portfolio)" for r in rows]
            summary = "\n".join(summary_lines)
            st.markdown(portfolio_deep_analysis(summary))

st.divider()
st.subheader("Remove a Holding")
idx_to_remove = st.selectbox(
    "Select holding to remove",
    options=list(range(len(holdings))),
    format_func=lambda i: f"{holdings[i]['ticker']} — {holdings[i]['shares']} shares",
)
if st.button("Remove", type="secondary"):
    remove_holding(idx_to_remove)
    st.rerun()

render_disclosure()
