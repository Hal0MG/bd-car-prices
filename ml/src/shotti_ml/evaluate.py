"""Cross-validation and error metrics."""

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


def learning_curve(
    make_model: Callable,
    X: pd.DataFrame,
    y: pd.Series,
    *,
    fractions=(0.1, 0.2, 0.35, 0.5, 0.75, 1.0),
    n_splits: int = 5,
    n_repeats: int = 3,
    seed: int = 0,
) -> pd.DataFrame:
    """Median error as the training set grows, always scored on the same untouched test folds.

    A curve that is still falling at 100% says more data would help; a flat one says it would not.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for fold, (train, test) in enumerate(RepeatedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed).split(X)):
        shuffled = rng.permutation(train)
        for fraction in fractions:
            used = shuffled[: max(30, int(len(shuffled) * fraction))]
            model = make_model().fit(X.iloc[used], y.iloc[used])
            error = score(y.iloc[test].to_numpy(), np.asarray(model.predict(X.iloc[test])))["median_ape"]
            rows.append({"fold": fold, "fraction": fraction, "n_train": len(used), "median_ape": error})
    return pd.DataFrame(rows)
