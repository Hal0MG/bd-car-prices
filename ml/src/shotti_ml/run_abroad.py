"""Collect real export prices from Japan for every Japan-market catalogue car.

Run from the ml/ folder:  .venv/Scripts/python.exe -I -m shotti_ml.run_abroad
For each car, reads SBT Japan's stock pages for its model and keeps the cars of the catalogue's
build year whose model code (or, where no code is given, fuel) and engine size match, then
summarises their FOB prices. Writes the matched cars (attributes and price only) to
data/raw/sbt/<date>.csv and the summary to ../web/src/lib/abroad.json, and sets the catalogue
price of every car with enough matches to their median (see abroad_store.py). For partner stock, which
gives no build year, the registration year stands in. A listing whose engine size is more than
CC_SLACK away from the catalogue's is left out.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import asdict, dataclass
from datetime import date

from . import abroad_store as store
from .collect.fetch import FetchError, PoliteFetcher
from .collect.sbt import PER_PAGE, Listing, fuel_matches, page_url, parse_page
from .export import catalogue as read_catalogue

RAW = store.ROOT / "ml" / "data" / "raw" / "sbt"

MAX_PAGES = 3
CC_SLACK = 100


@dataclass(frozen=True)
class Target:
    """Where a catalogue car sits in SBT's stock, and how to pick it out of its model's listings."""

    make: str
    model: str
    #: model codes of the catalogue's generation and engine; a listing matches if its code contains
    #: one. Empty means match on fuel instead.
    codes: tuple[str, ...] = ()
    #: words the listing title must, or must not, contain (trims sold under the same model)
    has: str | None = None
    without: tuple[str, ...] = ()


T = Target
TARGETS: dict[tuple[str, str], Target] = {
    # cars with a local price
    ("Toyota", "Axio"): T("toyota", "corolla-axio", ("NRE161",)),
    ("Toyota", "Axio Hybrid"): T("toyota", "corolla-axio", ("NKE165",)),
    ("Toyota", "Fielder"): T("toyota", "corolla-fielder", ("NRE161",)),
    ("Toyota", "Fielder Hybrid"): T("toyota", "corolla-fielder", ("NKE165",)),
    ("Toyota", "Premio"): T("toyota", "premio", ("NZT260",)),
    ("Toyota", "Allion"): T("toyota", "allion", ("NZT260",)),
    ("Toyota", "Aqua"): T("toyota", "aqua", ("MXPK1",)),
    ("Toyota", "Yaris Hybrid"): T("toyota", "yaris", ("MXPH1",)),
    ("Toyota", "Prius"): T("toyota", "prius", ("ZVW5",)),
    ("Toyota", "Corolla Cross Hybrid"): T("toyota", "corolla-cross", ("ZVG1",)),
    ("Toyota", "Yaris Cross Hybrid"): T("toyota", "yaris-cross", ("MXPJ1",)),
    ("Toyota", "Raize"): T("toyota", "raize", ("A200A", "A210A")),
    ("Toyota", "C-HR"): T("toyota", "c-hr", ("NGX10", "NGX50")),
    ("Toyota", "C-HR Hybrid"): T("toyota", "c-hr", ("ZYX1",)),
    ("Toyota", "Harrier"): T("toyota", "harrier", ("MXUA8",)),
    ("Toyota", "Harrier Hybrid"): T("toyota", "harrier-hybrid", ("AXUH8",)),
    ("Toyota", "RAV4"): T("toyota", "rav4", ("MXAA5",)),
    ("Toyota", "RAV4 Hybrid"): T("toyota", "rav4", ("AXAH5",)),
    ("Toyota", "Camry Hybrid"): T("toyota", "camry", ("AXVH7",)),
    ("Toyota", "Crown Crossover"): T("toyota", "crown", ("AZSH35",)),
    ("Toyota", "Land Cruiser Prado TX"): T("toyota", "land-cruiser-prado", ("TRJ150",)),
    ("Toyota", "Noah"): T("toyota", "noah", ("MZRA9",)),
    ("Toyota", "Noah Hybrid"): T("toyota", "noah", ("ZWR9",)),
    ("Toyota", "Voxy Hybrid"): T("toyota", "voxy", ("ZWR9",)),
    ("Toyota", "Esquire Hybrid"): T("toyota", "esquire", ("ZWR80",)),
    ("Toyota", "HiAce"): T("toyota", "hiace-van", ("GDH2",)),
    ("Toyota", "Alphard"): T("toyota", "alphard", ("AGH3",)),
    ("Toyota", "Sienta Hybrid"): T("toyota", "sienta", ("MXPL1",)),
    ("Honda", "Insight"): T("honda", "insight", ("ZE4",)),
    ("Honda", "Vezel e:HEV"): T("honda", "vezel", ("RV5", "RV6")),
    ("Honda", "Civic"): T("honda", "civic", ("FL1",)),
    ("Honda", "CR-V"): T("honda", "crv", ("RW1", "RW2")),
    ("Nissan", "X-Trail e-Power"): T("nissan", "xtrail", ("SNT33",)),
    ("Lexus", "RX 350h"): T("lexus", "rx", ("AALH1",)),
    # the rest of the Japan list
    ("Toyota", "GR Yaris"): T("toyota", "yaris", ("GXPA16",)),
    ("Toyota", "Prius Alpha"): T("toyota", "prius-alpha", ("ZVW4",)),
    ("Toyota", "Corolla Touring Hybrid"): T("toyota", "corolla-touring", ("ZWE21",)),
    ("Toyota", "GR86"): T("toyota", "86", ("ZN8",)),
    ("Toyota", "GR Supra"): T("toyota", "supra"),
    ("Toyota", "Vellfire"): T("toyota", "vellfire", ("AGH3",)),
    ("Toyota", "Land Cruiser 300"): T("toyota", "land-cruiser", ("FJA300",)),
    ("Toyota", "Century"): T("toyota", "century", ("UWG60",)),
    ("Toyota", "GR Corolla"): T("toyota", "corolla", ("GZEA14",)),
    ("Toyota", "bZ4X"): T("toyota", "bz4x"),
    ("Toyota", "Roomy"): T("toyota", "roomy", ("M900A", "M910A")),
    ("Honda", "Fit e:HEV"): T("honda", "fit", ("GR3", "GR4", "GR6", "GR8")),
    ("Honda", "Civic Type R"): T("honda", "civic", ("FL5",)),
    ("Honda", "S660"): T("honda", "s660", ("JW5",)),
    ("Honda", "NSX"): T("honda", "nsx", ("NC1",)),
    ("Honda", "N-Box"): T("honda", "n-box", ("JF3", "JF4")),
    ("Honda", "Freed Hybrid"): T("honda", "freed", ("GB7", "GB8")),
    ("Nissan", "Note e-Power"): T("nissan", "note", ("E13",)),
    ("Nissan", "Kicks e-Power"): T("nissan", "kicks", ("P15",)),
    ("Nissan", "Serena e-Power"): T("nissan", "serena"),
    ("Nissan", "Fairlady Z"): T("nissan", "fairlady-z", ("RZ34",), None, ("NISMO",)),
    ("Nissan", "GT-R"): T("nissan", "gt-r", ("R35",), without=("NISMO",)),
    ("Nissan", "GT-R NISMO"): T("nissan", "gt-r", ("R35",), has="NISMO"),
    ("Nissan", "Skyline 400R"): T("nissan", "skyline", ("RV37",), has="400R"),
    ("Nissan", "Leaf"): T("nissan", "leaf", ("ZE1",)),
    ("Nissan", "Ariya"): T("nissan", "ariya", ("FE0",)),
    ("Mitsubishi", "Outlander PHEV"): T("mitsubishi", "outlander-phev", ("GN0W",)),
    ("Mitsubishi", "Eclipse Cross PHEV"): T("mitsubishi", "eclipse-cross"),
    ("Mitsubishi", "Delica D:5"): T("mitsubishi", "delica-d5"),
    ("Mazda", "CX-5 2.0 Petrol"): T("mazda", "cx5"),
    ("Mazda", "MX-5 Roadster"): T("mazda", "roadster", ("ND5RC",)),
    ("Mazda", "CX-8"): T("mazda", "cx8"),
    ("Mazda", "CX-60 PHEV"): T("mazda", "cx-60"),
    ("Mazda", "MX-30 EV"): T("mazda", "mx-30"),
    ("Subaru", "Forester e-Boxer"): T("subaru", "forester", ("SKE",)),
    ("Subaru", "XV"): T("subaru", "xv", ("GT3",)),
    ("Subaru", "BRZ"): T("subaru", "brz", ("ZD8",)),
    ("Subaru", "WRX S4"): T("subaru", "wrx-s4", ("VBH",)),
    ("Subaru", "Levorg"): T("subaru", "levorg", ("VN5",)),
    ("Lexus", "NX 350h"): T("lexus", "nx", ("AAZH2",)),
    ("Lexus", "LC 500 Convertible"): T("lexus", "lc500", ("URZ100",), has="CONVERTIBLE"),
    ("Lexus", "LC 500h"): T("lexus", "lc500", ("GWZ100",)),
    ("Lexus", "UX 250h"): T("lexus", "ux", ("MZAH1",)),
    ("Lexus", "ES 300h"): T("lexus", "es", ("AXZH1",)),
    ("Lexus", "LS 500h"): T("lexus", "ls", ("GVF5",)),
    ("Lexus", "LX 600"): T("lexus", "lx", ("VJA310",)),
    ("Lexus", "RC 300"): T("lexus", "rc", ("ASC10",)),
    ("Lexus", "IS 300"): T("lexus", "is", ("ASE30",)),
    ("Suzuki", "Swift"): T("suzuki", "swift"),
    ("Suzuki", "Jimny"): T("suzuki", "jimny", ("JB64",)),
    ("Suzuki", "Jimny Sierra"): T("suzuki", "jimny-sierra", ("JB74",)),
    ("Suzuki", "Hustler"): T("suzuki", "hustler", ("MR52S", "MR92S")),
    ("Suzuki", "Spacia"): T("suzuki", "spacia", ("MK53S",)),
    ("Daihatsu", "Copen"): T("daihatsu", "copen", ("LA400K",)),
    ("Daihatsu", "Taft"): T("daihatsu", "taft", ("LA900S", "LA910S")),
    ("Nissan", "Fairlady Z NISMO"): T("nissan", "fairlady-z", ("RZ34",), "NISMO"),
    ("Daihatsu", "Rocky Hybrid"): T("daihatsu", "rocky", ("A202S",)),
        ("Honda", "Civic e:HEV"): T("honda", "civic", ("FL4",)),
    ("Honda", "Prelude"): T("honda", "prelude"),
    ("Subaru", "Crosstrek"): T("subaru", "crosstrek"),
    ("Lexus", "LBX"): T("lexus", "lbx", ("MAYH1",)),
    ("Lexus", "RZ 450e"): T("lexus", "rz"),
    ("Lexus", "LM 500h"): T("lexus", "lm", ("TAWH15",)),
    ("Lexus", "GX 550"): T("lexus", "gx", ("VJA25",)),
    ("Toyota", "Crown Sport"): T("toyota", "crown", ("AZSH36",)),
    ("Nissan", "Sakura"): T("nissan", "sakura"),
    ("Lexus", "IS 500"): T("lexus", "is", ("USE30",)),
    ("Honda", "Stepwgn e:HEV"): T("honda", "stepwgn", ("RP8",)),
    ("Nissan", "Aura Nismo"): T("nissan", "aura", (), "NISMO"),
    ("Subaru", "Solterra"): T("subaru", "solterra"),
    ("Toyota", "Crown Estate"): T("toyota", "crown", (), "ESTATE"),
    ("Lexus", "LX 700h"): T("lexus", "lx", (), "700"),
    ("Mitsubishi", "Delica Mini"): T("mitsubishi", "delica-mini"),
}


def matches(car: Listing, year: int, cc: int, fuel: str, target: Target) -> bool:
    title = car.title.upper()
    # Partner stock gives no build year; a Japanese car's first registration is within months of
    # its build, so the registration year stands in for it there.
    return (
        (car.built if car.built is not None else car.registered) == year
        # electric cars have no engine size on either side
        and (cc == 0 or (car.cc is not None and abs(car.cc - cc) <= CC_SLACK))
        and (any(c in car.model_code.upper() for c in target.codes) if target.codes else fuel_matches(car.fuel, fuel))
        and (target.has is None or target.has.upper() in title)
        and not any(w.upper() in title for w in target.without)
    )


def catalogue() -> dict[tuple[str, str], tuple[int, int, str]]:
    """(make, model) -> (year, cc, fuel) for every catalogue car, read from the web source."""
    return {(m, n): (y, cc, f) for m, n, y, cc, f in read_catalogue()}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cars = catalogue()
    fetcher = PoliteFetcher(delay=3)
    pages: dict[tuple[str, str, int], list[Listing]] = {}
    rows, summary = [], []

    # "Make/Model" arguments search only those cars and keep everyone else's rows
    wanted = {tuple(arg.split("/", 1)) for arg in sys.argv[1:]}
    targets = {k: t for k, t in TARGETS.items() if not wanted or k in wanted}
    for (make, model), target in targets.items():
        year, cc, fuel = cars[(make, model)]
        key = (target.make, target.model, year)
        if key not in pages:
            seen: list[Listing] = []
            for page in range(1, MAX_PAGES + 1):
                try:
                    found, total = parse_page(fetcher.get(page_url(target.make, target.model, year, year + 1, page)))
                except FetchError as e:
                    print(f"  {target.make}/{target.model}: {e}", flush=True)
                    break
                seen += found
                if total is None or page * PER_PAGE >= total:
                    break
            pages[key] = seen
        hits = [c for c in pages[key] if matches(c, year, cc, fuel, target)]
        print(f"{make} {model} {year}: {len(hits)} of {len(pages[key])} listings match", flush=True)
        rows += [{"make": make, "model": model, **asdict(c)} for c in hits]
        if hits:
            summary.append({"make": make, "model": model, "year": year, **store.summarise([c.fob_usd for c in hits])})

    today = date.today().isoformat()
    RAW.mkdir(parents=True, exist_ok=True)
    if rows:
        with (RAW / f"{today}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    stored = store.save("sbt", "USD", summary, set(targets))
    print(f"{len(summary)} cars priced -> {store.OUT}; {store.apply_to_catalogue(stored)} catalogue prices updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
