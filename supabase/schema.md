# Supabase Schema — Multi-Brand Framework

This document describes every table the brand intelligence framework reads from
and writes to. Verified against project `mnxfmzrcsbxqjswfuqeh` on 2026-04-20.

---

## Tables used by brand agents

### `brands` (new — see migration 001)

Registry of all active brands. One row per brand.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK, gen_random_uuid() |
| slug | text | UNIQUE. Short identifier: "ae", "mfd", "joe" |
| name | text | Full brand name: "Artificial Education" |
| handle | text | Social handle: "@artificialeducation" |
| agent_name | text | Service name: "ae-intel" |
| active | bool | Default true. Set false to pause without deleting. |
| created_at | timestamptz | Default now() |

**Agents read this table** to confirm their `brand_slug` is registered before
writing any content_jobs rows.

---

### `signals`

Raw intelligence signals written by brand agents.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| brand | text | Brand slug: "ae", "mfd", "KAL" |
| topic | text | Headline or topic string (max 500 chars) |
| hook | text | Short summary (max 300 chars) |
| score | int | 0–10 |
| why_now | text | Full reasoning (max 2000 chars) |
| source | text | Feed name or source type |
| source_agent | text | NEW — which agent wrote this: "ae-intel", "kal" |
| created_at | timestamptz | Default now() |

**Write pattern (agent):**
```python
supabase.table("signals").insert({
    "brand":        brand_slug,
    "topic":        topic[:500],
    "hook":         hook[:300],
    "score":        score,
    "why_now":      why_now[:2000],
    "source":       feed_name,
    "source_agent": agent_name,
}).execute()
```

---

### `content_jobs`

The handoff table between agents and Scribe/Content Engine.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| brand | text | Brand slug: "ae", "mfd" |
| renderer | text | Default "remotion" |
| template | text | Composition key: "ae-signal", "mfd-market-focus" |
| content | jsonb | `{hook, points, cta}` or `{raw_signal, template, brand}` |
| format | text | Default "vertical_30s". Also: "square_30s", "landscape_30s" |
| status | text | See status lifecycle below |
| output_url | text | Filled by Content Engine after render |
| source_agent | text | NEW — which agent created this job: "ae-intel" |
| signal_ids | uuid[] | NEW — signals table IDs this job was derived from |
| created_at | timestamptz | Default now() |
| updated_at | timestamptz | Default now() |

**Status lifecycle:**
```
pending → scripted → rendered → approved → posted
                                         → rejected
```

| Status | Set by |
|--------|--------|
| pending | Intelligence agent (ae-intel, etc.) |
| scripted | Scribe worker |
| rendered | Content Engine |
| approved | Human in HQ Dashboard |
| posted | HQ Dashboard after publish |
| rejected | Human in HQ Dashboard |

**Write pattern (agent):**
```python
signal_row = supabase.table("signals").insert({...}).execute()
signal_id  = signal_row.data[0]["id"]

supabase.table("content_jobs").insert({
    "brand":        brand_slug,
    "template":     template,
    "content":      {"hook": hook, "points": points, "cta": cta},
    "format":       "vertical_30s",
    "status":       "pending",
    "source_agent": agent_name,
    "signal_ids":   [signal_id],
}).execute()
```

---

### `agent_logs`

Operational event log. Every agent writes here for observability.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| service | text | Default "kal". Set to agent_name: "ae-intel" |
| event | text | Event key: "agent_started", "scan_complete", "job_created" |
| detail | jsonb | Arbitrary metadata |
| created_at | timestamptz | Default now() |

**Write pattern (agent):**
```python
supabase.table("agent_logs").insert({
    "service": agent_name,
    "event":   "scan_complete",
    "detail":  {"signals_found": 3, "jobs_created": 1},
}).execute()
```

---

## Tables agents do NOT touch

| Table | Owner | Why |
|-------|-------|-----|
| `markets_log` | Kal | Trading data, private |
| `ai_decisions` | Kal | Trading data, private |
| `trades` | Kal | Trading data, private |
| `bot_config` | Kal | Kal-specific runtime config |
| `daily_summary` | Kal | Kal-specific P&L |
| `strategy_report` | Kal | Kal-specific analysis |
| `bot_communications` | Kal | Kal legacy comms log |
| `rss_articles` | Kal | Kal-specific RSS log |

---

## RLS policies

All tables have RLS enabled. Brand agents authenticate with the
`SUPABASE_SERVICE_ROLE_KEY` — this bypasses RLS.

Never expose the service role key in frontend code or client-side environments.
