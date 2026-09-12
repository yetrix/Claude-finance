"""Environment/key loading. Never print or log key values."""
import os
from dotenv import load_dotenv

load_dotenv()


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
