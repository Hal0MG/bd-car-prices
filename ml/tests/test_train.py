import json

import pytest

from shotti_ml import settings, train


def test_the_command_line_trains_and_saves_an_artifact(synthetic_dir, tmp_path, capsys, monkeypatch):
    clean = {"commit": "abc1234", "dirty": False, "changed": []}
    monkeypatch.setattr(train, "git_state", lambda: clean)
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


def test_the_command_line_refuses_uncommitted_code_unless_allowed(synthetic_dir, tmp_path, capsys, monkeypatch):
    dirty = {"commit": "abc1234", "dirty": True, "changed": ["ml/src/shotti_ml/current.py"]}
    monkeypatch.setattr(train, "git_state", lambda: dirty)
    args = ["--data-dir", str(synthetic_dir), "--out-dir", str(tmp_path), "--cv-repeats", "0", "--no-mlflow", "--version", "dirty"]
    assert train.main(args) == 2
    assert "Uncommitted changes in ml/src/shotti_ml/current.py" in capsys.readouterr().err
    assert not (tmp_path / "dirty").exists()

    assert train.main([*args, "--allow-dirty"]) == 0
    meta = json.loads((tmp_path / "dirty" / "metadata.json").read_text(encoding="utf-8"))
    assert meta["git_commit"] == "abc1234" and meta["git_dirty"] is True
    assert meta["git_changed"] == ["ml/src/shotti_ml/current.py"]


def test_the_artifact_records_its_code_and_library_versions(trained):
    meta = json.loads((trained[0] / "metadata.json").read_text(encoding="utf-8"))
    assert {"git_commit", "git_dirty", "git_changed"} <= set(meta)
    assert meta["libraries"]["lightgbm"] and meta["libraries"]["pandas"] and meta["libraries"]["python"]
    assert "pyarrow" in meta["libraries"]  # None when not installed: it changes how pandas stores strings


def test_git_state_names_changed_code_files(monkeypatch):
    outputs = {"rev-parse": "0934759\n", "status": " M ml/src/shotti_ml/train.py\n?? ml/src/shotti_ml/new.py\n"}
    monkeypatch.setattr(train, "_git", lambda *args: outputs[args[0]])
    assert train.git_state() == {"commit": "0934759", "dirty": True, "changed": ["ml/src/shotti_ml/new.py", "ml/src/shotti_ml/train.py"]}
    outputs["status"] = ""
    assert train.git_state()["dirty"] is False
    monkeypatch.setattr(train, "_git", lambda *args: None)
    assert train.git_state() == {"commit": None, "dirty": None, "changed": []}
