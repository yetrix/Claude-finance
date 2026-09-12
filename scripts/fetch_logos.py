"""Best-effort logo downloader for the tickers in lib.logos.TICKER_DOMAINS.

Tries, in order, until one succeeds:
  1. simple-icons SVG via jsdelivr (post-processed to fill="#ffffff" for dark mode)
  2. vectorlogo.zone SVG (best-effort; no stable public API, so this frequently misses)
  3. apple-touch-icon.png from the company's own domain
  4. Google's faviconV2 endpoint (size=256)
  5. DuckDuckGo's icon service

Saves to assets/logos/<TICKER>.<ext>. Safe to re-run: skips tickers that already
have a saved logo unless --force is passed. Network failures are per-ticker and
never abort the run.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.logos import LOGO_DIR, TICKER_DOMAINS, TICKER_SIMPLEICON_SLUGS  # noqa: E402

TIMEOUT = 6
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockMarketAnalystLogoFetcher/1.0)"}
MIN_BYTES = 100


def _sniff_ext(content: bytes, fallback: str) -> str:
    """Determine the real image type from magic bytes; downloaded content doesn't
    always match the extension its URL implied (e.g. a .png URL serving a JPEG)."""
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if content[:3] == b"\xff\xd8\xff":
        return "jpg"
    if content[:4] in (b"GIF8",):
        return "png"  # normalize; browsers render GIF fine even mislabeled, rare case
    if content[:4] == b"\x00\x00\x01\x00" or content[:4] == b"\x00\x00\x02\x00":
        return "ico"
    if content.lstrip()[:5] == b"<?xml" or b"<svg" in content[:200]:
        return "svg"
    return fallback


def _save(ticker: str, ext: str, content: bytes) -> str:
    os.makedirs(LOGO_DIR, exist_ok=True)
    real_ext = _sniff_ext(content, ext) if ext != "svg" else "svg"
    path = os.path.join(LOGO_DIR, f"{ticker}.{real_ext}")
    with open(path, "wb") as f:
        f.write(content)
    return path


def try_simple_icons(ticker: str) -> bool:
    slug = TICKER_SIMPLEICON_SLUGS.get(ticker)
    if not slug:
        return False
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200 and len(resp.content) > MIN_BYTES:
            svg = resp.text
            svg = re.sub(r'fill="#[0-9A-Fa-f]{3,6}"', 'fill="#ffffff"', svg)
            if "fill=" not in svg:
                svg = svg.replace("<svg ", '<svg fill="#ffffff" ', 1)
            _save(ticker, "svg", svg.encode("utf-8"))
            return True
    except requests.RequestException:
        pass
    return False


def try_vectorlogo_zone(ticker: str, domain: str) -> bool:
    # No stable public search API; best-effort guess using the domain's bare name.
    guess = domain.split(".")[0]
    url = f"https://cdn.freebiesupply.com/logos/thumbs/2x/{guess}-logo.png"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200 and len(resp.content) > MIN_BYTES and "image" in resp.headers.get("Content-Type", ""):
            _save(ticker, "png", resp.content)
            return True
    except requests.RequestException:
        pass
    return False


def try_apple_touch_icon(ticker: str, domain: str) -> bool:
    url = f"https://{domain}/apple-touch-icon.png"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > MIN_BYTES and "image" in resp.headers.get("Content-Type", ""):
            _save(ticker, "png", resp.content)
            return True
    except requests.RequestException:
        pass
    return False


def try_google_favicon(ticker: str, domain: str) -> bool:
    url = f"https://www.google.com/s2/favicons?sz=256&domain={domain}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200 and len(resp.content) > MIN_BYTES:
            _save(ticker, "png", resp.content)
            return True
    except requests.RequestException:
        pass
    return False


def try_duckduckgo(ticker: str, domain: str) -> bool:
    url = f"https://icons.duckduckgo.com/ip3/{domain}.ico"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200 and len(resp.content) > MIN_BYTES:
            _save(ticker, "ico", resp.content)
            return True
    except requests.RequestException:
        pass
    return False


def fetch_one(ticker: str, domain: str) -> tuple[str, bool, str]:
    for source_name, fn in (
        ("simple-icons", lambda: try_simple_icons(ticker)),
        ("vectorlogo.zone", lambda: try_vectorlogo_zone(ticker, domain)),
        ("apple-touch-icon", lambda: try_apple_touch_icon(ticker, domain)),
        ("google-favicon", lambda: try_google_favicon(ticker, domain)),
        ("duckduckgo", lambda: try_duckduckgo(ticker, domain)),
    ):
        if fn():
            return ticker, True, source_name
    return ticker, False, "none"


def already_has_logo(ticker: str) -> bool:
    for ext in ("svg", "png", "ico", "jpg", "jpeg"):
        if os.path.exists(os.path.join(LOGO_DIR, f"{ticker}.{ext}")):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-download even if a logo already exists.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N tickers (debugging).")
    args = parser.parse_args()

    tickers = list(TICKER_DOMAINS.items())
    if args.limit:
        tickers = tickers[: args.limit]

    results = {"simple-icons": 0, "vectorlogo.zone": 0, "apple-touch-icon": 0, "google-favicon": 0, "duckduckgo": 0, "none": 0}
    skipped = 0

    for ticker, domain in tickers:
        if not args.force and already_has_logo(ticker):
            skipped += 1
            continue
        _, ok, source = fetch_one(ticker, domain)
        results[source] += 1
        status = "OK" if ok else "MISS"
        print(f"[{status:4}] {ticker:8} via {source}")
        time.sleep(0.05)

    total = len(tickers)
    fetched = total - skipped - results["none"]
    print("\n--- Summary ---")
    for source, count in results.items():
        if count:
            print(f"{source}: {count}")
    print(f"Skipped (already had logo): {skipped}")
    print(f"Fetched this run: {fetched}/{total - skipped}")
    print(f"Total coverage: {total - results['none'] - (skipped and 0)} logos on disk (of {total} tickers)")


if __name__ == "__main__":
    main()
