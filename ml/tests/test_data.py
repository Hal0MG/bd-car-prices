import numpy as np
import pandas as pd

from shotti_ml.data import MAX_KM, clean
from shotti_ml.features import build_features


def listing(**overrides):
    row = dict(
        car_name="Toyota Axio 2012",
        brand="Toyota",
        car_model="Axio",
        model_year=2012,
        transmission="Automatic",
        body_type="Saloon",
        fuel_type="CNG, Octane",
        engine_capacity=1500,
        kilometers_run=60_000,
        price=1_000_000,
    )
    return {**row, **overrides}


def cleaned(*rows):
    return clean(pd.DataFrame(rows))


def test_reposts_with_a_different_title_are_dropped():
    df, report = cleaned(listing(), listing(car_name="Toyota Axio nice condition 2012"), listing(price=900_000))
    assert len(df) == 2
    assert report.reposts_dropped == 1


def test_build_year_comes_from_the_title_not_the_registration_year():
    df, report = cleaned(listing(car_name="Toyota Fielder 2004", car_model="Fielder", model_year=2009))
    assert df.loc[0, "build_year"] == 2004
    assert df.loc[0, "reg_gap"] == 5
    assert report.year_differs_from_title == 1


def test_engine_typos_take_the_median_of_the_same_model():
    df, report = cleaned(
        listing(price=1_000_000),
        listing(price=1_100_000, engine_capacity=1496),
        listing(price=1_200_000, engine_capacity=150),
    )
    assert report.engine_cc_imputed == 1
    assert df.loc[2, "engine_cc"] == 1498  # median of 1500 and 1496


def test_kei_car_engines_are_kept():
    df, report = cleaned(listing(car_name="Suzuki Alto 2011", brand="Suzuki", car_model="Alto", engine_capacity=660))
    assert df.loc[0, "engine_cc"] == 660
    assert report.engine_cc_imputed == 0


def test_absurd_mileage_is_capped():
    df, report = cleaned(listing(kilometers_run=900_000))
    assert df.loc[0, "km"] == MAX_KM
    assert report.km_capped == 1


def test_fuel_strings_become_flags():
    df, _ = cleaned(
        listing(fuel_type="CNG, Octane"),
        listing(fuel_type="Hybrid", price=1_100_000),
        listing(fuel_type="Diesel, Petrol", price=1_200_000),
    )
    flags = df[["fuel_petrol", "fuel_cng", "fuel_hybrid", "fuel_diesel"]].to_numpy()
    assert flags.tolist() == [[1, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 1]]


def test_missing_body_type_becomes_unknown():
    df, report = cleaned(listing(), listing(body_type=np.nan, price=1_100_000))
    assert df["body_type"].tolist() == ["Saloon", "Unknown"]
    assert report.body_type_missing == 1


def test_rare_models_are_pooled_and_the_target_is_log_price():
    rows = [listing(price=1_000_000 + i * 1000, kilometers_run=50_000 + i) for i in range(6)]
    rows.append(listing(car_name="Toyota Rarity 2012", car_model="Rarity", price=2_000_000))
    df, _ = cleaned(*rows)
    X, y = build_features(df)
    assert set(X["model"].astype(str)) == {"Axio", "Other model"}
    assert np.allclose(np.exp(y), df["price"])
