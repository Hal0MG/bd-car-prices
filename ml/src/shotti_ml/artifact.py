"""Save and load a trained price model, and price one car with it.

An artifact is a folder:

    model.txt              LightGBM price model (log price), in LightGBM's own text format
    difficulty.txt         LightGBM model of how hard each car is to price (sets the interval width)
    metadata.json          version, features and their categories, conformal factor, imputation medians
    metrics.json           holdout and cross-validated errors
    training_summary.json  aggregate statistics of the training data, for the drift check

The models are saved as text, not pickled, so loading one never runs code. Nothing in the folder is a
single listing: only the fitted trees, category names with counts, medians and binned shares.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from .current import _tidy_case, canonical_current
from .data import FUEL_COLUMNS, MAX_KM
from .features import feature_frame
from .intervals import Interval, ScaledConformal

FORMAT_VERSION = 1
MODEL_FILE = "model.txt"
DIFFICULTY_FILE = "difficulty.txt"
METADATA_FILE = "metadata.json"
METRICS_FILE = "metrics.json"
SUMMARY_FILE = "training_summary.json"

#: Fuel as a request names it -> the fuel flags the model was trained on. "other" sets none,
#: like the cards that say "Other", "Gas" or nothing.
FUELS = {
    "petrol": ["fuel_petrol"],
    "octane": ["fuel_petrol"],
    "hybrid": ["fuel_hybrid"],
    "diesel": ["fuel_diesel"],
    "cng": ["fuel_cng"],
    "lpg": ["fuel_lpg"],
    "other": [],
}


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=_plain) + "\n", encoding="utf-8")


def _plain(value):
    """numpy scalars and arrays to plain JSON values."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"not JSON serialisable: {type(value)}")


def save_artifact(directory: Path, fitted: ScaledConformal, metadata: dict, metrics: dict, summary: dict) -> Path:
    """Write a new artifact folder. Refuses to overwrite one that exists, so a version always means one model."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    fitted.model.booster_.save_model(str(directory / MODEL_FILE))
    fitted.difficulty.booster_.save_model(str(directory / DIFFICULTY_FILE))
    meta = {**metadata, "format": FORMAT_VERSION, "interval": {"method": "scaled by difficulty", "alpha": fitted.alpha, "q": fitted.q}}
    write_json(directory / METADATA_FILE, meta)
    write_json(directory / METRICS_FILE, metrics)
    write_json(directory / SUMMARY_FILE, summary)
    return directory


@dataclass
class Artifact:
    directory: Path
    metadata: dict
    metrics: dict
    summary: dict
    conformal: ScaledConformal

    @property
    def version(self) -> str:
        return self.metadata["version"]

    @property
    def coverage(self) -> float:
        return 1 - self.conformal.alpha

    def features(self, df: pd.DataFrame, reference_year: int | None = None) -> pd.DataFrame:
        """Model inputs for cleaned listings, with categories matched to the ones training saw."""
        feats = self.metadata["features"]
        year = self.metadata["reference_year"] if reference_year is None else reference_year
        X = feature_frame(df, year, tuple(feats["extra"]), feats["categories"])
        return X[feats["columns"]]

    def predict(self, df: pd.DataFrame, reference_year: int | None = None) -> Interval:
        """Log-price prediction and 80% interval for cleaned listings."""
        return self.conformal.predict(self.features(df, reference_year))

    # -- one car, as the API receives it --------------------------------------------

    def _match(self, text: str, names: dict[str, int]) -> str | None:
        lowered = text.strip().lower()
        return next((name for name in names if name.lower() == lowered), None)

    def price_car(self, car: dict) -> dict:
        """Price one car described by plain fields (see api.Car). Missing engine size and mileage
        are filled from the training data's medians, the way cleaning fills them."""
        meta = self.metadata
        brand = self._match(car["brand"], meta["brands"]) or _tidy_case(car["brand"].strip())
        model = self._match(car["model"], meta["car_models"])
        if model is None:
            canonical = _tidy_case(canonical_current(car["model"].strip(), meta["known_models"]))
            model = self._match(canonical, meta["car_models"]) or canonical

        imputed = []
        impute = meta["impute"]
        engine = car.get("engine_cc")
        if engine is None:
            engine = impute["engine_by_model"].get(model) or impute["engine_by_brand"].get(brand) or impute["engine_overall"]
            imputed.append("engine_cc")
        km = car.get("mileage_km")
        if km is None:
            km = impute["km_by_year"].get(str(car["build_year"]), impute["km_overall"])
            imputed.append("mileage_km")
        registered = car.get("registration_year")

        row = {
            "build_year": car["build_year"],
            "km": min(float(km), MAX_KM),
            "engine_cc": float(engine),
            "reg_gap": max(0, registered - car["build_year"]) if registered else 0,
            "automatic": int(car.get("transmission", "automatic") == "automatic"),
            **{col: int(col in FUELS[car["fuel"]]) for col in FUEL_COLUMNS},
            "brand": brand,
            "car_model": model,
            "body_type": "Unknown",
            "source": car.get("listing_site", "garirbazar"),
            "condition": car.get("condition", "Unknown"),
        }
        X = self.features(pd.DataFrame([row]))
        iv = self.conformal.predict(X)
        return {
            "price_bdt": int(round(float(np.exp(iv.pred[0])), -3)),
            "low_bdt": int(round(float(np.exp(iv.lo[0])), -3)),
            "high_bdt": int(round(float(np.exp(iv.hi[0])), -3)),
            "coverage": self.coverage,
            "model_version": self.version,
            "matched_brand": brand,
            "matched_model": model,
            "model_seen_in_training": bool(X["model"].iloc[0] == model),
            "imputed": imputed,
        }


def load_artifact(directory: Path | str) -> Artifact:
    directory = Path(directory)
    if not (directory / METADATA_FILE).exists():
        raise FileNotFoundError(f"{directory} is not a model artifact (no {METADATA_FILE})")
    read = lambda name: json.loads((directory / name).read_text(encoding="utf-8"))  # noqa: E731
    metadata = read(METADATA_FILE)
    if metadata.get("format") != FORMAT_VERSION:
        raise ValueError(f"artifact format {metadata.get('format')} is not {FORMAT_VERSION}")
    conformal = ScaledConformal(
        model=lgb.Booster(model_file=str(directory / MODEL_FILE)),
        difficulty=lgb.Booster(model_file=str(directory / DIFFICULTY_FILE)),
        q=float(metadata["interval"]["q"]),
        alpha=float(metadata["interval"]["alpha"]),
    )
    return Artifact(directory, metadata, read(METRICS_FILE), read(SUMMARY_FILE), conformal)
