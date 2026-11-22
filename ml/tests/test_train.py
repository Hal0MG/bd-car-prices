import json

import pytest

from shotti_ml import settings, train


def test_the_command_line_trains_and_saves_an_artifact(synthetic_dir, tmp_path, capsys):
    code = train.main(["--data-dir", str(synthetic_dir), "--out-dir", str(tmp_path), "--cv-repeats", "0", "--no-mlflow", "--version", "cli"])
    assert code == 0
    assert {p.name for p in (tmp_path / "cli").iterdir()} == {"model.txt", "difficulty.txt", "metadata.json", "metrics.json", "training_summary.json"}
    assert "Holdout" in capsys.readouterr().out


def test_the_data_folder_comes_from_the_environment_when_not_given(monkeypatch, tmp_path):
    monkeypatch.setenv(settings.DATA_ENV, str(tmp_path))
    assert settings.data_dir() == tmp_path
    assert settings.data_dir(tmp_path / "x") == tmp_path / "x"


def test_the_newest_artifact_is_served_by_default(trained, tmp_path, monkeypatch):
    for name, created in [("old", "2026-01-01T00:00:00+00:00"), ("new", "2026-06-01T00:00:00+00:00")]:
        (tmp_path / name).mkdir()
        (tmp_path / name / "metadata.json").write_text(json.dumps({"created_at": created}))
    assert settings.latest_artifact(tmp_path).name == "new"
    with pytest.raises(FileNotFoundError, match="Train one first"):
        settings.latest_artifact(tmp_path / "empty")


def test_a_run_is_logged_to_a_local_mlflow_store(trained, tmp_path):
    mlflow = pytest.importorskip("mlflow")
    directory, metrics = trained
    meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    run_id = train.log_to_mlflow(directory, metrics, meta["params"], tmp_path / "mlruns", experiment="test")
    run = mlflow.get_run(run_id)
    assert run.data.metrics["holdout_median_ape"] == pytest.approx(metrics["holdout"]["median_ape"])
    assert run.data.params["lgbm.num_leaves"] == "15"
    assert run.data.tags["version"] == "test-model"
    files = {f.path for f in mlflow.MlflowClient().list_artifacts(run_id, "artifact")}
    assert "artifact/model.txt" in files
