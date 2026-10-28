"""Collect one snapshot of current GarirBazar car listings.

Run from the ml/ folder:
    .venv/Scripts/python.exe -I -m shotti_ml.collect.run --pages 40

It fetches page 1 to learn how many listing pages exist, then a random sample of the
rest, so the snapshot spans old and new ads rather than only the newest. One page holds
about 20 cars. Output is a JSON-lines file under data/raw/garirbazar/snapshots/, which
git ignores: raw listings are the site's content and stay on this machine.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .fetch import FetchError, Halt, PoliteFetcher
from .garirbazar import page_url, parse_listing_page, total_pages

SNAPSHOTS = Path(__file__).resolve().parents[3] / "data" / "raw" / "garirbazar" / "snapshots"

#: Guard rails: a typo must not turn into a large crawl, or a fast one.
MAX_PAGES_PER_RUN = 300
MIN_DELAY_SECONDS = 2.0


def collect(
    fetcher: PoliteFetcher,
    n_pages: int,
    seed: int,
    *,
    filters: dict[str, str | int] | None = None,
    now: datetime | None = None,
    log: Callable[[str], None] = print,
) -> tuple[list[dict], dict]:
    """Fetch `n_pages` listing pages (page 1 plus a random sample) and return the listings and a summary."""
    observed_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    started = time.monotonic()

    first = fetcher.get(page_url(1, filters))
    listings = {l.id: l for l in parse_listing_page(first, observed_at)}
    pages = total_pages(first) or 1
    log(f"{pages:,} listing pages in total; sampling {min(n_pages, pages)}")

    chosen = random.Random(seed).sample(range(2, pages + 1), min(max(n_pages - 1, 0), pages - 1))
    failed = halted = 0
    for number in chosen:
        try:
            for listing in parse_listing_page(fetcher.get(page_url(number, filters)), observed_at):
                listings[listing.id] = listing
        except FetchError as error:
            failed += 1
            log(f"skipped page {number}: {error}")
        except Halt as error:
            halted = 1
            log(f"stopping early: {error}")
            break
        if len(listings) and (len(chosen) < 10 or (chosen.index(number) + 1) % 10 == 0):
            log(f"  {len(listings)} listings so far")

    summary = {
        "observed_at": observed_at.isoformat(),
        "pages_in_site": pages,
        "pages_requested": fetcher.requests,
        "pages_failed": failed,
        "halted_early": bool(halted),
        "filters": filters or {},
        "listings": len(listings),
        "seconds": round(time.monotonic() - started),
    }
    return [l.as_dict() for l in listings.values()], summary


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pages", type=int, default=40, help=f"listing pages to fetch (max {MAX_PAGES_PER_RUN})")
    parser.add_argument("--delay", type=float, default=3.0, help=f"seconds between requests (min {MIN_DELAY_SECONDS})")
    parser.add_argument("--seed", type=int, default=0, help="seed for choosing which pages to sample")
    parser.add_argument("--min-price", type=int, help="only ads asking at least this many taka (uses the site's own price filter)")
    parser.add_argument("--max-price", type=int, help="only ads asking at most this many taka")
    parser.add_argument("--condition", type=int, choices=(1, 2, 3), help="the site's filter: 1 new, 2 used, 3 imported (reconditioned)")
    args = parser.parse_args(argv)

    if not 1 <= args.pages <= MAX_PAGES_PER_RUN:
        parser.error(f"--pages must be between 1 and {MAX_PAGES_PER_RUN}")
    if args.delay < MIN_DELAY_SECONDS:
        parser.error(f"--delay must be at least {MIN_DELAY_SECONDS} seconds")

    filters: dict[str, str | int] = {}
    if args.min_price is not None or args.max_price is not None:
        # The site returns nothing for a lone minimum, so a missing bound gets a harmless extreme.
        filters["minprice"] = args.min_price if args.min_price is not None else 0
        filters["maxprice"] = args.max_price if args.max_price is not None else 900_000_000
    if args.condition:
        filters["condition"] = args.condition

    fetcher = PoliteFetcher(delay=args.delay)
    try:
        rows, summary = collect(fetcher, args.pages, args.seed, filters=filters)
    except Halt as error:
        print(f"Nothing collected: {error}")
        return 1

    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.fromisoformat(summary["observed_at"]).strftime("%Y-%m-%dT%H%M")
    path = SNAPSHOTS / f"{stamp}{'-filtered' if filters else ''}.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {len(rows)} listings to {path}")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
