"""Export the aggregates the site's Market and Method pages show.

Run from the ml/ folder (after run_current):
    .venv/Scripts/python.exe -I -m shotti_ml.export_site
Writes ../web/src/lib/data-science.json. Only counts, medians and percentile bands leave this
script, never individual listings: the site shows aggregates, not individual ads. A cell with fewer than MIN_CELL listings is left out.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .current import clean_current, load_all
from .data import clean, load_raw

ROOT = Path(__file__).resolve().parents[3]
METRICS = ROOT / "ml" / "reports" / "current" / "baseline_metrics.json"
DUPLICATES = ROOT / "ml" / "reports" / "duplicates.json"
COLDSTART = ROOT / "ml" / "reports" / "coldstart.json"
OUT = ROOT / "web" / "src" / "lib" / "data-science.json"

MIN_CELL = 8
MODELS_SHOWN = 6
MAX_AGE = 12
#: Band keys in the metrics file carry a broken dash; match them by their first digits.
BANDS = {"3": "Under 28 lakh", "28": "28 to 40", "40": "40 to 51", "51": "51 to 75", "75": "75 lakh and up"}


def band_label(key: str) -> str:
    return next(label for prefix, label in BANDS.items() if key.startswith(prefix) and (prefix != "3" or key.startswith("3�") or key.startswith("3–")))


def duplicates() -> dict:
    """The duplicate-ad check, written by run_duplicates.py (rerun it after a retrain)."""
    d = json.loads(DUPLICATES.read_text(encoding="utf-8"))
    r = d["results"]
    return {
        "adsWithTwin": d["ads_with_a_twin"],
        "crossSiteClusters": d["clusters_spanning_both_sites"],
        "dropped": d["dropped"],
        "setups": [
            {"name": "Random folds (the headline test)", "miss": r["random folds (main results)"]["miss"]},
            {"name": "Possible twins kept in the same fold", "miss": r["loose twin groups held out together"]["miss"]},
            {"name": "Confirmed twins kept in the same fold", "miss": r["confirmed twin groups held out together"]["miss"]},
            {"name": "Twins dropped, random folds", "miss": r["twins dropped, random folds"]["miss"]},
        ],
    }


def coldstart() -> list[dict]:
    """Pricing a model with no ads, from run_coldstart.py: the current booster against versions that borrow from related cars."""
    r = json.loads(COLDSTART.read_text(encoding="utf-8"))["results"]
    names = [
        ("LightGBM (current)", "LightGBM as used, with the model name"),
        ("LightGBM without the model name", "LightGBM without the model name"),
        ("+ brand price level", "Also given the brand's price level"),
        ("+ words in the model name", "Also given the words in the model name"),
    ]
    return [
        {"name": label, "miss": r[k]["miss"], "gain": r[k]["gain_vs_current"], "se": r[k]["gain_se"], "better": r[k]["better_in_folds"]}
        for k, label in names
    ]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    m = json.loads(METRICS.read_text(encoding="utf-8"))
    old, _ = clean(load_raw())
    raw = load_all()
    df, report, year = clean_current(raw, sorted(old["car_model"].unique()))
    df = df.assign(age=(year - df["build_year"]).clip(lower=0))

    def ape(table: dict, name: str) -> dict:
        return {"miss": round(table[name]["median_ape"]["mean"], 4), "spread": round(table[name]["median_ape"]["std"], 4)}

    models = [
        {"name": n, "familiar": ape(m["cv_random_5x3"], n), "unseen": ape(m["cv_held_out_models_5x3"], n)}
        for n in ["Median by model", "Ridge", "LightGBM"]
    ]

    bands = []
    for key in m["intervals_by_price_band"]["Constant width"]:
        bands.append({
            "band": band_label(key),
            "order": float(key.replace("–", "�").split("�")[0]),
            "constant": m["intervals_by_price_band"]["Constant width"][key]["coverage"],
            "scaled": m["intervals_by_price_band"]["Scaled by difficulty"][key]["coverage"],
        })
    bands.sort(key=lambda b: b["order"])
    for b in bands:
        del b["order"]

    top = df["car_model"].value_counts().head(MODELS_SHOWN).index
    by_age = []
    for name in top:
        sub = df[df["car_model"] == name]
        cells = []
        for age, g in sub.groupby("age"):
            if len(g) >= MIN_CELL and 1 <= age <= MAX_AGE:
                p10, med, p90 = np.percentile(g["price"], [10, 50, 90])
                cells.append({"age": int(age), "n": int(len(g)), "p10": round(p10, -3), "median": round(med, -3), "p90": round(p90, -3)})
        by_age.append({"model": f"{sub['make'].mode().iat[0]} {name}", "listings": int(len(sub)), "cells": cells})

    both = df.groupby(["car_model", "build_year", "source"])["price"].agg(["median", "size"]).reset_index()
    wide = both.pivot_table(index=["car_model", "build_year"], columns="source", values=["median", "size"])
    ok = wide[(wide[("size", "bikroy")] >= 3) & (wide[("size", "garirbazar")] >= 3)]
    ratio = (ok[("median", "bikroy")] / ok[("median", "garirbazar")])

    makes = df["make"].value_counts()
    payload = {
        "asOf": str(pd.to_datetime(raw["observed_at"]).max().date()),
        "listings": int(report.rows_clean),
        "bySource": {s: int(n) for s, n in df["source"].value_counts().items()},
        "funnel": {
            "read": report.rows_raw,
            "repeats": report.seen_in_several_snapshots,
            "noPrice": report.no_price,
            "badOrSuspect": report.electric_dropped + report.implausible_year + report.implausible_price + report.suspect_dropped + report.price_outliers + report.no_model,
            "used": report.rows_clean,
        },
        "imputed": {"engine": round(report.engine_imputed / report.rows_clean, 3), "mileage": round(report.mileage_imputed / report.rows_clean, 3)},
        "makes": [{"make": k, "listings": int(v)} for k, v in makes.head(8).items()],
        "modelsWithFive": int((df["car_model"].value_counts() >= 5).sum()),
        "modelsTotal": int(df["car_model"].nunique()),
        "models": models,
        "coverage": {"target": m["intervals"]["target_coverage"], "overall": {k: v["coverage"] for k, v in m["intervals"]["overall"].items()}, "bands": bands},
        "learning": {name: [{"n": int(n), "miss": v} for n, v in curve.items()] for name, curve in m["learning_curve"].items()},
        "features": [{"name": k, "swing": v} for k, v in list(m["feature_swing_pct"].items())[:8]],
        "byAge": by_age,
        "duplicates": duplicates(),
        "coldstart": coldstart(),
        "siteAgreement": {"cells": int(len(ratio)), "medianRatio": round(float(ratio.median()), 3)},
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"-> {OUT}")
    print(json.dumps({k: payload[k] for k in ("funnel", "imputed", "makes", "siteAgreement", "coverage")}, ensure_ascii=False)[:1200])
    print([(b["model"], len(b["cells"])) for b in by_age])
    return 0


if __name__ == "__main__":
    sys.exit(main())
