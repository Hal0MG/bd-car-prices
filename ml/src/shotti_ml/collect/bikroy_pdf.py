"""Read Bikroy car cards from a print-to-PDF of its listing pages, after OCR.

Bikroy sits behind a Cloudflare challenge, so nothing here touches the site. The input is
pages the user saved from their own browser, run through scripts/ocr_pdf.py, which writes
one list of (box, text) pairs per page. Cards are rebuilt from the position of each price
("BDT 27,50,000"): the card is the column of text under it.

As with the GarirBazar reader, only car attributes are kept. The description is read for
year, mileage and engine size and then dropped, because sellers put phone numbers in it.

Printed pages cut cards at page breaks and clip the right-hand column, so some cards come
out without a title or location; those are dropped rather than guessed at.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from .garirbazar import KNOWN_MAKES, canonical_model, parse_engine_cc, split_title

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
    return make, _ANY_YEAR.split(model)[0].strip(), year


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


def _lines_in_column(boxes: list, x: int, top: int, bottom: int) -> list[tuple[int, str]]:
    return sorted(
        (box[1], text)
        for box, text in boxes
        if abs(box[0] - x) <= COLUMN_TOLERANCE and top <= box[1] < bottom
    )


def parse_page(boxes: list, page: int) -> list[dict]:
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
            continue  # cut off by a page break
        condition = _USED.search(lines[used_at][1]).group(0).strip()
        body = [text for _, text in lines[:used_at]]
        if not body:
            continue
        location = body.pop() if "," in body[-1] and len(body) >= 2 else None
        used_y = lines[used_at][0]
        beside = " ".join(t for b, t in boxes if abs(b[1] - used_y) <= 15 and x + 60 < b[0] < x + 300 and not _USED.search(t))
        transmission = _transmission(beside)
        location = _clean_location(location)

        text = " ".join(body)
        title = body[0] if body else ""
        if not _ANY_YEAR.search(title) and len(body) > 1:
            title = f"{body[0]} {body[1]}"  # the year often wraps onto the second line
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
                "location": location,
                "registration_year": int(reg.group(1)) if reg else None,
            }
        )
    return cards


# -- price sanity ------------------------------------------------------------


def check_prices(rows: list[dict], known_models: list[str] | None = None) -> dict:
    """Mark prices that are not believable and repair the ones that are plainly off by a factor of 10 or 100.

    Sellers add a zero, OCR doubles a digit, and a few type a phone number in the price box.
    The yardstick is the median price of the same make and model built within three years
    (else the same make within three years, with a looser 8x test). A price more than 4x that median is first tried
    divided by 10 and by 100 and kept only if that lands close to it; otherwise it is excluded.
    A price under a fifth of it is excluded too, since a missing zero cannot be repaired
    reliably. Nothing is silently dropped: every row gets a `price_check` of ok / fixed / excluded.
    """
    known = known_models or []
    for row in rows:
        row["_key"] = (row["make"].lower(), canonical_model(row["model"], known).lower())
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


def parse_ocr(ocr_paths: list[Path]) -> list[dict]:
    rows = []
    for source, ocr_path in enumerate(ocr_paths, 1):
        pages = json.loads(ocr_path.read_text(encoding="utf-8"))
        rows += [{**card, "source": source} for number, boxes in enumerate(pages, 1) for card in parse_page(boxes, number)]
    # A card cut by a page break, or listed in two print-outs, can appear twice; keep one per (title, price, location).
    seen, unique = set(), []
    for row in rows:
        key = (row["title"], row["price_bdt"], row["location"])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique


def _known_models() -> list[str]:
    """Model names from the 2021 file, so 'Land Cruiser Prado' is one model and not 'Land'."""
    try:
        from ..data import clean, load_raw

        return sorted(clean(load_raw())[0]["car_model"].dropna().unique())
    except Exception:  # the file is optional; fall back to first words
        return []


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print("usage: python -I -m shotti_ml.collect.bikroy_pdf OCR.json [OCR.json ...] OUT.jsonl")
        return 2
    rows = parse_ocr([Path(a) for a in args[:-1]])
    counts = check_prices(rows, _known_models())
    Path(args[-1]).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows)} cards; prices {counts}")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
