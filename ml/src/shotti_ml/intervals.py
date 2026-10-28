"""Prediction intervals that stay honest for cheap and expensive cars alike.

All three methods are split conformal: the model fits on most of the training data,
a held-back calibration set sets how wide the interval must be to hit its coverage
target, and the held-out cars are scored once, untouched. They differ in how the
width varies from car to car:

- Constant width: the same factor above and below every prediction.
- Scaled by difficulty: a second model predicts how big this car's error will be.
- Quantile (CQR): two quantile models give a lower and upper bound, which conformal
  calibration then stretches or shrinks as needed (Romano, Patterson, Candes, 2019).

Everything is on the log-price scale, so a width is a ratio: an interval of 1.25
means "between the prediction divided by 1.25 and multiplied by 1.25".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, RepeatedKFold

from .models import make_lgbm


@dataclass(frozen=True)
class Interval:
    pred: np.ndarray
    lo: np.ndarray
    hi: np.ndarray


def conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    """The finite-sample conformal quantile: the ceil((n+1)(1-alpha))-th smallest score."""
    ordered = np.sort(np.asarray(scores, dtype=float))
    rank = min(int(np.ceil((len(ordered) + 1) * (1 - alpha))), len(ordered))
    return float(ordered[rank - 1])


def constant_width(make_model, X_fit, y_fit, X_cal, y_cal, X_test, alpha) -> Interval:
    model = make_model().fit(X_fit, y_fit)
    q = conformal_quantile(np.abs(y_cal.to_numpy() - model.predict(X_cal)), alpha)
    pred = np.asarray(model.predict(X_test))
    return Interval(pred, pred - q, pred + q)


def scaled_by_difficulty(make_model, X_fit, y_fit, X_cal, y_cal, X_test, alpha, *, folds: int = 5, seed: int = 0) -> Interval:
    model = make_model().fit(X_fit, y_fit)

    # A boosted model's errors on its own training rows are far too small to learn from,
    # so the difficulty model trains on errors from rows each fit never saw.
    out_of_fold = np.zeros(len(X_fit))
    for train, test in KFold(folds, shuffle=True, random_state=seed).split(X_fit):
        out_of_fold[test] = make_model().fit(X_fit.iloc[train], y_fit.iloc[train]).predict(X_fit.iloc[test])
    abs_error = np.abs(y_fit.to_numpy() - out_of_fold)
    difficulty = make_lgbm(n_estimators=150, learning_rate=0.05, num_leaves=7, min_child_samples=20)
    difficulty.fit(X_fit, np.log(abs_error + 1e-3))

    def sigma(X):
        return np.exp(difficulty.predict(X))

    q = conformal_quantile(np.abs(y_cal.to_numpy() - model.predict(X_cal)) / sigma(X_cal), alpha)
    pred = np.asarray(model.predict(X_test))
    half = q * sigma(X_test)
    return Interval(pred, pred - half, pred + half)


def quantile_cqr(make_model, X_fit, y_fit, X_cal, y_cal, X_test, alpha) -> Interval:
    model = make_model().fit(X_fit, y_fit)
    params = dict(objective="quantile", n_estimators=300, learning_rate=0.03, num_leaves=7, min_child_samples=15)
    low = make_lgbm(alpha=alpha / 2, **params).fit(X_fit, y_fit)
    high = make_lgbm(alpha=1 - alpha / 2, **params).fit(X_fit, y_fit)

    y = y_cal.to_numpy()
    q = conformal_quantile(np.maximum(low.predict(X_cal) - y, y - high.predict(X_cal)), alpha)
    lo, hi = low.predict(X_test) - q, high.predict(X_test) + q
    # A negative q can push the bounds past each other; collapse those to their midpoint.
    mid = (lo + hi) / 2
    lo, hi = np.where(lo > hi, mid, lo), np.where(lo > hi, mid, hi)
    return Interval(np.asarray(model.predict(X_test)), lo, hi)


METHODS: dict[str, Callable] = {
    "Constant width": constant_width,
    "Scaled by difficulty": scaled_by_difficulty,
    "Quantile (CQR)": quantile_cqr,
}


def evaluate_intervals(
    X: pd.DataFrame,
    y: pd.Series,
    methods: dict[str, Callable] = METHODS,
    *,
    make_model=make_lgbm,
    alpha: float = 0.2,
    n_splits: int = 5,
    n_repeats: int = 3,
    cal_fraction: float = 0.25,
    seed: int = 0,
) -> pd.DataFrame:
    """One row per held-out car per method. Every method sees the same splits."""
    rng = np.random.default_rng(seed)
    frames = []
    for fold, (train, test) in enumerate(RepeatedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed).split(X)):
        train = rng.permutation(train)
        n_cal = int(len(train) * cal_fraction)
        cal, fit = train[:n_cal], train[n_cal:]
        for name, method in methods.items():
            iv = method(make_model, X.iloc[fit], y.iloc[fit], X.iloc[cal], y.iloc[cal], X.iloc[test], alpha)
            frames.append(
                pd.DataFrame(
                    {"method": name, "fold": fold, "row": test, "y": y.iloc[test].to_numpy(), "pred": iv.pred, "lo": iv.lo, "hi": iv.hi}
                )
            )
    out = pd.concat(frames, ignore_index=True)
    out["covered"] = (out["y"] >= out["lo"]) & (out["y"] <= out["hi"])
    out["ratio"] = np.exp((out["hi"] - out["lo"]) / 2)  # the interval is pred divided and multiplied by this
    return out


def summarise_intervals(df: pd.DataFrame) -> pd.DataFrame:
    """Coverage and typical width per method, with the spread of coverage across folds."""
    by_fold = df.groupby(["method", "fold"])["covered"].mean().groupby("method")
    grouped = df.groupby("method")
    return pd.DataFrame(
        {
            "coverage": grouped["covered"].mean(),
            "coverage_std": by_fold.std(),
            "median_ratio": grouped["ratio"].median(),
        }
    )


def by_band(df: pd.DataFrame, band: pd.Series) -> pd.DataFrame:
    """Coverage and median width per method within each band of cars (needs one band per row)."""
    keyed = df.assign(band=band.reindex(df["row"]).to_numpy())
    return keyed.groupby(["method", "band"], observed=True).agg(coverage=("covered", "mean"), median_ratio=("ratio", "median"), n=("covered", "size"))
