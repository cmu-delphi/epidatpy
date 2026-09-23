"""Offline tests for how EpiDataContext builds cast-API requests."""

from urllib.parse import parse_qs, urlparse

import pytest

from epidatpy import EpiDataContext, EpiRange, InvalidArgumentException
from epidatpy._call import EpiDataCall


def _params(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


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
    # epidatr wires `limit` into epidata_aux() too (cmu-delphi/epidatr#379).
    aux = ctx.epidata_aux("nwss", limit=3)
    assert isinstance(aux, EpiDataCall)
    assert _params(aux.request_url())["limit"] == ["3"]


def test_limit_none_and_minus_one_are_omitted() -> None:
    ctx = EpiDataContext()
    assert "limit" not in _params(ctx.epidata_snapshot("nssp", "a", "state", limit=None).request_url())
    assert "limit" not in _params(ctx.epidata_snapshot("nssp", "a", "state", limit=-1).request_url())


@pytest.mark.parametrize("bad", [0, -2, 2.5, True, "10"])
def test_limit_invalid(bad: object) -> None:
    with pytest.raises(InvalidArgumentException):
        EpiDataContext().epidata_snapshot("nssp", "a", "state", limit=bad)  # type: ignore[arg-type]
