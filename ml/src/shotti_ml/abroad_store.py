"""The site's file of real prices abroad, shared by the Japan (SBT) and UK (CarGurus) collectors.

`web/src/lib/abroad.json` holds one row per catalogue car: how many matching listings were found
and their median and 10th/90th percentile, in the currency the source lists them in. Each
collector replaces only its own rows. Cars with MIN_LISTINGS or more matches also get their
median written into `web/src/lib/cars.ts` as the price the calculator starts from.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "web" / "src" / "lib" / "abroad.json"
MARKET_TS = ROOT / "web" / "src" / "lib" / "market.ts"
CARS_TS = ROOT / "web" / "src" / "lib" / "cars.ts"

#: fewer listings than this and the catalogue keeps its example price
MIN_LISTINGS = 5
SOURCES = {"sbt": "SBT Japan's export stock", "cargurus": "CarGurus UK"}
#: the catalogue's currency for each source's cars, and what to round its prices to
CATALOGUE = {"sbt": ("JPY", 10_000), "cargurus": ("GBP", 100)}


def summarise(prices: list[int]) -> dict:
    p10, med, p90 = np.percentile(prices, [10, 50, 90])
    return {"n": len(prices), "median": int(round(med, -1)), "p10": int(round(p10, -1)), "p90": int(round(p90, -1))}


def rate(currency: str) -> float:
    """Taka per unit, from the site's own exchange rates so the catalogue and the calculator agree."""
    return float(re.search(currency + r": ([\d.]+)", MARKET_TS.read_text(encoding="utf-8"))[1])


def load() -> dict:
    if OUT.exists():
        return json.loads(OUT.read_text(encoding="utf-8"))
    return {"sources": {}, "prices": []}


def save(source: str, currency: str, rows: list[dict], attempted: set[tuple[str, str]]) -> list[dict]:
    """Replace this source's rows for the cars just searched (`attempted`, as make and model), keeping
    the rest. Returns the new rows as stored."""
    data = load()
    data["sources"][source] = {"name": SOURCES[source], "currency": currency, "asOf": date.today().isoformat()}
    kept = [p for p in data["prices"] if p["source"] != source or (p["make"], p["model"]) not in attempted]
    added = [{"source": source, "currency": currency, **row} for row in rows]
    data["prices"] = kept + added
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return added


def in_catalogue_currency(row: dict, value: float) -> int:
    target, step = CATALOGUE[row["source"]]
    converted = value * rate(row["currency"]) / rate(target) if row["currency"] != target else value
    return int(round(converted / step) * step)


def apply_to_catalogue(rows: list[dict] | None = None) -> int:
    """Set each well-sampled car's example price in cars.ts to its median (every saved row by default)."""
    if rows is None:
        rows = load()["prices"]
    text = CARS_TS.read_text(encoding="utf-8")
    changed = 0
    for row in rows:
        if row["n"] < MIN_LISTINGS:
            continue
        price = in_catalogue_currency(row, row["median"])
        pattern = re.compile(r'(\["{}", "{}", {}, \d+, "\w+", "\w+", )[\d_]+'.format(re.escape(row["make"]), re.escape(row["model"]), row["year"]))
        text, n = pattern.subn(lambda m: m[1] + f"{price:_}", text)
        changed += n
    CARS_TS.write_text(text, encoding="utf-8")
    return changed


if __name__ == "__main__":
    # .venv/Scripts/python.exe -I -m shotti_ml.abroad_store  re-applies every saved price to cars.ts
    print(f"{apply_to_catalogue()} catalogue prices set")
