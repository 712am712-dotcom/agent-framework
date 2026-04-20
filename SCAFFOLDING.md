# Scaffolding a New Brand Agent

A new brand agent should be deployable in under 2 hours once the brief is written.
Work through this checklist top to bottom. Do not skip steps.

---

## Pre-flight: Write the Brand Brief

Before touching any code, fill in the 7-field brief. This is the only input you
need to derive everything else. Template: `briefs/BRIEF_TEMPLATE.md`.

**Time estimate: 15–30 min.** If a field takes longer than 5 minutes it means the
brand strategy isn't clear yet — resolve that first.

---

## The 9-Step Checklist

### Step 1 — Write `/brief.md`

Copy `briefs/BRIEF_TEMPLATE.md` into your new agent repo as `/brief.md`.
Fill in all 7 fields. Keep each answer to 2–3 sentences max.

**Done when:** Every field is filled. No placeholder text remains.

---

### Step 2 — Fork or copy the agent template

```bash
# Option A: fork on GitHub (recommended for a real agent)
# Go to https://github.com/712am712-dotcom/agent-framework
# Click "Use this template" → new repo named {brand}-intel

# Option B: clone and re-init
git clone https://github.com/712am712-dotcom/agent-framework {brand}-intel
cd {brand}-intel
rm -rf .git
git init
git remote add origin https://github.com/712am712-dotcom/{brand}-intel.git
```

**Done when:** New repo exists, clean git history, agent_template contents are at root.

---

### Step 3 — Derive the agent prompt from the brief

Open `prompts/{agent_name}_prompt.txt` (copy from `agent_template/prompts/PROMPT_TEMPLATE.txt`).

Map each brief field to the prompt:

| Brief field | Prompt section |
|-------------|---------------|
| Persona | ROLE block at top |
| Niche / domain | TOPIC FILTER section |
| Filter logic | ACCEPT / REJECT rules |
| Output format | OUTPUT FORMAT section |

**Done when:** Prompt file has no `{placeholder}` tokens. Test it manually with one
real headline from the signal sources before proceeding.

---

### Step 4 — Fill `config/brand_config.json`

Open `config/brand_config.json` (copy from `agent_template/config/brand_config.template.json`).

Required fields:
- `brand_id` — matches the slug in Supabase `brands` table
- `agent_name` — e.g. `"ae-intel"`
- `posting_schedule` — array of UTC hours when the agent should fire
- `target_platforms` — e.g. `["instagram", "tiktok"]`
- `cta` — the fixed call-to-action appended to all content
- `voice` — one-line tone descriptor used by Scribe
- `visual_template` — Remotion composition ID (e.g. `"AESignal-vertical-30s"`)

**Done when:** JSON validates (`python -c "import json; json.load(open('config/brand_config.json'))"`)

---

### Step 5 — Wire signal sources

Edit `signals/sources.py` (or `sources.ts`). Configure:

1. Which RSS feeds to poll and at what frequency
2. Which API endpoints to call (with auth)
3. Any custom scrapers

Use the shared adapters in `signals/adapters/`. Write brand-specific scoring in
`signals/scorer.py` if the generic scorer isn't enough.

**Done when:** Running `python signals/test_fetch.py` returns at least 3 articles
from live sources with no errors.

---

### Step 6 — Add a row to Supabase `brands` table

```sql
INSERT INTO brands (slug, name, handle, agent_name, active)
VALUES (
  '{brand_slug}',          -- e.g. 'ae'
  '{Full Brand Name}',     -- e.g. 'Artificial Education'
  '@{handle}',             -- e.g. '@artificialeducation'
  '{agent_name}',          -- e.g. 'ae-intel'
  true
);
```

Also copy your `/brief.md` into the central archive:
```bash
cp brief.md ../agent-framework/briefs/{brand_slug}.md
git -C ../agent-framework add briefs/{brand_slug}.md
git -C ../agent-framework commit -m "briefs: add {brand_slug} brand brief"
```

**Done when:** `SELECT * FROM brands WHERE slug = '{brand_slug}';` returns 1 row.

---

### Step 7 — Deploy to Railway as its own service

1. Push the agent repo to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Select `{brand}-intel` repo
4. Set env vars (see `.env.example` in the agent template):
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `ANTHROPIC_API_KEY`
   - `BRAND_SLUG` (matches Supabase `brands.slug`)
5. Deploy. Check Railway logs — agent should log `agent_started brand={slug}`.

**Done when:** Railway shows green deploy. Logs show at least one successful
signal fetch within the first scan interval.

---

### Step 8 — Register with HQ Dashboard

Open the HQ Dashboard admin panel and add the new brand:
- Brand slug (must match Supabase)
- Agent name
- Posting platforms
- Whether human approval is required before posting

**Done when:** Brand appears in the HQ Dashboard brand list. Content jobs from
this agent show up in the queue view.

---

### Step 9 — End-to-end test

Run the full pipeline:

```bash
# Trigger one manual scan
python main.py --once

# Check Supabase: signal was written
# SELECT * FROM signals WHERE brand = '{brand_slug}' ORDER BY created_at DESC LIMIT 1;

# Check Supabase: content_job was created
# SELECT id, status, source_agent, template FROM content_jobs
#   WHERE brand = '{brand_slug}' ORDER BY created_at DESC LIMIT 1;

# Wait for Scribe to pick it up (status → scripted)
# Wait for Content Engine to render (status → rendered)
# Approve in HQ Dashboard → status → approved
```

**Done when:** A rendered MP4 appears in the HQ Dashboard queue with status `rendered`.
The full path raw signal → agent → content_job → scripted → rendered must complete
without manual intervention.

---

## Agent template directory map

```
{brand}-intel/
├── brief.md                    ← 7-field brand brief (local copy)
├── main.py                     ← entry point (scheduler + scan loop)
├── README.md                   ← required sections (see agent_template/README.md)
├── .env.example                ← required env vars, no secrets
├── requirements.txt            ← Python deps
├── config/
│   └── brand_config.json       ← voice, schedule, platforms, CTA
├── prompts/
│   └── {agent_name}_prompt.txt ← persona + filter + output format
└── signals/
    ├── sources.py              ← feed URLs, API endpoints
    ├── scorer.py               ← brand-specific signal scoring
    ├── adapters/
    │   ├── rss.py              ← generic RSS fetcher
    │   └── api.py              ← generic API fetcher
    └── test_fetch.py           ← smoke test for signal sources
```

---

## Time budget

| Step | Estimated time |
|------|----------------|
| Brief | 15–30 min |
| Fork + setup | 5 min |
| Prompt derivation | 20–30 min |
| brand_config.json | 10 min |
| Signal sources | 20–30 min |
| Supabase row | 5 min |
| Railway deploy | 10–15 min |
| HQ Dashboard | 5 min |
| End-to-end test | 15–20 min |
| **Total** | **~2 hours** |

The brief is the long pole. Everything else is mechanical once the brief is clear.
