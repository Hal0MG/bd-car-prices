"""Read UK asking prices from CarGurus' public search pages.

European cars come to Bangladesh from the UK, so their "price abroad" is a UK used price. A
CarGurus search page (`/Cars/l-Used-<Make>-<Model>-d<id>?startYear=..&endYear=..`) carries its
results as JSON in the page itself: year, trim, mileage and price for up to 23 cars. robots.txt
allows these pages. Only those attributes are kept, never VINs, stock numbers or dealer details.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import urlencode

BASE = "https://www.cargurus.co.uk"
#: CarGurus' own fuel groups; plug-in hybrids are listed under HYBRID
FUEL_GROUP = {"petrol": "GASOLINE", "diesel": "DIESEL", "hybrid": "HYBRID", "phev": "HYBRID", "ev": "ELECTRIC"}

_DECODER = json.JSONDecoder()


@dataclass(frozen=True)
class Listing:
    title: str
    trim: str
    year: int
    mileage: int | None
    price_gbp: int


def slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-")


def make_url(make: str, make_id: str) -> str:
    return f"{BASE}/Cars/l-Used-{slug(make)}-{make_id}"


def search_url(make: str, model: str, model_id: str, year: int, fuel: str | None = None, page: int = 1) -> str:
    query: dict = {"startYear": year, "endYear": year, "distance": 1000}
    if fuel:
        query["fuelTypes"] = FUEL_GROUP[fuel]
    if page > 1:
        query["page"] = page
    return f"{BASE}/Cars/l-Used-{slug(make)}-{slug(model)}-{model_id}?{urlencode(query)}"


def _array_after(page: str, key: str) -> list:
    i = page.find(f'"{key}":[')
    if i < 0:
        return []
    value, _ = _DECODER.raw_decode(page[i + len(key) + 3:])
    return value


def make_ids(page: str) -> dict[str, str]:
    """Make name -> id (m256), from the make filter that every search page carries."""
    return {label: mid for mid, label in re.findall(r'\{"name":"(m\d+)","label":"([^"]+)"', page)}


def model_ids(page: str, make_id: str) -> dict[str, str]:
    """Model name -> id (d2887) for one make, from the model filter on that make's page."""
    found = re.findall(r'\{"name":"' + make_id + r'/(d\d+)","label":"([^"]+)"', page)
    return {label: did for did, label in found}


def parse_page(page: str) -> tuple[list[Listing], int]:
    """The listings on one search page, and how many pages the search has."""
    cars = []
    for tile in _array_after(page, "tiles"):
        if not str(tile.get("type", "")).startswith("LISTING"):
            continue
        d = tile["data"]
        onto, price = d.get("ontologyDto") or {}, (d.get("priceDto") or {}).get("current")
        if not price or not onto.get("carYear"):
            continue
        cars.append(Listing(
            title=d.get("listingTitle", ""),
            trim=onto.get("trimName") or "",
            year=int(onto["carYear"]),
            mileage=(d.get("mileage") or {}).get("value"),
            price_gbp=int(price),
        ))
    pages = re.search(r'"pageCount":(\d+)', page)
    return cars, int(pages[1]) if pages else 1
