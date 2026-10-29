"""How much do likely duplicate ads flatter the headline error?

Run from the ml/ folder:  .venv/Scripts/python.exe -I -m shotti_ml.run_duplicates
Compares LightGBM's typical miss when (a) folds are random, as in the main results, (b) every
possible same model/year/price twin is kept in the same fold, (c) every confirmed twin is, and
(d) the confirmed twins are dropped first. If (a) and (b) agree, duplicates are not what is
making the model look good.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from .current import clean_current, load_all
from .data import clean, load_raw
from .dedupe import LOOSE_KEY, drop_twins, twin_clusters
from .evaluate import cross_validate, summarise
from .features import build_features
from .models import make_lgbm
from .run_current import EXTRA

OUT = Path(__file__).resolve().parents[2] / "reports" / "duplicates.json"


def miss(df: pd.DataFrame, year: int, groups: pd.Series | None) -> dict[str, float]:
    X, y = build_features(df, year, EXTRA)
    folds, _ = cross_validate(make_lgbm, X, y, groups=groups)
    s = summarise(folds)["median_ape"]
    return {"miss": round(s["mean"], 4), "spread": round(s["std"], 4), "rows": int(len(df))}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    old, _ = clean(load_raw())
    df, _, year = clean_current(load_all(), sorted(old["car_model"].unique()))
    df = df.reset_index(drop=True)

    clusters, pairs = twin_clusters(df)
    sizes = clusters.value_counts()
    in_twin_cluster = int((clusters.map(sizes) > 1).sum())
    loose = df.groupby(LOOSE_KEY).ngroup()
    cross_site = int(df.assign(c=clusters).groupby("c")["source"].nunique().gt(1).sum())

    results = {
        "random folds (main results)": miss(df, year, None),
        "loose twin groups held out together": miss(df, year, loose),
        "confirmed twin groups held out together": miss(df, year, clusters),
    }
    deduped, dropped = drop_twins(df)
    results["twins dropped, random folds"] = miss(deduped, year, None)
    results["twins dropped, random folds"]["dropped"] = dropped

    payload = {
        "ads": len(df),
        "twin_pairs": pairs,
        "ads_with_a_twin": in_twin_cluster,
        "clusters_spanning_both_sites": cross_site,
        "dropped": dropped,
        "results": results,
    }
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(json.dumps(payload, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
