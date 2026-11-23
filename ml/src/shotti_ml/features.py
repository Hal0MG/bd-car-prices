"""Turn cleaned listings into model inputs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import FUEL_COLUMNS, REFERENCE_YEAR

NUMERIC = ["age", "log_km", "engine_cc", "reg_gap", "automatic", *FUEL_COLUMNS]
CATEGORICAL = ["brand", "model", "body_type"]

#: Brands and models seen fewer times than this are pooled, so a one-off listing
#: can't carve out its own category. Counts use features only, never the price.
MIN_BRAND_COUNT = 10
MIN_MODEL_COUNT = 5


def _pool_rare(values: pd.Series, min_count: int, label: str) -> pd.Series:
    counts = values.map(values.value_counts())
    return values.where(counts >= min_count, label)


def _match_known(values: pd.Series, known, label: str) -> pd.Series:
    """Keep names the training data knew; send the rest to the pooled label."""
    return values.where(values.isin(set(known)), label)


def feature_frame(
    df: pd.DataFrame,
    reference_year: int = REFERENCE_YEAR,
    extra: tuple[str, ...] = (),
    categories: dict[str, list] | None = None,
) -> pd.DataFrame:
    """The model inputs for cleaned listings, without the target.

    With `categories` (the training data's categories, for serving and monitoring) a brand or model
    is matched to the names training saw instead of pooled by its count in `df`; unseen names get
    the pooled label, and any value outside the training categories becomes missing.
    """
    if categories is None:
        brand = _pool_rare(df["brand"], MIN_BRAND_COUNT, "Other brand")
        model = _pool_rare(df["car_model"], MIN_MODEL_COUNT, "Other model")
    else:
        brand = _match_known(df["brand"], categories["brand"], "Other brand")
        model = _match_known(df["car_model"], categories["model"], "Other model")
    X = pd.DataFrame(
        {
            "age": (reference_year - df["build_year"]).clip(lower=0),
            "log_km": np.log1p(df["km"]),
            "engine_cc": df["engine_cc"],
            "reg_gap": df["reg_gap"],
            "automatic": df["automatic"],
            **{col: df[col] for col in FUEL_COLUMNS},
            "brand": brand,
            "model": model,
            "body_type": df["body_type"],
        }
    )
    for col in extra:
        X[col] = df[col].astype(str)
    for col in [*CATEGORICAL, *extra]:
        if categories is None:
            X[col] = X[col].astype("category")
        else:
            known = categories[col]
            X[col] = pd.Categorical(X[col].where(X[col].isin(known)), categories=known)
    return X


def build_features(df: pd.DataFrame, reference_year: int = REFERENCE_YEAR, extra: tuple[str, ...] = ()) -> tuple[pd.DataFrame, pd.Series]:
    """Return the feature table and the target, the log of the asking price.

    Age is measured to `reference_year`: 2021 for the Bikroy file, the year of collection for fresh listings.
    `extra` names more columns of `df` to include as categories, such as "condition" or "source".
    """
    X = feature_frame(df, reference_year, extra)
    y = np.log(df["price"].astype(float)).rename("log_price")
    return X, y
