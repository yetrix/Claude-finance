"""Shared constants and environment/key loading. Never print or log key values."""
import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Stock Market Analyst"
APP_ICON = "📈"
SIDEBAR_BRAND = "📈 Market Analyst"
BASE_FONT_SIZE = "17px"

DISCLOSURE = (
    "This dashboard is for educational and informational purposes only. "
    "It is not financial advice, not a recommendation to buy or sell any "
    "security, and is not personalized to your situation. Consult a "
    "licensed advisor before making investment decisions."
)


def get_anthropic_key() -> str | None:
    key = os.getenv("ANTHROPIC_API_KEY")
    return key if key else None


def get_fred_key() -> str | None:
    key = os.getenv("FRED_API_KEY")
    return key if key else None


def missing_key_message(service: str) -> str:
    if service == "anthropic":
        return (
            "🔑 No Anthropic API key found. Add `ANTHROPIC_API_KEY` to your `.env` "
            "file to enable AI analysis on this page."
        )
    if service == "fred":
        return (
            "🔑 No FRED API key found. Add `FRED_API_KEY` to your `.env` file to "
            "enable macro indicators on this page. Get a free key at "
            "https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    return f"🔑 Missing API key for {service}."


def inject_base_style():
    """Larger base font for accessibility + sidebar branding, applied on every page."""
    import streamlit as st

    st.markdown(
        f"""
        <style>
        .main .block-container {{ font-size: {BASE_FONT_SIZE}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(f"### {SIDEBAR_BRAND}")


def render_disclosure():
    import streamlit as st

    st.divider()
    st.caption(DISCLOSURE)
