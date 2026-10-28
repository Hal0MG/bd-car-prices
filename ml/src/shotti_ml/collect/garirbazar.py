"""Read car listing cards from GarirBazar's public listing pages.

A listing page (`/buy-cars?page=N`) holds about 20 cards, each with the title, price,
mileage, engine, fuel, gearbox, location and a "posted" time. One request per 20 cars
is far lighter on the site than opening every ad.

Only car attributes are kept. The card's description is read for one thing, the
registration year, and then thrown away: sellers put their phone numbers and email
addresses in it, and this project has no use for them.
"""

from __future__ import annotations

from urllib.parse import urlencode

import html as htmllib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

BASE = "https://www.garirbazar.com"
LISTING_PATH = "/buy-cars"
CARDS_PER_PAGE = 20

# Longest names first, so "Land Rover" wins over "Land".
KNOWN_MAKES = sorted(
    [
        "Toyota", "Honda", "Nissan", "Mitsubishi", "Suzuki", "Maruti Suzuki", "Mazda", "Subaru", "Lexus", "Daihatsu",
        "Isuzu", "Hyundai", "Kia", "Ford", "Tata", "Mahindra", "Proton", "MG", "BMW", "Mercedes-Benz", "Mercedes Benz",
        "Audi", "Volkswagen", "Porsche", "Land Rover", "Range Rover", "Jaguar", "Mini", "Bentley", "Rolls-Royce",
        "Rolls Royce", "Aston Martin", "McLaren", "Lotus", "Volvo", "Peugeot", "Renault", "Citroen", "Skoda", "Fiat",
        "Jeep", "Chevrolet", "Tesla", "BYD", "Chery", "Haval", "Changan", "JAC", "Foton", "Hino", "Datsun", "Ssangyong",
        "Maserati", "Ferrari", "Lamborghini", "Opel", "Smart", "Genesis", "Infiniti", "Acura", "Cadillac", "Dodge",
    ],
    key=len,
    reverse=True,
)

_CARD_START = re.compile(r'(?=<a class="common-ad-card)')
_UNITS = {"minute": 60, "hour": 3600, "day": 86400, "week": 7 * 86400, "month": 30 * 86400, "year": 365 * 86400}


@dataclass(frozen=True)
class Listing:
    id: int
    observed_at: str
    title: str
    make: str
    model: str
    year: int | None
    price_bdt: int | None
    mileage_km: int | None
    engine_cc: int | None
    fuel: str | None
    transmission: str | None
    location: str | None
    posted_at: str | None
    registration_year: int | None

    def as_dict(self) -> dict:
        return asdict(self)


# -- small parsers ---------------------------------------------------------


def _first(pattern: str, text: str, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags | re.S)
    return match.group(1) if match else None


def _strip_tags(text: str) -> str:
    return htmllib.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _digits(text: str | None) -> int | None:
    cleaned = re.sub(r"[^\d]", "", text or "")
    return int(cleaned) if cleaned else None


def parse_engine_cc(text: str | None) -> int | None:
    """'2.5 L' -> 2500, '1,500 cc' -> 1500, 'N/A' -> None."""
    match = re.search(r"([\d.,]+)\s*(l|litre|liter|cc)\b", text or "", re.I)
    if not match:
        return None
    try:
        value = float(match.group(1).replace(",", ""))
    except ValueError:
        return None
    cc = value * 1000 if match.group(2).lower() != "cc" else value
    return round(cc) if 500 <= cc <= 9000 else None  # real car engines start near 660cc (kei cars)


def parse_posted(text: str | None, observed_at: datetime) -> datetime | None:
    """'Posted about 17 hours ago' -> a time 17 hours before the page was fetched."""
    if not text:
        return None
    lowered = text.lower()
    if "less than a minute" in lowered or "just now" in lowered:
        return observed_at
    match = re.search(r"(?:(\d+)|an?)\s+(minute|hour|day|week|month|year)s?\s+ago", lowered)
    if not match:
        return None
    count = int(match.group(1)) if match.group(1) else 1
    return observed_at - timedelta(seconds=count * _UNITS[match.group(2)])


def split_title(title: str) -> tuple[str, str, int | None]:
    """'2005 Toyota Allion 2005' -> ('Toyota', 'Allion', 2005)."""
    text = re.sub(r"\s+", " ", title).strip()
    years = re.findall(r"\b(?:19|20)\d{2}\b", text)
    year = int(years[0]) if years else None
    text = re.sub(r"^(?:19|20)\d{2}\s+", "", text)
    text = re.sub(r"\s+(?:19|20)\d{2}$", "", text)
    for make in KNOWN_MAKES:
        if text.lower().startswith(make.lower() + " ") or text.lower() == make.lower():
            return make.replace("Mercedes Benz", "Mercedes-Benz").replace("Rolls Royce", "Rolls-Royce"), text[len(make):].strip(), year
    head, _, rest = text.partition(" ")
    return head, rest.strip(), year


def canonical_model(model_raw: str, known_models: list[str]) -> str:
    """Reduce 'Axio X package' to 'Axio': the longest known model the text starts with, else its first word."""
    lowered = model_raw.lower()
    for known in sorted(known_models, key=len, reverse=True):
        if lowered == known.lower() or lowered.startswith(known.lower() + " "):
            return known
    return model_raw.split(" ")[0] if model_raw else ""


# -- cards -----------------------------------------------------------------


def parse_card(card: str, observed_at: datetime) -> Listing | None:
    href = _first(r'href="([^"]+)"', card) or ""
    id_match = re.search(r"-(\d+)$", href.split("?")[0])
    title = htmllib.unescape(_first(r'<h4[^>]*title="([^"]*)"', card) or "")
    if not id_match or not title:
        return None

    make, model, year = split_title(title)
    engine_match = re.search(r'<div class="engine-capacity">\s*(?:<img[^>]*>\s*)?<span>([^<]*)</span>\s*<span>\s*\(([^)]*)\)\s*</span>', card, re.S)
    description = _first(r'<div class="[^"]*sort-ad-description">(.*?)</div>', card) or ""
    reg = re.search(r"\bregistration\b\D{0,12}((?:19|20)\d{2})", _strip_tags(description), re.I)  # description is dropped here
    posted_text = _first(r'<div class="ad-post-date">\s*(?:<(?:i|img)[^>]*>(?:</i>)?\s*)*<span>([^<]*)</span>', card)
    posted = parse_posted(posted_text, observed_at)
    location = _first(r'<div class="location">(.*?)</div>', card)

    return Listing(
        id=int(id_match.group(1)),
        observed_at=observed_at.isoformat(timespec="seconds"),
        title=title,
        make=make,
        model=model,
        year=year,
        price_bdt=_digits(_first(r'<span class="price">\s*([\d,]+)\s*</span>', card)),
        mileage_km=_digits(_first(r'class="value">\s*([\d,]+)\s*km', card, re.I)),
        engine_cc=parse_engine_cc(engine_match.group(1) if engine_match else None),
        fuel=htmllib.unescape(engine_match.group(2)).strip() if engine_match else None,
        transmission=_first(r'<div class="transmission">\s*(?:<img[^>]*>\s*)?<span>([^<]*)</span>', card),
        location=_strip_tags(location) if location else None,
        posted_at=posted.isoformat(timespec="seconds") if posted else None,
        registration_year=int(reg.group(1)) if reg else None,
    )


def parse_listing_page(page: str, observed_at: datetime) -> list[Listing]:
    cards = _CARD_START.split(page)[1:]
    listings = (parse_card(block.split("</a>", 1)[0], observed_at) for block in cards)
    return [listing for listing in listings if listing is not None]


def total_listings(page: str) -> int | None:
    """'41,646 vehicles for sale in Bangladesh' -> 41646."""
    return _digits(_first(r'class="count-cars">\s*([\d,]+)\s+vehicles', page))


def total_pages(page: str) -> int | None:
    count = total_listings(page)
    return -(-count // CARDS_PER_PAGE) if count else None


def page_url(page_number: int, filters: dict[str, str | int] | None = None) -> str:
    """A listing page, optionally narrowed with the site's own search filters (min_price, max_price, condition)."""
    query = {f"listing[{name}]": value for name, value in (filters or {}).items()}
    if page_number > 1:
        query["page"] = page_number
    return f"{BASE}{LISTING_PATH}" + (f"?{urlencode(query)}" if query else "")
