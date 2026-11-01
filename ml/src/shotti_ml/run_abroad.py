"""Collect real export prices from Japan for the catalogue cars that have a local price.

Run from the ml/ folder:  .venv/Scripts/python.exe -I -m shotti_ml.run_abroad
For each car, reads SBT Japan's stock pages for its model, keeps the cars of the catalogue's
build year whose model code matches the catalogue's engine and fuel, and summarises their FOB
prices. Writes the matched cars (attributes and price only) to data/raw/sbt/<date>.csv and the
summary to ../web/src/lib/abroad.json. For partner stock, which gives no build year, the
registration year stands in. A listing whose engine size is more than CC_SLACK away from the
catalogue's is left out.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

import numpy as np

from .collect.fetch import FetchError, PoliteFetcher
from .collect.sbt import PER_PAGE, Listing, page_url, parse_page
from .export import catalogue as read_catalogue

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "ml" / "data" / "raw" / "sbt"
OUT = ROOT / "web" / "src" / "lib" / "abroad.json"

MAX_PAGES = 3
CC_SLACK = 100
#: fewer listings than this and the catalogue keeps its example price
MIN_LISTINGS = 5
MARKET_TS = ROOT / "web" / "src" / "lib" / "market.ts"
CARS_TS = ROOT / "web" / "src" / "lib" / "cars.ts"

# catalogue make and model -> SBT make and model slugs, and the model codes of the catalogue's
# generation and engine (a listing matches if its code contains one of them)
TARGETS: dict[tuple[str, str], tuple[str, str, list[str]]] = {
    ("Toyota", "Axio"): ("toyota", "corolla-axio", ["NRE161"]),
    ("Toyota", "Axio Hybrid"): ("toyota", "corolla-axio", ["NKE165"]),
    ("Toyota", "Fielder"): ("toyota", "corolla-fielder", ["NRE161"]),
    ("Toyota", "Fielder Hybrid"): ("toyota", "corolla-fielder", ["NKE165"]),
    ("Toyota", "Premio"): ("toyota", "premio", ["NZT260"]),
    ("Toyota", "Allion"): ("toyota", "allion", ["NZT260"]),
    ("Toyota", "Aqua"): ("toyota", "aqua", ["MXPK1"]),
    ("Toyota", "Yaris Hybrid"): ("toyota", "yaris", ["MXPH1"]),
    ("Toyota", "Prius"): ("toyota", "prius", ["ZVW5"]),
    ("Toyota", "Corolla Cross Hybrid"): ("toyota", "corolla-cross", ["ZVG1"]),
    ("Toyota", "Yaris Cross Hybrid"): ("toyota", "yaris-cross", ["MXPJ1"]),
    ("Toyota", "Raize"): ("toyota", "raize", ["A200A", "A210A"]),
    ("Toyota", "C-HR"): ("toyota", "c-hr", ["NGX10", "NGX50"]),
    ("Toyota", "C-HR Hybrid"): ("toyota", "c-hr", ["ZYX1"]),
    ("Toyota", "Harrier"): ("toyota", "harrier", ["MXUA8"]),
    ("Toyota", "Harrier Hybrid"): ("toyota", "harrier-hybrid", ["AXUH8"]),
    ("Toyota", "RAV4"): ("toyota", "rav4", ["MXAA5"]),
    ("Toyota", "RAV4 Hybrid"): ("toyota", "rav4", ["AXAH5"]),
    ("Toyota", "Camry Hybrid"): ("toyota", "camry", ["AXVH7"]),
    ("Toyota", "Crown Crossover"): ("toyota", "crown", ["AZSH35"]),
    ("Toyota", "Land Cruiser Prado TX"): ("toyota", "land-cruiser-prado", ["TRJ150"]),
    ("Toyota", "Noah"): ("toyota", "noah", ["MZRA9"]),
    ("Toyota", "Noah Hybrid"): ("toyota", "noah", ["ZWR9"]),
    ("Toyota", "Voxy Hybrid"): ("toyota", "voxy", ["ZWR9"]),
    ("Toyota", "Esquire Hybrid"): ("toyota", "esquire", ["ZWR80"]),
    ("Toyota", "HiAce"): ("toyota", "hiace-van", ["GDH2"]),
    ("Toyota", "Alphard"): ("toyota", "alphard", ["AGH3"]),
    ("Toyota", "Sienta Hybrid"): ("toyota", "sienta", ["MXPL1"]),
    ("Honda", "Insight"): ("honda", "insight", ["ZE4"]),
    ("Honda", "Vezel e:HEV"): ("honda", "vezel", ["RV5", "RV6"]),
    ("Honda", "Civic"): ("honda", "civic", ["FL1"]),
    ("Honda", "CR-V"): ("honda", "crv", ["RW1", "RW2"]),
    ("Nissan", "X-Trail e-Power"): ("nissan", "xtrail", ["SNT33"]),
    ("Lexus", "RX 350h"): ("lexus", "rx", ["AALH1"]),
}


def matches(car: Listing, year: int, cc: int, codes: list[str]) -> bool:
    # Partner stock gives no build year; a Japanese car's first registration is within months of
    # its build, so the registration year stands in for it there.
    return (
        (car.built if car.built is not None else car.registered) == year
        and abs(car.cc - cc) <= CC_SLACK
        and any(c in car.model_code.upper() for c in codes)
    )


def summarise(prices: list[int]) -> dict:
    p10, med, p90 = np.percentile(prices, [10, 50, 90])
    return {"n": len(prices), "medianUsd": int(round(med, -1)), "p10Usd": int(round(p10, -1)), "p90Usd": int(round(p90, -1))}


def yen_per_dollar() -> float:
    """From the site's own exchange rates, so the catalogue and the calculator agree."""
    text = MARKET_TS.read_text(encoding="utf-8")
    usd, jpy = (float(re.search(cur + r": ([\d.]+)", text)[1]) for cur in ("USD", "JPY"))
    return usd / jpy


def apply_to_catalogue(summary: list[dict]) -> int:
    """Set each well-sampled car's example price in cars.ts to its median, rounded to ¥10,000."""
    text = CARS_TS.read_text(encoding="utf-8")
    per_dollar, changed = yen_per_dollar(), 0
    for row in summary:
        if row["n"] < MIN_LISTINGS:
            continue
        yen = int(round(row["medianUsd"] * per_dollar, -4))
        pattern = re.compile(r'(\["{}", "{}", {}, \d+, "\w+", "\w+", )[\d_]+'.format(re.escape(row["make"]), re.escape(row["model"]), row["year"]))
        text, n = pattern.subn(lambda m: m[1] + f"{yen:_}", text)
        changed += n
    CARS_TS.write_text(text, encoding="utf-8")
    return changed


def catalogue() -> dict[tuple[str, str], tuple[int, int]]:
    """(make, model) -> (year, cc) for every catalogue car, read from the web source."""
    return {(m, n): (y, cc) for m, n, y, cc, _ in read_catalogue()}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cars = catalogue()
    fetcher = PoliteFetcher(delay=3)
    pages: dict[tuple[str, str, int], list[Listing]] = {}
    rows, summary = [], []

    for (make, model), (sbt_make, sbt_model, codes) in TARGETS.items():
        year, cc = cars[(make, model)]
        key = (sbt_make, sbt_model, year)
        if key not in pages:
            seen: list[Listing] = []
            for page in range(1, MAX_PAGES + 1):
                try:
                    found, total = parse_page(fetcher.get(page_url(sbt_make, sbt_model, year, year + 1, page)))
                except FetchError as e:
                    print(f"  {sbt_make}/{sbt_model}: {e}", flush=True)
                    break
                seen += found
                if total is None or page * PER_PAGE >= total:
                    break
            pages[key] = seen
        hits = [c for c in pages[key] if matches(c, year, cc, codes)]
        print(f"{make} {model} {year}: {len(hits)} of {len(pages[key])} listings match", flush=True)
        rows += [{"make": make, "model": model, **asdict(c)} for c in hits]
        if hits:
            summary.append({"make": make, "model": model, "year": year, **summarise([c.fob_usd for c in hits])})

    today = date.today().isoformat()
    RAW.mkdir(parents=True, exist_ok=True)
    if rows:
        with (RAW / f"{today}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    OUT.write_text(json.dumps({"asOf": today, "source": "SBT Japan stock, FOB prices", "prices": summary}, indent=1) + "\n", encoding="utf-8")
    print(f"{len(summary)} cars priced -> {OUT}; {apply_to_catalogue(summary)} catalogue prices updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
