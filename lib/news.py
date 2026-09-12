"""News aggregation: yfinance first, then FMP (if a key is configured), then
Yahoo Finance RSS as a last resort — each tier only runs if the previous one
came back empty."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
import streamlit as st
import yfinance as yf

from lib import fmp

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockMarketAnalystNews/1.0)"}
RSS_TIMEOUT = 6


def _normalize_yf_item(item: dict) -> dict | None:
    content = item.get("content", item)
    title = content.get("title") or item.get("title")
    if not title:
        return None
    link = (content.get("canonicalUrl") or {}).get("url") or item.get("link")
    publisher = (content.get("provider") or {}).get("displayName") or item.get("publisher")
    summary = content.get("summary") or content.get("description") or ""
    pub_date = content.get("pubDate") or content.get("displayTime")
    published = None
    if pub_date:
        try:
            published = datetime.fromisoformat(str(pub_date).replace("Z", "+00:00"))
        except ValueError:
            pass
    if published is None and item.get("providerPublishTime"):
        try:
            published = datetime.fromtimestamp(item["providerPublishTime"], tz=timezone.utc)
        except (ValueError, OSError):
            pass
    return {
        "title": title,
        "link": link,
        "publisher": publisher or "Unknown",
        "summary": summary,
        "published": published,
    }


def _parse_rss(xml_text: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub_date_raw = item.findtext("pubDate")
        published = None
        if pub_date_raw:
            try:
                published = parsedate_to_datetime(pub_date_raw)
            except (TypeError, ValueError):
                pass
        source_el = item.find("source")
        publisher = source_el.text.strip() if source_el is not None and source_el.text else "Yahoo Finance"
        items.append({"title": title, "link": link, "publisher": publisher, "summary": desc, "published": published})
    return items


@st.cache_data(ttl=600, show_spinner=False)
def ticker_news(ticker: str, limit: int = 10) -> list[dict]:
    items: list[dict] = []
    try:
        raw = yf.Ticker(ticker).news or []
        for r in raw:
            normalized = _normalize_yf_item(r)
            if normalized:
                items.append(normalized)
    except Exception:
        pass

    if not items:
        items = fmp.get_stock_news(ticker, limit=limit)

    if not items:
        try:
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
            resp = requests.get(url, headers=HEADERS, timeout=RSS_TIMEOUT)
            if resp.status_code == 200:
                items = _parse_rss(resp.text)
        except requests.RequestException:
            pass

    items.sort(key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return items[:limit]


@st.cache_data(ttl=600, show_spinner=False)
def market_news(limit: int = 10) -> list[dict]:
    """Aggregate general market headlines across a few broad tickers, deduped by title."""
    items: list[dict] = []
    seen_titles = set()
    for symbol in ("^GSPC", "^DJI", "^NDX"):
        try:
            raw = yf.Ticker(symbol).news or []
        except Exception:
            raw = []
        for r in raw:
            normalized = _normalize_yf_item(r)
            if normalized and normalized["title"] not in seen_titles:
                seen_titles.add(normalized["title"])
                items.append(normalized)

    if not items:
        items = fmp.get_general_news(limit=limit)

    if not items:
        try:
            resp = requests.get("https://finance.yahoo.com/news/rssindex", headers=HEADERS, timeout=RSS_TIMEOUT)
            if resp.status_code == 200:
                items = _parse_rss(resp.text)
        except requests.RequestException:
            pass

    items.sort(key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return items[:limit]


def time_ago(published: datetime | None) -> str:
    if published is None:
        return ""
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - published
    seconds = delta.total_seconds()
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"
