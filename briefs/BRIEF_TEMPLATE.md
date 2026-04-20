# Brand Brief — {Brand Name}

> This is the source of truth for the agent's identity.
> Fill in all 7 fields before writing any code or prompts.
> Keep each answer to 2–3 sentences max.
> Once complete, copy this file to your agent repo as `/brief.md`
> AND commit it here to the central archive at `briefs/{brand_slug}.md`.

---

## Field 1 — Brand Handle

The public-facing social handle this agent creates content for.

```
@{handle}
```

Example: `@artificialeducation`

---

## Field 2 — Agent Name

The name of the intelligence agent (service name in Railway, source_agent in Supabase).

```
{brand_slug}-intel
```

Example: `ae-intel`

---

## Field 3 — Persona

Who the agent is embodying when it writes content. Must be specific — name a real
person or a highly specific archetype with a recognizable voice and worldview.
Generic descriptions ("motivational agent", "finance expert") are not acceptable.

```
{persona}
```

Good examples:
- "Eric Thomas as a professional speaker — intense, high-energy, uses personal story
  to make abstract ideas concrete, every post ends with a direct challenge to the
  audience"
- "Michael Saylor explaining Bitcoin — supremely confident, uses first-principles
  arguments, dismisses conventional finance with specific data points"
- "The Kobeissi Letter — data-first, no hype, every claim backed by a number,
  writes like a professional analyst briefing institutional clients"

Bad examples:
- "A motivational finance educator" ← too vague
- "An AI expert who explains things simply" ← no voice
- "A friendly financial advisor" ← no personality

---

## Field 4 — Niche / Domain

The content lane. One tight sentence: what is this brand ONLY about?
Include the specific angle that differentiates it from every other finance/AI/etc.
account.

```
{niche}
```

Examples:
- "AI tools and model releases — specifically what changes for non-technical
  creators and knowledge workers, never for developers"
- "Macro market moves explained in terms of everyday household financial impact —
  how Fed decisions affect your mortgage, not your portfolio"
- "Prediction market alpha — teaching retail traders how professional bettors
  think about probability vs price"

---

## Field 5 — Filter Logic

One sentence: what signals does this agent accept, and what does it reject?
This becomes the ACCEPT/REJECT rules in the prompt.

```
ACCEPT: {what passes}
REJECT: {what gets filtered}
```

Examples:
- "ACCEPT: AI model releases, product launches, and funding rounds from named
  companies with a specific number or capability claim. REJECT: opinion pieces,
  general AI trends without a named entity, anything older than 48 hours."
- "ACCEPT: Fed decisions, CPI/jobs reports, and earnings moves that shift the
  S&P by more than 0.5%. REJECT: individual stock picks, crypto, anything
  without a household economic consequence."

---

## Field 6 — Output Format

The structural template for every piece of content this agent produces.
Name the format pattern and describe each slot. This maps directly to the
Remotion composition's input props (hook, points, cta).

```
Format: {format name}
Structure: {slot 1} → {slot 2} → {slot 3} → {CTA}
```

Examples:
- "Event → Mechanism → Personal Impact → CTA: Follow for daily market moves"
  - Slot 1 (hook): what happened, in one punchy sentence with a number
  - Slot 2 (points[0]): why it happened (the mechanism)
  - Slot 3 (points[1]): what it means for your money specifically
  - CTA: fixed"
- "Claim → Proof → Implication → CTA"
  - Slot 1 (hook): a bold claim that challenges a common belief
  - Slot 2 (points[0]): the specific data that supports it
  - Slot 3 (points[1]): what you should do differently as a result
  - CTA: fixed"

---

## Field 7 — Signal Sources

Where the raw material comes from. List each source with its type and URL/endpoint.
Mark each as PRIMARY (always polled) or SECONDARY (polled if primary is slow).

```
PRIMARY:
  - {source name} ({type: rss | api | scraper}) — {url or endpoint}

SECONDARY:
  - {source name} ({type}) — {url or endpoint}
```

Example:
```
PRIMARY:
  - AI News (rss) — https://www.artificialintelligence-news.com/feed/
  - TechCrunch (rss) — https://feeds.feedburner.com/techcrunch
  - Hacker News (rss) — https://hnrss.org/frontpage

SECONDARY:
  - AI Newsletter (rss) — https://buttondown.email/ainews/rss
  - The Verge (rss) — https://feeds.feedburner.com/TheVerge
```

---

## Checklist before submitting this brief

- [ ] All 7 fields filled — no placeholder text
- [ ] Persona names a specific person or highly specific archetype (not generic)
- [ ] Filter logic is one sentence, binary (accept/reject), no grey area
- [ ] Output format maps to Remotion input props (hook, points, cta)
- [ ] Signal sources list at least 2 PRIMARY sources with live URLs verified
- [ ] File saved to `briefs/{brand_slug}.md` in the agent-framework central archive
- [ ] File copied to `/brief.md` in the agent repo
