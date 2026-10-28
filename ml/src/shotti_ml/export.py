"""Export expected local asking prices for the site's catalogue cars.

Run from the ml/ folder (after run_current):
    .venv/Scripts/python.exe -I -m shotti_ml.export
Writes ../web/src/lib/local-prices.json, which the car pages read. The site never runs Python:
the model predicts once per catalogue car, here, and the page shows the stored range.

Only cars with real comparables get a price. A catalogue car is priced when its model has at
least MIN_MODEL_LISTINGS current listings, at least MIN_NEAR listings built within a year of
its model year, and a range no wider than MAX_SPREAD. Everything else is left out, because a number from nothing would be a guess.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .current import clean_current, load_all
from .data import FUEL_COLUMNS, clean, load_raw
from .features import MIN_MODEL_COUNT, build_features
from .intervals import scaled_by_difficulty
from .models import make_lgbm
from .run_current import EXTRA

CARS_TS = Path(__file__).resolve().parents[3] / "web" / "src" / "lib" / "cars.ts"
OUT = Path(__file__).resolve().parents[3] / "web" / "src" / "lib" / "local-prices.json"

MIN_MODEL_LISTINGS = MIN_MODEL_COUNT
MIN_NEAR = 5
#: A range wider than this (high / low) says too little to be worth showing.
MAX_SPREAD = 2.5
ALPHA = 0.2

#: Catalogue name -> the listing model it is sold as locally, with the fuel it implies.
SUFFIXES = [" Hybrid", " e:HEV", " e-Power"]
ALIASES = {"HiAce": "Hiace", "Land Cruiser Prado TX": "Prado", "Crown Crossover": "Crown", "Yaris Hybrid": "Yaris", "Fit e:HEV": "Fit", "RX 350h": "RX"}

ROW = re.compile(r'\["([^"]+)",\s*"([^"]+)",\s*(\d{4}),\s*(\d+),\s*"(\w+)"')


def catalogue() -> list[tuple[str, str, int, int, str]]:
    """(make, model, year, cc, fuel) for each catalogue row, read from cars.ts."""
    return [(m, n, int(y), int(cc), f) for m, n, y, cc, f in ROW.findall(CARS_TS.read_text(encoding="utf-8"))]


def local_name(model: str, known: set[str]) -> str | None:
    """The listing model a catalogue car corresponds to, or None."""
    if model in ALIASES:
        return ALIASES[model] if ALIASES[model] in known else None
    for candidate in [model] + [model.replace(s, "") for s in SUFFIXES if s in model]:
        candidate = candidate.strip()
        if candidate in known:
            return candidate
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    old, _ = clean(load_raw())
    raw = load_all()
    df, report, year = clean_current(raw, sorted(old["car_model"].unique()))
    X, y = build_features(df, year, EXTRA)

    rng = np.random.default_rng(0)
    order = rng.permutation(len(X))
    n_cal = int(len(X) * 0.25)
    cal, fit = order[:n_cal], order[n_cal:]

    counts = df["car_model"].value_counts()
    known = set(counts[counts >= MIN_MODEL_LISTINGS].index)
    typical = df.groupby("car_model").agg(engine_cc=("engine_cc", "median"), km_by_year=("km", "median"))

    queries, meta = [], []
    for make, model, model_year, _cc, fuel in catalogue():
        name = local_name(model, known)
        if name is None:
            continue
        pool = df[df["car_model"] == name]
        near = pool[(pool["build_year"] - model_year).abs() <= 1]
        if len(near) < MIN_NEAR:
            continue
        same_age = pool[(pool["build_year"] - model_year).abs() <= 2]
        row = X[df["car_model"] == name].iloc[0].copy()
        row["age"] = year - model_year
        row["log_km"] = np.log1p(same_age["km"].median())
        row["engine_cc"] = typical.loc[name, "engine_cc"]
        row["reg_gap"] = 0
        row["automatic"] = 1
        row["source"], row["condition"] = "bikroy", "Reconditioned"  # the catalogue prices reconditioned imports
        for col in FUEL_COLUMNS:
            row[col] = 0
        row["fuel_hybrid" if fuel == "hybrid" else "fuel_diesel" if fuel == "diesel" else "fuel_petrol"] = 1
        queries.append(row)
        meta.append({"make": make, "model": model, "year": model_year, "local_model": name, "listings_near": int(len(near)), "listings_model": int(counts[name])})

    Q = pd.DataFrame(queries).reset_index(drop=True)
    for col in X.columns:
        if str(X[col].dtype) == "category":
            Q[col] = pd.Categorical(Q[col], categories=X[col].cat.categories)
        else:
            Q[col] = pd.to_numeric(Q[col])
    Q = Q[X.columns]

    iv = scaled_by_difficulty(make_lgbm, X.iloc[fit], y.iloc[fit], X.iloc[cal], y.iloc[cal], Q, ALPHA)
    out = []
    for m, pred, lo, hi in zip(meta, iv.pred, iv.lo, iv.hi):
        if np.exp(hi - lo) > MAX_SPREAD:
            continue
        out.append({**m, "expected": round(float(np.exp(pred)), -3), "low": round(float(np.exp(lo)), -3), "high": round(float(np.exp(hi)), -3)})

    payload = {
        "asOf": str(pd.to_datetime(raw["observed_at"]).max().date()),
        "listings": report.rows_clean,
        "coverage": 1 - ALPHA,
        "note": "Asking prices on GarirBazar and Bikroy for reconditioned cars of this model and age, not sale prices.",
        "prices": out,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(out)} of {len(catalogue())} catalogue cars priced -> {OUT}")
    for r in out:
        print(f"{r['year']} {r['make']} {r['model']:<26} {r['expected'] / 1e5:6.1f} lakh  ({r['low'] / 1e5:.1f}-{r['high'] / 1e5:.1f})  near={r['listings_near']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
