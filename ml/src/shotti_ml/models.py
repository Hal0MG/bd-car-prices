"""The three models compared in the baseline.

All predict the log of the asking price. Each factory returns a fresh,
unfitted estimator so cross-validation never reuses a fitted one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .features import CATEGORICAL, NUMERIC


class GroupMedian(RegressorMixin, BaseEstimator):
    """Predict the median log price of the car's model, else its brand, else everything.

    This is the number a dealer would quote from memory, so any real model has to beat it.
    """

    def fit(self, X: pd.DataFrame, y) -> "GroupMedian":
        y = pd.Series(np.asarray(y), index=X.index)
        self.global_ = float(y.median())
        self.by_model_ = y.groupby(X["model"].astype(str)).median()
        self.by_brand_ = y.groupby(X["brand"].astype(str)).median()
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        pred = X["model"].astype(str).map(self.by_model_)
        pred = pred.fillna(X["brand"].astype(str).map(self.by_brand_)).fillna(self.global_)
        return pred.to_numpy(dtype=float)


def make_group_median() -> GroupMedian:
    return GroupMedian()


def make_ridge():
    """Linear model on standardised numbers and one-hot categories; the penalty is chosen by CV."""
    prep = ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ]
    )
    return make_pipeline(prep, RidgeCV(alphas=np.logspace(-2, 2, 25)))


LGBM_PARAMS = dict(
    n_estimators=500,
    learning_rate=0.03,
    num_leaves=15,
    min_child_samples=8,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.8,
    reg_lambda=2.0,
    cat_smooth=20,
    min_data_per_group=10,
    random_state=0,
    verbose=-1,
)


def make_lgbm(**overrides) -> LGBMRegressor:
    """Gradient boosting with deliberately modest capacity: there are only ~1,200 rows."""
    return LGBMRegressor(**{**LGBM_PARAMS, **overrides})


MODELS = {
    "Median by model": make_group_median,
    "Ridge": make_ridge,
    "LightGBM": make_lgbm,
}
