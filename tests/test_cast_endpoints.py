"""Offline tests for the cast endpoints: the requests they build, with the HTTP layer stubbed."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from unittest.mock import MagicMock, patch

from epidatpy import EpiDataContext, EpiRange


def test_multiple_geo_types_fan_out_one_request_each_and_combine() -> None:
    """Mirrors epidatr's "epidata_snapshot sends multiple signals comma-joined
    in a single request" and "...one call per geo_type, signals comma-joined"
    tests: signals stay comma-joined per request, one request is issued per
    geo_type, and the results are combined."""
    seen: list[Mapping[str, str]] = []

    def fake_request(url: str, params: Mapping[str, str], *_args: Any, **_kwargs: Any) -> MagicMock:
        seen.append(dict(params))
        resp = MagicMock()
        resp.status_code = 200
        g = params["geo_type"]
        rows = [f"{sig},{g},ca,2024-01-01,2024-01-02,1.0" for sig in params["signal"].split(",")]
        resp.text = "\n".join(["signal,geo_type,geo_value,reference_time,report_time,value", *rows]) + "\n"
        return resp

    with patch("epidatpy._call._request_with_retry", fake_request):
        df = (
            EpiDataContext()
            .epidata_snapshot(source="nssp", signals=["sig1", "sig2"], geo_type=["state", "nation"])
            .df()
        )

    assert [p["geo_type"] for p in seen] == ["state", "nation"]
    assert all(p["signal"] == "sig1,sig2" for p in seen)
    assert sorted(df["geo_type"].unique()) == ["nation", "state"]


def test_epidata_archive_report_time_epirange_is_inclusive_range() -> None:
    """EpiRange maps to a server-side "from:to" range query."""
    call = EpiDataContext().epidata_archive(
        source="nssp", signals="sig1", geo_type="state", report_time=EpiRange("2024-01-02", "2024-01-05")
    )
    _, params = call.request_arguments()
    assert params["report_time_query"] == "2024-01-02:2024-01-05"


def test_epidata_snapshot_snapshot_date_accepts_utc_timestamp() -> None:
    call = EpiDataContext().epidata_snapshot(
        source="nssp", signals="sig1", geo_type="state", snapshot_date="2024-01-02T13:45:00Z"
    )
    _, params = call.request_arguments()
    assert params["snapshot_date"] == "2024-01-02T13:45:00Z"
