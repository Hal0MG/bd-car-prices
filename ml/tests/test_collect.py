import json
import random
import urllib.error
from datetime import datetime, timedelta, timezone

import pytest

from shotti_ml.collect.fetch import Disallowed, FetchError, Halt, PoliteFetcher
from shotti_ml.collect.garirbazar import (
    canonical_model,
    parse_engine_cc,
    parse_listing_page,
    parse_posted,
    split_title,
    total_pages,
)

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


def card(
    ad_id=91610,
    title="2005 Toyota Allion 2005",
    price="1,550,000",
    mileage="180,000 km",
    engine="N/A",
    fuel="CNG",
    transmission="Automatic",
    location="Dhaka",
    posted="Posted about 17 hours ago",
    description="Registration 2010, Personal Use. Call +8801700000000 or mail seller@example.com",
):
    """A listing card shaped like the real ones, with made-up content."""
    # Real cards show the word NEGOTIABLE instead of a number when the seller gives no price.
    price_html = (
        f'<div class="ad-vehicle-price"><div class="title">Price</div><div class="value"><span class="price-wrap ">BDT <span class="price">{price}</span></span></div></div>'
        if price
        else '<div class="ad-vehicle-price"><div class="title">Price</div><div class="value">NEGOTIABLE</div></div>'
    )
    mileage_html = f'<div class="ad-vehicle-mileage"><div class="title" title="Mileage">Mileage<div class="value">{mileage}</div></div></div>' if mileage else ""
    return (
        f'<a class="common-ad-card " target="_blank" href="/en/vehicle_listings/ad-x-{ad_id}">'
        '<div class="ad-image gb"><img alt="x" src="data:image/gif;base64,AAAA"/></div>'
        f'<div class="ad-specification"><div class="specification-section"><div class="_ad-title"><h4 title="{title}">{title}</h4>'
        f'<div class="location"><i class="fa fa-map-marker"></i>{location}</div></div></div>'
        f'<div class="specification-section xl-wrapper"><div class="wrapper">{price_html}{mileage_html}</div>'
        f'<div class="ad-vehicle-engine"><div class="engine-capacity"><img src="engine.svg" alt="Engine xs"/><span>{engine}</span><span> ({fuel})</span></div>'
        f'<div class="transmission"><img src="gear.svg" alt="Transmission xs"/><span>{transmission}</span></div></div></div>'
        f'<div class="specification-section"><div class="md-hidden sort-ad-description">{description}</div>'
        f'<div class="ad-post-date"><i class="fa fa-clock-o"></i><span>{posted}</span></div></div></div></a>'
    )


def page(*cards, count="41,646"):
    return f'<h1 class="count-cars">{count} vehicles for sale in Bangladesh</h1><div id="ads-list">{"".join(cards)}</div>'


# -- the parser ---------------------------------------------------------------


def test_a_card_becomes_a_listing():
    [listing] = parse_listing_page(page(card()), NOW)
    assert (listing.id, listing.make, listing.model, listing.year) == (91610, "Toyota", "Allion", 2005)
    assert (listing.price_bdt, listing.mileage_km, listing.engine_cc) == (1_550_000, 180_000, None)
    assert (listing.fuel, listing.transmission, listing.location) == ("CNG", "Automatic", "Dhaka")
    assert listing.registration_year == 2010


def test_nothing_personal_survives_parsing():
    [listing] = parse_listing_page(page(card()), NOW)
    stored = json.dumps(listing.as_dict())
    assert "+880" not in stored and "@" not in stored and "Personal Use" not in stored


def test_litres_become_cc():
    [listing] = parse_listing_page(page(card(engine="2.5 L", fuel="Petrol")), NOW)
    assert listing.engine_cc == 2500


def test_posted_time_is_counted_back_from_when_the_page_was_fetched():
    [listing] = parse_listing_page(page(card()), NOW)
    assert datetime.fromisoformat(listing.posted_at) == NOW - timedelta(hours=17)


def test_the_icon_in_front_of_engine_and_gearbox_does_not_hide_them():
    [listing] = parse_listing_page(page(card(engine="1.5 L", fuel="Hybrid", transmission="Manual")), NOW)
    assert (listing.engine_cc, listing.fuel, listing.transmission) == (1500, "Hybrid", "Manual")


def test_negotiable_prices_and_missing_mileage_come_out_empty_not_wrong():
    [listing] = parse_listing_page(page(card(price=None, mileage=None)), NOW)
    assert listing.price_bdt is None and listing.mileage_km is None
    assert listing.make == "Toyota"  # the rest of the card is still read


def test_a_card_without_an_id_is_skipped():
    broken = card().replace("/en/vehicle_listings/ad-x-91610", "/en/vehicle_listings/ad-x")
    assert parse_listing_page(page(broken), NOW) == []


def test_every_card_on_the_page_is_read():
    cards = [card(ad_id=i, title=f"2015 Honda Fit {i}") for i in range(1, 21)]
    assert len(parse_listing_page(page(*cards), NOW)) == 20


def test_page_count_comes_from_the_heading():
    assert total_pages(page(count="41,646")) == 2083
    assert total_pages("<html></html>") is None


@pytest.mark.parametrize(
    "text, cc",
    [("2.5 L", 2500), ("1,500 CC", 1500), ("1.8 litre", 1800), ("N/A", None), ("0.1 L", None), (None, None)],
)
def test_engine_sizes(text, cc):
    assert parse_engine_cc(text) == cc


@pytest.mark.parametrize(
    "text, delta",
    [
        ("Posted 7 minutes ago", timedelta(minutes=7)),
        ("Posted about 1 hour ago", timedelta(hours=1)),
        ("Posted an hour ago", timedelta(hours=1)),
        ("Posted 3 days ago", timedelta(days=3)),
        ("Posted about 1 month ago", timedelta(days=30)),
        ("Posted less than a minute ago", timedelta(0)),
    ],
)
def test_posted_times(text, delta):
    assert parse_posted(text, NOW) == NOW - delta


def test_unreadable_posted_text_gives_none():
    assert parse_posted("Posted whenever", NOW) is None


@pytest.mark.parametrize(
    "title, expected",
    [
        ("2005 Toyota Allion 2005", ("Toyota", "Allion", 2005)),
        ("2019 Mercedes Benz C 200", ("Mercedes-Benz", "C 200", 2019)),
        ("Land Rover Range Rover Evoque 2018", ("Land Rover", "Range Rover Evoque", 2018)),
        ("2012 Foo Bar", ("Foo", "Bar", 2012)),
    ],
)
def test_titles_split_into_make_model_and_year(title, expected):
    assert split_title(title) == expected


def test_models_reduce_to_a_known_name():
    known = ["Axio", "Land Cruiser", "Land Cruiser Prado"]
    assert canonical_model("Axio X package", known) == "Axio"
    assert canonical_model("Land Cruiser Prado TX", known) == "Land Cruiser Prado"
    assert canonical_model("Mystery GT", known) == "Mystery"


# -- the polite fetcher -------------------------------------------------------


class Response:
    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body.encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(url, code, headers=None):
    return urllib.error.HTTPError(url, code, "error", headers or {}, None)


def fetcher(routes, **options):
    """A fetcher on a fake network and clock. `routes` maps URL to a body, an exception or a callable."""
    seen = {"sleeps": [], "urls": []}
    clock = [0.0]

    def sleep(seconds):
        seen["sleeps"].append(seconds)
        clock[0] += seconds

    def opener(request, timeout):
        url = request.full_url
        seen["urls"].append(url)
        result = routes.get(url, http_error(url, 404))
        result = result() if callable(result) else result
        if isinstance(result, Exception):
            raise result
        return Response(result)

    f = PoliteFetcher(opener=opener, sleep=sleep, clock=lambda: clock[0], rng=random.Random(0), delay=3.0, jitter=0.0, **options)
    return f, seen


BASE = "https://example.test"


def test_it_waits_between_requests():
    f, seen = fetcher({f"{BASE}/robots.txt": "", f"{BASE}/a": "A", f"{BASE}/b": "B"})
    assert (f.get(f"{BASE}/a"), f.get(f"{BASE}/b")) == ("A", "B")
    assert seen["sleeps"] and all(s >= 3.0 for s in seen["sleeps"])
    assert len(seen["sleeps"]) == 2  # before /a (after robots.txt) and before /b


def test_it_will_not_fetch_what_robots_txt_disallows():
    f, seen = fetcher({f"{BASE}/robots.txt": "User-agent: *\nDisallow: /admin", f"{BASE}/admin/x": "secret"})
    with pytest.raises(Disallowed):
        f.get(f"{BASE}/admin/x")
    assert f"{BASE}/admin/x" not in seen["urls"]


def test_a_missing_robots_txt_means_anything_goes():
    f, _ = fetcher({f"{BASE}/a": "A"})  # robots.txt is a 404
    assert f.get(f"{BASE}/a") == "A"


def test_a_broken_robots_txt_means_stay_away():
    f, _ = fetcher({f"{BASE}/robots.txt": http_error(f"{BASE}/robots.txt", 503), f"{BASE}/a": "A"})
    with pytest.raises(Disallowed):
        f.get(f"{BASE}/a")


def test_it_backs_off_and_retries_when_told_to_slow_down():
    calls = []

    def flaky():
        calls.append(1)
        return http_error(f"{BASE}/a", 429, {"Retry-After": "7"}) if len(calls) == 1 else "A"

    f, seen = fetcher({f"{BASE}/robots.txt": "", f"{BASE}/a": flaky})
    assert f.get(f"{BASE}/a") == "A"
    assert 7.0 in seen["sleeps"]  # it honoured Retry-After


def test_it_stops_after_repeated_failures():
    f, _ = fetcher({f"{BASE}/robots.txt": ""})  # every page is a 404
    with pytest.raises(FetchError):
        f.get(f"{BASE}/p1")
    with pytest.raises(FetchError):
        f.get(f"{BASE}/p2")
    with pytest.raises(Halt):
        f.get(f"{BASE}/p3")


def test_a_success_resets_the_failure_count():
    f, _ = fetcher({f"{BASE}/robots.txt": "", f"{BASE}/ok": "fine"})
    for url in ("p1", "p2"):
        with pytest.raises(FetchError):
            f.get(f"{BASE}/{url}")
    assert f.get(f"{BASE}/ok") == "fine"
    with pytest.raises(FetchError):
        f.get(f"{BASE}/p3")  # would have halted without the reset
