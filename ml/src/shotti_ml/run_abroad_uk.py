"""Collect UK asking prices for every UK-market catalogue car.

Run from the ml/ folder:  .venv/Scripts/python.exe -I -m shotti_ml.run_abroad_uk
European cars reach Bangladesh from the UK, so their price abroad is a UK used price. For each
car, searches CarGurus UK for its model, year and fuel, keeps the listings whose trim names the
catalogue's version (a regular expression, as in "330e" or "P400e"), and summarises their prices
in pounds. Writes the matched cars (attributes and price only) to data/raw/cargurus/<date>.csv
and the summary to ../web/src/lib/abroad.json, and sets the catalogue price of every car with
enough matches to their median (see abroad_store.py). The Ariel Atom and Bugatti Chiron are not
on CarGurus and keep their example prices.
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date

from . import abroad_store as store
from .collect import cargurus as cg
from .collect.fetch import FetchError, PoliteFetcher
from .export import catalogue as read_catalogue

RAW = store.ROOT / "ml" / "data" / "raw" / "cargurus"
MAX_PAGES = 4
#: any CarGurus search page carries the full make list, so one fetch maps every make to its id
INDEX = cg.BASE + "/Cars/l-Used-BMW-m256"


@dataclass(frozen=True)
class Target:
    """A catalogue car's model on CarGurus, and how to pick its version out of that model's listings."""

    make: str
    model: str
    #: a regular expression the trim must match (case ignored); None takes every trim
    trim: str | None = None
    #: and one it must not match
    not_trim: str | None = None
    #: False when CarGurus' fuel label can't be trusted for this car, so the search leaves fuel out
    by_fuel: bool = True


T = Target
TARGETS: dict[tuple[str, str], Target] = {
    ("Land Rover", "Range Rover P400e"): T("Land Rover", "Range Rover", r"P400E"),
    ("Land Rover", "Range Rover Sport P400e"): T("Land Rover", "Range Rover Sport", r"P400E"),
    ("Land Rover", "Range Rover Velar P400e"): T("Land Rover", "Range Rover Velar", r"P400E"),
    ("Land Rover", "Range Rover Evoque P300e"): T("Land Rover", "Range Rover Evoque", r"P300E"),
    ("Land Rover", "Discovery Sport P300e"): T("Land Rover", "Discovery Sport", r"P300E"),
    ("Land Rover", "Defender 110 P400e"): T("Land Rover", "Defender", r"P400E"),
    ("Land Rover", "Defender 90"): T("Land Rover", "Defender", r"\b90\b"),
    ("Jaguar", "F-Pace P400e"): T("Jaguar", "F-PACE", r"P400E"),
    ("Jaguar", "XE"): T("Jaguar", "XE"),
    ("Jaguar", "F-Type P300"): T("Jaguar", "F-TYPE", r"P300|\b2\.0"),
    ("Jaguar", "I-Pace"): T("Jaguar", "I-Pace"),
    ("Jaguar", "F-Pace SVR"): T("Jaguar", "F-PACE", r"SVR"),
    ("Bentley", "Continental GT V8"): T("Bentley", "Continental GT", r"V8", r"CONVERTIBLE|GTC|SPEED"),
    ("Bentley", "Continental GTC V8"): T("Bentley", "Continental GTC", r"V8"),
    ("Bentley", "Continental GT Speed"): T("Bentley", "Continental GT", r"SPEED", r"CONVERTIBLE|GTC"),
    ("Bentley", "Flying Spur Hybrid"): T("Bentley", "Flying Spur"),
    ("Bentley", "Bentayga Hybrid"): T("Bentley", "Bentayga"),
    ("Rolls-Royce", "Ghost"): T("Rolls-Royce", "Ghost"),
    ("Rolls-Royce", "Cullinan"): T("Rolls-Royce", "Cullinan"),
    ("Rolls-Royce", "Phantom"): T("Rolls-Royce", "Phantom"),
    ("Rolls-Royce", "Wraith"): T("Rolls-Royce", "Wraith"),
    ("Rolls-Royce", "Dawn"): T("Rolls-Royce", "Dawn"),
    ("Rolls-Royce", "Spectre"): T("Rolls-Royce", "Spectre"),
    ("Aston Martin", "Vantage"): T("Aston Martin", "Vantage", None, r"V12|F1"),
    ("Aston Martin", "DBX"): T("Aston Martin", "DBX", None, r"707"),
    ("Aston Martin", "DB11"): T("Aston Martin", "DB11", r"V8"),
    ("Aston Martin", "DBS Superleggera"): T("Aston Martin", "DBS", r"SUPERLEGGERA"),
    ("McLaren", "GT"): T("McLaren", "GT"),
    ("McLaren", "Artura"): T("McLaren", "Artura"),
    ("McLaren", "720S"): T("McLaren", "720S"),
    ("Lotus", "Emira"): T("Lotus", "Emira", None, r"V6"),
    ("Lotus", "Evora GT"): T("Lotus", "Evora", r"\bGT\b"),
    ("Lotus", "Elise Sport 240 Final Edition"): T("Lotus", "Elise", r"240"),
    ("Lotus", "Exige Sport 420 Final Edition"): T("Lotus", "Exige", r"420"),
    ("Mini", "Cooper"): T("MINI", "Hatchback", r"\bCOOPER\b(?! ?S)", r"ELECTRIC"),
    ("Mini", "Clubman"): T("MINI", "Clubman", r"\bCOOPER\b(?! ?S)"),
    ("Mini", "Countryman Cooper S E"): T("MINI", "Countryman"),
    ("Mercedes-Benz", "C 300 e"): T("Mercedes-Benz", "C-Class", r"C ?300 ?E\b"),
    ("Mercedes-Benz", "E 300 e"): T("Mercedes-Benz", "E-Class", r"E ?300 ?E\b"),
    ("Mercedes-Benz", "S 580 e"): T("Mercedes-Benz", "S-Class", r"S ?580 ?E\b"),
    ("Mercedes-Benz", "GLC 300 e"): T("Mercedes-Benz", "GLC", r"300 ?E\b"),
    ("Mercedes-Benz", "C 200 Cabriolet"): T("Mercedes-Benz", "C-Class", r"C ?200.*CABRIOLET|CABRIOLET.*C ?200"),
    ("Mercedes-Benz", "AMG GT"): T("Mercedes-Benz", "AMG GT", None, r"4-DOOR|4 DOOR|\b63\b|\b53\b|\b43\b"),
    ("Mercedes-Benz", "G 400 d"): T("Mercedes-Benz", "G-Class", r"G ?400 ?D\b"),
    ("Mercedes-Benz", "S 580 Maybach"): T("Mercedes-Benz", "S-Class", r"MAYBACH"),
    ("Mercedes-Benz", "GLE 350 de"): T("Mercedes-Benz", "GLE", r"350 ?DE\b"),
    ("Mercedes-Benz", "EQS 450+"): T("Mercedes-Benz", "EQS", r"450"),
    ("Mercedes-Benz", "AMG G 63"): T("Mercedes-Benz", "G-Class", r"G ?63"),
    ("Mercedes-Benz", "SL 43"): T("Mercedes-Benz", "SL-Class", r"SL ?43"),
    ("Mercedes-Benz", "AMG C 63 S E Performance"): T("Mercedes-Benz", "C-Class", r"C ?63"),
    ("Mercedes-Benz", "A 250 e"): T("Mercedes-Benz", "A-Class", r"A ?250 ?E\b"),
    ("Mercedes-Benz", "B 250 e"): T("Mercedes-Benz", "B-Class", r"B ?250 ?E\b"),
    ("Mercedes-Benz", "CLA 250 e"): T("Mercedes-Benz", "CLA", r"250 ?E\b"),
    ("Mercedes-Benz", "GLA 250 e"): T("Mercedes-Benz", "GLA", r"250 ?E\b"),
    ("Mercedes-Benz", "GLB 200"): T("Mercedes-Benz", "GLB-Class", r"\b200\b"),
    ("BMW", "330e"): T("BMW", "3 Series", r"330E"),
    ("BMW", "530e"): T("BMW", "5 Series", r"530E"),
    ("BMW", "745e"): T("BMW", "7 Series", r"745E"),
    ("BMW", "X1 xDrive25e"): T("BMW", "X1", r"25E"),
    ("BMW", "M4 Convertible"): T("BMW", "M4", r"CONVERTIBLE"),
    ("BMW", "i4 eDrive40"): T("BMW", "i4", r"40"),
    ("BMW", "X5 xDrive45e"): T("BMW", "X5", r"45E"),
    ("BMW", "Z4 sDrive20i"): T("BMW", "Z4", r"20I"),
    ("BMW", "M3 Competition"): T("BMW", "M3", r"COMPETITION"),
    ("BMW", "M5 Competition"): T("BMW", "M5", r"COMPETITION"),
    ("BMW", "X7 xDrive40i"): T("BMW", "X7", r"40I"),
    ("BMW", "iX xDrive40"): T("BMW", "iX", r"40"),
    ("BMW", "M2"): T("BMW", "M2"),
    ("BMW", "840i"): T("BMW", "8 Series", r"840I"),
    ("BMW", "i7 xDrive60"): T("BMW", "i7", r"60"),
    ("BMW", "XM"): T("BMW", "XM"),
    ("BMW", "118i"): T("BMW", "1 Series", r"118I"),
    ("BMW", "225e Active Tourer"): T("BMW", "2 Series", r"225E"),
    ("BMW", "X2 xDrive25e"): T("BMW", "X2", r"25E"),
    ("BMW", "X3 xDrive30e"): T("BMW", "X3", r"30E"),
    ("Volkswagen", "Golf GTE"): T("Volkswagen", "Golf", r"GTE"),
    ("Volkswagen", "Passat GTE"): T("Volkswagen", "Passat", r"GTE"),
    ("Volkswagen", "Tiguan eHybrid"): T("Volkswagen", "Tiguan", r"E-?HYBRID"),
    ("Volkswagen", "ID.4"): T("Volkswagen", "ID.4"),
    ("Volkswagen", "Polo"): T("Volkswagen", "Polo", r"\b1\.0", r"\bGTI\b"),
    ("Volkswagen", "T-Roc"): T("Volkswagen", "T-Roc", r"\b1\.0"),
    ("Volkswagen", "Up"): T("Volkswagen", "Up", None, r"\bGTI\b|E-UP"),
    ("Audi", "A4"): T("Audi", "A4", r"\b(35|40|45) TFSI\b|\b2\.0 TFSI"),
    ("Audi", "A6 50 TFSI e"): T("Audi", "A6", r"50 ?TFSI ?E\b"),
    ("Audi", "A5 Cabriolet"): T("Audi", "A5", r"CABRIOLET"),
    ("Audi", "e-tron GT"): T("Audi", "E-Tron GT"),
    ("Audi", "R8 V10"): T("Audi", "R8"),
    ("Audi", "Q3 45 TFSI e"): T("Audi", "Q3", r"45 ?TFSI ?E\b"),
    ("Audi", "Q5 55 TFSI e"): T("Audi", "Q5", r"55 ?TFSI ?E\b"),
    ("Audi", "Q7 60 TFSI e"): T("Audi", "Q7", r"60 ?TFSI ?E\b"),
    ("Audi", "RS6 Avant"): T("Audi", "RS6"),
    ("Audi", "RS3"): T("Audi", "RS3"),
    ("Audi", "RS Q8"): T("Audi", "RS Q8"),
    ("Audi", "TT RS"): T("Audi", "TT", r"\bRS\b"),
    ("Audi", "A8 L 60 TFSI e"): T("Audi", "A8", r"60 ?TFSI ?E\b"),
    ("Audi", "A1 25 TFSI"): T("Audi", "A1", r"25 ?TFSI"),
    ("Audi", "A3 40 TFSI e"): T("Audi", "A3", r"40 ?TFSI ?E\b"),
    ("Audi", "Q2 30 TFSI"): T("Audi", "Q2", r"30 ?TFSI"),
    # CarGurus names the base car's trim without "Carrera" ("2dr PDK"), so it is whatever is not a named version
    ("Porsche", "911 Carrera"): T("Porsche", "911", None, r"\b(S|4|4S|T|GTS|GT3|TURBO|TARGA|CABRIOLET|DAKAR|SPORT CLASSIC)\b"),
    ("Porsche", "718 Boxster"): T("Porsche", "718", r"BOXSTER", r"\bS\b|GTS|SPYDER"),
    ("Porsche", "Macan"): T("Porsche", "Macan", None, r"\bS\b|GTS|TURBO|ELECTRIC"),
    ("Porsche", "Panamera 4 E-Hybrid"): T("Porsche", "Panamera", r"E-?HYBRID", r"TURBO|4S"),
    ("Porsche", "Taycan"): T("Porsche", "Taycan", None, r"TURBO|4S|GTS|CROSS"),
    ("Porsche", "Cayenne E-Hybrid"): T("Porsche", "Cayenne", r"E-?HYBRID", r"TURBO"),
    ("Porsche", "911 GT3"): T("Porsche", "911", r"GT3", r"\bRS\b"),
    ("Porsche", "718 Cayman GT4"): T("Porsche", "718", r"GT4"),
    ("Porsche", "Cayenne Turbo GT"): T("Porsche", "Cayenne", r"TURBO GT"),
    ("Porsche", "911 Turbo S"): T("Porsche", "911", r"TURBO S"),
    ("Ferrari", "Roma"): T("Ferrari", "Roma"),
    ("Ferrari", "F8 Tributo"): T("Ferrari", "F8", None, r"SPIDER"),
    ("Ferrari", "296 GTB"): T("Ferrari", "296", r"GTB"),
    ("Ferrari", "SF90 Stradale"): T("Ferrari", "SF90", None, r"SPIDER"),
    ("Ferrari", "812 Superfast"): T("Ferrari", "812 Superfast"),
    ("Lamborghini", "Huracan EVO"): T("Lamborghini", "Huracan", r"EVO"),
    ("Lamborghini", "Urus SE"): T("Lamborghini", "Urus", r"\bSE\b"),
    ("Lamborghini", "Aventador SVJ"): T("Lamborghini", "Aventador", r"SVJ"),
    ("Lamborghini", "Revuelto"): T("Lamborghini", "Revuelto"),
    ("Maserati", "Ghibli"): T("Maserati", "Ghibli", None, r"TROFEO|V8", by_fuel=False),
    ("Maserati", "MC20"): T("Maserati", "MC20"),
    ("Alfa Romeo", "Giulia"): T("Alfa Romeo", "Giulia", None, r"QUADRIFOGLIO"),
    ("Alfa Romeo", "Stelvio"): T("Alfa Romeo", "Stelvio", None, r"QUADRIFOGLIO"),
    ("Volvo", "XC60 Recharge T6"): T("Volvo", "XC60", r"T6"),
    ("Volvo", "XC90 Recharge T8"): T("Volvo", "XC90", r"T8"),
    ("Cupra", "Formentor e-Hybrid"): T("Cupra", "Formentor"),
    ("Ford", "Mustang EcoBoost"): T("Ford", "Mustang", r"2\.3|ECOBOOST"),
    ("Hyundai", "Ioniq 5"): T("Hyundai", "IONIQ 5", None, r"N"),
    ("Hyundai", "i30 N"): T("Hyundai", "i30 N"),
    ("Alpine", "A110 S"): T("Alpine", "A110", r"S"),
    ("Ineos", "Grenadier"): T("INEOS", "Grenadier"),
    ("Land Rover", "Defender Octa"): T("Land Rover", "Defender", r"OCTA"),
    ("Hyundai", "Ioniq 5 N"): T("Hyundai", "IONIQ 5", r"N"),
    ("Porsche", "718 Spyder RS"): T("Porsche", "718", r"SPYDER RS"),
    ("Alfa Romeo", "Giulia Quadrifoglio"): T("Alfa Romeo", "Giulia", r"QUADRIFOGLIO"),
    ("Maserati", "Grecale Trofeo"): T("Maserati", "Grecale", r"TROFEO", by_fuel=False),
    ("Maserati", "GranTurismo Trofeo"): T("Maserati", "GranTurismo", r"TROFEO", by_fuel=False),
    ("BMW", "M3 Touring"): T("BMW", "M3", r"TOURING"),
    ("Jaguar", "F-Type R75"): T("Jaguar", "F-TYPE", r"R75|R-?75"),
    ("Aston Martin", "Vanquish"): T("Aston Martin", "Vanquish"),
    ("Mercedes-Benz", "AMG One"): T("Mercedes-Benz", "AMG One"),
    ("Ferrari", "Purosangue"): T("Ferrari", "Purosangue"),
    ("Ferrari", "12Cilindri"): T("Ferrari", "12Cilindri"),
    ("Kia", "EV6"): T("Kia", "EV6"),
    ("Kia", "Stinger GT"): T("Kia", "Stinger", r"\bGT|3\.3"),
    ("Tesla", "Model Y"): T("Tesla", "Model Y"),
    ("Tesla", "Model S Plaid"): T("Tesla", "Model S", r"PLAID"),
    ("Caterham", "Seven 170"): T("Caterham", "Seven", r"170"),
    ("Morgan", "Plus Four"): T("Morgan", "Plus 4"),
}


def matches(car: cg.Listing, year: int, target: Target) -> bool:
    text = f"{car.trim} {car.title}"
    return (
        car.year == year
        and (target.trim is None or re.search(target.trim, text, re.I) is not None)
        and (target.not_trim is None or re.search(target.not_trim, text, re.I) is None)
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cars = {(m, n): (y, f) for m, n, y, _, f in read_catalogue()}
    fetcher = PoliteFetcher(delay=3)
    makes = cg.make_ids(fetcher.get(INDEX))
    models: dict[str, dict[str, str]] = {}
    pages: dict[tuple, list[cg.Listing]] = {}
    rows, summary = [], []

    # "Make/Model" arguments search only those cars and keep everyone else's rows
    wanted = {tuple(arg.split("/", 1)) for arg in sys.argv[1:]}
    targets = {k: t for k, t in TARGETS.items() if not wanted or k in wanted}
    for (make, model), target in targets.items():
        year, fuel = cars[(make, model)]
        make_id = makes.get(target.make)
        if make_id and target.make not in models:
            try:
                models[target.make] = cg.model_ids(fetcher.get(cg.make_url(target.make, make_id)), make_id)
            except FetchError as e:
                print(f"  {target.make}: {e}", flush=True)
                models[target.make] = {}
        model_id = models.get(target.make, {}).get(target.model)
        if not model_id:
            print(f"{make} {model}: no CarGurus model {target.make} {target.model}", flush=True)
            continue
        key = (model_id, year, fuel if target.by_fuel else None)
        if key not in pages:
            seen: list[cg.Listing] = []
            for page in range(1, MAX_PAGES + 1):
                try:
                    found, count = cg.parse_page(fetcher.get(cg.search_url(target.make, target.model, model_id, year, key[2], page)))
                except FetchError as e:
                    print(f"  {target.model}: {e}", flush=True)
                    break
                seen += found
                if page >= count:
                    break
            pages[key] = seen
        hits = [c for c in pages[key] if matches(c, year, target)]
        print(f"{make} {model} {year}: {len(hits)} of {len(pages[key])} listings match", flush=True)
        rows += [{"make": make, "model": model, **asdict(c)} for c in hits]
        if hits:
            summary.append({"make": make, "model": model, "year": year, **store.summarise([c.price_gbp for c in hits])})

    RAW.mkdir(parents=True, exist_ok=True)
    if rows:
        with (RAW / f"{date.today().isoformat()}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    stored = store.save("cargurus", "GBP", summary, set(targets))
    print(f"{len(summary)} cars priced -> {store.OUT}; {store.apply_to_catalogue(stored)} catalogue prices updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
