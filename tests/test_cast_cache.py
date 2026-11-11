"""Only cast requests for a fixed past version are cached, and the raw CSV is what is stored."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from epidatpy import _call
from epidatpy._call import _is_fixed_past_version
from epidatpy.request import EpiDataContext

_TODAY = datetime.now(UTC).date()
_OLD = (_TODAY - timedelta(days=10)).isoformat()
_OLDER = (_TODAY - timedelta(days=20)).isoformat()
_RECENT = (_TODAY - timedelta(days=1)).isoformat()


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"snapshot_date": _OLD}, True),
        ({"snapshot_date": f"{_OLD}T13:45:00Z"}, True),
        ({"snapshot_date": _RECENT}, False),
        ({"report_time_query": f"<{_OLD}"}, True),
        ({"report_time_query": f"{_OLDER}:{_OLD}"}, True),
        ({"report_time_query": f"{_OLDER}:{_RECENT}"}, False),
        ({"report_time_query": f">{_OLDER}"}, False),
        ({"report_time_query": f">={_OLDER}"}, False),
        ({"snapshot_date": _OLD, "limit": 10}, False),
        ({"snapshot_date": _OLD, "limit": -1}, True),
        ({}, False),
    ],
)
def test_is_fixed_past_version(params: dict, expected: bool) -> None:
    assert _is_fixed_past_version(params) is expected


def test_fixed_past_snapshot_is_cached_but_latest_is_not(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(_call, "CACHE_DIRECTORY", str(tmp_path))
    fetches: list[dict[str, Any]] = []

    def fake_call(self: _call.EpiDataCall, *args: Any, **kwargs: Any) -> _call.Response:
        fetches.append(dict(self._params))
        res = _call.Response()
        res.status_code = 200
        res._content = b"geo_value,value\nca,1\n"
        return res

    monkeypatch.setattr(_call.EpiDataCall, "_call", fake_call)
    ctx = EpiDataContext(use_cache=True)

    for _ in range(2):
        ctx.epidata_snapshot("nssp", "a", "state", snapshot_date=_OLD, return_empty=True).df()
    assert len(fetches) == 1

    for _ in range(2):
        ctx.epidata_snapshot("nssp", "a", "state", return_empty=True).df()
    assert len(fetches) == 3


def test_refresh_cache_refetches_and_rewrites_the_same_entry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(_call, "CACHE_DIRECTORY", str(tmp_path))
    bodies = iter([b"geo_value,value\nca,1\n", b"geo_value,value\nca,2\n"])
    fetches = 0

    def fake_call(self: _call.EpiDataCall, *args: Any, **kwargs: Any) -> _call.Response:
        nonlocal fetches
        fetches += 1
        res = _call.Response()
        res.status_code = 200
        res._content = next(bodies)
        return res

    monkeypatch.setattr(_call.EpiDataCall, "_call", fake_call)
    call = EpiDataContext(use_cache=True).epidata_snapshot("nssp", "a", "state", snapshot_date=_OLD, return_empty=True)

    assert call.df()["value"].tolist() == [1]
    assert call.df()["value"].tolist() == [1]
    assert fetches == 1
    assert call.df(refresh_cache=True)["value"].tolist() == [2]
    assert fetches == 2
    assert call.df()["value"].tolist() == [2]
    assert fetches == 2
