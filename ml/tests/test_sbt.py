from shotti_ml.collect.sbt import Listing, fuel_matches, page_url, parse_page
from shotti_ml.abroad_store import summarise
from shotti_ml.run_abroad import TARGETS, Target, catalogue, matches


def car(title, km, code, fuel, cc, built, price):
    made = f"<span>Manufacture:</span><span>{built}</span>" if built else "<span>Manufacture:</span>"
    reg = f"{built}/3" if built else "2023"
    engine = f"<p>{cc}cc</p>" if cc else "<p>-</p>"
    return (
        f"<div><h2>{reg} {title} </h2><p>{km}km</p><p>Mileage</p><p>{code}</p><p>Model Code</p><p>AT</p><p>Transmission</p>"
        f"<p>{fuel}</p><p>Fuel Type</p><p>2WD</p><p>Drive</p>{engine}<p>Engine</p>{made}"
        f"<p>Vehicle Price</p><p>USD</p><p>{price}</p><p>Total Price</p></div>"
    )


PAGE = (
    "<p>4</p><p>Results</p>"
    + car("TOYOTA HARRIER G", "73,000", "MXUA80", "PETROL", "1,986", 2022, "17,080")
    # reserved: no price, so it must not borrow the next car's
    + car("TOYOTA HARRIER Z", "51,000", "MXUA80", "PETROL", "2,000", 2022, "Ask").replace("<p>USD</p><p>Ask</p>", "<p>Ask</p>")
    + car("TOYOTA HARRIER HYBRID", "20,000", "AXUH80", "HYBRID(PETROL)", "2,487", None, "25,000")
    + car("NISSAN LEAF X", "9,000", "ZE1", "ELECTRIC", None, 2022, "12,000")
)


def harrier_target(*codes, **kw):
    return Target("toyota", "harrier", codes, **kw)


def test_reads_each_priced_car_once():
    cars, total = parse_page(PAGE)
    assert total == 4
    assert [(c.title, c.fob_usd) for c in cars] == [("TOYOTA HARRIER G", 17080), ("TOYOTA HARRIER HYBRID", 25000), ("NISSAN LEAF X", 12000)]
    assert cars[0] == Listing("TOYOTA HARRIER G", "MXUA80", "PETROL", 1986, 73000, 2022, 2022, 17080)


def test_partner_stock_has_no_build_year_and_evs_no_engine():
    cars = parse_page(PAGE)[0]
    assert cars[1].built is None
    assert cars[2].cc is None


def test_matches_needs_year_engine_and_code():
    harrier = parse_page(PAGE)[0][0]
    assert matches(harrier, 2022, 1986, "petrol", harrier_target("MXUA8"))
    assert not matches(harrier, 2023, 1986, "petrol", harrier_target("MXUA8"))
    assert not matches(harrier, 2022, 2487, "petrol", harrier_target("MXUA8"))
    assert not matches(harrier, 2022, 1986, "petrol", harrier_target("AXUH8"))


def test_partner_stock_uses_the_registration_year():
    hybrid = parse_page(PAGE)[0][1]
    assert matches(hybrid, 2023, 2487, "hybrid", harrier_target("AXUH8"))
    assert not matches(hybrid, 2022, 2487, "hybrid", harrier_target("AXUH8"))


def test_matches_on_fuel_and_title_words_without_codes():
    harrier, _, leaf = parse_page(PAGE)[0]
    assert matches(harrier, 2022, 1986, "petrol", harrier_target())
    assert not matches(harrier, 2022, 1986, "hybrid", harrier_target())
    assert matches(harrier, 2022, 1986, "petrol", harrier_target(has="G"))
    assert not matches(harrier, 2022, 1986, "petrol", harrier_target(without=("HARRIER G",)))
    assert matches(leaf, 2022, 0, "ev", Target("nissan", "leaf"))


def test_fuel_labels():
    assert fuel_matches("PLUG-IN HYBRID(PETROL)", "phev")
    assert not fuel_matches("PLUG-IN HYBRID(PETROL)", "hybrid")
    assert fuel_matches("HYBRID(PETROL)", "hybrid")
    assert not fuel_matches("HYBRID(PETROL)", "petrol")


def test_every_target_is_a_catalogue_car():
    assert [k for k in TARGETS if k not in catalogue()] == []


def test_summary_and_url():
    assert summarise([10_000, 20_000, 30_000])["median"] == 20_000
    assert page_url("toyota", "harrier", 2022, 2023, 2).endswith("harrier?year__from=2022&year__to=2023&show_numbers=100&page=2")
