import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from shotti_ml.api import create_app  # noqa: E402

AXIO = {"brand": "Toyota", "model": "Axio", "build_year": 2018, "mileage_km": 60000, "engine_cc": 1500, "fuel": "petrol", "transmission": "automatic"}


@pytest.fixture(scope="module")
def client(trained):
    with TestClient(create_app(trained[0])) as c:  # the with block runs startup, which loads the model
        yield c


def test_health_names_the_model(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "model_version": "test-model"}


def test_model_reports_version_and_metrics(client):
    body = client.get("/model").json()
    assert body["version"] == "test-model"
    assert body["interval"]["alpha"] == 0.2
    assert 0 < body["metrics"]["holdout"]["median_ape"] < 0.2
    assert body["data"]["rows_clean"] > 500


def test_predict_returns_a_price_inside_its_range(client):
    r = client.post("/predict", json=AXIO)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["low_bdt"] < body["price_bdt"] < body["high_bdt"]
    assert body["coverage"] == 0.8 and body["model_version"] == "test-model"
    assert 1_000_000 < body["price_bdt"] < 4_000_000  # a 2018 Axio in the synthetic data
    assert body["model_seen_in_training"] and body["imputed"] == []


def test_older_cars_are_priced_lower(client):
    new = client.post("/predict", json={**AXIO, "build_year": 2022}).json()["price_bdt"]
    old = client.post("/predict", json={**AXIO, "build_year": 2010}).json()["price_bdt"]
    assert old < new


def test_optional_fields_can_be_left_out_and_case_does_not_matter(client):
    r = client.post("/predict", json={"brand": "toyota", "model": "AXIO", "build_year": 2018, "fuel": "Hybrid"})
    assert r.status_code == 200, r.text
    assert r.json()["imputed"] == ["engine_cc", "mileage_km"]
    assert r.json()["matched_model"] == "Axio"


def test_an_unknown_model_is_priced_but_flagged(client):
    body = client.post("/predict", json={**AXIO, "model": "Nonesuch"}).json()
    assert body["model_seen_in_training"] is False


def errors(r):
    assert r.status_code == 422, r.text
    return {".".join(map(str, e["loc"][1:])): e["msg"] for e in r.json()["detail"]}


@pytest.mark.parametrize(
    "change, field",
    [
        ({"build_year": 1950}, "build_year"),
        ({"build_year": 2100}, "build_year"),
        ({"mileage_km": -5}, "mileage_km"),
        ({"engine_cc": 150}, "engine_cc"),
        ({"fuel": "steam"}, "fuel"),
        ({"transmission": "cvt"}, "transmission"),
        ({"brand": "  "}, "brand"),
        ({"build_year": "new"}, "build_year"),
    ],
)
def test_out_of_range_values_get_a_422_naming_the_field(client, change, field):
    assert field in errors(client.post("/predict", json={**AXIO, **change}))


def test_missing_required_fields_are_named(client):
    detail = errors(client.post("/predict", json={"brand": "Toyota"}))
    assert {"model", "build_year", "fuel"} <= set(detail)


def test_electric_cars_are_refused_with_a_reason(client):
    detail = errors(client.post("/predict", json={**AXIO, "fuel": "electric"}))
    assert "electric cars are not priced" in detail["fuel"]


def test_registration_before_build_is_refused(client):
    detail = errors(client.post("/predict", json={**AXIO, "registration_year": 2015}))
    assert any("registration_year cannot be before build_year" in m for m in detail.values())


def test_unknown_fields_are_refused(client):
    assert "colour" in errors(client.post("/predict", json={**AXIO, "colour": "white"}))
