# Agent Framework

Reusable template and documentation for brand intelligence agents.

Every brand agent (ae-intel, joe-intel, hope-intel, etc.) is a standalone service
that reads raw signals, filters them through a brand-specific persona and logic,
and writes structured `content_jobs` rows to Supabase for Scribe + Content Engine
to pick up.

**Kal is not part of this framework.** Kal is a personal trading agent with its
own private repo. This framework is for content-intelligence agents only.

---

## What lives here

| Path | Purpose |
|------|---------|
| `/briefs/` | Central archive of all brand briefs (one file per brand) |
| `/agent_template/` | Cloneable starter for a new agent repo |
| `/supabase/` | Schema documentation + migrations for multi-brand tables |
| `SCAFFOLDING.md` | Step-by-step checklist to spin up a new agent in < 2 hours |

---

## The pipeline every agent follows

```
Signal sources (RSS / API / scraper)
        │
        ▼
  signals table   ← agent writes raw signals here
        │
        ▼
  Brand filter + LLM prompt  ← persona + filter logic from /prompts/
        │
        ▼
  content_jobs table  ← pending row written with brand_id + source_agent
        │
        ▼
  Scribe  → scripts the content
        │
        ▼
  Content Engine  → renders MP4 / image
        │
        ▼
  HQ Dashboard  → approve / reject / post
```

---

## Quick start — new brand agent

1. Read `SCAFFOLDING.md`
2. Fill in `briefs/BRIEF_TEMPLATE.md` for your brand
3. `git clone https://github.com/712am712-dotcom/agent-framework agent_template`  
   or fork the template into a new repo
4. Follow the 9-step checklist in `SCAFFOLDING.md`

---

## Conventions

- **One agent per brand per repo.** Keep ae-intel, joe-intel, etc. separate.
- **No shared state between agents.** Each agent reads its own signals and writes
  its own `content_jobs` rows. Coordination happens at the Supabase layer.
- **Prompts live with the agent, briefs live here.** The `/briefs/` directory is
  the authoritative archive; each agent repo has a local copy at `/brief.md`.
- **Signal adapters are shared code.** Common RSS/API adapters live in
  `/agent_template/signals/` and are copied (not imported) into each agent.
  Keep agent-specific scoring in the prompt layer, not the adapter.
