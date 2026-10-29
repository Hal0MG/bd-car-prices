import numpy as np
import pandas as pd

from shotti_ml.dedupe import drop_twins, place, twin_clusters


def ads(rows):
    return pd.DataFrame(rows, columns=["car_model", "build_year", "price", "mileage_km", "location", "observed_at", "source"])


def test_place_takes_the_last_part():
    assert place("Dhaka, Mirpur") == place("Mirpur") == "mirpur"
    assert place(np.nan) == ""


def test_same_price_alone_is_not_a_twin():
    df = ads([
        ["Axio", 2018, 1_750_000, 60_000, "Mirpur", "2026-10-01", "garirbazar"],
        ["Axio", 2018, 1_750_000, 95_000, "Mirpur", "2026-10-02", "bikroy"],
    ])
    clusters, pairs = twin_clusters(df)
    assert clusters.nunique() == 2 and pairs["by_mileage"] == 0


def test_matching_mileage_makes_a_twin_across_sites():
    df = ads([
        ["Axio", 2018, 1_750_000, 60_000, "Mirpur", "2026-10-01", "garirbazar"],
        ["Axio", 2018, 1_750_000, 60_500, "Dhaka, Uttara", "2026-10-02", "bikroy"],
        ["Axio", 2018, 1_800_000, 60_000, "Mirpur", "2026-10-02", "bikroy"],
    ])
    clusters, pairs = twin_clusters(df)
    assert clusters.nunique() == 2 and pairs["by_mileage"] == 1
    kept, dropped = drop_twins(df)
    assert dropped == 1 and len(kept) == 2
    assert "2026-10-02" in kept["observed_at"].tolist()  # the latest sighting is the one kept


def test_missing_mileage_needs_the_same_place():
    df = ads([
        ["Axio", 2018, 1_750_000, np.nan, "Dhaka, Mirpur", "2026-10-01", "bikroy"],
        ["Axio", 2018, 1_750_000, 60_000, "Mirpur", "2026-10-02", "garirbazar"],
        ["Axio", 2018, 1_750_000, 90_000, "Savar", "2026-10-02", "garirbazar"],
    ])
    clusters, pairs = twin_clusters(df)
    assert pairs["by_place"] == 1 and clusters.nunique() == 2
