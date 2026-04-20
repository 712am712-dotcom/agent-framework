"""
signals/scorer.py — Brand-specific pre-filter and keyword scoring.

This runs BEFORE any LLM call to discard obvious noise cheaply.
The LLM prompt in prompts/{agent_name}_prompt.txt handles the final
accept/reject decision and content generation.

Customize the keyword lists and scoring logic for your brand's niche.
"""
from __future__ import annotations

import re

# ── Keywords that indicate a relevant signal ───────────────────────────────────
# Replace these with keywords specific to your brand's niche.

HIGH_PRIORITY_KEYWORDS: list[str] = [
    # Add keywords that are strong signals for your niche
    # Example for AI niche:
    # "openai", "anthropic", "gpt-5", "gemini", "released", "launched",
    # "model", "benchmark", "raises", "acquisition"
]

LOW_PRIORITY_KEYWORDS: list[str] = [
    # Add keywords that indicate off-niche content to skip entirely
    # Example: "sports", "celebrity", "entertainment", "recipe"
]

# ── Minimum keyword score to pass pre-filter ──────────────────────────────────
# Articles scoring below this are discarded without an LLM call.
# 0 = pass everything to LLM (expensive). 1 = must match at least one keyword.
MIN_KEYWORD_SCORE = 1


def keyword_priority(title: str, description: str = "") -> str:
    """
    Quick keyword pre-filter. Returns:
      "high"    — pass to LLM for full evaluation
      "context" — save to context file but skip LLM
      "skip"    — discard entirely

    Runs before any LLM call. Keep this fast and cheap.
    """
    text = (title + " " + description).lower()

    # Hard skip: low-priority content
    if any(kw in text for kw in LOW_PRIORITY_KEYWORDS):
        return "skip"

    # High priority: matches niche keywords
    if any(kw in text for kw in HIGH_PRIORITY_KEYWORDS):
        return "high"

    # Default: save as context (useful for morning brief) but don't call LLM
    return "context"


def score_article(
    title: str,
    description: str = "",
    source_name: str = "",
    is_primary_source: bool = False,
) -> int:
    """
    Pre-LLM score 0–10 based on keyword density and source trust.
    Higher score = higher priority for LLM evaluation.

    This is a cheap filter — the LLM prompt does the real scoring.
    """
    text  = (title + " " + description).lower()
    score = 0

    # Keyword matches
    high_matches = sum(1 for kw in HIGH_PRIORITY_KEYWORDS if kw in text)
    score += min(6, high_matches * 2)

    # Source trust bonus
    if is_primary_source:
        score += 2

    # Specificity: named entity or number present
    has_number = bool(re.search(r'\$[\d,.]+[BMKbmk]?|\d+[\d,.]*\s*(?:billion|million|%)', title, re.I))
    if has_number:
        score += 1

    return min(10, score)
