"""
signals/sources.py — Feed definitions for this agent.

Edit this file to configure which RSS feeds and APIs to poll.
Values come from config/brand_config.json — do not hardcode URLs here.
"""
from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "brand_config.json"


def _load_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_primary_feeds() -> list[tuple[str, str]]:
    """Returns list of (source_name, url) for PRIMARY signal sources."""
    cfg = _load_config()
    sources = cfg.get("signal_sources", {}).get("primary", [])
    return [(s["name"], s["url"]) for s in sources if s.get("type") == "rss"]


def get_secondary_feeds() -> list[tuple[str, str]]:
    """Returns list of (source_name, url) for SECONDARY signal sources."""
    cfg = _load_config()
    sources = cfg.get("signal_sources", {}).get("secondary", [])
    return [(s["name"], s["url"]) for s in sources if s.get("type") == "rss"]


def get_api_sources() -> list[dict]:
    """Returns API source configs from brand_config.json."""
    cfg = _load_config()
    primary   = cfg.get("signal_sources", {}).get("primary",   [])
    secondary = cfg.get("signal_sources", {}).get("secondary", [])
    return [s for s in primary + secondary if s.get("type") == "api"]
