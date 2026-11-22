"""Train the production price model and save it as a versioned artifact.

Run from the ml/ folder:
    .venv/Scripts/python.exe -I -m shotti_ml.train                  # all listings, logged to MLflow
    .venv/Scripts/python.exe -I -m shotti_ml.train --sources garirbazar --cv-repeats 1 --no-mlflow

The model is the one export.py fits for the site: LightGBM on log price with the same features,
fitted on a seeded 75% of the cleaned listings, with the other 25% setting the width of the
"scaled by difficulty" 80% range. The same seed and split give the same model.

Writes artifacts/<version>/ (see artifact.py) and, unless --no-mlflow, logs the parameters,
metrics and artifact folder to a local MLflow store in mlruns/.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import settings
from .artifact import save_artifact
from .current import clean_current, load_all
from .data import clean, load_raw
from .drift import training_summary
from .evaluate import cross_validate, score, summarise
from .features import build_features
from .intervals import evaluate_intervals, fit_scaled_by_difficulty, scaled_by_difficulty, summarise_intervals
from .models import LGBM_PARAMS, make_lgbm
from .run_current import EXTRA

#: The split export.py uses, so the artifact and the site's prices come from the same model.
ALPHA = 0.2
CAL_FRACTION = 0.25
SPLIT_SEED = 0
EXPERIMENT = "shotti-dam-price"
SOURCES = ("garirbazar", "bikroy")


def load_training_data(data_dir: Path, sources: tuple[str, ...] = SOURCES) -> tuple[pd.DataFrame, list[str]]:
    """Raw sightings from the chosen sites, and the model names of the 2021 file that cleaning matches against."""
    data_dir = Path(data_dir)
    old_file = data_dir / "mendeley" / "car_dataset.csv"
    if not old_file.exists():
        raise FileNotFoundError(f"{old_file} is missing. Point --data-dir (or ${settings.DATA_ENV}) at a folder laid out like data/raw.")
    try:
        raw = load_all(data_dir)
    except ValueError:  # nothing to concatenate
        raw = pd.DataFrame()
    if raw.empty:
        raise FileNotFoundError(f"No listings under {data_dir}/garirbazar/snapshots or {data_dir}/bikroy.")
    raw = raw[raw["source"].isin(sources)].reset_index(drop=True)
    old, _ = clean(load_raw(old_file))
    return raw, sorted(old["car_model"].unique())


def fingerprint(X: pd.DataFrame, y: pd.Series) -> str:
    """A hash of the exact model inputs and targets: two artifacts with the same one trained on the same data."""
    h = hashlib.sha256(pd.util.hash_pandas_object(X, index=False).to_numpy().tobytes())
    h.update(np.ascontiguousarray(y.to_numpy(dtype=float)).tobytes())
    return h.hexdigest()


def git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=settings.ML_ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def train(
    data_dir: Path,
    out_root: Path,
    *,
    sources: tuple[str, ...] = SOURCES,
    cv_repeats: int = 3,
    version: str | None = None,
) -> tuple[Path, dict, dict]:
    """Fit, evaluate and save. Returns the artifact folder, its metrics and the parameters to log."""
    with settings.reproducible_pandas():
        return _train(Path(data_dir), Path(out_root), sources, cv_repeats, version)


def _train(data_dir: Path, out_root: Path, sources: tuple[str, ...], cv_repeats: int, version: str | None) -> tuple[Path, dict, dict]:
    started = time.time()
    raw, known_models = load_training_data(data_dir, sources)
    df, report, year = clean_current(raw, known_models)
    X, y = build_features(df, year, EXTRA)

    order = np.random.default_rng(SPLIT_SEED).permutation(len(X))
    n_cal = int(len(X) * CAL_FRACTION)
    cal, fit = order[:n_cal], order[n_cal:]
    fitted = fit_scaled_by_difficulty(make_lgbm, X.iloc[fit], y.iloc[fit], X.iloc[cal], y.iloc[cal], ALPHA)

    # The calibration rows never trained the trees, so they give an honest single-split error.
    # They did set the conformal factor, so their coverage is close to 80% by construction.
    iv = fitted.predict(X.iloc[cal])
    y_cal = y.iloc[cal].to_numpy()
    metrics: dict = {
        "holdout": {
            "rows": int(n_cal),
            **score(y_cal, iv.pred),
            "coverage": float(np.mean((y_cal >= iv.lo) & (y_cal <= iv.hi))),
            "median_ratio": float(np.median(np.exp((iv.hi - iv.lo) / 2))),
        }
    }
    if cv_repeats > 0:
        folds, _ = cross_validate(make_lgbm, X, y, n_repeats=cv_repeats)
        metrics["cv_random"] = {"n_splits": 5, "n_repeats": cv_repeats, **summarise(folds)}
        ivs = summarise_intervals(evaluate_intervals(X, y, {"Scaled by difficulty": scaled_by_difficulty}, alpha=ALPHA, n_repeats=cv_repeats))
        row = ivs.loc["Scaled by difficulty"]
        metrics["interval_cv"] = {"n_splits": 5, "n_repeats": cv_repeats, **{k: float(v) for k, v in row.items()}}

    created = datetime.now(timezone.utc)
    fp = fingerprint(X, y)
    version = version or f"{created:%Y%m%d-%H%M%S}-{fp[:6]}"
    metrics = {"version": version, **metrics, "train_seconds": round(time.time() - started, 1)}

    impute = {
        "engine_by_model": df.groupby("car_model")["engine_cc"].median().to_dict(),
        "engine_by_brand": df.groupby("brand")["engine_cc"].median().to_dict(),
        "engine_overall": float(df["engine_cc"].median()),
        "km_by_year": {str(k): float(v) for k, v in df.groupby("build_year")["km"].median().items()},
        "km_overall": float(df["km"].median()),
    }
    params = {
        "lgbm": LGBM_PARAMS,
        "difficulty_model": {"n_estimators": 150, "learning_rate": 0.05, "num_leaves": 7, "min_child_samples": 20},
        "alpha": ALPHA,
        "cal_fraction": CAL_FRACTION,
        "split_seed": SPLIT_SEED,
        "sources": list(sources),
        "cv_repeats": cv_repeats,
    }
    metadata = {
        "version": version,
        "created_at": created.isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "data_fingerprint": fp,
        "data": {
            "sources": list(sources),
            "rows_read": int(len(raw)),
            "rows_clean": int(len(df)),
            "rows_fit": int(len(fit)),
            "rows_calibration": int(n_cal),
            "rows_by_source": {k: int(v) for k, v in df["source"].value_counts().items()},
            "observed_from": str(raw["observed_at"].min())[:10],
            "observed_to": str(raw["observed_at"].max())[:10],
            "cleaning": report.as_dict(),
        },
        "reference_year": year,
        "known_models": known_models,
        "brands": {k: int(v) for k, v in df["brand"].value_counts().items()},
        "car_models": {k: int(v) for k, v in df["car_model"].value_counts().items()},
        "features": {
            "columns": list(X.columns),
            "extra": list(EXTRA),
            "categories": {col: X[col].cat.categories.tolist() for col in X.columns if isinstance(X[col].dtype, pd.CategoricalDtype)},
        },
        "impute": impute,
        "params": params,
    }
    directory = save_artifact(Path(out_root) / version, fitted, metadata, metrics, training_summary(X, y, report))
    return directory, metrics, params


def flat_metrics(metrics: dict) -> dict[str, float]:
    out = {f"holdout_{k}": v for k, v in metrics["holdout"].items()}
    for k, v in metrics.get("cv_random", {}).items():
        if isinstance(v, dict):
            out[f"cv_{k}"] = v["mean"]
            out[f"cv_{k}_std"] = v["std"]
    for k, v in metrics.get("interval_cv", {}).items():
        if k not in ("n_splits", "n_repeats"):
            out[f"interval_cv_{k}"] = v
    out["train_seconds"] = metrics["train_seconds"]
    return {k: float(v) for k, v in out.items()}


def log_to_mlflow(directory: Path, metrics: dict, params: dict, mlruns: Path, experiment: str = EXPERIMENT) -> str:
    """Log one training run to a local MLflow store (SQLite file plus an artifact folder, both under `mlruns`)."""
    import json

    import mlflow

    mlruns = Path(mlruns).resolve()
    mlruns.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri("sqlite:///" + (mlruns / "mlflow.db").as_posix())
    if mlflow.get_experiment_by_name(experiment) is None:
        mlflow.create_experiment(experiment, artifact_location=(mlruns / "artifacts").as_uri())
    mlflow.set_experiment(experiment)
    meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    flat_params = {f"lgbm.{k}": v for k, v in params["lgbm"].items()}
    flat_params.update({f"difficulty.{k}": v for k, v in params["difficulty_model"].items()})
    flat_params.update({k: v for k, v in params.items() if k not in ("lgbm", "difficulty_model")})
    flat_params.update({"rows_clean": meta["data"]["rows_clean"], "rows_fit": meta["data"]["rows_fit"], "reference_year": meta["reference_year"]})
    with mlflow.start_run(run_name=meta["version"]) as run:
        mlflow.set_tags({"version": meta["version"], "git_commit": meta["git_commit"] or "", "data_fingerprint": meta["data_fingerprint"]})
        mlflow.log_params(flat_params)
        mlflow.log_metrics(flat_metrics(metrics))
        mlflow.log_metric("conformal_q", meta["interval"]["q"])
        mlflow.log_artifacts(str(directory), artifact_path="artifact")
    return run.info.run_id


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Train the price model and save a versioned artifact.")
    p.add_argument("--data-dir", type=Path, help=f"folder laid out like data/raw (default: ${settings.DATA_ENV} or ml/data/raw)")
    p.add_argument("--out-dir", type=Path, default=settings.DEFAULT_ARTIFACTS_DIR, help="where artifacts/<version>/ is written")
    p.add_argument("--sources", default=",".join(SOURCES), help="comma-separated sites to train on")
    p.add_argument("--cv-repeats", type=int, default=3, help="repeats of 5-fold CV for the metrics; 0 skips CV")
    p.add_argument("--version", help="artifact name (default: UTC time and data fingerprint)")
    p.add_argument("--no-mlflow", action="store_true", help="skip MLflow logging")
    p.add_argument("--mlruns", type=Path, help=f"MLflow store folder (default: ${settings.MLRUNS_ENV} or ml/mlruns)")
    args = p.parse_args(argv)

    sources = tuple(s.strip() for s in args.sources.split(",") if s.strip())
    directory, metrics, params = train(settings.data_dir(args.data_dir), args.out_dir, sources=sources, cv_repeats=args.cv_repeats, version=args.version)
    h = metrics["holdout"]
    print(f"Saved {directory}")
    print(f"Holdout ({h['rows']:,} cars): median error {h['median_ape']:.1%}, inside the 80% range {h['coverage']:.1%}, median range x/÷ {h['median_ratio']:.3f}")
    if "cv_random" in metrics:
        cv, ivs = metrics["cv_random"], metrics["interval_cv"]
        print(f"5-fold CV x{cv['n_repeats']}: median error {cv['median_ape']['mean']:.1%} ± {cv['median_ape']['std']:.1%}; "
              f"range coverage {ivs['coverage']:.1%} ± {ivs['coverage_std']:.1%}, median x/÷ {ivs['median_ratio']:.3f}")
    if not args.no_mlflow:
        run_id = log_to_mlflow(directory, metrics, params, settings.mlruns_dir(args.mlruns))
        print(f"MLflow run {run_id} in {settings.mlruns_dir(args.mlruns)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
