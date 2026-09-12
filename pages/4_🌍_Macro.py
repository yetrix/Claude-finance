import plotly.graph_objects as go
import streamlit as st

from lib.claude_analyst import get_client, macro_pulse_check
from lib.config import get_fred_key, inject_base_style, missing_key_message, render_disclosure
from lib.macro import INDICATORS, get_indicator_latest, get_indicator_series
from lib.rates import get_yield_curve_snapshot, get_yield_curve_snapshot_years_ago

st.set_page_config(page_title="Macro", page_icon="🌍", layout="wide")
inject_base_style()
st.title("🌍 Macro")

if not get_fred_key():
    st.info(missing_key_message("fred"))
    st.stop()

st.subheader("Macro Indicators")

labels = list(INDICATORS.keys())
cols = st.columns(4)
latest_cache = {}
for i, label in enumerate(labels):
    with st.spinner(f"Loading {label}..."):
        series = get_indicator_series(label)
        latest = get_indicator_latest(label)
    latest_cache[label] = latest
    with cols[i % 4]:
        with st.container(border=True):
            st.caption(label)
            if latest["value"] is None:
                st.markdown("**N/A**")
            else:
                st.markdown(f"**{latest['value']:,.2f}{latest['unit']}**")
                st.caption(f"As of {latest['date'].date() if hasattr(latest['date'], 'date') else latest['date']}")
            if series is not None and not series.empty:
                fig = go.Figure(go.Scatter(x=series.index, y=series.values, mode="lines", line=dict(color="#3498db")))
                fig.update_layout(template="plotly_dark", height=150, margin=dict(l=0, r=0, t=5, b=0),
                                   xaxis=dict(visible=False), yaxis=dict(visible=False))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"macro_{label}")

st.divider()

st.subheader("Treasury Yield Curve")
curve_now = get_yield_curve_snapshot()
curve_prior = get_yield_curve_snapshot_years_ago(1)

if curve_now.empty:
    st.info("Yield curve data not available.")
else:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve_now["Maturity"], y=curve_now["Yield"], mode="lines+markers", name="Today", line=dict(color="#2ecc71", width=3)))
    if not curve_prior.empty:
        fig.add_trace(go.Scatter(x=curve_prior["Maturity"], y=curve_prior["Yield"], mode="lines+markers", name="1 Year Ago", line=dict(color="#999", width=2, dash="dot")))
    fig.update_layout(template="plotly_dark", height=420, margin=dict(l=10, r=10, t=20, b=10),
                       yaxis_title="Yield (%)", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("🤖 AI Macro Pulse-Check")
if get_client() is None:
    st.info(missing_key_message("anthropic"))
else:
    st.caption("Educational context on the current macro backdrop — not investment advice.")
    if st.button("Generate Pulse-Check", type="primary"):
        with st.spinner("Analyzing..."):
            st.markdown(macro_pulse_check(latest_cache))

render_disclosure()
