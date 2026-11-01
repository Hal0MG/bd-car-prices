"""Read export prices from SBT Japan's public stock pages.

SBT Japan sells used Japanese cars to importers abroad, Bangladesh included, and lists each
car's FOB price: the price at a Japanese port, before shipping. That is the "price in Japan"
the site's calculator asks for, so these listings replace the catalogue's rounded examples.

A stock page (`/used-cars/<make>/<model>?show_numbers=100`) holds up to 100 cars, filtered
by registration year. Only car attributes and the price are kept, never stock ids or seller
details, and the run uses the same polite fetcher as the GarirBazar collector.
"""

from __future__ import annotations

import html as htmllib
import re
from dataclasses import dataclass
from urllib.parse import urlencode

BASE = "https://www.sbtjapan.com"
PER_PAGE = 100

_TAGS = re.compile(r"<script.*?</script>|<style.*?</style>", re.S)
# Each car starts like this once tags are stripped: |2022/12 TOYOTA HARRIER G |73,000km|Mileage|
# Partner stock leaves out the month and the build year.
_START = re.compile(r"\|(?P<reg>\d{4})(?:/\d+)? (?P<title>[A-Z0-9][^|]*?) \|(?P<km>[\d,]+)km\|Mileage\|")
_TOTAL = re.compile(r"\|([\d,]+)\|Results\|")


def _before(block: str, label: str) -> str | None:
    """The value printed just before a label, as in |MXUA80|Model Code|."""
    m = re.search(r"\|([^|]*)\|" + re.escape(label) + r"\|", block)
    return m[1].strip() if m else None

@dataclass(frozen=True)
class Listing:
    title: str
    model_code: str
    fuel: str
    #: None when the page gives no engine size, as for electric cars
    cc: int | None
    mileage_km: int
    #: None for partner stock, which doesn't say
    built: int | None
    registered: int
    fob_usd: int


def _num(s: str) -> int:
    return int(s.replace(",", ""))


def page_url(make: str, model: str, year_from: int, year_to: int, page: int = 1) -> str:
    query = {"year__from": year_from, "year__to": year_to, "show_numbers": PER_PAGE}
    if page > 1:
        query["page"] = page
    return f"{BASE}/used-cars/{make}/{model}?{urlencode(query)}"


def parse_page(page: str) -> tuple[list[Listing], int | None]:
    """The priced cars on one stock page, and the total the search says it found.

    The page is cut into one block per car before anything is read, so a reserved car
    (price "Ask") is skipped rather than picking up the next car's price.
    """
    text = re.sub(r"<[^>]+>", "|", _TAGS.sub("", page))
    text = htmllib.unescape(re.sub(r"(\| ?)+", "|", re.sub(r"\s+", " ", text)))
    starts = list(_START.finditer(text))
    cars = []
    for m, nxt in zip(starts, starts[1:] + [None]):
        block = text[m.start(): nxt.start() if nxt else len(text)]
        price = re.search(r"Vehicle Price ?\|USD\|([\d,]+)\|", block)
        cc, code, fuel = _before(block, "Engine"), _before(block, "Model Code"), _before(block, "Fuel Type")
        if not price or not fuel:
            continue
        built = re.search(r"Manufacture:\|(\d{4})\|", block)
        cars.append(Listing(
            title=m["title"].strip(),
            model_code=code or "",
            fuel=fuel,
            cc=_num(cc[:-2]) if cc and re.fullmatch(r"[\d,]+cc", cc) else None,
            mileage_km=_num(m["km"]),
            built=int(built[1]) if built else None,
            registered=int(m["reg"]),
            fob_usd=_num(price[1]),
        ))
    total = _TOTAL.search(text)
    return cars, _num(total[1]) if total else None


def fuel_matches(listing_fuel: str, fuel: str) -> bool:
    """SBT writes PETROL, DIESEL, HYBRID(PETROL), PLUG-IN HYBRID(PETROL) or ELECTRIC; the catalogue
    writes petrol, diesel, hybrid, phev or ev."""
    f = listing_fuel.upper()
    if fuel == "phev":
        return "PLUG-IN" in f
    if fuel == "hybrid":
        return "HYBRID" in f and "PLUG-IN" not in f
    if fuel == "ev":
        return "ELECTRIC" in f
    return fuel.upper() in f and "HYBRID" not in f
