from shotti_ml.export import catalogue, local_name

KNOWN = {"Axio", "Noah", "Prado", "Corolla", "Vezel", "RX", "Yaris", "Prius"}


def test_hybrid_suffix_maps_to_the_base_model():
    assert local_name("Noah Hybrid", KNOWN) == "Noah"
    assert local_name("Vezel e:HEV", KNOWN) == "Vezel"


def test_different_cars_sharing_a_first_word_do_not_match():
    assert local_name("Corolla Cross Hybrid", KNOWN) is None
    assert local_name("Yaris Cross Hybrid", KNOWN) is None
    assert local_name("Prius Alpha", KNOWN) is None


def test_aliases_need_the_local_model_to_exist():
    assert local_name("Land Cruiser Prado TX", KNOWN) == "Prado"
    assert local_name("Crown Crossover", KNOWN) is None


def test_catalogue_is_read_from_the_web_source():
    rows = catalogue()
    assert len(rows) > 100
    assert ("Toyota", "Axio", 2021, 1496, "petrol") in rows
