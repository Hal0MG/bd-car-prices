from shotti_ml.collect.bikroy_pdf import _clean_location, _split_title, _transmission, check_prices, parse_page


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
