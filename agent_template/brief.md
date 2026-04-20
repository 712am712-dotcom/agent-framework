# Brand Brief — {Brand Name}

> Local copy. Authoritative version: agent-framework/briefs/{brand_slug}.md
> Fill in all 7 fields before writing any code or prompts.

---

## Field 1 — Brand Handle

```
@{handle}
```

---

## Field 2 — Agent Name

```
{brand_slug}-intel
```

---

## Field 3 — Persona

{Who the agent embodies. Be specific — name a real person or a highly specific
archetype with a recognizable voice. No generic descriptions.}

---

## Field 4 — Niche / Domain

{One tight sentence: what this brand is ONLY about, including the angle that
differentiates it from similar accounts.}

---

## Field 5 — Filter Logic

```
ACCEPT: {what signals pass}
REJECT: {what gets filtered without an LLM call}
```

---

## Field 6 — Output Format

```
Format: {format name}
Structure: {slot 1} → {slot 2} → {slot 3} → {CTA}

Slot 1 (hook):     {description}
Slot 2 (points[0]): {description}
Slot 3 (points[1]): {description}
Slot 4 (points[2]): {description — omit if only 2 points}
CTA:               {fixed CTA string}
```

---

## Field 7 — Signal Sources

```
PRIMARY:
  - {source name} (rss) — {url}
  - {source name} (api) — {endpoint}

SECONDARY:
  - {source name} (rss) — {url}
```
