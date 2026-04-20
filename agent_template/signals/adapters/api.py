"""
signals/adapters/api.py — Generic JSON API fetcher.

Usage:
    from signals.adapters.api import fetch_json

    data = await fetch_json(
        url="https://api.example.com/v1/articles",
        headers={"X-API-KEY": api_key},
        params={"limit": 10},
    )
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)


async def fetch_json(
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    timeout: float = 10.0,
) -> Any:
    """
    Fetch a JSON endpoint. Returns parsed JSON or None on error.

    Use this for REST APIs (financialdatasets.ai, Finnhub, etc.)
    The caller is responsible for extracting the relevant fields.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers or {}, params=params or {})
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        log.warning("[api] http_error url=%s status=%s", url, exc.response.status_code)
        return None
    except Exception as exc:
        log.warning("[api] fetch_failed url=%s error=%s", url, exc)
        return None


async def post_json(
    url: str,
    body: dict,
    headers: dict | None = None,
    timeout: float = 10.0,
) -> Any:
    """POST a JSON body and return the parsed response. Returns None on error."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=body, headers=headers or {})
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        log.warning("[api] post_failed url=%s error=%s", url, exc)
        return None
