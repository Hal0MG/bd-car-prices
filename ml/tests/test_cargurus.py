import json

from shotti_ml import abroad_store as store
from shotti_ml.collect import cargurus as cg
from shotti_ml.run_abroad_uk import TARGETS, Target, matches
from shotti_ml.export import catalogue


def tile(year, trim, price, kind="LISTING_USED_STANDARD"):
    return {"type": kind, "data": {
        "listingTitle": f"{year} BMW 3 Series", "vin": "SECRET", "mileage": {"value": 12000, "unit": "MILES"},
        "ontologyDto": {"carYear": str(year), "trimName": trim}, "priceDto": {"current": price},
        "sellerDto": {"phoneNumber": "+44 1234"},
    }}


PAGE = (
    '<script>{"filters":[{"name":"m256","label":"BMW"},{"name":"m256/d2887","label":"3 Series"}],'
    '"pageCount":10,"tiles":' + json.dumps([
        tile(2022, "330e M Sport 5dr Step Auto", 24995),
        {"type": "AD", "data": {}},
        tile(2022, "320i M Sport 4dr Step Auto", 21000),
        tile(2022, "M340i xDrive 4dr Step Auto", 0),
    ]) + "}</script>"
)


def test_reads_priced_listings_and_drops_seller_details():
    cars, pages = cg.parse_page(PAGE)
    assert pages == 10
    assert cars == [
        cg.Listing("2022 BMW 3 Series", "330e M Sport 5dr Step Auto", 2022, 12000, 24995),
        cg.Listing("2022 BMW 3 Series", "320i M Sport 4dr Step Auto", 2022, 12000, 21000),
    ]
    assert "SECRET" not in repr(cars) and "+44" not in repr(cars)


def test_ids_and_urls():
    assert cg.make_ids(PAGE) == {"BMW": "m256"}
    assert cg.model_ids(PAGE, "m256") == {"3 Series": "d2887"}
    assert cg.search_url("BMW", "3 Series", "d2887", 2022, "phev", 2) == (
        "https://www.cargurus.co.uk/Cars/l-Used-BMW-3-Series-d2887?startYear=2022&endYear=2022&distance=1000&fuelTypes=HYBRID&page=2"
    )


def test_trim_patterns():
    phev, petrol = cg.parse_page(PAGE)[0]
    assert matches(phev, 2022, TARGETS[("BMW", "330e")])
    assert not matches(petrol, 2022, TARGETS[("BMW", "330e")])
    assert not matches(phev, 2023, TARGETS[("BMW", "330e")])
    assert not matches(phev, 2022, Target("BMW", "3 Series", r"330E", r"M SPORT"))


def test_every_target_is_a_uk_catalogue_car():
    names = {(m, n) for m, n, *_ in catalogue()}
    assert [k for k in TARGETS if k not in names] == []


def test_catalogue_prices_round_in_their_own_currency():
    assert store.in_catalogue_currency({"source": "cargurus", "currency": "GBP"}, 24_949) == 24_900
    yen = store.in_catalogue_currency({"source": "sbt", "currency": "USD"}, 10_000)
    assert yen % 10_000 == 0 and abs(yen - 10_000 * store.rate("USD") / store.rate("JPY")) <= 5_000


def test_save_replaces_only_the_cars_searched(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "OUT", tmp_path / "abroad.json")
    row = lambda model, median: {"make": "BMW", "model": model, "year": 2022, "n": 9, "median": median, "p10": median, "p90": median}
    store.save("cargurus", "GBP", [row("330e", 25_000), row("530e", 30_000)], {("BMW", "330e"), ("BMW", "530e")})
    store.save("sbt", "USD", [{**row("Aqua", 11_000), "make": "Toyota"}], {("Toyota", "Aqua")})
    added = store.save("cargurus", "GBP", [row("330e", 26_000)], {("BMW", "330e")})
    prices = {(p["source"], p["model"]): p["median"] for p in store.load()["prices"]}
    assert prices == {("cargurus", "330e"): 26_000, ("cargurus", "530e"): 30_000, ("sbt", "Aqua"): 11_000}
    assert added[0]["source"] == "cargurus" and added[0]["currency"] == "GBP"
