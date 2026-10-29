"""Find ads that are probably the same car listed more than once.

The same car can sit on GarirBazar and Bikroy, or be reposted on one site under a new id. A copy
in training and its twin in a test fold would make the model look better than it is.

Round asking prices collide constantly (133 ads ask exactly 55 lakh), so a price match alone
proves nothing. A pair is called a twin when it shares model, build year and price AND either
  * both ads state a mileage and the two agree within 2% (at least 500 km), or
  * neither mileage can settle it (one is missing) and both name the same place.
The first rule is strong evidence; the second is plausible but not proof, so the two are
reported separately.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

KM_TOLERANCE = 0.02
KM_FLOOR = 500

LOOSE_KEY = ["car_model", "build_year", "price"]


def place(location) -> str:
    """The last comma-separated part, lower-cased: 'Dhaka, Mirpur' and 'Mirpur' both give 'mirpur'."""
    if not isinstance(location, str):
        return ""
    return location.split(",")[-1].strip().lower()


def _find(parent: list[int], i: int) -> int:
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def twin_clusters(df: pd.DataFrame) -> tuple[pd.Series, dict[str, int]]:
    """Cluster id per row (rows with no twin get their own id), and how many pairs each rule found."""
    df = df.reset_index(drop=True)
    parent = list(range(len(df)))
    pairs = {"by_mileage": 0, "by_place": 0}
    places = df["location"].map(place).to_numpy()
    km = df["mileage_km"].to_numpy(dtype=float)

    for _, idx in df.groupby(LOOSE_KEY).indices.items():
        if len(idx) < 2:
            continue
        for a, b in combinations(idx, 2):
            if np.isfinite(km[a]) and np.isfinite(km[b]):
                tolerance = max(KM_FLOOR, KM_TOLERANCE * max(km[a], km[b]))
                rule = "by_mileage" if abs(km[a] - km[b]) <= tolerance else None
            else:
                rule = "by_place" if places[a] and places[a] == places[b] else None
            if rule:
                pairs[rule] += 1
                parent[_find(parent, a)] = _find(parent, b)

    return pd.Series([_find(parent, i) for i in range(len(df))], name="twin_cluster"), pairs


def drop_twins(df: pd.DataFrame, *, rule: str = "all") -> tuple[pd.DataFrame, int]:
    """Keep one ad per twin cluster (the latest sighting). rule='mileage' keeps place-only matches."""
    clusters, _ = twin_clusters(df) if rule == "all" else _clusters_by_mileage(df)
    df = df.reset_index(drop=True)
    clusters = clusters.reset_index(drop=True)
    order = df["observed_at"].argsort(kind="stable")
    keep = pd.Series(False, index=df.index)
    seen: set[int] = set()
    for i in order[::-1]:
        c = int(clusters.iloc[i])
        if c not in seen:
            seen.add(c)
            keep.iloc[i] = True
    return df[keep].reset_index(drop=True), int((~keep).sum())


def _clusters_by_mileage(df: pd.DataFrame) -> tuple[pd.Series, dict[str, int]]:
    """Like twin_clusters but only the mileage rule, so place-only matches stay separate."""
    df = df.reset_index(drop=True)
    parent = list(range(len(df)))
    km = df["mileage_km"].to_numpy(dtype=float)
    for _, idx in df.groupby(LOOSE_KEY).indices.items():
        for a, b in combinations(idx, 2):
            if np.isfinite(km[a]) and np.isfinite(km[b]) and abs(km[a] - km[b]) <= max(KM_FLOOR, KM_TOLERANCE * max(km[a], km[b])):
                parent[_find(parent, a)] = _find(parent, b)
    return pd.Series([_find(parent, i) for i in range(len(df))]), {}
