import plotly.graph_objects as go
import streamlit as st

from utils.config import get_fred_key, missing_key_message
from utils.macro_data import MACRO_SERIES, get_series
from utils.ai_analysis import ask_claude, get_client

st.set_page_config(page_title="Macro Dashboard", page_icon="🌐", layout="wide")
st.title("🌐 Macro Dashboard")

if not get_fred_key():
    st.info(missing_key_message("fred"))
    st.stop()

selected = st.multiselect(
    "Indicators", list(MACRO_SERIES.keys()), default=["CPI (Inflation)", "Fed Funds Rate", "Unemployment Rate"]
)

if not selected:
    st.stop()

cols = st.columns(2)
series_cache = {}
for i, label in enumerate(selected):
    series_id = MACRO_SERIES[label]
    with st.spinner(f"Loading {label}..."):
        s = get_series(series_id)
    series_cache[label] = s
    if s is None or s.empty:
        cols[i % 2].warning(f"No data for {label}.")
        continue
    fig = go.Figure(go.Scatter(x=s.index, y=s.values, mode="lines", name=label))
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10), title=label)
    cols[i % 2].plotly_chart(fig, use_container_width=True)
    cols[i % 2].metric("Latest", f"{s.dropna().iloc[-1]:,.2f}", help=f"As of {s.dropna().index[-1].date()}")

st.divider()
st.subheader("🤖 Ask Claude About Macro Trends")
if get_client() is None:
    st.info(missing_key_message("anthropic"))
else:
    question = st.text_area(
        "Question", value="Explain what these current macro readings suggest about the broader economy."
    )
    if st.button("Ask Claude", type="primary"):
        with st.spinner("Thinking..."):
            snapshot_lines = []
            for label, s in series_cache.items():
                if s is not None and not s.empty:
                    snapshot_lines.append(f"{label}: latest = {s.dropna().iloc[-1]:,.2f}")
            snapshot = "\n".join(snapshot_lines) + f"\n\nUser question: {question}"
            st.markdown(ask_claude(snapshot))
