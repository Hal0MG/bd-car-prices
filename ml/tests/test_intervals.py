import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from shotti_ml.evaluate import learning_curve
from shotti_ml.intervals import conformal_quantile, evaluate_intervals, summarise_intervals


def noisy_data(n=600, seed=0):
    """A straight line whose scatter grows 20-fold from left to right, like prices of dearer cars."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 4, n)
    y = 2 + x + rng.normal(0, 0.05 + 0.25 * x, n)
    return pd.DataFrame({"x": x}), pd.Series(y, name="y")


@pytest.fixture(scope="module")
def intervals():
    X, y = noisy_data()
    return X, evaluate_intervals(X, y, make_model=LinearRegression, n_repeats=2)


def test_conformal_quantile_picks_the_right_order_statistic():
    assert conformal_quantile(np.arange(1, 10), alpha=0.2) == 8  # ceil(10 * 0.8)
    assert conformal_quantile([1, 2], alpha=0.01) == 2  # clipped to the largest score


def test_every_method_hits_its_coverage_target(intervals):
    _, df = intervals
    coverage = summarise_intervals(df)["coverage"]
    assert coverage.between(0.72, 0.88).all(), coverage.to_dict()


def test_intervals_are_never_inverted(intervals):
    _, df = intervals
    assert (df["lo"] <= df["hi"]).all()


def test_constant_width_fails_where_the_noise_is_worst(intervals):
    X, df = intervals
    noisy = df[X["x"].reindex(df["row"]).to_numpy() > 3]
    coverage = noisy.groupby("method")["covered"].mean()
    assert coverage["Constant width"] < 0.7
    assert coverage["Scaled by difficulty"] > coverage["Constant width"] + 0.08
    assert coverage["Quantile (CQR)"] > coverage["Constant width"] + 0.08


def test_adaptive_intervals_are_wider_where_the_noise_is(intervals):
    X, df = intervals
    x = X["x"].reindex(df["row"]).to_numpy()
    for method in ("Scaled by difficulty", "Quantile (CQR)"):
        rows = df["method"] == method
        calm = df.loc[rows & (x < 1), "ratio"].median()
        wild = df.loc[rows & (x > 3), "ratio"].median()
        assert wild > 2 * calm, (method, calm, wild)


def test_learning_curve_uses_more_rows_as_the_fraction_grows():
    X, y = noisy_data(n=300)
    curve = learning_curve(LinearRegression, X, y, fractions=(0.2, 1.0), n_repeats=1)
    sizes = curve.groupby("fraction")["n_train"].mean()
    assert sizes[1.0] > sizes[0.2]
    assert len(curve) == 10  # 5 folds, 2 fractions
