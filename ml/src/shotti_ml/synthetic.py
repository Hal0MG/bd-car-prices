"""Made-up listings in the collector's format, for tests and CI, which never see the real data.

    .venv/Scripts/python.exe -I -m shotti_ml.synthetic OUT_DIR [--rows 900]

writes OUT_DIR laid out like data/raw: garirbazar/snapshots/<day>.jsonl, bikroy/bikroy_clean.jsonl
and a small mendeley/car_dataset.csv. Prices follow a simple rule (a base price per model, about 9%
off per year of age, a little off for mileage, noise of about 8%), so a model trained on them has
something real to learn. No row is a real ad.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

#: (make, model, base price in taka for a new car, engine cc, fuels it comes in)
MODELS = [
    ("Toyota", "Axio", 3_200_000, 1500, ["Hybrid", "Petrol"]),
    ("Toyota", "Premio", 4_800_000, 1500, ["Petrol"]),
    ("Toyota", "Noah", 4_500_000, 2000, ["Hybrid", "Petrol"]),
    ("Toyota", "Prius", 4_000_000, 1800, ["Hybrid"]),
    ("Toyota", "Harrier", 9_000_000, 2000, ["Petrol", "Hybrid"]),
    ("Toyota", "Corolla Cross", 5_000_000, 1800, ["Hybrid"]),
    ("Honda", "Vezel", 4_200_000, 1500, ["Hybrid"]),
    ("Honda", "Grace", 3_000_000, 1500, ["Hybrid"]),
    ("Nissan", "X-Trail", 5_500_000, 2000, ["Petrol", "Hybrid"]),
    ("Mitsubishi", "Pajero", 6_000_000, 3000, ["Diesel"]),
]
#: One-off models and brands, so training has the pooled "Other model" and "Other brand" categories.
RARE = [
    ("Toyota", "Crown", 7_000_000, 2500, ["Hybrid"]),
    ("Mazda", "Axela", 3_000_000, 1500, ["Petrol"]),
    ("Suzuki", "Swift", 2_000_000, 1200, ["Petrol"]),
]
DAY = "2026-10-28"


def listings(rows: int = 900, seed: int = 0, *, day: str = DAY, year_shift: int = 0, price_factor: float = 1.0) -> pd.DataFrame:
    """Synthetic listings. `year_shift` makes every car that many years older, `price_factor` scales every price,
    so a test can build a batch that has drifted."""
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(MODELS), rows)
    reference = int(day[:4])
    out = []
    for i, m in enumerate(pick):
        make, model, base, cc, fuels = RARE[(i // 150) % len(RARE)] if i % 150 == 7 else MODELS[m]
        age = int(np.clip(rng.gamma(3.0, 2.2), 0, 25)) + year_shift
        km = float(np.clip(age * rng.normal(12_000, 3_000), 500, 350_000))
        fuel = fuels[rng.integers(0, len(fuels))]
        price = base * np.exp(-0.09 * age - 0.03 * np.log1p(km / 10_000) + (0.06 if fuel == "Hybrid" else 0) + rng.normal(0, 0.08))
        out.append(
            {
                "id": 1_000_000 + seed * 100_000 + i,
                "observed_at": f"{day}T12:00:00+00:00",
                "title": f"{reference - age} {make} {model}",
                "make": make,
                "model": model,
                "year": reference - age,
                "price_bdt": int(round(price * price_factor, -3)),
                "mileage_km": None if rng.random() < 0.4 else int(km),
                "engine_cc": None if rng.random() < 0.2 else cc,
                "fuel": fuel,
                "transmission": "Automatic" if rng.random() < 0.95 else "Manual",
                "location": "Dhaka",
                "posted_at": None,
                "registration_year": None if rng.random() < 0.6 else reference - age + int(rng.integers(0, 3)),
            }
        )
    return pd.DataFrame(out)


def as_bikroy(df: pd.DataFrame) -> pd.DataFrame:
    """The same shape as bikroy_clean.jsonl: a source column, condition, and a suspect flag."""
    rng = np.random.default_rng(len(df))
    return df.assign(
        source="bikroy",
        condition=np.where(rng.random(len(df)) < 0.7, "Reconditioned", "Used"),
        body_type=None,
        suspect=False,
    )


def old_file() -> pd.DataFrame:
    """A stand-in for the 2021 Mendeley file: cleaning only needs its model names."""
    return pd.DataFrame(
        [
            {
                "car_name": f"{make} {model} 2015",
                "brand": make,
                "car_model": model,
                "model_year": 2015,
                "transmission": "Automatic",
                "body_type": "Saloon",
                "fuel_type": fuels[0],
                "engine_capacity": cc,
                "kilometers_run": 60_000,
                "price": base // 2,
            }
            for make, model, base, cc, fuels in MODELS
        ]
    )


def write_jsonl(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = df.astype(object).where(df.notna(), None).to_dict(orient="records")
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def write_data_dir(out: Path, rows: int = 900, seed: int = 0) -> Path:
    """A folder laid out like data/raw, about three quarters GarirBazar and one quarter Bikroy."""
    out = Path(out)
    df = listings(rows, seed)
    n_gb = int(rows * 0.75)
    write_jsonl(out / "garirbazar" / "snapshots" / f"{DAY}T1200.jsonl", df.iloc[:n_gb])
    write_jsonl(out / "bikroy" / "bikroy_clean.jsonl", as_bikroy(df.iloc[n_gb:]))
    (out / "mendeley").mkdir(parents=True, exist_ok=True)
    old_file().to_csv(out / "mendeley" / "car_dataset.csv", index=False)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Write made-up listings laid out like data/raw.")
    p.add_argument("out", type=Path)
    p.add_argument("--rows", type=int, default=900)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)
    print(f"Wrote synthetic listings to {write_data_dir(args.out, args.rows, args.seed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
