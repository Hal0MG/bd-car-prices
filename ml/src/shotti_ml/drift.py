"""Check a new batch of listings against the data a model was trained on.

Run from the ml/ folder:
    .venv/Scripts/python.exe -I -m shotti_ml.drift path/to/batch.jsonl [--artifact artifacts/<version>]

The batch is listings in the collector's format (JSONL or CSV: make, model, year, price_bdt, mileage_km,
engine_cc, fuel, transmission, observed_at, ...), or a folder laid out like data/raw. It is cleaned the
same way as training data, then compared with the artifact's training summary:

- numbers (age, log mileage, engine size, log price): population stability index (PSI) over the
  training data's deciles;
- categories (brand, model, fuel, gearbox, site, condition): PSI and the largest change in share;
- missing engine sizes and mileages: the share the cleaning had to fill in;
- if the batch has prices: the model's median absolute percentage error against its cross-validated
  error, and how many prices fall inside the 80% range.

Writes a markdown and a JSON report and exits 1 if any check passes its alert threshold.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import settings
from .artifact import load_artifact, write_json
from .current import CurrentCleaningReport, clean_current, load_all

NUMERIC = ["age", "log_km", "engine_cc", "log_price"]
CATEGORICAL = ["brand", "model", "fuel", "gearbox", "source", "condition"]
FUEL_ORDER = ["hybrid", "diesel", "cng", "lpg", "petrol"]  # a car flagged twice counts as the first match
EPS = 1e-4
UNSEEN = "(not in training)"
REPORTS = settings.ML_ROOT / "reports" / "drift"


@dataclass
class Thresholds:
    psi_warn: float = 0.10
    psi_alert: float = 0.25
    share_shift_alert: float = 0.10
    missing_shift_alert: float = 0.15
    mape_ratio_alert: float = 1.5
    coverage_min: float = 0.70


# -- statistics -------------------------------------------------------------------


def psi(expected, actual, eps: float = EPS) -> float:
    """Population stability index between two sets of bin shares: sum of (a - e) * ln(a / e).

    Empty bins are floored at `eps` so the log stays finite. Below 0.1 is usually read as stable,
    0.1 to 0.25 as a moderate shift, above 0.25 as a large one.
    """
    e = np.clip(np.asarray(expected, dtype=float), eps, None)
    a = np.clip(np.asarray(actual, dtype=float), eps, None)
    return float(np.sum((a - e) * np.log(a / e)))


def decile_edges(values) -> list[float]:
    """Interior bin edges at the deciles; repeated edges (an integer feature like age) are merged."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    return np.unique(np.quantile(v, np.linspace(0.1, 0.9, 9))).tolist()


def bin_shares(values, edges) -> list[float]:
    """Share of values in each bin (-inf, e1], (e1, e2], ..., (ek, inf). Missing values are left out."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    counts = np.bincount(np.searchsorted(np.asarray(edges, dtype=float), v, side="left"), minlength=len(edges) + 1)
    return (counts / max(len(v), 1)).tolist()


def category_shares(values: pd.Series) -> dict[str, float]:
    return {str(k): float(v) for k, v in values.astype(str).value_counts(normalize=True).items()}


def drift_frame(X: pd.DataFrame, y: pd.Series | None = None) -> pd.DataFrame:
    """The columns the drift check compares, from the model inputs (and the target, when there is one)."""
    fuel = pd.Series("other", index=X.index)
    for name in reversed(FUEL_ORDER):
        fuel = fuel.mask(X[f"fuel_{name}"] == 1, name)
    out = pd.DataFrame(
        {
            "age": X["age"].astype(float),
            "log_km": X["log_km"].astype(float),
            "engine_cc": X["engine_cc"].astype(float),
            "brand": X["brand"].astype(str),
            "model": X["model"].astype(str),
            "fuel": fuel,
            "gearbox": np.where(X["automatic"] == 1, "automatic", "manual"),
            "source": X["source"].astype(str),
            "condition": X["condition"].astype(str),
        }
    )
    out["log_price"] = np.nan if y is None else np.asarray(y, dtype=float)
    return out


def missing_shares(report: CurrentCleaningReport) -> dict[str, float]:
    rows = max(report.rows_clean, 1)
    return {"engine_cc": report.engine_imputed / rows, "mileage_km": report.mileage_imputed / rows}


def training_summary(X: pd.DataFrame, y: pd.Series, report: CurrentCleaningReport) -> dict:
    """Aggregate statistics of the training data that a later batch is compared with."""
    frame = drift_frame(X, y)
    numeric = {}
    for col in NUMERIC:
        edges = decile_edges(frame[col])
        numeric[col] = {"edges": edges, "shares": bin_shares(frame[col], edges), "median": float(frame[col].median())}
    return {
        "rows": len(frame),
        "numeric": numeric,
        "categorical": {col: category_shares(frame[col]) for col in CATEGORICAL},
        "missing": missing_shares(report),
    }


# -- comparison --------------------------------------------------------------------


def _status(value: float, warn: float, alert: float) -> str:
    return "alert" if value > alert else "warn" if value > warn else "ok"


def compare_numeric(ref: dict, values: pd.Series, t: Thresholds) -> dict:
    if values.notna().sum() == 0:
        return {"psi": None, "status": "skipped", "train_median": ref["median"], "batch_median": None}
    shares = bin_shares(values, ref["edges"])
    value = psi(ref["shares"], shares)
    return {"psi": value, "status": _status(value, t.psi_warn, t.psi_alert), "train_median": ref["median"], "batch_median": float(values.median())}


def compare_categorical(ref: dict[str, float], values: pd.Series, t: Thresholds) -> dict:
    batch = values.astype(str).where(values.astype(str).isin(list(ref)), UNSEEN)
    batch_shares = batch.value_counts(normalize=True)
    keys = list(ref) + ([UNSEEN] if UNSEEN in batch_shares else [])
    e = [ref.get(k, 0.0) for k in keys]
    a = [float(batch_shares.get(k, 0.0)) for k in keys]
    value = psi(e, a)
    shifts = sorted(({"value": k, "train": ek, "batch": ak, "shift": ak - ek} for k, ek, ak in zip(keys, e, a)), key=lambda s: -abs(s["shift"]))
    max_shift = abs(shifts[0]["shift"]) if shifts else 0.0
    status = "alert" if value > t.psi_alert or max_shift > t.share_shift_alert else "warn" if value > t.psi_warn else "ok"
    return {"psi": value, "max_share_shift": max_shift, "status": status, "top_shifts": shifts[:3]}


def performance(artifact, df: pd.DataFrame, reference_year: int, t: Thresholds) -> dict:
    """Live error and interval coverage on a batch that has prices."""
    iv = artifact.predict(df, reference_year)
    price = df["price"].to_numpy(dtype=float)
    ape = np.abs(np.exp(iv.pred) - price) / price
    log_price = np.log(price)
    coverage = float(np.mean((log_price >= iv.lo) & (log_price <= iv.hi)))
    cv = artifact.metrics.get("cv_random", {}).get("median_ape", {}).get("mean")
    reference = cv if cv is not None else artifact.metrics["holdout"]["median_ape"]
    live = float(np.median(ape))
    ratio = live / reference
    return {
        "rows": int(len(df)),
        "median_ape": live,
        "reference_median_ape": reference,
        "reference": "5-fold CV" if cv is not None else "calibration holdout",
        "ratio": ratio,
        "mape_status": "alert" if ratio > t.mape_ratio_alert else "ok",
        "coverage": coverage,
        "target_coverage": artifact.coverage,
        "coverage_status": "alert" if coverage < t.coverage_min else "ok",
    }


def check(artifact, df: pd.DataFrame, report: CurrentCleaningReport, reference_year: int, t: Thresholds, ignore: tuple[str, ...] = ()) -> dict:
    """Every drift check for a cleaned batch. `ignore` names features to report but not alert on."""
    summary = artifact.summary
    X = artifact.features(df, reference_year)
    has_price = "price" in df and df["price"].notna().all() and len(df) > 0
    frame = drift_frame(X, np.log(df["price"].astype(float)) if has_price else None)

    numeric = {col: compare_numeric(summary["numeric"][col], frame[col], t) for col in NUMERIC}
    categorical = {col: compare_categorical(summary["categorical"][col], frame[col], t) for col in CATEGORICAL}
    batch_missing = missing_shares(report)
    missing = {
        col: {
            "train": summary["missing"][col],
            "batch": batch_missing[col],
            "status": "alert" if abs(batch_missing[col] - summary["missing"][col]) > t.missing_shift_alert else "ok",
        }
        for col in batch_missing
    }
    perf = performance(artifact, df, reference_year, t) if has_price else None

    alerts = [f"{col}: PSI {r['psi']:.2f}" for col, r in numeric.items() if r["status"] == "alert" and col not in ignore]
    alerts += [
        f"{col}: PSI {r['psi']:.2f}, largest share change {r['max_share_shift']:.0%}"
        for col, r in categorical.items()
        if r["status"] == "alert" and col not in ignore
    ]
    alerts += [f"{col} missing: {r['train']:.0%} in training, {r['batch']:.0%} now" for col, r in missing.items() if r["status"] == "alert" and col not in ignore]
    if perf and perf["mape_status"] == "alert":
        alerts.append(f"median error {perf['median_ape']:.1%}, {perf['ratio']:.1f} times the {perf['reference']} error")
    if perf and perf["coverage_status"] == "alert":
        alerts.append(f"80% range holds {perf['coverage']:.0%} of prices")
    return {
        "model_version": artifact.version,
        "batch_rows_clean": report.rows_clean,
        "batch_rows_raw": report.rows_raw,
        "reference_year": reference_year,
        "thresholds": asdict(t),
        "ignored": list(ignore),
        "numeric": numeric,
        "categorical": categorical,
        "missing": missing,
        "performance": perf,
        "alerts": alerts,
        "drift": bool(alerts),
    }


# -- input and output ---------------------------------------------------------------


def load_batch(paths: list[Path]) -> pd.DataFrame:
    """Listings from JSONL or CSV files, or folders laid out like data/raw, in the collector's format."""
    parts = []
    for path in map(Path, paths):
        if path.is_dir():
            part = load_all(path)
        elif path.suffix == ".csv":
            part = pd.read_csv(path)
        else:
            part = pd.read_json(path, lines=True, dtype=False)
        if "observed_at" not in part:
            raise ValueError(f"{path}: every listing needs an observed_at timestamp")
        part["observed_at"] = pd.to_datetime(part["observed_at"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        part["source"] = part["source"].fillna("garirbazar") if "source" in part else "garirbazar"
        if "id" not in part:
            part["id"] = [f"{path.name}:{i}" for i in range(len(part))]
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def markdown(result: dict, batch_name: str) -> str:
    lines = [
        f"# Drift check: {batch_name}",
        "",
        f"Model {result['model_version']}. Batch: {result['batch_rows_clean']:,} listings after cleaning ({result['batch_rows_raw']:,} read), "
        f"ages measured to {result['reference_year']}.",
        "",
        f"**Result: {'drift, ' + str(len(result['alerts'])) + ' alert(s)' if result['drift'] else 'no alert'}.**",
        "",
    ]
    lines += [f"- {a}" for a in result["alerts"]]
    if result["ignored"]:
        lines += ["", f"Reported but not alerted on: {', '.join(result['ignored'])}."]
    perf = result["performance"]
    if perf:
        lines += [
            "",
            "## Accuracy on this batch",
            "",
            "| Check | Training | This batch | Status |",
            "|---|---|---|---|",
            f"| Median error | {perf['reference_median_ape']:.1%} ({perf['reference']}) | {perf['median_ape']:.1%} | {perf['mape_status']} |",
            f"| Inside the 80% range | {perf['target_coverage']:.0%} (target) | {perf['coverage']:.1%} | {perf['coverage_status']} |",
        ]
    lines += ["", "## Numbers", "", "| Feature | PSI | Median in training | Median now | Status |", "|---|---|---|---|---|"]
    for col, r in result["numeric"].items():
        if r["psi"] is None:
            lines.append(f"| {col} | n/a | {r['train_median']:.2f} | n/a | {r['status']} |")
        else:
            lines.append(f"| {col} | {r['psi']:.3f} | {r['train_median']:.2f} | {r['batch_median']:.2f} | {r['status']} |")
    lines += ["", "## Categories", "", "| Feature | PSI | Largest share changes | Status |", "|---|---|---|---|"]
    for col, r in result["categorical"].items():
        shifts = "; ".join(f"{s['value']} {s['train']:.0%} to {s['batch']:.0%}" for s in r["top_shifts"])
        lines.append(f"| {col} | {r['psi']:.3f} | {shifts} | {r['status']} |")
    lines += ["", "## Filled-in values", "", "| Field | Filled in training | Filled now | Status |", "|---|---|---|---|"]
    for col, r in result["missing"].items():
        lines.append(f"| {col} | {r['train']:.0%} | {r['batch']:.0%} | {r['status']} |")
    t = result["thresholds"]
    lines += [
        "",
        f"Thresholds: PSI above {t['psi_alert']} (warn above {t['psi_warn']}), a category's share moving more than "
        f"{t['share_shift_alert']:.0%}, the filled-in share moving more than {t['missing_shift_alert']:.0%}, "
        f"median error above {t['mape_ratio_alert']} times training, range coverage below {t['coverage_min']:.0%}.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("batch", nargs="+", type=Path, help="JSONL or CSV files of listings, or data/raw-style folders")
    p.add_argument("--artifact", type=Path, help=f"artifact folder (default: ${settings.ARTIFACT_ENV} or the newest)")
    p.add_argument("--out-dir", type=Path, default=REPORTS)
    p.add_argument("--name", help="report file name (default: the first batch file's name)")
    p.add_argument("--ignore", default="", help="comma-separated features to report but not alert on")
    for field, default in asdict(Thresholds()).items():
        p.add_argument("--" + field.replace("_", "-"), type=float, default=default)
    args = p.parse_args(argv)

    artifact = load_artifact(settings.artifact_dir(args.artifact))
    with settings.reproducible_pandas():
        raw = load_batch(args.batch)
        df, report, year = clean_current(raw, artifact.metadata["known_models"])
    if df.empty:
        print("No usable listings in the batch after cleaning.")
        return 2
    t = Thresholds(**{f: getattr(args, f) for f in asdict(Thresholds())})
    ignore = tuple(s.strip() for s in args.ignore.split(",") if s.strip())
    result = check(artifact, df, report, year, t, ignore)

    name = args.name or args.batch[0].stem
    args.out_dir.mkdir(parents=True, exist_ok=True)
    md = markdown(result, name)
    (args.out_dir / f"{name}.md").write_text(md, encoding="utf-8")
    write_json(args.out_dir / f"{name}.json", result)
    print(md)
    print(f"Wrote {args.out_dir / name}.md and .json")
    return 1 if result["drift"] else 0


if __name__ == "__main__":
    sys.exit(main())
