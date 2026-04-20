"""
signals/adapters/rss.py — Generic RSS/Atom feed fetcher.

Usage:
    from signals.adapters.rss import fetch_feed

    articles = await fetch_feed("https://feeds.feedburner.com/techcrunch", "TechCrunch")
    # Returns list of {title, url, description, pub_date, source}
"""
from __future__ import annotations

import asyncio
import datetime
import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx

log = logging.getLogger(__name__)

_ATOM_NS = "http://www.w3.org/2005/Atom"


def _strip_html(text: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&amp;",  "&", text)
    text = re.sub(r"&lt;",   "<", text)
    text = re.sub(r"&gt;",   ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+",    " ", text)
    return text.strip()


def _parse_feed(xml_text: str) -> list[dict]:
    """Parse RSS 2.0 or Atom feed into article dicts."""
    articles: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        log.debug("[rss] xml parse error: %s", exc)
        return articles

    root_tag = root.tag.split("}", 1)[-1] if "}" in root.tag else root.tag

    if root_tag == "rss":
        channel = root.find("channel")
        if channel is None:
            return articles
        for item in channel.findall("item"):
            title = _strip_html(item.findtext("title") or "")
            link  = (item.findtext("link") or "").strip()
            if not link:
                guid = item.find("guid")
                if guid is not None and guid.get("isPermaLink", "true").lower() != "false":
                    link = (guid.text or "").strip()
            desc = _strip_html(
                item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")
                or item.findtext("description")
                or ""
            )[:400]
            pub_date = item.findtext("pubDate") or ""
            if title and link:
                articles.append({
                    "title":       title,
                    "url":         link,
                    "description": desc,
                    "pub_date":    pub_date,
                })

    elif root_tag == "feed":
        for entry in root.findall(f"{{{_ATOM_NS}}}entry"):
            title = _strip_html((entry.findtext(f"{{{_ATOM_NS}}}title") or "").strip())
            link_el = entry.find(f"{{{_ATOM_NS}}}link[@rel='alternate']") \
                   or entry.find(f"{{{_ATOM_NS}}}link")
            link    = (link_el.get("href", "") if link_el is not None else "").strip()
            summary = _strip_html(entry.findtext(f"{{{_ATOM_NS}}}summary") or "")[:400]
            updated = entry.findtext(f"{{{_ATOM_NS}}}updated") or ""
            if title and link:
                articles.append({
                    "title":       title,
                    "url":         link,
                    "description": summary,
                    "pub_date":    updated,
                })

    return articles


async def fetch_feed(
    url: str,
    source_name: str,
    timeout: float = 10.0,
) -> list[dict]:
    """
    Fetch one RSS/Atom feed. Returns list of article dicts, each with:
      {title, url, description, pub_date, source}
    Returns [] on any network or parse error.
    """
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AgentFramework/1.0)"},
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        articles = _parse_feed(resp.text)
        for a in articles:
            a["source"] = source_name
        log.debug("[rss] %s → %d articles", source_name, len(articles))
        return articles
    except Exception as exc:
        log.warning("[rss] fetch_failed source=%s error=%s", source_name, exc)
        return []


async def fetch_all_feeds(
    feeds: list[tuple[str, str]],
    delay_between: float = 0.5,
) -> list[dict]:
    """
    Fetch multiple feeds sequentially with a small delay between each.

    Args:
        feeds: list of (source_name, url) tuples
        delay_between: seconds to sleep between requests

    Returns:
        Flat list of all articles from all feeds, each with 'source' set.
    """
    all_articles: list[dict] = []
    for source_name, url in feeds:
        articles = await fetch_feed(url, source_name)
        all_articles.extend(articles)
        if delay_between > 0:
            await asyncio.sleep(delay_between)
    return all_articles
