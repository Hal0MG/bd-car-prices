"""Where the serving and monitoring tools look for data, artifacts and MLflow runs.

Each path can be set on the command line, then by an environment variable, then falls back to a
folder inside ml/. Raw listings never leave ml/data/raw (git ignores it), and nothing here copies them.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ML_ROOT / "data" / "raw"
DEFAULT_ARTIFACTS_DIR = ML_ROOT / "artifacts"
DEFAULT_MLRUNS_DIR = ML_ROOT / "mlruns"

DATA_ENV = "SHOTTI_DATA_DIR"
ARTIFACT_ENV = "SHOTTI_ARTIFACT"
MLRUNS_ENV = "SHOTTI_MLRUNS_DIR"


def data_dir(cli: str | Path | None = None) -> Path:
    """The folder laid out like data/raw: garirbazar/snapshots/, bikroy/bikroy_clean.jsonl, mendeley/car_dataset.csv."""
    return Path(cli or os.environ.get(DATA_ENV) or DEFAULT_DATA_DIR)


def mlruns_dir(cli: str | Path | None = None) -> Path:
    return Path(cli or os.environ.get(MLRUNS_ENV) or DEFAULT_MLRUNS_DIR)


def latest_artifact(root: Path = DEFAULT_ARTIFACTS_DIR) -> Path:
    """The most recently created artifact under `root`, by the creation time in its metadata."""
    found = []
    for meta in Path(root).glob("*/metadata.json"):
        created = json.loads(meta.read_text(encoding="utf-8")).get("created_at", "")
        found.append((created, meta.parent))
    if not found:
        raise FileNotFoundError(f"No model artifact under {root}. Train one first: python -m shotti_ml.train")
    return max(found)[1]


def artifact_dir(cli: str | Path | None = None) -> Path:
    """An artifact folder: the one given, else $SHOTTI_ARTIFACT, else the newest under ml/artifacts."""
    chosen = cli or os.environ.get(ARTIFACT_ENV)
    return Path(chosen) if chosen else latest_artifact()
