"""Price a car model the training data has never listed.

The main model leans on the model name, which is useless for a name it has not seen. This module
borrows strength from related cars instead, using only facts that exist before a price does:
  * the brand's price level,
  * the words in the model name (a "Corolla Cross" shares "corolla" with other Corollas, a
    "Prado TX" shares "prado"), and
  * the usual age, mileage and engine size.
Each name-based price level is a smoothed mean of log price, computed out of fold inside the
training data (whole models held out), so the booster learns how far to trust it for a car it
has not seen. Without that step it would trust a level that already contains the car's own price.
"""

from __future__ import annotations

import re
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import GroupKFold

from .models import make_lgbm

SMOOTHING = 20.0
STOP = {"hybrid", "e:hev", "e-power", "phev", "ev", "turbo", "the", "new"}


def tokens(name: str) -> list[str]:
    words = re.findall(r"[a-z0-9:+\-]+", str(name).lower())
    return [w for w in words if w not in STOP]


def _level(sums: dict, counts: dict, key, mu: float) -> float:
    n = counts.get(key, 0)
    return (sums.get(key, 0.0) + SMOOTHING * mu) / (n + SMOOTHING)


class SimilarCarModel(BaseEstimator, RegressorMixin):
    """LightGBM plus name- and brand-level price features that need no listing of the model itself.

    `X` must carry two extra string columns, `_name` (the car model) and `_brand`; both are dropped
    before the booster sees the table, along with the pooled `model` category.
    """

    def __init__(self, use_brand: bool = True, use_tokens: bool = True, keep_model: bool = False, inner_folds: int = 5):
        self.use_brand = use_brand
        self.use_tokens = use_tokens
        self.keep_model = keep_model
        self.inner_folds = inner_folds

    # ------------------------------------------------------------------ price levels
    def _maps(self, names, brands, y):
        tok_sum, tok_n = defaultdict(float), defaultdict(int)
        br_sum, br_n = defaultdict(float), defaultdict(int)
        for name, brand, v in zip(names, brands, y):
            br_sum[brand] += v
            br_n[brand] += 1
            for t in set(tokens(name)):
                tok_sum[t] += v
                tok_n[t] += 1
        return tok_sum, tok_n, br_sum, br_n

    def _features(self, names, brands, maps, mu) -> pd.DataFrame:
        tok_sum, tok_n, br_sum, br_n = maps
        rows = []
        for name, brand in zip(names, brands):
            levels = [(_level(tok_sum, tok_n, t, mu), tok_n.get(t, 0)) for t in set(tokens(name))]
            known = [lv for lv, n in levels if n > 0]
            rows.append({
                "brand_level": _level(br_sum, br_n, brand, mu),
                "tok_mean": float(np.mean(known)) if known else mu,
                "tok_max": max(known) if known else mu,
                "tok_min": min(known) if known else mu,
                "tok_known": len(known),
            })
        out = pd.DataFrame(rows)
        keep = []
        if self.use_brand:
            keep.append("brand_level")
        if self.use_tokens:
            keep += ["tok_mean", "tok_max", "tok_min", "tok_known"]
        return out[keep]

    # ------------------------------------------------------------------ sklearn API
    def _base(self, X: pd.DataFrame) -> pd.DataFrame:
        drop = ["_name", "_brand"] + ([] if self.keep_model else ["model"])
        return X.drop(columns=[c for c in drop if c in X.columns]).reset_index(drop=True)

    def fit(self, X: pd.DataFrame, y: pd.Series):
        names, brands = X["_name"].to_numpy(), X["_brand"].to_numpy()
        yv = np.asarray(y, dtype=float)
        self.mu_ = float(yv.mean())
        base = self._base(X)
        if not (self.use_brand or self.use_tokens):
            extra = pd.DataFrame(index=base.index)
        else:
            extra = pd.DataFrame(index=base.index, columns=self._features(names[:1], brands[:1], self._maps([], [], []), self.mu_).columns, dtype=float)
            groups = pd.factorize(names)[0]
            splits = GroupKFold(n_splits=min(self.inner_folds, len(set(groups))), shuffle=True, random_state=0).split(base, yv, groups)
            for fit_idx, hold_idx in splits:
                maps = self._maps(names[fit_idx], brands[fit_idx], yv[fit_idx])
                extra.iloc[hold_idx] = self._features(names[hold_idx], brands[hold_idx], maps, float(yv[fit_idx].mean())).to_numpy()
            extra = extra.astype(float)
        self.maps_ = self._maps(names, brands, yv)
        self.model_ = make_lgbm().fit(pd.concat([base, extra], axis=1), yv)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        base = self._base(X)
        if self.use_brand or self.use_tokens:
            extra = self._features(X["_name"].to_numpy(), X["_brand"].to_numpy(), self.maps_, self.mu_)
            base = pd.concat([base, extra], axis=1)
        return self.model_.predict(base)


class NoNameModel(BaseEstimator, RegressorMixin):
    """LightGBM that never sees the model name. It is the best way found to price a car model with no listings.

    On whole models held out it misses by about 23% against 26% for the same booster given the name
    (which is a category it has never seen at test time). Brand and name-word price levels, tried
    above, made it worse. Needs the `_name` and `_brand` helper columns only so it can share a table
    with SimilarCarModel; both are dropped.
    """

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.model_ = make_lgbm().fit(self._base(X), np.asarray(y, dtype=float))
        return self

    @staticmethod
    def _base(X: pd.DataFrame) -> pd.DataFrame:
        return X.drop(columns=[c for c in ("_name", "_brand", "model") if c in X.columns])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model_.predict(self._base(X))
