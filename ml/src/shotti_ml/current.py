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

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def load_snapshots(directory: Path = SNAPSHOT_DIR) -> pd.DataFrame:
    rows = [
        {**json.loads(line), "filtered": path.stem.endswith("-filtered")}
        for path in sorted(directory.glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return pd.DataFrame(rows)


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

    several = int(df.duplicated("id").sum())
    df = df.drop_duplicates("id", keep="last")  # the latest sighting of each ad

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
    df["car_model"] = [_tidy_case(canonical_model(m, known_models)) for m in df["model"].fillna("")]
    df = df[df["car_model"] != ""].reset_index(drop=True)

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
    )
    return df, report, reference_year
