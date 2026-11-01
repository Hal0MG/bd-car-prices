from shotti_ml.export_site import drift_warnings


def payload(familiar: float, unseen: float, coverage: float) -> dict:
    return {
        "models": [{"name": "LightGBM", "familiar": {"miss": familiar}, "unseen": {"miss": unseen}}],
        "coverage": {"overall": {"Scaled by difficulty": coverage}},
    }


def test_small_moves_pass_quietly():
    assert drift_warnings(payload(0.065, 0.27, 0.80), payload(0.068, 0.25, 0.81)) == []


def test_large_moves_are_flagged():
    warnings = drift_warnings(payload(0.065, 0.27, 0.80), payload(0.090, 0.27, 0.74))
    assert len(warnings) == 2
    assert warnings[0].startswith("familiar miss")
    assert warnings[1].startswith("coverage")
