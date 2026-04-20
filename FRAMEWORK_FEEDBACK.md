# Framework Feedback — ae-intel Build Session

**Session:** 2026-04-20
**Agent built:** ae-intel (@artificialeducation)
**Status:** First agent built on this framework. This is a stress-test session.

This document captures every moment during the ae-intel build where something
in the framework felt clunky, required special-case code, or will cause friction
when building joe-intel and future agents. Fix these before the next build.

---

## BLOCKER 1 — Railway: No CLI command to create a new service

**Severity:** High — manually blocked deployment.

**What happened:**
`railway up --service ae-intel` returns "Service not found" because the service
doesn't exist yet. The Railway GraphQL API `serviceCreate` mutation is blocked
by "trial expired" on the account. There is no `railway service create` CLI
command. The only path to create a new service is via the Railway web UI.

**Required fix:**
The SCAFFOLDING.md Step 7 says "Go to railway.app → New Project → Deploy from
GitHub." This needs to be more explicit:

1. The ae-intel service should be added to the **existing** `courteous-gentleness`
   project (not a new project), alongside `kalshi-bot` and `scribe`.
2. The `courteous-gentleness` project needs to be on a Railway plan that allows
   more than 2 services.
3. Add to SCAFFOLDING.md: "Go to railway.app → courteous-gentleness → New Service
   → GitHub Repo → select {brand}-intel → set env vars (see .env.example)."

**Current workaround:**
Create the service manually in Railway UI, connect to GitHub repo
`712am712-dotcom/ae-intel`, set env vars from the list below, and Railway
will auto-deploy on push to main.

**Env vars to set in Railway for ae-intel:**
```
SUPABASE_URL           — same as kalshi-bot
SUPABASE_SERVICE_ROLE_KEY — same as kalshi-bot
ANTHROPIC_API_KEY      — same as kalshi-bot
BRAND_SLUG             = ae
AGENT_NAME             = ae-intel
SCAN_INTERVAL_MINUTES  = 30
CLAUDE_MODEL           = claude-haiku-4-5-20251001
REDDIT_MIN_SCORE       = 500
```

---

## FRICTION 2 — RSS feed URLs: Company blogs often don't have RSS feeds

**Severity:** Medium — caught during smoke test, easy to fix per-agent.

**What happened:**
The brief spec listed official company blogs for OpenAI/Anthropic/Google/Meta.
Three of the seven primary feed URLs were dead (404):
- `https://www.anthropic.com/news/rss.xml` → 404 (Anthropic has no RSS feed at all)
- `https://www.theverge.com/ai-artificial-intelligence/rss/index.xml` → 404
  (correct URL is `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml`)
- `https://ai.meta.com/blog/rss/` → 404 (Meta AI blog has no RSS)

**Required fix:**
Add a "verified feed URLs" section to BRIEF_TEMPLATE.md Field 7 with a note
that feed URLs must be smoke-tested before committing to the brief. Company
official blogs frequently don't publish RSS — fallback to: Techmeme,
TechCrunch, and The Verge pick them up within minutes anyway.

Add a known-dead-feeds warning:
```
KNOWN: Anthropic has no RSS feed as of 2026-04-20. Use Techmeme as proxy.
KNOWN: Meta AI Blog (ai.meta.com) has no RSS. Use research.facebook.com/feed/
```

---

## FRICTION 3 — Post-type rotation: No "current state" concept in framework

**Severity:** Medium — required custom logic in main.py.

**What happened:**
The template `main.py` has no concept of post-type rotation (News/Concept/Tool).
ae-intel needed to:
1. Query Supabase to find the last content_job and read its `content.post_type`
2. Advance the sequence and inject `{post_type}` into the prompt
3. Handle "never two Concept back-to-back" logic

This is brand-specific but will be needed by every brand with a content rotation
strategy (which is all of them).

**Proposed fix:**
Add an optional `post_type_rotation` block to `brand_config.template.json`
(already added for ae-intel). The framework template's `main.py` should include
a commented-out `get_next_post_type_from_db()` function showing the pattern,
and the prompt template should include `{post_type}` as a documented placeholder.

---

## FRICTION 4 — Opening sequence: No "editorial hold" status in content_jobs

**Severity:** Medium — worked around it but the workaround is fragile.

**What happened:**
The brief requires posts 2–5 to be human-reviewed before any auto-generated
content enters the queue. The current `content_jobs` schema only has:
`pending → scripted → rendered → approved → posted`

The `pending` status means "ready for Scribe to pick up." There's no "human
approval required before Scribe touches this" status.

**Workaround used:**
ae-intel writes `content_jobs` with `status=pending` but adds `opening_sequence_slot`
to the content JSONB. This relies on HQ Dashboard showing the metadata and humans
not approving them — but Scribe might pick them up anyway if it's running.

**Proposed fix:**
Add a `queued` status to the `content_jobs` lifecycle:
```
queued → pending → scripted → rendered → approved → posted
```
`queued` = written by agent, waiting for human to promote to `pending`.
`pending` = approved for scripting, Scribe will pick up.

This requires:
1. Supabase migration to add `queued` as a valid status value
2. Scribe must filter for `status=pending` (not `queued`)
3. HQ Dashboard "promote to queue" button for `queued` jobs

---

## FRICTION 5 — Prompt template: `{post_type}` not a standard placeholder

**Severity:** Low — easy to add.

**What happened:**
The `PROMPT_TEMPLATE.txt` defines `{title}`, `{description}`, `{source}` as
the three standard input placeholders. ae-intel needed a fourth: `{post_type}`
for the rotation-aware evaluation. This was injected in `_load_prompt()` before
passing to the evaluate function.

**Proposed fix:**
Add `{post_type}` to `PROMPT_TEMPLATE.txt` as an optional fourth placeholder
with documentation. Also update `evaluate_signal()` in `main.py` template to
accept and inject it (default to `"A"` if not set in brand_config).

---

## FRICTION 6 — Reddit adapter: Not in the framework, needs to be

**Severity:** Low — easy fix.

**What happened:**
The brief specified Reddit r/singularity and r/LocalLLaMA as signal sources.
The framework has `rss.py` and `api.py` adapters but no `reddit.py` adapter.
Writing a Reddit adapter required:
1. Understanding Reddit's `.json` API endpoint format
2. Handling score-based filtering (posts ≥500 upvotes)
3. Differentiating self-posts from link posts (permalink vs external URL)
4. Proper User-Agent (Reddit blocks generic ones)

This is likely needed for any social/culture-focused brand agent.

**Proposed fix:**
Add `signals/adapters/reddit.py` to `agent_template/signals/adapters/` with
the full implementation from ae-intel. Also add `"reddit"` as a valid source
type in `brand_config.template.json` and `sources.py`.

---

## WHAT WORKED WELL

1. **Brief-first workflow** — having all 7 fields filled before writing code
   made every subsequent decision obvious. No ambiguity about filter logic,
   output format, or persona. This is the right process.

2. **scorer.py separation** — keeping the entity+action pre-filter completely
   separate from the LLM prompt means LLM budget is not wasted. The named-entity
   + action-word detector from Kal translated cleanly.

3. **brand_config.json as single config source** — sources.py, scorer.py, and
   main.py all read from brand_config.json. Adding a new source is one JSON edit.

4. **agent_template structure** — the directory layout maps exactly to the
   deployable service with no translation step. What you clone is what you deploy.

5. **Supabase schema** — the `brands` table verification before first write is
   a good guard. The `source_agent` field on both `signals` and `content_jobs`
   makes multi-brand observability straightforward.

---

## FRICTION 7 — Prompt filename must use hyphens matching AGENT_NAME

**Severity:** Low but causes confusing runtime crash.

**What happened:**
`_load_prompt()` builds the path as `f"{AGENT_NAME}_prompt.txt"`. With
`AGENT_NAME=ae-intel`, this resolves to `ae-intel_prompt.txt`. The file was
created as `ae_intel_prompt.txt` (underscore). Silent at commit time, crashes
at first run with `FileNotFoundError`.

**Fix:**
Document in SCAFFOLDING.md Step 3: "Name the prompt file
`{agent_name}_prompt.txt` where `agent_name` exactly matches the `AGENT_NAME`
env var (hyphens, not underscores). Example: `ae-intel_prompt.txt`."

Or: sanitize in `_load_prompt()` by replacing `-` with `_` in the filename.

---

## PRIORITY ORDER FOR FIXES (before building joe-intel)

1. **P0:** Add `queued` status to content_jobs schema (Supabase migration needed)
2. **P1:** Add Reddit adapter to agent_template
3. **P1:** Update SCAFFOLDING.md Railway step to use existing project + manual UI creation
4. **P2:** Add `{post_type}` placeholder and rotation pattern to PROMPT_TEMPLATE.txt
5. **P2:** Add known-dead-feeds warning to BRIEF_TEMPLATE.md Field 7
