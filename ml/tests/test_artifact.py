import json

import numpy as np
import pandas as pd
import pytest

from shotti_ml.artifact import load_artifact, save_artifact
from shotti_ml.current import clean_current
from shotti_ml.data import FUEL_COLUMNS
from shotti_ml.features import build_features, feature_frame
from shotti_ml.intervals import fit_scaled_by_difficulty, scaled_by_difficulty
from shotti_ml.models import make_lgbm
from shotti_ml.run_current import EXTRA
from shotti_ml.synthetic import listings
from shotti_ml.train import load_training_data, train


@pytest.fixture(scope="module")
def cleaned(synthetic_dir):
    raw, known = load_training_data(synthetic_dir)
    df, _, year = clean_current(raw, known)
    X, y = build_features(df, year, EXTRA)
    return df, X, y, year


def test_a_saved_model_predicts_exactly_what_it_did_before_saving(cleaned, tmp_path):
    _, X, y, _ = cleaned
    fitted = fit_scaled_by_difficulty(make_lgbm, X.iloc[:500], y.iloc[:500], X.iloc[500:700], y.iloc[500:700], 0.2)
    before = fitted.predict(X.iloc[700:])
    meta = {"version": "rt", "features": {"columns": list(X.columns), "extra": list(EXTRA), "categories": {}}}
    save_artifact(tmp_path / "rt", fitted, meta, {"version": "rt"}, {})
    loaded = load_artifact(tmp_path / "rt")
    after = loaded.conformal.predict(X.iloc[700:])
    for a, b in [(before.pred, after.pred), (before.lo, after.lo), (before.hi, after.hi)]:
        np.testing.assert_allclose(a, b, rtol=0, atol=1e-12)
    assert loaded.conformal.q == fitted.q


def test_the_split_helper_matches_the_one_call_export_uses(cleaned):
    _, X, y, _ = cleaned
    args = (make_lgbm, X.iloc[:500], y.iloc[:500], X.iloc[500:700], y.iloc[500:700])
    direct = scaled_by_difficulty(*args, X.iloc[700:], 0.2)
    split = fit_scaled_by_difficulty(*args, 0.2).predict(X.iloc[700:])
    np.testing.assert_array_equal(direct.pred, split.pred)
    np.testing.assert_array_equal(direct.hi, split.hi)


def test_feature_frame_without_categories_is_build_features(cleaned):
    df, X, _, year = cleaned
    pd.testing.assert_frame_equal(feature_frame(df, year, EXTRA), X)


def test_a_loaded_artifact_builds_the_same_inputs_as_training(trained, cleaned):
    df, X, _, year = cleaned
    served = load_artifact(trained[0]).features(df, year)
    pd.testing.assert_frame_equal(served, X)


def test_an_artifact_folder_is_never_overwritten(trained):
    artifact = load_artifact(trained[0])
    with pytest.raises(FileExistsError):
        save_artifact(trained[0], artifact.conformal, artifact.metadata, artifact.metrics, artifact.summary)


def test_loading_a_folder_that_is_not_an_artifact_fails_clearly(tmp_path):
    with pytest.raises(FileNotFoundError, match="not a model artifact"):
        load_artifact(tmp_path)


def test_artifact_holds_metrics_and_aggregates_but_no_listing(trained):
    directory, metrics = trained
    meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    assert meta["version"] == "test-model"
    assert meta["interval"]["alpha"] == 0.2 and meta["interval"]["q"] > 0
    assert 0 < metrics["holdout"]["median_ape"] < 0.2
    assert metrics["cv_random"]["n_repeats"] == 1
    assert 0.6 < metrics["interval_cv"]["coverage"] < 0.95
    text = "".join(p.read_text(encoding="utf-8") for p in directory.glob("*.json"))
    assert not any(str(i) in text for i in listings(900, 0)["id"]), "an ad id leaked into the artifact"


def test_unseen_names_go_to_the_pooled_category(trained):
    artifact = load_artifact(trained[0])
    row = {col: 0 for col in ["reg_gap", "automatic", *FUEL_COLUMNS]}
    row.update(build_year=2018, km=50_000.0, engine_cc=1500.0, brand="Toyota", car_model="Nonesuch", body_type="Unknown", source="garirbazar", condition="Unknown")
    X = artifact.features(pd.DataFrame([row]))
    assert X.loc[0, "model"] == "Other model"
    assert X.loc[0, "brand"] == "Toyota"


def test_price_car_matches_names_and_fills_gaps(trained):
    artifact = load_artifact(trained[0])
    full = artifact.price_car({"brand": "Toyota", "model": "Axio", "build_year": 2018, "mileage_km": 60_000, "engine_cc": 1500, "fuel": "petrol"})
    loose = artifact.price_car({"brand": "toyota", "model": "axio", "build_year": 2018, "fuel": "petrol"})
    assert full["low_bdt"] < full["price_bdt"] < full["high_bdt"]
    assert full["imputed"] == [] and loose["imputed"] == ["engine_cc", "mileage_km"]
    assert (loose["matched_brand"], loose["matched_model"], loose["model_seen_in_training"]) == ("Toyota", "Axio", True)
    assert full["model_version"] == "test-model"


def test_the_same_data_gives_the_same_fingerprint_and_model(synthetic_dir, tmp_path):
    a, _, _ = train(synthetic_dir, tmp_path, cv_repeats=0, version="a")
    b, _, _ = train(synthetic_dir, tmp_path, cv_repeats=0, version="b")
    meta_a, meta_b = (json.loads((d / "metadata.json").read_text(encoding="utf-8")) for d in (a, b))
    assert meta_a["data_fingerprint"] == meta_b["data_fingerprint"]
    assert (a / "model.txt").read_text() == (b / "model.txt").read_text()


def test_training_on_one_site_only(synthetic_dir, tmp_path):
    directory, _, _ = train(synthetic_dir, tmp_path, sources=("garirbazar",), cv_repeats=0, version="gb")
    meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    assert set(meta["data"]["rows_by_source"]) == {"garirbazar"}


def test_training_without_the_2021_file_says_what_is_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="car_dataset.csv"):
        train(tmp_path, tmp_path / "out", cv_repeats=0)
