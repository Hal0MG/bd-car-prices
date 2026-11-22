import json
import math

import numpy as np
import pandas as pd
import pytest

from shotti_ml import drift
from shotti_ml.artifact import load_artifact
from shotti_ml.current import clean_current
from shotti_ml.drift import Thresholds, bin_shares, compare_categorical, decile_edges, psi
from shotti_ml.synthetic import as_bikroy, listings, write_jsonl


def test_psi_of_identical_shares_is_zero():
    assert psi([0.2, 0.3, 0.5], [0.2, 0.3, 0.5]) == 0.0


def test_psi_matches_hand_computed_values():
    # (0.25 - 0.5) ln(0.25 / 0.5) + (0.75 - 0.5) ln(0.75 / 0.5) = 0.25 ln 2 + 0.25 ln 1.5
    assert psi([0.5, 0.5], [0.25, 0.75]) == pytest.approx(0.274653, abs=1e-6)
    # (0.3 - 0.1) ln 3 + (0.5 - 0.4) ln 1.25 + (0.2 - 0.5) ln 0.4 = 0.219722 + 0.022314 + 0.274887
    assert psi([0.1, 0.4, 0.5], [0.3, 0.5, 0.2]) == pytest.approx(0.516924, abs=1e-6)


def test_psi_floors_an_empty_bin_instead_of_dividing_by_zero():
    # (1 - 0.5) ln(1 / 0.5) + (0.0001 - 0.5) ln(0.0001 / 0.5)
    assert psi([0.5, 0.5], [1.0, 0.0]) == pytest.approx(0.5 * math.log(2) + (1e-4 - 0.5) * math.log(1e-4 / 0.5))
    assert psi([0.5, 0.5], [1.0, 0.0]) == pytest.approx(4.604, abs=1e-3)


def test_bins_are_closed_on_the_right_and_skip_missing_values():
    assert bin_shares(range(1, 11), [3, 7]) == pytest.approx([0.3, 0.4, 0.3])
    assert bin_shares([np.nan, 1, 5], [3]) == pytest.approx([0.5, 0.5])


def test_decile_edges_merge_repeats():
    assert decile_edges([1] * 50 + [2] * 50) == [1.0, 1.5, 2.0]
    assert len(decile_edges(np.arange(1000))) == 9


def test_a_category_training_never_saw_gets_its_own_bucket():
    result = compare_categorical({"Toyota": 0.8, "Honda": 0.2}, pd.Series(["Toyota"] * 5 + ["Tesla"] * 5), Thresholds())
    assert result["status"] == "alert"
    assert result["max_share_shift"] == pytest.approx(0.5)
    assert result["top_shifts"][0]["value"] == drift.UNSEEN


def run_check(trained, tmp_path, batch: pd.DataFrame, *extra):
    path = tmp_path / "batch.jsonl"
    write_jsonl(path, batch)
    code = drift.main([str(path), "--artifact", str(trained[0]), "--out-dir", str(tmp_path), *extra])
    return code, json.loads((tmp_path / "batch.json").read_text(encoding="utf-8"))


def test_a_fresh_batch_like_the_training_data_raises_no_alert(trained, tmp_path):
    fresh = listings(800, seed=1)
    batch = pd.concat([fresh.iloc[:600], as_bikroy(fresh.iloc[600:])])
    code, result = run_check(trained, tmp_path, batch)
    assert code == 0, result["alerts"]
    assert result["performance"]["coverage"] > 0.7
    assert (tmp_path / "batch.md").read_text(encoding="utf-8").startswith("# Drift check: batch")


def test_older_and_dearer_cars_raise_alerts(trained, tmp_path):
    code, result = run_check(trained, tmp_path, listings(600, seed=2, year_shift=6, price_factor=1.6))
    assert code == 1
    assert result["numeric"]["age"]["status"] == "alert"
    assert result["performance"]["mape_status"] == "alert"
    assert result["performance"]["coverage_status"] == "alert"


def test_ignored_features_are_reported_but_do_not_fail_the_check(trained, tmp_path):
    batch = listings(600, seed=3)  # GarirBazar only, so the site's share moves from 75% to 100%
    code, result = run_check(trained, tmp_path, batch, "--ignore", "source,condition")
    assert result["categorical"]["source"]["status"] == "alert"
    assert code == 0, result["alerts"]


def test_thresholds_can_be_set_on_the_command_line(trained, tmp_path):
    code, result = run_check(trained, tmp_path, listings(600, seed=3), "--ignore", "source,condition", "--psi-alert", "0.0001", "--share-shift-alert", "0.0001")
    assert code == 1 and result["thresholds"]["psi_alert"] == 0.0001


def test_a_batch_without_prices_still_gets_the_feature_checks(trained):
    artifact = load_artifact(trained[0])
    df, report, year = clean_current(listings(300, seed=4), artifact.metadata["known_models"])
    result = drift.check(artifact, df.drop(columns="price"), report, year, Thresholds())
    assert result["performance"] is None
    assert result["numeric"]["log_price"]["status"] == "skipped"
    assert result["numeric"]["age"]["psi"] is not None


def test_a_batch_file_with_no_price_column_gets_the_feature_checks_from_the_command_line(trained, tmp_path):
    code, result = run_check(trained, tmp_path, listings(600, seed=5, year_shift=6).drop(columns="price_bdt"))
    assert code == 1  # the cars are six years older: drift, found without any prices
    assert result["numeric"]["age"]["status"] == "alert"
    assert result["performance"] is None and result["batch_rows_priced"] == 0
    assert result["numeric"]["log_price"]["status"] == "skipped"
    assert "accuracy was not checked" in (tmp_path / "batch.md").read_text(encoding="utf-8")


def test_null_prices_are_kept_and_accuracy_uses_only_the_priced_listings(trained, tmp_path):
    fresh = listings(600, seed=8)
    fresh["price_bdt"] = fresh["price_bdt"].astype(object)
    fresh.loc[fresh.index[:200], "price_bdt"] = None
    code, result = run_check(trained, tmp_path, fresh, "--ignore", "source,condition")
    assert result["batch_rows_clean"] > 500  # the 200 unpriced listings were not dropped
    assert result["batch_rows_priced"] == result["performance"]["rows"] < result["batch_rows_clean"]

    fresh["price_bdt"] = None
    code, result = run_check(trained, tmp_path, fresh, "--ignore", "source,condition")
    assert code == 0, result["alerts"]
    assert result["performance"] is None and result["batch_rows_clean"] > 500


def test_a_failed_check_exits_3_not_1(trained, tmp_path, capsys):
    assert drift.main([str(tmp_path / "missing.jsonl"), "--artifact", str(trained[0]), "--out-dir", str(tmp_path)]) == drift.EXIT_ERROR
    assert "not drift" in capsys.readouterr().err
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"make": "Toyota"}\n', encoding="utf-8")  # no observed_at
    assert drift.main([str(bad), "--artifact", str(trained[0]), "--out-dir", str(tmp_path)]) == drift.EXIT_ERROR
    assert drift.main(["--no-such-flag"]) == drift.EXIT_ERROR
