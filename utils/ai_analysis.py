"""Claude-powered descriptive analysis. No buy/sell recommendations are requested or produced."""
from utils.config import get_anthropic_key

SYSTEM_PROMPT = (
    "You are a financial data explainer for a personal, educational research dashboard. "
    "Summarize and explain the data you are given in plain language: trends, what key "
    "metrics mean, and context. You must NOT give investment advice, price targets, or "
    "buy/sell/hold recommendations. If asked for one, explain that this tool is for "
    "education only and does not provide recommendations. Keep responses concise."
)


def get_client():
    key = get_anthropic_key()
    if not key:
        return None
    import anthropic

    return anthropic.Anthropic(api_key=key)


def ask_claude(prompt: str, model: str = "claude-sonnet-5", max_tokens: int = 1024) -> str:
    client = get_client()
    if client is None:
        return ""
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
    except Exception as e:
        return f"⚠️ AI analysis unavailable: {e}"
