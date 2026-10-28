import numpy as np
import pandas as pd

from shotti_ml.current import clean_current
from shotti_ml.features import build_features

KNOWN = ["Axio", "Corolla Cross", "Premio"]


def row(**overrides):
    base = dict(
        id=1, observed_at="2026-10-28T12:00:00+00:00", title="2019 Toyota Axio", make="Toyota", model="Axio",
        year=2019, price_bdt=1_900_000, mileage_km=40_000, engine_cc=1500, fuel="Hybrid", transmission="Automatic",
        location="Dhaka", posted_at=None, registration_year=None,
    )
    return {**base, **overrides}


def cleaned(*rows):
    # Eight comparable Axios, so the price-outlier rule has something to compare against.
    comparables = [row(id=100 + i, price_bdt=1_850_000 + i * 20_000, mileage_km=38_000 + i * 900) for i in range(8)]
    return clean_current(pd.DataFrame(comparables + list(rows)), KNOWN)


def test_the_latest_sighting_of_an_ad_wins():
    older = row(id=7, observed_at="2026-10-01T09:00:00+00:00", price_bdt=2_100_000)
    newer = row(id=7, observed_at="2026-10-28T09:00:00+00:00", price_bdt=1_950_000)
    df, report, _ = cleaned(older, newer)
    assert report.seen_in_several_snapshots == 1
    assert df.loc[df["id"] == 7, "price"].item() == 1_950_000


def test_negotiable_electric_and_impossible_rows_are_dropped_and_counted():
    df, report, _ = cleaned(
        row(id=1, price_bdt=None),
        row(id=2, fuel="Electric"),
        row(id=3, year=1950),
        row(id=4, price_bdt=50_000),
    )
    assert (report.no_price, report.electric_dropped, report.implausible_year, report.implausible_price) == (1, 1, 1, 1)
    assert not {1, 2, 3, 4} & set(df["id"])


def test_bait_and_typo_prices_are_dropped_against_comparable_cars():
    df, report, _ = cleaned(row(id=1, price_bdt=300_000), row(id=2, price_bdt=19_000_000))
    assert report.price_outliers == 2
    assert not {1, 2} & set(df["id"])


def test_names_are_tidied_to_the_known_spelling():
    df, _, _ = cleaned(row(id=1, make="toyota", model="corolla cross", price_bdt=3_900_000, year=2021))
    car = df[df["id"] == 1].iloc[0]
    assert (car["brand"], car["car_model"]) == ("Toyota", "Corolla Cross")


def test_missing_engine_and_mileage_are_filled_from_similar_cars_and_counted():
    df, report, _ = cleaned(row(id=1, engine_cc=np.nan, mileage_km=np.nan))
    car = df[df["id"] == 1].iloc[0]
    assert car["engine_cc"] == 1500  # the median Axio
    assert 38_000 <= car["km"] <= 46_000  # the median of cars built the same year
    assert report.engine_imputed >= 1 and report.mileage_imputed >= 1


def test_fuel_gearbox_and_age_reach_the_model_inputs():
    df, _, reference_year = cleaned(row(id=1, fuel="Petrol", transmission="Manual", year=2020))
    assert reference_year == 2026
    X, y = build_features(df, reference_year)
    car = df.index[df["id"] == 1][0]
    assert (X.loc[car, "fuel_petrol"], X.loc[car, "fuel_hybrid"], X.loc[car, "automatic"], X.loc[car, "age"]) == (1, 0, 0, 6)
    assert np.allclose(np.exp(y), df["price"])


def test_cross_models_are_not_folded_into_their_base_model():
    from shotti_ml.current import canonical_current

    known = ["Corolla", "Yaris", "Land Cruiser", "Axio"]
    assert canonical_current("corolla cross z leather", known) == "Corolla Cross"
    assert canonical_current("Yaris Cross Hybrid", known) == "Yaris Cross"
    assert canonical_current("land cruiser prado txl", known) == "Prado"
    assert canonical_current("corolla axio x", known) == "Axio"
    assert canonical_current("land cruiser vx-v8", known) == "Land Cruiser"
    assert canonical_current("corolla x", known) == "Corolla"
