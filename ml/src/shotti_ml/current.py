"""Load and clean collected GarirBazar snapshots into the shape the models expect.

The cards are sparser than the 2021 dataset: about one in five omits engine size ("N/A"),
about six in ten omit mileage, and about one in twenty has no price ("NEGOTIABLE"). They also
never show body style, or whether a car is used or reconditioned. Each gap is handled in the
open and counted in the cleaning report.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .collect.garirbazar import canonical_model
from .data import FUEL_PATTERNS, MAX_KM, MIN_PLAUSIBLE_CC

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "garirbazar" / "snapshots"
BIKROY_FILE = Path(__file__).resolve().parents[2] / "data" / "raw" / "bikroy" / "bikroy_clean.jsonl"

#: Models whose name starts with another model's name. Without these, "Corolla Cross" collapses into
#: "Corolla" and "Yaris Cross" into "Yaris", which are different cars at different prices.
PREFIX_ALIASES = {
    "land cruiser prado": "Prado",
    "land cruiser-prado": "Prado",
    "corolla cross": "Corolla Cross",
    "corolla fielder": "Fielder",
    "corolla axio": "Axio",
    "yaris cross": "Yaris Cross",
    "rav 4": "RAV4",
}

MIN_PRICE = 100_000
MAX_PRICE = 300_000_000
#: A car priced below a quarter or above four times the median of comparable cars is a typo or a bait ad.
OUTLIER_LOW, OUTLIER_HIGH = 0.25, 4.0
MIN_COMPARABLES = 5


@dataclass
class CurrentCleaningReport:
    rows_raw: int
    seen_in_several_snapshots: int
    no_price: int
    electric_dropped: int
    implausible_year: int
    implausible_price: int
    price_outliers: int
    engine_imputed: int
    mileage_imputed: int
    rows_clean: int
    suspect_dropped: int = 0
    rows_from_bikroy: int = 0
    no_model: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def canonical_current(model_raw: str, known_models: list[str]) -> str:
    """The model's canonical name: the explicit aliases first, then the longest known model the text starts with."""
    lowered = model_raw.lower().strip()
    for prefix, name in sorted(PREFIX_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if lowered == prefix or lowered.startswith((prefix + " ", prefix + "-")):
            return name
    return canonical_model(model_raw, known_models)


def load_snapshots(directory: Path = SNAPSHOT_DIR) -> pd.DataFrame:
    rows = [
        {**json.loads(line), "filtered": path.stem.endswith("-filtered"), "source": "garirbazar", "condition": None}
        for path in sorted(directory.glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return pd.DataFrame(rows)


def load_bikroy(path: Path = BIKROY_FILE) -> pd.DataFrame:
    """Bikroy listings prepared by collect/bikroy_pdf.py; empty if the file isn't there.

    These were read from pages saved in a browser and skew towards dearer cars, so they count as
    over-sampled (`filtered`) and stay out of the like-for-like comparison with 2021.
    """
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_json(path, lines=True, dtype=False)
    df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    df["filtered"] = True
    df["suspect"] = df["suspect"].fillna(False).astype(bool)
    return df


def load_all() -> pd.DataFrame:
    """GarirBazar snapshots and the Bikroy file, one row per sighting, with a `source` column."""
    parts = [load_snapshots(), load_bikroy()]
    return pd.concat([p for p in parts if not p.empty], ignore_index=True)


def _tidy_case(value: str) -> str:
    """'corolla cross' -> 'Corolla Cross', but leave 'BMW' and 'CR-V' alone."""
    return value.title() if value.islower() else value


def _impute(values: pd.Series, *groupings: pd.Series) -> pd.Series:
    """Fill gaps with the median of the same group, trying each grouping in turn, then the overall median."""
    filled = values.copy()
    for grouping in groupings:
        filled = filled.fillna(values.groupby(grouping).transform("median"))
    return filled.fillna(values.median())


def _price_outliers(df: pd.DataFrame) -> pd.Series:
    """True for listings far from comparable cars: same model, build year within two."""
    flagged = pd.Series(False, index=df.index)
    for _, group in df.groupby("car_model"):
        if len(group) < MIN_COMPARABLES + 1:
            continue
        for index, row in group.iterrows():
            others = group[(group.index != index) & ((group["build_year"] - row["build_year"]).abs() <= 2)]
            if len(others) >= MIN_COMPARABLES:
                ratio = row["price"] / others["price"].median()
                flagged[index] = ratio < OUTLIER_LOW or ratio > OUTLIER_HIGH
    return flagged


def clean_current(raw: pd.DataFrame, known_models: list[str]) -> tuple[pd.DataFrame, CurrentCleaningReport, int]:
    """Return the cleaned listings, a count of every change, and the year ages are measured to."""
    rows_raw = len(raw)
    df = raw.sort_values("observed_at").copy()
    reference_year = int(pd.to_datetime(df["observed_at"]).dt.year.max())

    if "source" not in df:
        df["source"] = "garirbazar"
    if "condition" not in df:
        df["condition"] = None
    suspect = df["suspect"].fillna(False).astype(bool) if "suspect" in df else pd.Series(False, index=df.index)
    n_suspect = int(suspect.sum())
    df = df[~suspect]  # prices a human would call a misread (an extra zero), left unrepaired and unused

    several = int(df.duplicated(["source", "id"]).sum())
    df = df.drop_duplicates(["source", "id"], keep="last")  # the latest sighting of each ad

    no_price = int(df["price_bdt"].isna().sum())
    df = df[df["price_bdt"].notna()]

    electric = df["fuel"].fillna("").str.contains("electric", case=False)
    n_electric = int(electric.sum())
    df = df[~electric]

    bad_year = ~df["year"].between(1985, reference_year + 1)
    n_bad_year = int(bad_year.sum())
    df = df[~bad_year]

    bad_price = ~df["price_bdt"].between(MIN_PRICE, MAX_PRICE)
    n_bad_price = int(bad_price.sum())
    df = df[~bad_price].reset_index(drop=True)

    df["price"] = df["price_bdt"].astype(float)
    df["build_year"] = df["year"].astype(int)
    df["brand"] = df["make"].map(_tidy_case)
    df["car_model"] = [
        _tidy_case(m if source == "bikroy" else canonical_current(m, known_models))  # Bikroy names were already made canonical
        for m, source in zip(df["model"].fillna(""), df["source"])
    ]
    df["condition"] = df["condition"].fillna("Unknown")
    no_model = df["car_model"] == ""
    n_no_model = int(no_model.sum())
    df = df[~no_model].reset_index(drop=True)

    outliers = _price_outliers(df)
    n_outliers = int(outliers.sum())
    df = df[~outliers].reset_index(drop=True)

    engine = df["engine_cc"].where(df["engine_cc"] >= MIN_PLAUSIBLE_CC)
    n_engine = int(engine.isna().sum())
    df["engine_cc"] = _impute(engine, df["car_model"], df["brand"])

    mileage = df["mileage_km"].clip(upper=MAX_KM)
    n_mileage = int(mileage.isna().sum())
    df["km"] = _impute(mileage, df["build_year"])

    registered = df["registration_year"]
    df["reg_gap"] = (registered - df["build_year"]).clip(lower=0).fillna(0).astype(int)
    df["automatic"] = (df["transmission"].fillna("Automatic").str.lower() == "automatic").astype(int)
    fuel = df["fuel"].fillna("").str.lower()
    for name, pattern in FUEL_PATTERNS.items():
        df[f"fuel_{name}"] = fuel.str.contains(pattern).astype(int)
    df["body_type"] = "Unknown"  # the cards don't show it

    report = CurrentCleaningReport(
        rows_raw=rows_raw,
        seen_in_several_snapshots=several,
        no_price=no_price,
        electric_dropped=n_electric,
        implausible_year=n_bad_year,
        implausible_price=n_bad_price,
        price_outliers=n_outliers,
        engine_imputed=n_engine,
        mileage_imputed=n_mileage,
        rows_clean=len(df),
        suspect_dropped=n_suspect,
        rows_from_bikroy=int((df["source"] == "bikroy").sum()),
        no_model=n_no_model,
    )
    return df, report, reference_year
