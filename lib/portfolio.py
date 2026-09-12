"""Local JSON-backed holdings storage (personal use, never committed to git)."""
import json
import os

PORTFOLIO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portfolio.json")


def _ensure_file():
    os.makedirs(os.path.dirname(PORTFOLIO_PATH), exist_ok=True)
    if not os.path.exists(PORTFOLIO_PATH):
        with open(PORTFOLIO_PATH, "w") as f:
            json.dump({"holdings": []}, f)


def load_portfolio() -> dict:
    _ensure_file()
    try:
        with open(PORTFOLIO_PATH) as f:
            return json.load(f)
    except Exception:
        return {"holdings": []}


def save_portfolio(data: dict):
    _ensure_file()
    with open(PORTFOLIO_PATH, "w") as f:
        json.dump(data, f, indent=2)


def add_holding(ticker: str, shares: float, cost_basis: float):
    data = load_portfolio()
    data["holdings"].append({"ticker": ticker.upper(), "shares": shares, "cost_basis": cost_basis})
    save_portfolio(data)


def remove_holding(index: int):
    data = load_portfolio()
    if 0 <= index < len(data["holdings"]):
        data["holdings"].pop(index)
        save_portfolio(data)
