import json
import re
from pathlib import Path

import pytest

from shotti_ml.collect.bikroy_pdf import CLEAN_FIELDS, build_clean
from shotti_ml.collect.bikroy_pdf import _clean_location, _split_title, _transmission, check_prices, normalize_models, parse_page


def box(x, y, text):
    return [x, y, x + 100, y + 20], text


def card(x, y, price, title, location="Dhaka, Gulshan", condition="Local Used", transmission="Autom"):
    return [
        box(x, y, price),
        box(x, y + 40, title),
        box(x, y + 80, "Brand: Toyota Registration 2019 Mileage 56k 1500CC"),
        box(x, y + 120, location),
        box(x, y + 150, condition),
        box(x + 190, y + 150, transmission),
    ]


def row(title, price, year, make="Toyota", model="Allion"):
    return {"title": title, "price_bdt": price, "year": year, "make": make, "model": model}


def test_parse_page_reads_a_card():
    [c] = parse_page(card(455, 400, "BDT 27,50,000", "Toyota C-HR 2018"), page=3)
    assert (c["price_bdt"], c["make"], c["model"], c["year"]) == (2_750_000, "Toyota", "C-HR", 2018)
    assert (c["location"], c["condition"], c["transmission"]) == ("Dhaka, Gulshan", "Local Used", "Automatic")
    assert (c["mileage_km"], c["registration_year"]) == (56_000, 2019)


def test_parse_page_keeps_columns_apart_and_drops_cut_cards():
    boxes = card(455, 400, "BDT 19,80,000", "Toyota Aqua 2021") + card(735, 400, "BDT 36,50,000", "Honda Insight 2021")
    boxes += [box(1000, 400, "BDT 15,30,000"), box(1000, 440, "Toyota Allion 2012")]  # page ends before the card does
    assert sorted(c["model"] for c in parse_page(boxes, page=1)) == ["Aqua", "Insight"]


def test_the_description_is_not_kept():
    [c] = parse_page(card(455, 400, "BDT 19,80,000", "Toyota Aqua 2021", ), page=1)
    assert "Registration" not in str(c)


def test_glued_ocr_text():
    assert _split_title("HondaVezel2021Pearl")[0:3:2] == ("Honda", 2021)
    assert _split_title("NewMercedes-BenzG-ClassG63AMG 2024")[0] == "Mercedes-Benz"
    assert _split_title("LandRoverRangeRover Vogue 2025")[:2] == ("Land Rover", "RangeRover Vogue")
    assert _split_title("New Toyota Hilux 3.0 2012White")[2] == 2012


def test_location_and_transmission_cleanup():
    assert _clean_location("oDhaka, Banani") == "Dhaka, Banani"
    assert _clean_location("。Dhaka, Banani") == "Dhaka, Banani"
    assert _clean_location("Chattogram, Agrabad") == "Chattogram, Agrabad"
    assert [_transmission(t) for t in ("Autom", "Autc", "CVT", "Manual", "")] == ["Automatic", "Automatic", "CVT", "Manual", None]


def test_extra_zero_is_repaired():
    rows = [row(f"Toyota Allion {2010 + i}", 2_000_000 + i * 50_000, 2010 + i) for i in range(5)]
    rows.append(row("Toyota Allion 2012", 21_500_000, 2012))  # a zero too many
    check_prices(rows)
    assert (rows[-1]["price_check"], rows[-1]["price_bdt"], rows[-1]["price_listed_bdt"]) == ("fixed", 2_150_000, 21_500_000)
    assert all(r["price_check"] == "ok" for r in rows[:-1])


def test_unrepairable_prices_are_excluded_not_guessed():
    rows = [row(f"Toyota Allion {2010 + i}", 2_000_000 + i * 50_000, 2010 + i) for i in range(5)]
    rows += [row("Toyota Allion 2012", 9_000_000, 2012), row("Toyota Allion 2012", 50_000, 2012)]
    check_prices(rows)
    assert [r["price_check"] for r in rows[-2:]] == ["excluded", "excluded"]


def test_rare_expensive_models_are_not_mistaken_for_typos():
    rows = [row(f"Toyota Corolla {2015 + i % 4}", 1_800_000 + i * 20_000, 2015 + i % 4, model="Corolla") for i in range(12)]
    rows.append(row("Toyota Land Cruiser 2015", 13_900_000, 2015, model="Land Cruiser"))  # a genuine 1.39 crore
    check_prices(rows)
    assert rows[-1]["price_check"] == "ok" and rows[-1]["price_bdt"] == 13_900_000


def test_a_misleading_median_does_not_condemn_correct_prices():
    # Three of five Allions carry an extra zero, which drags the median up; the correct two must survive.
    rows = [row("Toyota Allion 2010", 20_000_000, 2010), row("Toyota Allion 2011", 22_000_000, 2011), row("Toyota Allion 2012", 22_500_000, 2012)]
    rows += [row("Toyota Allion 2012", 2_150_000, 2012), row("Toyota Allion 2013", 2_300_000, 2013), row("Toyota Allion 2014", 2_400_000, 2014)]
    check_prices(rows)
    assert [r["price_bdt"] for r in rows] == [2_000_000, 2_200_000, 2_250_000, 2_150_000, 2_300_000, 2_400_000]


def test_range_rover_is_a_land_rover_model():
    assert _split_title("Range Rover Vogue 2025 Black")[:2] == ("Land Rover", "Range Rover Vogue")
    assert _split_title("Land Rover Range Rover Vogue 2025")[:2] == ("Land Rover", "Range Rover Vogue")


def test_models_are_reduced_to_a_name_and_a_variant():
    raws = [
        ("Toyota", "Axio1.5 X Two. Wheel Drive"), ("Toyota", "Axio 1.5 G 2 WD"), ("Toyota", "Axio G BEIGE 19000 KM"),
        ("Toyota", "Corolla Cross Z"), ("Toyota", "Corolla Cross 1.8 Hybrid"), ("Toyota", "CorollaCross"),
        ("Toyota", "Corolla Cross"), ("Toyota", "Corolla Cross"), ("Toyota", "Corolla Cross"), ("Toyota", "CorollaCrossS Package"),
        ("Toyota", "Noah S-Z"), ("Toyota", "Noah"), ("Toyota", "Noah 2.0 All- Wheel Drive (8 Seater)"),
        ("Toyota", "Noah"), ("Toyota", "Noah"), ("Toyota", "Noah"),
        ("Mercedes-Benz", "GLS-Class GLS 400d"), ("BMW", "7 Series 730Ld"),
    ]
    rows = [{"make": make, "model": model} for make, model in raws]
    normalize_models(rows)
    assert [r["model"] for r in rows] == [
        "Axio", "Axio", "Axio", *["Corolla Cross"] * 7,
        "Noah", "Noah", "Noah", "Noah", "Noah", "Noah", "GLS-Class", "7 Series",
    ]
    assert rows[0]["variant"] == "1.5 X Two. Wheel Drive" and rows[2]["variant"] == "G BEIGE 19000 KM"
    assert rows[9]["variant"] == "S Package" and rows[3]["variant"] == "Z"
    assert rows[0]["model_raw"] == "Axio1.5 X Two. Wheel Drive"


def test_a_common_two_word_model_is_not_collapsed_into_its_first_word():
    raws = [("Toyota", "Corolla Cross")] * 6 + [("Toyota", "Corolla")] * 6 + [("Toyota", "Land Cruiser Prado")] * 5 + [("Toyota", "Land Cruiser")] * 5
    rows = [{"make": make, "model": model} for make, model in raws]
    normalize_models(rows)
    assert {r["model"] for r in rows} == {"Corolla Cross", "Corolla", "Land Cruiser Prado", "Land Cruiser"}


# -- the clean file ----------------------------------------------------------------

PHONE, EMAIL = "01712345678", "seller@example.com"
STAMP = box(51, 32, "10/28/26, 1:27 PM")


def page(*cards):
    return [STAMP] + [b for c in cards for b in c]


def allion_page(i, price, year, place):
    return page(card(455, 400, f"BDT {price:,}", f"Toyota Allion {year} White", location=place))


def write_ocr(tmp_path, pages):
    path = tmp_path / "ocr.json"
    path.write_text(json.dumps(pages), encoding="utf-8")
    return path


def string_values(row):
    return [v for v in row.values() if isinstance(v, str)]


def leaks(rows):
    """Digit runs of 8+ in any text field (prices and ids are numbers, not text), or an '@' anywhere."""
    return [v for row in rows for v in string_values(row) if re.search(r"\d{8,}|@", v)]


def test_clean_file_has_the_agreed_fields_and_never_edits_a_price(tmp_path):
    pages = [allion_page(i, 2_000_000 + i * 50_000, 2010 + i, f"Dhaka, Area{i}") for i in range(5)]
    pages.append(allion_page(9, 21_500_000, 2012, "Dhaka, Mirpur"))  # one zero too many
    report = build_clean([write_ocr(tmp_path, pages)], tmp_path / "out")
    rows = [json.loads(line) for line in (tmp_path / "out" / "bikroy_clean.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 6 and all(list(r) == CLEAN_FIELDS for r in rows)
    slip = next(r for r in rows if r["location"] == "Dhaka, Mirpur")
    assert (slip["price_bdt"], slip["suspect"]) == (21_500_000, True)  # flagged, number untouched
    assert not any(r["suspect"] for r in rows if r is not slip)
    first = rows[0]
    assert (first["make"], first["model"], first["source"], first["condition"], first["transmission"]) == ("Toyota", "Allion", "bikroy", "Used", "Automatic")
    assert first["observed_at"].startswith("2026-10-28T") and first["posted_at"] is None
    assert isinstance(first["id"], int) and first["id"] > 0 and len({r["id"] for r in rows}) == 6
    assert report["dropped"]["repeat_sighting"] == 0


def test_phone_numbers_and_emails_never_reach_the_file(tmp_path):
    wrapped = [box(455, 400, "BDT 19,80,000"), box(455, 440, "Toyota Allion"), box(455, 470, f"2012 {PHONE} {EMAIL}"),
               box(455, 520, f"Call {PHONE} or {EMAIL} Registration 2019"), box(455, 560, "Dhaka, Gulshan"), box(455, 590, "Foreign Used")]
    build_clean([write_ocr(tmp_path, [page(wrapped)])], tmp_path / "out")
    text = (tmp_path / "out" / "bikroy_clean.jsonl").read_text(encoding="utf-8")
    assert PHONE not in text and "@" not in text
    rows = [json.loads(line) for line in text.splitlines()]
    assert rows and not leaks(rows) and rows[0]["condition"] == "Reconditioned"


def test_repeat_sightings_keep_the_latest_and_bad_rows_are_counted(tmp_path):
    early = page(card(455, 400, "BDT 19,80,000", "Toyota Aqua 2021"))
    late = [box(51, 32, "10/28/26, 1:47 PM")] + card(455, 400, "BDT 19,80,000", "Toyota Aqua 2021")
    old_car = page(card(455, 400, "BDT 19,80,000", "Toyota Crown 1970"))
    cut_off = page([box(455, 400, "BDT 15,30,000"), box(455, 440, "Toyota Allion 2012")])
    tiny = page(card(455, 400, "BDT 50,000", "Toyota Aqua 2019", location="Dhaka, Uttara"))
    a, b = write_ocr(tmp_path, [early, old_car, cut_off, tiny]), tmp_path / "ocr2.json"
    b.write_text(json.dumps([late]), encoding="utf-8")
    report = build_clean([a, b], tmp_path / "out")
    rows = [json.loads(line) for line in (tmp_path / "out" / "bikroy_clean.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["observed_at"][11:16] for r in rows] == ["18:47"]  # 1:47 PM is the later print
    dropped = report["dropped"]
    assert (dropped["repeat_sighting"], dropped["year_out_of_range"], dropped["price_out_of_range"], dropped["cut_off_card"]) == (1, 1, 1, 1)


def test_fuel_and_body_type_only_when_the_card_says_so():
    from shotti_ml.collect.bikroy_pdf import _body_type, _fuel

    assert _fuel("Harrier non-hybrid pearl") is None and _fuel("Prius Hybrid 1.8") == "Hybrid"
    assert _fuel("Land Cruiser V8 DSL") == "Diesel" and _fuel("Axio Octane 2013") == "Octane"
    assert _body_type("C-HR XLE FWD Sport Utility (2.0 L)") == "SUV" and _body_type("Suzuki WagonR 2019") is None
    assert _body_type("Premio sedan, nice wagon feel") == "Sedan"


CLEAN_FILE = Path(__file__).resolve().parents[1] / "data" / "raw" / "bikroy" / "bikroy_clean.jsonl"


@pytest.mark.skipif(not CLEAN_FILE.exists(), reason="no collected Bikroy file on this machine")
def test_the_real_clean_file_holds_no_phone_numbers_or_emails():
    text = CLEAN_FILE.read_text(encoding="utf-8")
    assert "@" not in text
    rows = [json.loads(line) for line in text.splitlines()]
    assert not leaks(rows), leaks(rows)[:3]
    assert all(list(r) == CLEAN_FIELDS for r in rows)
    assert all(r["price_bdt"] and 100_000 <= r["price_bdt"] <= 300_000_000 for r in rows)
    assert all(r["year"] is None or 1985 <= r["year"] <= 2026 for r in rows)
    assert all(r["engine_cc"] is None or 500 <= r["engine_cc"] <= 9000 for r in rows)
    assert len({r["id"] for r in rows}) == len(rows)
