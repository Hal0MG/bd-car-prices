"""Export "prediction check" aggregates for the site: what the model said against what ads asked,
on ads it had not trained on.

Run from the ml/ folder (after run_current):
    .venv/Scripts/python.exe -I -m shotti_ml.export_check
Writes ../web/src/lib/check.json. Every ad is predicted by a model that never saw it (5 random
folds, the same setup as the headline error). Only counts and medians per model and age leave this
script, never a single ad: the site shows aggregates, not individual listings. A cell with fewer than MIN_CELL ads is left out.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from .current import clean_current, load_all
from .data import clean, load_raw
from .features import build_features
from .intervals import scaled_by_difficulty
from .models import make_lgbm
from .run_current import EXTRA

OUT = Path(__file__).resolve().parents[3] / "web" / "src" / "lib" / "check.json"

ALPHA = 0.2
MIN_MODEL_ADS = 60
MIN_CELL = 8
MAX_AGE = 12
BINS = 10


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    old, _ = clean(load_raw())
    raw = load_all()
    df, _, year = clean_current(raw, sorted(old["car_model"].unique()))
    X, y = build_features(df, year, EXTRA)
    df = df.reset_index(drop=True)
    X, y = X.reset_index(drop=True), y.reset_index(drop=True)

    pred = np.zeros(len(df))
    lo = np.zeros(len(df))
    hi = np.zeros(len(df))
    rng = np.random.default_rng(0)
    for train, test in KFold(5, shuffle=True, random_state=0).split(X):
        train = rng.permutation(train)
        n_cal = int(len(train) * 0.25)
        cal, fit = train[:n_cal], train[n_cal:]
        iv = scaled_by_difficulty(make_lgbm, X.iloc[fit], y.iloc[fit], X.iloc[cal], y.iloc[cal], X.iloc[test], ALPHA)
        pred[test], lo[test], hi[test] = iv.pred, iv.lo, iv.hi

    df = df.assign(
        age=(year - df["build_year"]).clip(lower=0),
        predicted=np.exp(pred),
        miss=np.abs(np.exp(pred) / df["price"] - 1),
        inside=(np.log(df["price"]) >= lo) & (np.log(df["price"]) <= hi),
    )

    counts = df["car_model"].value_counts()
    models = []
    for name in counts[counts >= MIN_MODEL_ADS].index:
        sub = df[df["car_model"] == name]
        cells = []
        for age, g in sub.groupby("age"):
            if len(g) >= MIN_CELL and 1 <= age <= MAX_AGE:
                cells.append({
                    "age": int(age), "n": int(len(g)),
                    "actual": round(float(g["price"].median()), -3),
                    "predicted": round(float(g["predicted"].median()), -3),
                })
        if len(cells) < 3:
            continue
        models.append({
            "model": f"{sub['make'].mode().iat[0]} {name}",
            "ads": int(len(sub)),
            "miss": round(float(sub["miss"].median()), 4),
            "inside": round(float(sub["inside"].mean()), 3),
            "cells": cells,
        })
    models.sort(key=lambda m: -m["ads"])

    df["bin"] = pd.qcut(df["predicted"], BINS, labels=False)
    calibration = [
        {"n": int(len(g)), "predicted": round(float(g["predicted"].median()), -3), "actual": round(float(g["price"].median()), -3)}
        for _, g in df.groupby("bin")
    ]

    payload = {
        "ads": int(len(df)),
        "miss": round(float(df["miss"].median()), 4),
        "inside": round(float(df["inside"].mean()), 3),
        "target": 1 - ALPHA,
        "models": models,
        "calibration": calibration,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(models)} models -> {OUT}")
    print(payload["ads"], payload["miss"], payload["inside"], [(m["model"], m["ads"], m["miss"], m["inside"]) for m in models[:8]])
    print(calibration)
    return 0


if __name__ == "__main__":
    sys.exit(main())
