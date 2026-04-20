# {Brand Name} Intelligence Agent — {agent_name}

> Replace this header with your brand name and agent name.
> All sections marked with `{...}` must be filled in before deploying.

---

## Purpose

{One paragraph describing what this agent does, which brand it serves, and what
kind of content it produces. Example: "ae-intel is the intelligence layer for
@artificialeducation. It monitors AI news RSS feeds, scores articles for
carousel potential, and writes pending content_jobs rows that Scribe scripts
into short-form video content."}

---

## Signal Sources

| Source | Type | URL / Endpoint | Priority |
|--------|------|----------------|----------|
| {Source name} | rss / api / scraper | {url} | PRIMARY / SECONDARY |

**Scan interval:** {X} minutes during active hours, {Y} minutes overnight.

**Daily call limit:** {N} LLM calls/day maximum (controlled by `DAILY_CALL_LIMIT` env var).

---

## Filter Logic Summary

**ACCEPT:** {one sentence — what signals pass}

**REJECT:** {one sentence — what signals are discarded without an LLM call}

**Score threshold:** Signals below score {N}/10 are not escalated to the LLM.

Full filter logic lives in `signals/scorer.py` and `prompts/{agent_name}_prompt.txt`.

---

## Supabase Tables

### Reads from
| Table | Query | Purpose |
|-------|-------|---------|
| `brands` | `WHERE slug = '{brand_slug}'` | Confirm brand is registered |

### Writes to
| Table | Columns written | Status transitions |
|-------|----------------|-------------------|
| `signals` | brand, topic, hook, score, why_now, source, source_agent | n/a |
| `content_jobs` | brand, template, content, format, status, source_agent, signal_ids | pending only |
| `agent_logs` | service, event, detail | n/a |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in real values.

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | Service role key — never expose publicly |
| `ANTHROPIC_API_KEY` | yes | Claude API key |
| `BRAND_SLUG` | yes | Must match `brands.slug` in Supabase (e.g. `ae`) |
| `AGENT_NAME` | yes | Service name (e.g. `ae-intel`) |
| `SCAN_INTERVAL_MINUTES` | no | Default: 30 |
| `DAILY_CALL_LIMIT` | no | Max LLM calls/day. Default: 20 |
| `CLAUDE_MODEL` | no | Default: `claude-haiku-4-5-20251001` |

---

## Running locally

```bash
# Install deps
pip install -r requirements.txt

# Copy and fill env
cp .env.example .env

# Smoke test signal sources
python signals/test_fetch.py

# Run one scan (no loop)
python main.py --once

# Run continuously
python main.py
```

---

## Deploy to Railway

1. Push this repo to GitHub
2. New Railway project → Deploy from GitHub → select this repo
3. Set env vars in Railway dashboard (copy from `.env`, not `.env.example`)
4. Deploy. Check logs for `agent_started brand={brand_slug}`.
5. Confirm first content_job row appears in Supabase within one scan interval.

---

## Brief

See `/brief.md` for the 7-field brand brief that drives this agent's persona,
filter logic, and output format.
