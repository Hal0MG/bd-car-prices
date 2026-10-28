"""Load and clean the Bikroy used-car listings.

Source: Amik, Momen and Lanard, "Car Dataset: Used cars data from Bikroy.com",
Mendeley Data, v2, CC BY 4.0, doi:10.17632/fmb4xmp4k5.2. Prices are asking
prices in BDT. The file was created in November 2021, so every price here is
five years older than the site's tax figures.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

RAW_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "mendeley" / "car_dataset.csv"

#: The file is dated Nov 2021 and its newest model year is 2021, so age is measured to 2021.
REFERENCE_YEAR = 2021
#: Real engines start around 660cc (kei cars); anything lower is a typo (150 for 1500).
MIN_PLAUSIBLE_CC = 600
#: Seller-entered mileage runs to 900,000 km on a 2016 Prius, so it is capped.
MAX_KM = 400_000

FUEL_PATTERNS = {
    "petrol": "petrol|octane",  # "Octane" is petrol in Bangladesh
    "cng": "cng",
    "hybrid": "hybrid",
    "diesel": "diesel",
    "lpg": "lpg",
}
FUEL_COLUMNS = [f"fuel_{name}" for name in FUEL_PATTERNS]

_TEXT_COLUMNS = ("car_name", "brand", "car_model", "transmission", "body_type", "fuel_type")


@dataclass
class CleaningReport:
    rows_raw: int
    reposts_dropped: int
    engine_cc_imputed: int
    km_capped: int
    body_type_missing: int
    year_differs_from_title: int
    rows_clean: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def load_raw(path: Path | str = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    """Return the cleaned listings and a count of every change made."""
    df = raw.copy()
    for col in _TEXT_COLUMNS:
        df[col] = df[col].str.strip()

    # The same car re-posted under a new title: identical in every field but the title.
    reposts = df.drop(columns="car_name").duplicated()
    df = df.loc[~reposts].reset_index(drop=True)

    # The title ends with the build year. model_year is sometimes a later registration year.
    title_year = df["car_name"].str.extract(r"((?:19|20)\d{2})\s*$")[0].astype(float)
    df["build_year"] = title_year.fillna(df["model_year"]).astype(int)
    df["reg_gap"] = (df["model_year"] - df["build_year"]).clip(lower=0)

    # Typo engine sizes take the median of the same model (then brand, then everything).
    # Engine size is a feature, not the target, so this can't leak the label.
    bad_cc = df["engine_capacity"] < MIN_PLAUSIBLE_CC
    good = df.loc[~bad_cc]
    by_model = good.groupby("car_model")["engine_capacity"].median()
    by_brand = good.groupby("brand")["engine_capacity"].median()
    fill = (
        df["car_model"].map(by_model)
        .fillna(df["brand"].map(by_brand))
        .fillna(good["engine_capacity"].median())
    )
    df["engine_cc"] = df["engine_capacity"].where(~bad_cc, fill)

    df["km"] = df["kilometers_run"].clip(upper=MAX_KM)

    fuel = df["fuel_type"].str.lower()
    for name, pattern in FUEL_PATTERNS.items():
        df[f"fuel_{name}"] = fuel.str.contains(pattern).astype(int)
    df["automatic"] = (df["transmission"] == "Automatic").astype(int)

    body_missing = int(df["body_type"].isna().sum())
    df["body_type"] = df["body_type"].fillna("Unknown")

    report = CleaningReport(
        rows_raw=len(raw),
        reposts_dropped=int(reposts.sum()),
        engine_cc_imputed=int(bad_cc.sum()),
        km_capped=int((df["kilometers_run"] > MAX_KM).sum()),
        body_type_missing=body_missing,
        year_differs_from_title=int((df["reg_gap"] > 0).sum()),
        rows_clean=len(df),
    )
    return df, report
