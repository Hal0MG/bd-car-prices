"""Read Bikroy car cards from a print-to-PDF of its listing pages, after OCR.

Bikroy sits behind a Cloudflare challenge, so nothing here touches the site. The input is
pages the user saved from their own browser, run through scripts/ocr_pdf.py, which writes
one list of (box, text) pairs per page. Cards are rebuilt from the position of each price
("BDT 27,50,000"): the card is the column of text under it.

As with the GarirBazar reader, only car attributes are kept. The description is read for
year, mileage and engine size and then dropped, because sellers put phone numbers in it.

Printed pages cut cards at page breaks and clip the right-hand column, so some cards come
out without a title or location; those are dropped rather than guessed at.

`build_clean` turns the OCR files into one file of listings shaped like the GarirBazar ones
(see CLEAN_FIELDS), plus a reviewable model alias map and a list of names it could not map.
Prices are never edited: a price that looks like a lakh/crore slip is kept as listed and
flagged `suspect`.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .garirbazar import KNOWN_MAKES, parse_engine_cc, split_title

COLUMN_TOLERANCE = 40  # px at 150 dpi: how far a line may sit left or right of its price and still be in the column
MIN_PRICE = 100_000  # BDT 1 lakh; nothing real sells for less
MAX_PRICE = 300_000_000  # BDT 30 crore
OUTLIER_RATIO = 4.0  # a price this many times the same model's typical price is suspect
MAKE_OUTLIER_RATIO = 8.0  # ...or the same make's, which is a rougher yardstick
_PRICE = re.compile(r"^BDT\s*([\d,.\s]+)$", re.I)
_USED = re.compile(r"\b(local|foreign|recondition\w*|new)\s*used\b|\bbrand\s*new\b", re.I)
_YEAR = r"((?:19|20)\d{2})(?!\d)"
_ANY_YEAR = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")


def _digits(text: str) -> int | None:
    cleaned = re.sub(r"\D", "", text)
    return int(cleaned) if cleaned else None


def _mileage(text: str) -> int | None:
    match = re.search(r"mileage\D{0,3}([\d,.]+)\s*(k\b|km|kms)?|([\d,.]+)\s*(k\b|km\b|kms\b)", text, re.I)
    if not match:
        return None
    number, unit = (match.group(1), match.group(2)) if match.group(1) else (match.group(3), match.group(4))
    try:
        value = float(number.replace(",", ""))
    except ValueError:
        return None
    if unit and unit.lower() == "k":
        value *= 1000
    return round(value) if 100 <= value <= 600_000 else None


def _engine(text: str) -> int | None:
    match = re.search(r"(\d[\d,]{2,5})\s*cc\b", text, re.I) or re.search(r"(\d\.\d)\s*(?:L|litre|liter)\b", text, re.I)
    if not match:
        return None
    return parse_engine_cc(match.group(0))


def _split_title(title: str) -> tuple[str, str, int | None]:
    """split_title, after undoing what OCR does to a card title: glued words and a leading 'New' badge."""
    text = re.sub(r"^(?:New|Used)(?:\s+|(?=[A-Z]))|^(?:new|used)\s+", "", title.strip())
    text = re.sub(r"(?<=[a-z])(?=(?:19|20)\d{2}(?!\d))|(?<=\d)(?=[A-Z])", " ", text)  # 'Vezel2021Pearl' -> 'Vezel 2021 Pearl'
    for make in KNOWN_MAKES:  # 'HondaVezel' -> 'Honda Vezel', 'LandRoverRangeRover' -> 'Land Rover RangeRover'
        glued = make.replace(" ", "")
        if re.match(glued + r"(?=[A-Z0-9])", text):
            text = make + " " + text[len(glued):]
            break
    make, model, year = split_title(text)
    years = _ANY_YEAR.findall(text)
    year = int(years[0]) if years else None
    model = _ANY_YEAR.split(model)[0].strip()
    if make == "Range Rover":  # Range Rover is a Land Rover model, and some titles omit the maker
        make, model = "Land Rover", f"Range Rover {model}".strip()
    return make, model, year


def _transmission(text: str) -> str | None:
    """The badge is clipped by the page edge: 'Autom', 'Autc', 'CVT'."""
    lowered = text.lower()
    if re.search(r"\bman", lowered):
        return "Manual"
    if re.search(r"\bcvt\b", lowered):
        return "CVT"
    return "Automatic" if re.search(r"\bau[a-z]?", lowered) else None


def _clean_location(text: str | None) -> str | None:
    """Drop the pin icon OCR reads as a stray glyph ('o Dhaka, Gulshan', '。Dhaka, Banani')."""
    if not text:
        return None
    cleaned = re.sub(r"^[^A-Za-z]*(?:[A-Za-z]\s+|[A-Za-z](?=[A-Z][a-z]))?(?=[A-Z])", "", text).strip()
    return cleaned if "," in cleaned else None


_PRINTED = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2,4}),?\s*(\d{1,2}):(\d{2})\s*([AP])M", re.I)
_FUELS = [
    ("Electric", re.compile(r"\b(?:electric|ev)\b", re.I)),
    ("Diesel", re.compile(r"\b(?:diesel|dsl)\b", re.I)),
    ("CNG", re.compile(r"\bcng\b", re.I)),
    ("Octane", re.compile(r"\boctane\b", re.I)),
    ("Petrol", re.compile(r"\bpetrol\b", re.I)),
]
_HYBRID = re.compile(r"\b(non[\s-]*)?hybrid\b", re.I)
_BODIES = [
    ("SUV", re.compile(r"\bsuv\b|sport\s+utility", re.I)),
    ("Sedan", re.compile(r"\bsedan\b|\bsaloon\b", re.I)),
    ("Hatchback", re.compile(r"\bhatch(?:back)?\b", re.I)),
    ("Wagon", re.compile(r"\bwagon\b", re.I)),  # not WagonR: no word boundary after the n
    ("Coupe", re.compile(r"\bcoupe\b", re.I)),
    ("Convertible", re.compile(r"\bconvertible\b|\bcabriolet\b", re.I)),
    ("Minivan", re.compile(r"\bmini\s?van\b|\bmpv\b", re.I)),
    ("Pickup", re.compile(r"\bpick[\s-]?up\b", re.I)),
]
_CONDITIONS = {"local used": "Used", "foreign used": "Reconditioned", "brand new": "New"}


def _fuel(text: str) -> str | None:
    """Fuel when the card says so in words. 'Non-hybrid' says nothing about which fuel it burns."""
    if any(not m.group(1) for m in _HYBRID.finditer(text)):
        return "Hybrid"
    return next((name for name, pattern in _FUELS if pattern.search(text)), None)


def _body_type(text: str) -> str | None:
    """The first body style named in the text."""
    hits = [(m.start(), name) for name, pattern in _BODIES if (m := pattern.search(text))]
    return min(hits)[1] if hits else None


def _scrub(text: str) -> str:
    """Drop anything that could be a phone number or email from a title. Sellers write them anywhere."""
    words = [w for w in text.split() if "@" not in w and len(re.sub(r"\D", "", w)) < 7]
    return " ".join(words)


def _printed_at(boxes: list) -> datetime | None:
    """The browser stamps every printed page with the time it was printed ('10/28/26, 1:27 PM'), in local time."""
    for box, text in boxes:
        match = _PRINTED.search(text) if box[1] < 80 else None
        if match:
            month, day, year, hour, minute, half = match.groups()
            year = int(year) + (2000 if int(year) < 100 else 0)
            hour = int(hour) % 12 + (12 if half.upper() == "P" else 0)
            return datetime(year, int(month), int(day), hour, int(minute)).astimezone(timezone.utc)
    return None


def _lines_in_column(boxes: list, x: int, top: int, bottom: int) -> list[tuple[int, str]]:
    return sorted(
        (box[1], text)
        for box, text in boxes
        if abs(box[0] - x) <= COLUMN_TOLERANCE and top <= box[1] < bottom
    )


def parse_page(boxes: list, page: int, stats: collections.Counter | None = None) -> list[dict]:
    """Cards on one OCR'd page. Each price starts a card that ends at the next price in its column."""
    prices = [(box, _PRICE.match(text.strip())) for box, text in boxes]
    anchors = [(box, match) for box, match in prices if match]
    cards = []
    for box, match in anchors:
        x, y = box[0], box[1]
        below = [other[1] for other, _ in anchors if abs(other[0] - x) <= COLUMN_TOLERANCE and other[1] > y]
        end = min(below, default=10**6)
        lines = _lines_in_column(boxes, x, y + 1, end)

        # The card ends at its "Local Used / Foreign Used" row; location is the line above it.
        used_at = next((i for i, (_, text) in enumerate(lines) if _USED.search(text)), None)
        if used_at is None:
            if stats is not None:
                stats["cut_off"] += 1
            continue  # cut off by a page break
        condition = _USED.search(lines[used_at][1]).group(0).strip()
        body = [text for _, text in lines[:used_at]]
        if not body:
            if stats is not None:
                stats["cut_off"] += 1
            continue
        location = body.pop() if "," in body[-1] and len(body) >= 2 else None
        used_y = lines[used_at][0]
        beside = " ".join(t for b, t in boxes if abs(b[1] - used_y) <= 15 and x + 60 < b[0] < x + 300 and not _USED.search(t))
        transmission = _transmission(beside)
        location = _clean_location(location)

        text = " ".join(body)
        title = body[0]
        if not _ANY_YEAR.search(title) and len(body) > 1 and _ANY_YEAR.search(body[1]) and ":" not in body[1]:
            title = f"{body[0]} {body[1]}"  # the year often wraps onto the second line
        title = _scrub(title)
        make, model, year = _split_title(title)
        reg = re.search(r"registration\D{0,12}" + _YEAR, text, re.I)
        model_year = re.search(r"(?:model\s*)?year\D{0,10}" + _YEAR, text, re.I)
        year = year or (int(model_year.group(1)) if model_year else None)
        price = _digits(match.group(1))
        cards.append(
            {
                "page": page,
                "price_bdt": price,
                "title": title,
                "make": make,
                "model": model,
                "year": year,
                "mileage_km": _mileage(text),
                "engine_cc": _engine(text),
                "condition": "Brand New" if "brand" in condition.lower() else re.sub(r"\s+", " ", condition).title(),
                "transmission": transmission,
                "fuel": _fuel(text),
                "body_type": _body_type(text),
                "location": location,
                "registration_year": int(reg.group(1)) if reg else None,
            }
        )
    return cards


# -- model names ---------------------------------------------------------------

# Words that end a model name: engine and drivetrain text, body styles, colours, packaging.
_NOT_MODEL = set(
    """front rear four two all wheel drive fwd awd rwd 2wd 4wd 2wl 4wl hybrid petrol diesel cng octane ihv package pkg
    black white silver gray grey blue red pearl gold brown green maroon orange beige yellow purple bronze color colour
    sedan hatchback wagon suv sport utility seater seat km limited edition version type turbo plus with new used""".split()
)
# Capitalised words that are trims, not models ("Range Rover Vogue", "Hiace Super GL").
_TRIM_WORDS = set(
    """vogue autobiography leather special super prime dark hardtop executive premium luxury style non package
    exclusive standard advance calligraphy essence flagship push""".split()
)
_MIN_PREFIX_COUNT = 3  # a two-word model name must be seen this often as a stand-alone name


def _model_head(text: str) -> list[str]:
    """The leading words of a raw model string, before engine size, drivetrain, colour or a bracket."""
    text = re.sub(r"(?<=[A-Za-z])(?=\d\.\d)", " ", text)  # 'Axio1.5' -> 'Axio 1.5'
    text = re.sub(r"(?<=\d)(?=(?:19|20)\d\d(?!\d))", " ", text)  # 'Prado2.72020' -> 'Prado 2.7 2020'
    text = re.sub(r"(?<=[A-Za-z0-9])[sx]Drive\d.*$", "", text)  # 'X7xDrive40i' -> 'X7'
    text = re.sub(r"(-Class)(?=[A-Z0-9])", r"\1 ", text)  # 'G-ClassG63' -> 'G-Class G63'
    words = []
    for token in text.replace("(", " ( ").split():
        bare = token.lower().strip(".,-")
        if token == "(" or bare in _NOT_MODEL or (words and re.match(r"\d", token)):
            break
        words.append(token.rstrip(".,") or token)
    if not words and text.split():  # '7 Series', '3 Series': a model that starts with a digit
        words = text.split()[:2] if re.match(r"(?i)series|class", (text.split() + [""])[1]) else text.split()[:1]
    return words


def _is_model_word(word: str) -> bool:
    """A second word that can be part of a model name ('Cross', 'Fielder'), not a trim ('Z', 'EX', 'SUPER')."""
    return len(word) >= 4 and word[0].isupper() and not word.isupper() and not re.search(r"\d", word) and word.lower() not in _TRIM_WORDS


def _after_model(raw: str, model: str) -> str | None:
    """What follows the model in the raw text, matching letters and digits only: 'CorollaCrossS' after 'Corolla Cross' is 'S'."""
    want = re.sub(r"[\s-]", "", model.lower())
    i = taken = 0
    while i < len(raw) and taken < len(want):
        if raw[i].lower() == want[taken]:
            taken += 1
        elif not re.match(r"[\s-]", raw[i]):
            return raw.strip() or None  # the text does not start with the model; keep all of it
        i += 1
    return re.sub(r"\s+", " ", raw[i:]).strip(" -.") or None


def normalize_models(rows: list[dict], known: dict[str, str] | None = None) -> int:
    """Reduce each row's free-text `model` to one model name, keeping the rest as `variant`.

    'Axio1.5 X Two. Wheel Drive' -> model 'Axio', variant '1.5 X Two. Wheel Drive'. A second word is
    kept only when that two-word name is common in the data ('Corolla Cross', 'Land Cruiser Prado'),
    and spellings that differ only in case or spacing ('HiAce', 'Hiace', 'CorollaCross') are merged
    into the most common one. A two-word name the 2021 file lists ('Santa Fe') is kept whatever its count.
    Returns the number of distinct models.
    """
    known = known or {}
    heads = [(row["make"], _model_head(row["model"])) for row in rows]
    seen = defaultdict(int)  # how often each (make, word-prefix) is a complete head on its own
    for make, words in heads:
        for n in range(1, len(words) + 1):
            seen[(make, " ".join(words[:n]).lower())] += 0
        seen[(make, " ".join(words).lower())] += 1
    prefix_total = defaultdict(int)  # ...or the start of a longer one
    for (make, name), count in seen.items():
        for n in range(1, len(name.split()) + 1):
            prefix_total[(make, " ".join(name.split()[:n]))] += count

    chosen = []
    for make, words in heads:
        keep = words[:1]
        for word in words[1:3]:
            candidate = " ".join(keep + [word]).lower()
            series = keep[0][0].isdigit() and word.lower() in ("series", "class")  # '7 Series' is one name
            listed = re.sub(r"[\s-]", "", candidate) in known
            if series or listed or (_is_model_word(word) and prefix_total[(make, candidate)] >= _MIN_PREFIX_COUNT):
                keep.append(word)
            else:
                break
        chosen.append(" ".join(keep))

    # A rare name that starts with a common model plus glued text ('CorollaCrossS', 'Premio20', 'NoahS-Z') is that model.
    common = defaultdict(list)
    for (make, _), name in zip(heads, chosen):
        common[make].append(name)
    frequent = {
        make: sorted((n for n, c in collections.Counter(names).items() if c >= 5), key=len, reverse=True)
        for make, names in common.items()
    }
    own = collections.Counter((make, name) for (make, _), name in zip(heads, chosen))
    for i, ((make, _), name) in enumerate(zip(heads, chosen)):
        if own[(make, name)] >= 5:
            continue  # a common name is a model in its own right: 'Corolla Cross' is not 'Corolla' plus 'Cross'
        squashed = re.sub(r"[\s-]", "", name)
        for known in frequent[make]:
            key = re.sub(r"[\s-]", "", known)
            if len(squashed) > len(key) and squashed.lower().startswith(key.lower()) and not squashed[len(key)].islower():
                chosen[i] = known
                break

    # Merge spellings: the most common surface form of each (make, letters-only key) wins.
    forms = defaultdict(lambda: defaultdict(int))
    for (make, _), name in zip(heads, chosen):
        forms[(make, re.sub(r"[\s-]", "", name.lower()))][name] += 1
    best = {key: max(counts, key=counts.get) for key, counts in forms.items()}
    models = set()
    for row, name in zip(rows, chosen):
        model = best[(row["make"], re.sub(r"[\s-]", "", name.lower()))]
        raw = row["model"]
        row["model_raw"] = raw
        row["model"] = model
        row["variant"] = _after_model(raw, model)
        models.add((row["make"], model))
    return len(models)


# -- price sanity ------------------------------------------------------------


def check_prices(rows: list[dict]) -> dict:
    """Mark prices that are not believable and repair the ones that are plainly off by a factor of 10 or 100.

    Sellers add a zero, OCR doubles a digit, and a few type a phone number in the price box.
    The yardstick is the median price of the same make and model built within three years
    (else the same make within three years, with a looser 8x test). A price more than 4x that median is first tried
    divided by 10 and by 100 and kept only if that lands close to it; otherwise it is excluded.
    A price under a fifth of it is excluded too, since a missing zero cannot be repaired
    reliably. Nothing is silently dropped: every row gets a `price_check` of ok / fixed / excluded.
    """
    for row in rows:
        row["_key"] = (row["make"].lower(), row["model"].lower())
    for row in rows:
        row["_orig"] = row["price_bdt"]
    pool = [r for r in rows if r["_orig"] and MIN_PRICE <= r["_orig"] <= MAX_PRICE]

    def expected(row: dict) -> tuple[float | None, float]:
        """(typical price, how many times above it is suspect). A model's own median is a sharp
        yardstick; the whole make is not (a Land Cruiser is not a Corolla), so it only catches
        an extra zero."""
        if not row["year"]:
            return None, OUTLIER_RATIO
        near = [r for r in pool if r is not row and r["year"] and abs(r["year"] - row["year"]) <= 3]
        same_model = [r["price_bdt"] for r in near if r["_key"] == row["_key"]]
        if len(same_model) >= 4:
            return statistics.median(same_model), OUTLIER_RATIO
        same_make = [r["price_bdt"] for r in near if r["_key"][0] == row["_key"][0]]
        return (statistics.median(same_make), MAKE_OUTLIER_RATIO) if len(same_make) >= 8 else (None, OUTLIER_RATIO)

    # Two passes: the first repairs the obvious extra zeros, the second judges every price again
    # against medians that are no longer dragged up by them.
    for _ in range(2):
        for row in rows:
            price = row["_orig"]
            med, limit = expected(row)
            status, row["price_bdt"] = "ok", price
            row.pop("price_listed_bdt", None)
            if not price or price < MIN_PRICE:
                status = "excluded"
            elif price > MAX_PRICE or (med and price > limit * med):
                fixed = next(
                    (price // d for d in (10, 100, 1000) if MIN_PRICE <= price // d <= MAX_PRICE and med and 0.5 <= price / d / med <= 2),
                    None,
                )
                if fixed:
                    row["price_listed_bdt"], row["price_bdt"], status = price, fixed, "fixed"
                else:
                    status = "excluded"
            elif med and price < med / (limit + 1):
                status = "excluded"
            row["price_check"] = status
        pool = [r for r in rows if r["price_check"] != "excluded"]

    counts = {"ok": 0, "fixed": 0, "excluded": 0}
    for row in rows:
        counts[row["price_check"]] += 1
        del row["_key"], row["_orig"]
    return counts


def parse_ocr(ocr_paths: list[Path], stats: collections.Counter | None = None) -> list[dict]:
    """Every card in the OCR files, each stamped with when its page was printed (UTC)."""
    rows = []
    for source, ocr_path in enumerate(ocr_paths, 1):
        pages = json.loads(ocr_path.read_text(encoding="utf-8"))
        stamps = [_printed_at(boxes) for boxes in pages]
        usual = collections.Counter(t for t in stamps if t).most_common(1)  # a page whose header OCR failed
        for number, (boxes, stamp) in enumerate(zip(pages, stamps), 1):
            observed = stamp or (usual[0][0] if usual else None)
            for card in parse_page(boxes, number, stats):
                rows.append({**card, "source": source, "observed_at": observed.isoformat(timespec="seconds") if observed else None})
    return rows


# -- canonical model names -------------------------------------------------------

SNAPSHOT_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "garirbazar" / "snapshots"

#: Merges that no list would find: one car, several names in the wild. Keys are (make, name without spaces/hyphens, lowercased).
_ALIASES = {
    ("Toyota", "landcruiserprado"): "Prado",
    ("Toyota", "pradotx"): "Prado",
    ("Toyota", "pradotxl"): "Prado",
    ("Toyota", "lcprado"): "Prado",
    ("Toyota", "hiace"): "Hiace",
    ("Toyota", "corollafielder"): "Fielder",
    ("Toyota", "townace"): "TownAce",
    ("Toyota", "liteace"): "LiteAce",
    ("Mercedes-Benz", "e250"): "E250",
    ("Mercedes-Benz", "e200"): "E200",
    ("Mercedes-Benz", "c200"): "C200",
    ("Mercedes-Benz", "c180"): "C180",
}
#: 2021-file names that would undo the aliases above or are not models.
_IGNORED_KNOWN = {"other model", "e 250", "v6", "mpv", "x assista", "h-rv"}


def _squash(name: str) -> str:
    return re.sub(r"[\s-]", "", name.lower())


def _known_names() -> dict[str, str]:
    """squashed name -> spelling, from the 2021 file the model already trains on."""
    try:
        from ..data import clean, load_raw

        names = clean(load_raw())[0]["car_model"].dropna().unique()
    except Exception:  # the 2021 file is optional
        return {}
    return {_squash(n): n for n in names if n.lower() not in _IGNORED_KNOWN and not n.islower()}  # all-lowercase spellings are typing habits


def _garirbazar_names(directory: Path = SNAPSHOT_DIR) -> dict[tuple[str, str], str]:
    """(make, squashed name) -> its commonest properly-cased spelling in the GarirBazar snapshots (seen at least 3 times)."""
    counts: dict[tuple[str, str], collections.Counter] = defaultdict(collections.Counter)
    for path in sorted(directory.glob("*.jsonl")) if directory.exists() else []:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("model"):
                    counts[(row["make"], _squash(row["model"]))][row["model"]] += 1
    out = {}
    for key, spellings in counts.items():
        if sum(spellings.values()) >= 3:
            proper = [(n, sp) for sp, n in spellings.items() if all(w[0].isupper() or w[0].isdigit() for w in re.split(r"[\s-]+", sp) if w)]
            out[key] = max(proper)[1] if proper else ""  # "" = a real name, but only spelled sloppily there: keep ours
    return out


def canonicalize_models(rows: list[dict], known: dict[str, str] | None = None, garirbazar: dict | None = None) -> tuple[dict, collections.Counter]:
    """Give each car the name the model already trains on. Returns (aliases applied, names that matched nothing).

    Order of trust: the explicit aliases, then the 2021 file's spelling, then GarirBazar's. A name found in none of them
    is kept as it is and reported, not guessed at.
    """
    known = _known_names() if known is None else known
    garir = _garirbazar_names() if garirbazar is None else garirbazar
    aliases: dict[str, dict[str, str]] = defaultdict(dict)
    unmapped: collections.Counter = collections.Counter()
    for row in rows:
        make, model = row["make"], row["model"]
        key = _squash(model)
        canonical = _ALIASES.get((make, key)) or known.get(key)
        if canonical is None and (make, key) in garir:
            canonical = garir[(make, key)] or model
            if canonical.lower() == model.lower() and model[0].isupper():
                canonical = model  # GarirBazar only title-cases ('Es', 'Rx'); our 'ES', 'RX' are the right spelling
        if canonical is None:
            unmapped[(make, model)] += 1
            continue
        if canonical != model:
            aliases[make][model] = canonical
            row["model"] = canonical
    return {make: dict(sorted(names.items())) for make, names in sorted(aliases.items())}, unmapped


# -- the clean file ----------------------------------------------------------------

CLEAN_FIELDS = [
    "id", "observed_at", "title", "make", "model", "year", "price_bdt", "mileage_km", "engine_cc", "fuel",
    "transmission", "location", "posted_at", "registration_year", "condition", "body_type", "source", "suspect",
]
MIN_YEAR, MAX_YEAR = 1985, 2026
#: Makes the cards show that are not in the GarirBazar list of brands.
_EXTRA_MAKES = {"Omoda", "DFSK", "BAW", "Jetour", "GWM", "Zeekr", "Geely", "Dongfeng", "SsangYong", "Lincoln", "GMC"}


def _listing_id(row: dict) -> int:
    """No ad id on a printed card, so a stable one from what identifies the car: the same ad always gets the same number."""
    key = "|".join(str(row[k]) for k in ("make", "model", "year", "price_bdt", "location"))
    return int(hashlib.sha1(key.encode("utf-8")).hexdigest()[:15], 16)


def _condition(text: str | None) -> str | None:
    lowered = (text or "").lower()
    return _CONDITIONS.get(lowered) or ("New" if "new" in lowered else "Reconditioned" if "recondition" in lowered else None)


def build_clean(ocr_paths: list[Path], out_dir: Path) -> dict:
    """Write bikroy_clean.jsonl, model_aliases.json and unmapped_models.txt into out_dir; return what was dropped and why."""
    stats: collections.Counter = collections.Counter()
    rows = parse_ocr(ocr_paths, stats)
    report = {"cards_read": len(rows) + stats["cut_off"], "dropped": {"cut_off_card": stats["cut_off"]}}
    dropped = report["dropped"]
    for reason in ("no_title_or_location", "unrecognised_make", "no_model", "no_price", "price_out_of_range", "year_out_of_range", "repeat_sighting"):
        dropped[reason] = 0

    known = _known_names()
    normalize_models(rows, known)
    makes = set(KNOWN_MAKES) | _EXTRA_MAKES

    kept = []
    for row in rows:
        if not row["title"] or not row["location"]:
            dropped["no_title_or_location"] += 1
        elif row["make"] not in makes:
            dropped["unrecognised_make"] += 1
        elif not row["model"] or row["model"].lower() in _NOT_MODEL:  # a colour or drivetrain word read as the model
            dropped["no_model"] += 1
        elif not row["price_bdt"]:
            dropped["no_price"] += 1
        elif not MIN_PRICE <= row["price_bdt"] <= MAX_PRICE:
            dropped["price_out_of_range"] += 1
        elif row["year"] is not None and not MIN_YEAR <= row["year"] <= MAX_YEAR:
            dropped["year_out_of_range"] += 1
        else:
            kept.append(row)

    aliases, unmapped = canonicalize_models(kept, known)
    for row in kept:
        row["id"] = _listing_id(row)  # after the model name is final, so the same ad always hashes the same

    latest: dict[int, dict] = {}
    for row in kept:  # the latest sighting of each ad wins
        earlier = latest.get(row["id"])
        if earlier is None or (row["observed_at"] or "") >= (earlier["observed_at"] or ""):
            latest[row["id"]] = row
    dropped["repeat_sighting"] = len(kept) - len(latest)
    rows = list(latest.values())

    # Prices are never edited. A slip of a zero is flagged, and the number stays as the seller wrote it.
    check_prices(rows)
    for row in rows:
        if "price_listed_bdt" in row:
            row["price_bdt"] = row["price_listed_bdt"]
        row["suspect"] = row["price_check"] != "ok"
        row["condition"] = _condition(row["condition"])
        row["source"] = "bikroy"
        row["posted_at"] = None  # printed cards show no posting time
        if row["engine_cc"] is not None and not 500 <= row["engine_cc"] <= 9000:
            row["engine_cc"] = None

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "bikroy_clean.jsonl").write_text(
        "".join(json.dumps({k: r[k] for k in CLEAN_FIELDS}, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    (out_dir / "model_aliases.json").write_text(json.dumps(aliases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "unmapped_models.txt").write_text(
        "".join(f"{n}\t{make}\t{model}\n" for (make, model), n in sorted(unmapped.items(), key=lambda kv: (-kv[1], kv[0]))), encoding="utf-8"
    )
    report.update(rows=rows, aliases=sum(len(v) for v in aliases.values()), unmapped=len(unmapped))
    return report


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    out_dir = Path(__file__).resolve().parents[3] / "data" / "raw" / "bikroy"
    paths = [Path(a) for a in (argv if argv is not None else sys.argv[1:])] or sorted(out_dir.glob("ocr*.json"))
    if not paths:
        print("usage: python -I -m shotti_ml.collect.bikroy_pdf [OCR.json ...]   (default: data/raw/bikroy/ocr*.json)")
        return 2
    report = build_clean(paths, out_dir)
    rows = report.pop("rows")
    print(json.dumps({**report, "rows_written": len(rows), "suspect": sum(r["suspect"] for r in rows)}, indent=2))
    print(f"Wrote {out_dir / 'bikroy_clean.jsonl'}")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
