"""Can related cars help price a model nobody lists?

Result (see reports/coldstart.json): the one change that helps is leaving the model name out. Brand and
name-word price levels did not help.

Run from the ml/ folder:  .venv/Scripts/python.exe -I -m shotti_ml.run_coldstart
Every row is predicted by a model that never saw ANY listing of that car model (5 folds of whole
models, 8 repeats). Compares the current LightGBM with versions that borrow price levels from the
brand and from words in the model name. Writes reports/coldstart.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .coldstart import NoNameModel, SimilarCarModel
from .current import clean_current, load_all
from .data import clean, load_raw
from .evaluate import cross_validate, summarise
from .features import build_features
from .models import make_group_median, make_lgbm, make_ridge
from .run_current import EXTRA

REPEATS = 8
OUT = Path(__file__).resolve().parents[2] / "reports" / "coldstart.json"

CANDIDATES = {
    "Median by model (current)": make_group_median,
    "Ridge (current)": make_ridge,
    "LightGBM (current)": make_lgbm,
    "LightGBM without the model name": NoNameModel,
    "+ brand price level": lambda: SimilarCarModel(use_brand=True, use_tokens=False),
    "+ words in the model name": lambda: SimilarCarModel(use_brand=False, use_tokens=True),
    "+ both": lambda: SimilarCarModel(use_brand=True, use_tokens=True),
}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    old, _ = clean(load_raw())
    df, _, year = clean_current(load_all(), sorted(old["car_model"].unique()))
    df = df.reset_index(drop=True)
    X, y = build_features(df, year, EXTRA)
    X["_name"] = df["car_model"].to_numpy()
    X["_brand"] = df["brand"].to_numpy()
    groups = df["car_model"]

    rows, per_fold = {}, {}
    for name, make in CANDIDATES.items():
        # the plain baselines must not see the helper columns
        wrap = make
        if "current" in name:
            wrap = (lambda m=make: _Plain(m()))
        folds, oof = cross_validate(wrap, X, y, groups=groups, n_repeats=REPEATS)
        per_fold[name] = folds["median_ape"].to_numpy()
        s = summarise(folds)
        rows[name] = {"miss": round(s["median_ape"]["mean"], 4), "spread": round(s["median_ape"]["std"], 4),
                      "rmsle": round(s["rmsle"]["mean"], 4)}
        print(f"{name:32s} {rows[name]['miss']:.3f} ± {rows[name]['spread']:.3f}  rmsle {rows[name]['rmsle']:.3f}", flush=True)

    # same folds for every candidate, so the comparison can be paired
    base = per_fold["LightGBM (current)"]
    for name, v in per_fold.items():
        d = base - v
        rows[name]["gain_vs_current"] = round(float(d.mean()), 4)
        rows[name]["gain_se"] = round(float(d.std(ddof=1) / np.sqrt(len(d))), 4)
        rows[name]["better_in_folds"] = round(float((d > 0).mean()), 2)

    OUT.write_text(json.dumps({"ads": len(df), "models": int(df['car_model'].nunique()), "results": rows}, indent=1), encoding="utf-8")
    return 0


class _Plain:
    """Hides the helper columns from the current models, which expect the usual feature table."""

    def __init__(self, model):
        self.model = model

    def fit(self, X, y):
        self.model.fit(X.drop(columns=["_name", "_brand"]), y)
        return self

    def predict(self, X):
        return self.model.predict(X.drop(columns=["_name", "_brand"]))


if __name__ == "__main__":
    sys.exit(main())
