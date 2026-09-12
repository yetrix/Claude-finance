import pandas as pd
import streamlit as st

from utils import market_data as md
from utils.portfolio import add_holding, load_portfolio, remove_holding

st.set_page_config(page_title="My Portfolio", page_icon="💼", layout="wide")
st.title("💼 My Portfolio")

st.caption(
    "Your holdings are stored locally in `data/portfolio.json` on this machine only "
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
    st.stop()

rows = []
total_value = 0.0
total_cost = 0.0
for h in holdings:
    fi = md.get_fast_info(h["ticker"])
    last_price = fi.get("lastPrice") or fi.get("last_price")
    value = (last_price or 0) * h["shares"]
    cost = h["cost_basis"] * h["shares"]
    gain = value - cost
    gain_pct = (gain / cost * 100) if cost else 0
    total_value += value
    total_cost += cost
    rows.append(
        {
            "Ticker": h["ticker"],
            "Shares": h["shares"],
            "Cost Basis": h["cost_basis"],
            "Last Price": last_price,
            "Market Value": value,
            "Gain/Loss": gain,
            "Gain/Loss %": gain_pct,
        }
    )

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

col1, col2, col3 = st.columns(3)
col1.metric("Total Value", f"${total_value:,.2f}")
col2.metric("Total Cost Basis", f"${total_cost:,.2f}")
total_gain = total_value - total_cost
col3.metric(
    "Total Gain/Loss",
    f"${total_gain:,.2f}",
    f"{(total_gain / total_cost * 100) if total_cost else 0:+.2f}%",
)

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
