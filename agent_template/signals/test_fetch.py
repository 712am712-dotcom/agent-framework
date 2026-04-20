"""
signals/test_fetch.py — Smoke test for signal sources.

Run before deploying to verify all feeds are reachable:
    python signals/test_fetch.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from signals.adapters.rss import fetch_feed
from signals.sources import get_primary_feeds, get_secondary_feeds


async def main() -> None:
    primary   = get_primary_feeds()
    secondary = get_secondary_feeds()
    all_feeds = [("PRIMARY",   name, url) for name, url in primary] + \
                [("SECONDARY", name, url) for name, url in secondary]

    if not all_feeds:
        print("ERROR: No feeds configured. Fill in config/brand_config.json first.")
        sys.exit(1)

    print(f"Testing {len(all_feeds)} feed(s)...\n")

    any_failed = False
    for priority, name, url in all_feeds:
        articles = await fetch_feed(url, name, timeout=15.0)
        if articles:
            print(f"  [{priority}] {name}: OK — {len(articles)} articles")
            print(f"    Latest: {articles[0]['title'][:80]}")
        else:
            print(f"  [{priority}] {name}: FAILED — no articles returned")
            if priority == "PRIMARY":
                any_failed = True

    print()
    if any_failed:
        print("FAIL: One or more PRIMARY feeds returned no articles.")
        sys.exit(1)
    else:
        print("PASS: All primary feeds reachable.")


if __name__ == "__main__":
    asyncio.run(main())
