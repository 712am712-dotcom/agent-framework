"""
main.py — Brand intelligence agent entry point.

Replace {agent_name}, {brand_slug} with real values for your brand.

Architecture:
  1. Load config + verify brand is registered in Supabase
  2. Fetch signals from RSS/API sources (signals/sources.py)
  3. Keyword pre-filter (signals/scorer.py) — discard noise cheaply
  4. LLM evaluation for high-priority signals (prompts/{agent_name}_prompt.txt)
  5. Write accepted signals to Supabase signals table
  6. Write content_jobs rows for signals that pass the LLM filter
  7. Log scan completion to agent_logs

Usage:
  python main.py           # Run continuously (scheduled loop)
  python main.py --once    # Run one scan and exit (useful for testing)
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("agent")

# ── Config ────────────────────────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).parent / "config" / "brand_config.json"
_PROMPT_DIR  = Path(__file__).parent / "prompts"

SUPABASE_URL       = os.environ["SUPABASE_URL"]
SUPABASE_KEY       = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
BRAND_SLUG         = os.environ.get("BRAND_SLUG", "")
AGENT_NAME         = os.environ.get("AGENT_NAME", "")

SCAN_INTERVAL_MIN  = int(os.environ.get("SCAN_INTERVAL_MINUTES", 30))
DAILY_CALL_LIMIT   = int(os.environ.get("DAILY_CALL_LIMIT", 20))
CLAUDE_MODEL       = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")


def _load_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        log.error("config_load_failed path=%s error=%s", _CONFIG_PATH, exc)
        raise


def _load_prompt() -> str:
    """Load the agent's evaluation prompt from prompts/{agent_name}_prompt.txt."""
    prompt_path = _PROMPT_DIR / f"{AGENT_NAME}_prompt.txt"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except Exception as exc:
        log.error("prompt_load_failed path=%s error=%s", prompt_path, exc)
        raise


# ── Supabase helpers ──────────────────────────────────────────────────────────

_SB_HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=representation",
}


async def _sb_get(path: str, params: dict | None = None) -> list[dict]:
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(url, headers=_SB_HEADERS, params=params or {})
    if r.status_code == 200:
        return r.json() or []
    log.warning("supabase_get_failed path=%s status=%d", path, r.status_code)
    return []


async def _sb_insert(table: str, row: dict) -> dict | None:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.post(url, headers=_SB_HEADERS, json=row)
    if r.status_code in (200, 201):
        rows = r.json()
        return rows[0] if isinstance(rows, list) and rows else rows if isinstance(rows, dict) else None
    log.warning("supabase_insert_failed table=%s status=%d body=%s", table, r.status_code, r.text[:200])
    return None


async def _log_event(event: str, detail: dict | None = None) -> None:
    await _sb_insert("agent_logs", {
        "service": AGENT_NAME or "agent",
        "event":   event,
        "detail":  detail or {},
    })


# ── Brand registration check ──────────────────────────────────────────────────

async def verify_brand_registered() -> bool:
    """Confirm this brand_slug exists in the brands table before scanning."""
    rows = await _sb_get("brands", {"slug": f"eq.{BRAND_SLUG}", "select": "slug,active"})
    if not rows:
        log.error("brand_not_registered slug=%s — add row to brands table first", BRAND_SLUG)
        return False
    if not rows[0].get("active", False):
        log.warning("brand_inactive slug=%s", BRAND_SLUG)
        return False
    log.info("brand_verified slug=%s", BRAND_SLUG)
    return True


# ── LLM evaluation ────────────────────────────────────────────────────────────

async def evaluate_signal(
    title: str,
    description: str,
    source_name: str,
    prompt_template: str,
) -> dict | None:
    """
    Call Claude to evaluate a signal. Returns content dict or None if rejected.

    The prompt template contains {title}, {description}, {source} placeholders.
    Returns: {hook, points, cta, why_now, score, final_score} or None.
    """
    prompt = prompt_template.replace("{title}", title[:300]) \
                             .replace("{description}", description[:400]) \
                             .replace("{source}", source_name)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key":         ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type":      "application/json",
                },
                json={
                    "model":      CLAUDE_MODEL,
                    "max_tokens": 600,
                    "messages":   [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()

        # Strip markdown fences if present
        import re
        text = re.sub(r"^```[^\n]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text.strip()).strip()

        if text.lower() in ("null", "none", ""):
            return None

        data = json.loads(text)
        if data is None:
            return None

        final_score = int(data.get("final_score", 0))
        if final_score < 7:
            log.debug("llm_rejected score=%d title=%s", final_score, title[:60])
            return None

        return data

    except json.JSONDecodeError:
        log.debug("llm_json_parse_failed title=%s", title[:60])
        return None
    except Exception as exc:
        log.warning("llm_call_failed title=%s error=%s", title[:60], exc)
        return None


# ── Signal + job writer ───────────────────────────────────────────────────────

async def write_signal_and_job(
    title: str,
    source_name: str,
    eval_result: dict,
    config: dict,
) -> None:
    """Write a signal row and a pending content_job row to Supabase."""
    # 1. Write signal
    signal_row = await _sb_insert("signals", {
        "brand":        BRAND_SLUG,
        "topic":        title[:500],
        "hook":         eval_result.get("hook", "")[:300],
        "score":        int(eval_result.get("final_score", 7)),
        "why_now":      eval_result.get("why_now", "")[:2000],
        "source":       source_name,
        "source_agent": AGENT_NAME,
    })

    signal_id = signal_row.get("id") if signal_row else None

    # 2. Write content_job
    template       = config.get("visual_template", "")
    content_format = config.get("formats", {}).get("primary", "vertical_30s")

    await _sb_insert("content_jobs", {
        "brand":        BRAND_SLUG,
        "template":     template,
        "content": {
            "hook":   eval_result.get("hook", ""),
            "points": eval_result.get("points", []),
            "cta":    eval_result.get("cta", config.get("cta", "")),
        },
        "format":       content_format,
        "status":       "pending",
        "source_agent": AGENT_NAME,
        "signal_ids":   [signal_id] if signal_id else [],
    })

    log.info(
        "job_created brand=%s template=%s score=%d title=%s",
        BRAND_SLUG, template,
        int(eval_result.get("final_score", 0)),
        title[:60],
    )


# ── Main scan loop ────────────────────────────────────────────────────────────

async def run_scan(
    config: dict,
    prompt_template: str,
    seen_urls: set[str],
) -> int:
    """
    Run one scan: fetch → pre-filter → LLM → write.
    Returns number of content_jobs created.
    """
    from signals.adapters.rss import fetch_all_feeds
    from signals.scorer import keyword_priority, score_article
    from signals.sources import get_primary_feeds, get_secondary_feeds

    primary   = get_primary_feeds()
    secondary = get_secondary_feeds()
    primary_names = {name for name, _ in primary}

    all_feeds = primary + secondary
    articles  = await fetch_all_feeds(all_feeds, delay_between=0.5)

    max_jobs_day  = config.get("content_limits", {}).get("max_jobs_per_day", 3)
    min_score     = config.get("content_limits", {}).get("min_score_to_escalate", 7)

    jobs_created  = 0
    llm_calls     = 0

    for article in articles:
        url    = article.get("url", "")
        title  = article.get("title", "")
        desc   = article.get("description", "")
        source = article.get("source", "")

        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        if not title:
            continue

        # Pre-filter
        priority = keyword_priority(title, desc)
        if priority == "skip":
            continue

        if priority != "high":
            continue

        # Score check
        is_primary = source in primary_names
        raw_score  = score_article(title, desc, source, is_primary)
        if raw_score < min_score:
            continue

        if jobs_created >= max_jobs_day:
            log.debug("daily_job_cap_reached limit=%d", max_jobs_day)
            break

        # LLM evaluation
        llm_calls += 1
        result = await evaluate_signal(title, desc, source, prompt_template)
        if result is None:
            continue

        await write_signal_and_job(title, source, result, config)
        jobs_created += 1

    log.info(
        "scan_complete brand=%s articles=%d llm_calls=%d jobs=%d",
        BRAND_SLUG, len(articles), llm_calls, jobs_created,
    )
    await _log_event("scan_complete", {
        "articles": len(articles),
        "llm_calls": llm_calls,
        "jobs_created": jobs_created,
    })
    return jobs_created


# ── Entry point ───────────────────────────────────────────────────────────────

async def main_async(run_once: bool = False) -> None:
    if not BRAND_SLUG or not AGENT_NAME:
        raise RuntimeError("BRAND_SLUG and AGENT_NAME env vars must be set")

    config          = _load_config()
    prompt_template = _load_prompt()

    # Verify brand is registered before doing anything
    if not await verify_brand_registered():
        raise RuntimeError(f"Brand '{BRAND_SLUG}' not registered in Supabase brands table")

    await _log_event("agent_started", {"brand": BRAND_SLUG, "model": CLAUDE_MODEL})
    log.info("agent_started brand=%s agent=%s", BRAND_SLUG, AGENT_NAME)

    seen_urls: set[str] = set()
    interval = SCAN_INTERVAL_MIN * 60

    if run_once:
        await run_scan(config, prompt_template, seen_urls)
        return

    while True:
        try:
            await run_scan(config, prompt_template, seen_urls)
        except Exception as exc:
            log.error("scan_error error=%s", exc)
            await _log_event("scan_error", {"error": str(exc)[:500]})

        log.info("sleeping interval=%dm", SCAN_INTERVAL_MIN)
        await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Brand intelligence agent")
    parser.add_argument("--once", action="store_true", help="Run one scan and exit")
    args = parser.parse_args()
    asyncio.run(main_async(run_once=args.once))


if __name__ == "__main__":
    main()
