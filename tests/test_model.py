import datetime

from epidatpy._model import EpiRange, format_item, format_list


def test_epirange() -> None:
    r = EpiRange(20000101, 20000102)
    assert r.start == datetime.date(2000, 1, 1) and r.end == datetime.date(2000, 1, 2)
    assert str(r) == "20000101-20000102"


def test_epirange_wrong_order() -> None:
    r = EpiRange(20000101, 20000102)
    assert r.start == datetime.date(2000, 1, 1) and r.end == datetime.date(2000, 1, 2)


def test_format_item() -> None:
    assert format_item("a") == "a"
    assert format_item(1) == "1"
    assert format_item({"from": 1, "to": 3}) == "1-3"
    assert format_item(EpiRange(20000101, 20000102)) == "20000101-20000102"


def test_format_list() -> None:
    assert format_list("a") == "a"
    assert format_list(1) == "1"
    assert format_list({"from": 1, "to": 3}) == "1-3"
    assert format_list(EpiRange(20000101, 20000102)) == "20000101-20000102"

    assert format_list(["a", "b"]) == "a,b"
    assert format_list(("a", "b")) == "a,b"
    assert format_list(["a", 1]) == "a,1"
