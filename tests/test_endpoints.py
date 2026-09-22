"""Offline tests for how EpiDataContext builds cast-API requests."""

from collections.abc import Callable, Mapping
from urllib.parse import parse_qs, urlparse

import pytest

from epidatpy import EpiDataContext, EpiRange, InvalidArgumentException

from .conftest import FakeServer

CSV_HEADER = "signal,report_time,geo_type,geo_value,fill_method,reference_time,value"


def _params(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def _csv_rows(geo_type: str, signals: str) -> str:
    rows = [f"{s},2025-10-16T00:00:00Z,{geo_type},{geo_type}-x,source,2025-10-01,1.5" for s in signals.split(",")]
    return "\n".join([CSV_HEADER, *rows])


def test_multiple_geo_types_fan_out(fake_server: Callable[..., FakeServer]) -> None:
    def responder(url: str, params: Mapping[str, str]) -> str:
        return _csv_rows(params["geo_type"], params["signal"])

    server = fake_server(responder)
    df = EpiDataContext(use_cache=False).epidata_snapshot("nssp", ["a", "b"], ["state", "hhs", "state"]).df()
    assert [p["geo_type"] for _, p in server.requests] == ["state", "hhs"]
    assert all(p["signal"] == "a,b" for _, p in server.requests)
    assert sorted(df["geo_type"].unique()) == ["hhs", "state"]
    assert len(df) == 4


def test_comma_joined_geo_type_string_fans_out(fake_server: Callable[..., FakeServer]) -> None:
    server = fake_server(lambda url, params: _csv_rows(params["geo_type"], params["signal"]))
    df = EpiDataContext(use_cache=False).epidata_archive("nssp", "a", "state,nation").df()
    assert [p["geo_type"] for _, p in server.requests] == ["state", "nation"]
    assert len(df) == 2


def test_single_geo_type_is_one_request(fake_server: Callable[..., FakeServer]) -> None:
    server = fake_server(lambda url, params: _csv_rows(params["geo_type"], params["signal"]))
    EpiDataContext(use_cache=False).epidata_snapshot("nssp", "a", "state").df()
    assert len(server.requests) == 1


def test_snapshot_request_params() -> None:
    url = EpiDataContext().epidata_snapshot("nssp", ["a", "b"], "state", snapshot_date=20251016).request_url()
    p = _params(url)
    assert p["signal"] == ["a,b"]
    assert p["snapshot_date"] == ["2025-10-16"]
    assert "limit" not in p


def test_archive_request_params() -> None:
    url = EpiDataContext().epidata_archive("nssp", "a", "state", report_time=EpiRange(20250101, 20250201)).request_url()
    assert _params(url)["report_time_query"] == ["2025-01-01:2025-02-01"]


def test_limit_is_sent_when_positive() -> None:
    ctx = EpiDataContext()
    assert _params(ctx.epidata_snapshot("nssp", "a", "state", limit=10).request_url())["limit"] == ["10"]
    assert _params(ctx.epidata_archive("nssp", "a", "state", limit=10).request_url())["limit"] == ["10"]
    assert _params(ctx.epidata("nssp", "a", "state", report_time="<2025-01-01", limit=5).request_url())["limit"] == [
        "5"
    ]


def test_limit_none_and_minus_one_are_omitted() -> None:
    ctx = EpiDataContext()
    assert "limit" not in _params(ctx.epidata_snapshot("nssp", "a", "state", limit=None).request_url())
    assert "limit" not in _params(ctx.epidata_snapshot("nssp", "a", "state", limit=-1).request_url())


@pytest.mark.parametrize("bad", [0, -2, 2.5, True, "10"])
def test_limit_invalid(bad: object) -> None:
    with pytest.raises(InvalidArgumentException):
        EpiDataContext().epidata_snapshot("nssp", "a", "state", limit=bad)  # type: ignore[arg-type]
