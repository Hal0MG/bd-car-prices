"""How far the catalogue's rounded example prices were from the real listings that replaced them.

Run from the ml/ folder:  .venv/Scripts/python.exe -I -m shotti_ml.abroad_review
Reads the example prices from cars.ts as it stood before any real price was written in (git
revision EXAMPLES_REV), and the real medians from abroad.json, and writes one row per car with
enough listings to ../web/src/lib/abroad-review.json for The data: Abroad page.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

from . import abroad_store as store

#: the last commit whose catalogue held only example prices
EXAMPLES_REV = "610d0fe"
OUT = store.ROOT / "web" / "src" / "lib" / "abroad-review.json"
ROW = re.compile(r'\["([^"]+)", "([^"]+)", (\d{4}), (\d+), "(\w+)", "(\w+)", ([\d_]+)')


def examples() -> dict[tuple[str, str], tuple[str, int]]:
    """(make, model) -> (fuel, example price) from the catalogue before real prices."""
    text = subprocess.run(
        ["git", "show", f"{EXAMPLES_REV}:web/src/lib/cars.ts"], cwd=store.ROOT, capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout
    return {(m, n): (fuel, int(price.replace("_", ""))) for m, n, _, _, fuel, _, price in ROW.findall(text)}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    old = examples()
    rows = []
    for p in store.load()["prices"]:
        key = (p["make"], p["model"])
        if p["n"] < store.MIN_LISTINGS or key not in old:
            continue
        fuel, example = old[key]
        real = store.in_catalogue_currency(p, p["median"])
        rows.append({"make": p["make"], "model": p["model"], "source": p["source"], "fuel": fuel, "n": p["n"], "example": example, "real": real})
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(rows)} cars -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
