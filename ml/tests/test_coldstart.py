import numpy as np
import pandas as pd

from shotti_ml.coldstart import NoNameModel, SimilarCarModel, tokens


def table(n=120, seed=0):
    rng = np.random.default_rng(seed)
    age = rng.integers(1, 10, n)
    X = pd.DataFrame({"age": age, "log_km": rng.normal(11, 0.5, n), "engine_cc": rng.choice([1000, 1500, 2000], n)})
    X["model"] = pd.Categorical(rng.choice(["Axio", "Prado", "Noah"], n))
    X["_name"] = X["model"].astype(str).to_numpy()
    X["_brand"] = "Toyota"
    y = pd.Series(15.0 - 0.08 * age + 0.0002 * X["engine_cc"] + rng.normal(0, 0.05, n))
    return X, y


def test_tokens_drop_filler_words():
    assert tokens("Corolla Cross Hybrid") == ["corolla", "cross"]
    assert tokens("Land Cruiser Prado TX") == ["land", "cruiser", "prado", "tx"]


def test_the_model_name_never_reaches_the_booster():
    X, y = table()
    m = NoNameModel().fit(X, y)
    assert "model" not in m.model_.feature_name_ and "_name" not in m.model_.feature_name_
    unseen = X.head(5).assign(_name="Emira")
    assert np.isfinite(m.predict(unseen)).all()


def test_similar_car_model_predicts_for_an_unseen_name():
    X, y = table()
    m = SimilarCarModel().fit(X, y)
    unseen = X.head(5).assign(_name="Prado Plus")
    assert np.isfinite(m.predict(unseen)).all()
