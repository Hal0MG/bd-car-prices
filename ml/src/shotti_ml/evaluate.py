"""Cross-validation, error metrics and prediction intervals."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, RepeatedKFold


def score(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> dict[str, float]:
    """Errors on the log scale (R2, RMSLE) and in taka (MAE, relative error)."""
    true, pred = np.exp(y_true_log), np.exp(y_pred_log)
    ape = np.abs(pred - true) / true
    return {
        "r2_log": float(r2_score(y_true_log, y_pred_log)),
        "rmsle": float(np.sqrt(mean_squared_error(y_true_log, y_pred_log))),
        "mae_bdt": float(np.mean(np.abs(pred - true))),
        "median_ape": float(np.median(ape)),
        "mape": float(ape.mean()),
    }


def cross_validate(
    make_model: Callable,
    X: pd.DataFrame,
    y: pd.Series,
    *,
    groups: pd.Series | None = None,
    n_splits: int = 5,
    n_repeats: int = 3,
    seed: int = 0,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Repeated k-fold scores per fold, plus each row's out-of-fold prediction.

    Without `groups` every fold is random, which tests pricing a car like ones already
    seen. With `groups` (the car model) whole models are held out together, which tests
    pricing a model the training data has never listed.
    """
    if groups is None:
        splits = list(RepeatedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed).split(X))
    else:
        splits = []
        for repeat in range(n_repeats):
            folds = GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed + repeat)
            splits += list(folds.split(X, y, groups))

    oof = np.zeros((len(X), n_repeats))
    rows = []
    for i, (train, test) in enumerate(splits):
        model = make_model().fit(X.iloc[train], y.iloc[train])
        pred = np.asarray(model.predict(X.iloc[test]))
        rows.append(score(y.iloc[test].to_numpy(), pred))
        oof[test, i // n_splits] = pred
    return pd.DataFrame(rows), oof.mean(axis=1)


def summarise(folds: pd.DataFrame) -> dict[str, dict[str, float]]:
    return {col: {"mean": float(folds[col].mean()), "std": float(folds[col].std())} for col in folds}


def conformal_intervals(
    make_model: Callable,
    X: pd.DataFrame,
    y: pd.Series,
    *,
    alpha: float = 0.2,
    n_splits: int = 5,
    n_repeats: int = 3,
    cal_fraction: float = 0.25,
    seed: int = 0,
) -> pd.DataFrame:
    """Split conformal prediction: how wide an interval must be to hit its coverage target.

    Each training fold is split again: the model fits on most of it and the rest sets the
    interval half-width q (the (1 - alpha) quantile of its absolute log errors). Intervals on
    the held-out fold are prediction * exp(-q) to prediction * exp(+q). Coverage is then
    measured on rows that played no part in fitting or calibration.
    """
    rng = np.random.default_rng(seed)
    out = []
    for train, test in RepeatedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed).split(X):
        train = rng.permutation(train)
        n_cal = int(len(train) * cal_fraction)
        cal, fit = train[:n_cal], train[n_cal:]

        model = make_model().fit(X.iloc[fit], y.iloc[fit])
        resid = np.sort(np.abs(y.iloc[cal].to_numpy() - model.predict(X.iloc[cal])))
        rank = min(int(np.ceil((n_cal + 1) * (1 - alpha))), n_cal)
        q = float(resid[rank - 1])

        err = np.abs(y.iloc[test].to_numpy() - model.predict(X.iloc[test]))
        out.append({"q": q, "coverage": float(np.mean(err <= q)), "upper_to_lower": float(np.exp(2 * q))})
    return pd.DataFrame(out)
