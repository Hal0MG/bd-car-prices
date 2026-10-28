"""Retrain on the collected GarirBazar listings and compare prices with the 2021 file.

Run from the ml/ folder (after collecting at least one snapshot):
    .venv/Scripts/python.exe -I -m shotti_ml.run_current
Writes reports/current/ (metrics, report, figures).
"""

from __future__ import annotations

import sys

import pandas as pd

from . import run_baseline as base
from .current import clean_current, load_all
from .data import REFERENCE_YEAR, clean, load_raw
from .features import build_features


#: Which site an ad came from and whether it is used or reconditioned (only Bikroy says).
EXTRA = ("source", "condition")


def compare_with_2021(new: pd.DataFrame, new_year: int, old: pd.DataFrame, old_year: int, min_each: int = 8) -> pd.DataFrame:
    """Median asking price of cars five to ten years old, by model: in 2021 and now.

    Comparing cars of the same age at each date keeps the comparison fair, since a car
    that was five years old in 2021 is ten years old now.
    """
    rows = []
    for model in sorted(set(new["car_model"]) & set(old["car_model"])):
        then = old[(old["car_model"] == model) & (old_year - old["build_year"]).between(5, 10)]
        now = new[(new["car_model"] == model) & (new_year - new["build_year"]).between(5, 10)]
        if len(then) >= min_each and len(now) >= min_each:
            rows.append(
                {"model": model, "n_2021": len(then), "n_now": len(now), "median_2021": then["price"].median(), "median_now": now["price"].median()}
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["change_pct"] = 100 * (out["median_now"] / out["median_2021"] - 1)
    return out.sort_values("n_now", ascending=False).reset_index(drop=True)


def comparison_table(cmp: pd.DataFrame) -> str:
    if cmp.empty:
        return "Too few models with enough cars of the same age in both datasets to compare."
    rows = ["| Model | Cars (2021 / now) | Median 2021 | Median now | Change |", "|---|---|---|---|---|"]
    for _, r in cmp.iterrows():
        rows.append(
            f"| {r['model']} | {int(r['n_2021'])} / {int(r['n_now'])} | ৳{r['median_2021'] / 1e5:.1f} lakh | ৳{r['median_now'] / 1e5:.1f} lakh | {r['change_pct']:+.0f}% |"
        )
    return "\n".join(rows)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    base.apply_style()

    raw = load_all()
    if raw.empty:
        print("No snapshots yet. Collect one first:\n  .venv/Scripts/python.exe -I -m shotti_ml.collect.run --pages 40")
        return 1

    old, _ = clean(load_raw())
    df, report, year = clean_current(raw, sorted(old["car_model"].unique()))
    X, y = build_features(df, year, EXTRA)
    print("Cleaning:", report.as_dict())

    base.set_output(base.REPORTS / "current")
    snapshots = raw["observed_at"].str[:10].nunique()
    base.run(
        df, X, y,
        title="Results on current listings",
        intro=(
            f"Asking-price models on {report.rows_clean:,} current listings ({(df['source'] == 'garirbazar').sum():,} from GarirBazar, "
            f"{report.rows_from_bikroy:,} from Bikroy), collected on {snapshots} day(s) up to {raw['observed_at'].max()[:10]}. "
            f"{int(raw[raw['source'] == 'garirbazar']['filtered'].sum()):,} of the GarirBazar sightings come from the site's own filter for "
            "ads asking 50 lakh or more, and the Bikroy pages skew expensive too, so dear cars are over-represented. "
            f"Cards omit engine size on {report.engine_imputed / report.rows_clean:.0%} of listings and mileage on "
            f"{report.mileage_imputed / report.rows_clean:.0%}, and show body style rarely. Only Bikroy says whether a car is used or "
            "reconditioned. Missing engine sizes and mileages are filled in from similar cars."
        ),
        cleaning=report.as_dict(),
        extra={"reference_year": year},
    )

    # Price-filtered snapshots over-sample dear cars, which would drag up medians; compare on the random ones.
    random_df, _, _ = clean_current(raw[~raw["filtered"]], sorted(old["car_model"].unique()))
    cmp = compare_with_2021(random_df, year, old, REFERENCE_YEAR)
    section = f"\n## Prices since 2021\n\nMedian asking price of cars five to ten years old, same model, then and now.\n\n{comparison_table(cmp)}\n"
    path = base.REPORTS / "baseline_report.md"
    path.write_text(path.read_text(encoding="utf-8") + section, encoding="utf-8")
    print(comparison_table(cmp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
