import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.charts import VIEWS, render_gauge, render_price_chart
from lib.config import inject_base_style, render_disclosure
from lib.etf_peers import get_peers
from lib.logos import render_logo_html
from lib.market_data import get_etf_details, get_history, get_prev_close, get_quote
from lib.risk import compute_etf_risk_score

st.set_page_config(page_title="ETF Analyzer", page_icon="🧺", layout="wide")
inject_base_style()
st.title("🧺 ETF Analyzer")

c1, c2 = st.columns([3, 2])
ticker = c1.text_input("ETF ticker symbol", value="SPY").strip().upper()
period = c2.segmented_control(
    "Period", ["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y", "10Y", "20Y", "30Y", "Max"], default="1Y"
)
period = period or "1Y"

if not ticker:
    st.stop()

with st.spinner(f"Loading {ticker}..."):
    hist = get_history(ticker, period)
    details = get_etf_details(ticker)
    baseline = get_prev_close(ticker) if period == "1D" else None

if hist is None or hist.empty:
    st.error(f"No data found for '{ticker}'. Check the ticker symbol.")
    st.stop()

header_cols = st.columns([1, 5])
with header_cols[0]:
    st.markdown(render_logo_html(ticker, size=64), unsafe_allow_html=True)
with header_cols[1]:
    st.subheader(f"{details['name']} ({ticker})")
    if details.get("category"):
        st.caption(details["category"])

last_price = float(hist["Close"].iloc[-1])
m1, m2, m3, m4 = st.columns(4)
m1.metric("Last Close", f"${last_price:,.2f}")
aum = details.get("total_assets")
m2.metric("Total Assets (AUM)", f"${aum:,}" if aum else "N/A")
er = details.get("expense_ratio")
m3.metric("Expense Ratio", f"{er * 100:.2f}%" if er else "N/A")
m4.metric("NAV", f"${details.get('nav_price'):.2f}" if details.get("nav_price") else "N/A")

st.divider()

view = st.radio("View", VIEWS, horizontal=True, key="etf_view")
fig = render_price_chart(hist, view=view, baseline_price=baseline, height=450, show_volume=True)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Returns table ---------------------------------------------------------------

st.subheader("Returns")
returns_data = {
    "YTD Return": details.get("ytd_return"),
    "3Y Avg Return": details.get("three_year_avg_return"),
    "5Y Avg Return": details.get("five_year_avg_return"),
    "3Y Beta": details.get("beta_3y"),
}
returns_df = pd.DataFrame(
    {"Metric": list(returns_data.keys()),
     "Value": [f"{v * 100:.2f}%" if k != "3Y Beta" and v is not None else (f"{v:.2f}" if v is not None else "N/A")
               for k, v in returns_data.items()]}
)
st.dataframe(returns_df, use_container_width=True, hide_index=True)

st.divider()

# --- Risk gauge + Sector breakdown -----------------------------------------------

risk_col, sector_col = st.columns(2)

with risk_col:
    st.subheader("Risk Profile")
    risk = compute_etf_risk_score(hist, details.get("top_holdings"))
    st.caption("Composite of volatility, drawdown, and holdings concentration — not a recommendation.")
    st.plotly_chart(render_gauge(risk["score"]), use_container_width=True, config={"displayModeBar": False})
    if risk["score"] is not None:
        st.markdown(f"<div style='text-align:center;font-size:1.3em;font-weight:700;'>{risk['band']}</div>", unsafe_allow_html=True)
        st.markdown(f"- Annualized volatility: {risk['volatility_pct']}%")
        st.markdown(f"- Max drawdown (period): {risk['max_drawdown_pct']}%")
        if risk["concentration_pct"] is not None:
            st.markdown(f"- Top-holdings concentration: {risk['concentration_pct']}%")
    else:
        st.info("Not enough history to compute a risk score.")

with sector_col:
    st.subheader("Sector Breakdown")
    sector_weights = details.get("sector_weights")
    if sector_weights:
        df_sector = pd.DataFrame(
            {"Sector": list(sector_weights.keys()), "Weight": [w * 100 if w <= 1.5 else w for w in sector_weights.values()]}
        ).sort_values("Weight")
        bar_fig = go.Figure(go.Bar(x=df_sector["Weight"], y=df_sector["Sector"], orientation="h", marker_color="#3498db"))
        bar_fig.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=20, t=10, b=10), xaxis_title="% Weight")
        st.plotly_chart(bar_fig, use_container_width=True)
    else:
        st.info("Sector weighting data not available for this ETF.")

st.divider()

# --- Top holdings -----------------------------------------------------------------

st.subheader("Top Holdings")
top_holdings = details.get("top_holdings")
if top_holdings is not None and not top_holdings.empty:
    th = top_holdings.reset_index()
    symbol_col = th.columns[0]
    name_col = "Name" if "Name" in th.columns else None
    weight_col = next((c for c in ("Holding Percent", "holdingPercent", "% Assets") if c in th.columns), None)

    holdings_cols = st.columns(2)
    for i, row in th.iterrows():
        symbol = str(row[symbol_col])
        name = str(row[name_col]) if name_col else ""
        weight = row[weight_col] if weight_col else None
        weight_pct = weight * 100 if weight is not None and weight <= 1.5 else weight
        weight_str = f"{weight_pct:.2f}%" if weight_pct is not None else "N/A"
        with holdings_cols[i % 2]:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;padding:6px 0;">'
                f'{render_logo_html(symbol, size=28)}'
                f'<div style="flex:1;min-width:0;">'
                f'<div style="font-weight:600;">{symbol}</div>'
                f'<div style="font-size:0.8em;color:#999;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>'
                f'</div>'
                f'<div>{weight_str}</div></div>',
                unsafe_allow_html=True,
            )
else:
    st.info("Top holdings data not available for this ETF.")

st.divider()

# --- Peer comparison ----------------------------------------------------------------

st.subheader("Peer Cost Comparison")
peers = get_peers(ticker)
if not peers:
    st.info("No curated peer group found for this ticker.")
else:
    peer_rows = []
    for peer_symbol in [ticker] + peers:
        peer_details = get_etf_details(peer_symbol)
        peer_quote = get_quote(peer_symbol)
        peer_rows.append({
            "Ticker": peer_symbol,
            "Name": peer_details.get("name"),
            "Expense Ratio": peer_details.get("expense_ratio"),
            "AUM": peer_details.get("total_assets"),
            "Price": peer_quote.get("price"),
        })
    peer_df = pd.DataFrame(peer_rows).sort_values("Expense Ratio", na_position="last")
    display_df = peer_df.copy()
    display_df["Expense Ratio"] = display_df["Expense Ratio"].apply(lambda v: f"{v * 100:.2f}%" if v is not None else "N/A")
    display_df["AUM"] = display_df["AUM"].apply(lambda v: f"${v:,}" if v else "N/A")
    display_df["Price"] = display_df["Price"].apply(lambda v: f"${v:,.2f}" if v else "N/A")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    current_er = peer_df.loc[peer_df["Ticker"] == ticker, "Expense Ratio"].iloc[0] if ticker in peer_df["Ticker"].values else None
    if current_er is not None:
        cheaper = peer_df[(peer_df["Ticker"] != ticker) & (peer_df["Expense Ratio"].notna()) & (peer_df["Expense Ratio"] < current_er)]
        if not cheaper.empty:
            best = cheaper.sort_values("Expense Ratio").iloc[0]
            bps_savings = (current_er - best["Expense Ratio"]) * 10000
            dollar_savings = 100_000 * (current_er - best["Expense Ratio"])
            st.success(
                f"💡 **Cheaper alternative found:** {best['Ticker']} has an expense ratio "
                f"{bps_savings:.0f} bps lower than {ticker}. On a $100,000 position, that's "
                f"roughly **${dollar_savings:,.0f}/year** in expense-ratio cost difference. "
                f"(Informational only — not a recommendation to switch.)"
            )

render_disclosure()
