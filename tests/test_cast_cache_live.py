"""Live check that cast queries for a fixed past version are cached and read back unchanged.

Mirrors epidatr's `tests/testthat/test-live-cast-cache.R`. NHSN at state level is
small enough to fetch without a row limit.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from diskcache import Cache

from epidatpy import EpiDataContext, _call
from epidatpy._constants import CAST_BASE_URL

auth = os.environ.get("DELPHI_EPIDATA_KEY", "")
cast_base_url = os.environ.get("EPIDATPY_CAST_BASE_URL") or CAST_BASE_URL

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not auth, reason="DELPHI_EPIDATA_KEY not available."),
]

NHSN: dict[str, Any] = {"source": "nhsn", "signals": "confirmed_admissions_flu_ew", "geo_type": "state"}


class LiveCache:
    """A throwaway cache directory plus a count of the data requests that really reached the server."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.requests = 0

    def entries(self) -> int:
        with Cache(str(self.directory)) as cache:
            return len(cache)

    def ctx(self) -> EpiDataContext:
        return EpiDataContext(use_cache=True, cast_base_url=cast_base_url)


@pytest.fixture
def live_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[LiveCache]:
    monkeypatch.setattr(_call, "CACHE_DIRECTORY", str(tmp_path))
    state = LiveCache(tmp_path)
    real: Callable[..., Any] = _call._request_with_retry

    def counting(url: str, *args: Any, **kwargs: Any) -> Any:
        if url.rstrip("/").endswith(("snapshot", "archive")):
            state.requests += 1
        return real(url, *args, **kwargs)

    monkeypatch.setattr(_call, "_request_with_retry", counting)
    yield state


def _snapshot(cache: LiveCache, **kwargs: Any) -> pd.DataFrame:
    return cache.ctx().epidata_snapshot(**NHSN, snapshot_date="2025-06-01", limit=-1, **kwargs).df()


def _archive(cache: LiveCache, **kwargs: Any) -> pd.DataFrame:
    return cache.ctx().epidata_archive(**NHSN, report_time="<2025-06-01", limit=-1, **kwargs).df()


def test_past_snapshot_date_is_cached_and_read_back_unchanged(live_cache: LiveCache) -> None:
    first = _snapshot(live_cache)
    assert len(first) > 0
    assert live_cache.entries() == 1
    assert live_cache.requests == 1

    second = _snapshot(live_cache)
    assert live_cache.requests == 1
    pd.testing.assert_frame_equal(second, first)
    assert second.attrs == first.attrs


def test_past_report_time_archive_is_cached_and_read_back_unchanged(live_cache: LiveCache) -> None:
    first = _archive(live_cache)
    assert len(first) > 0
    assert live_cache.entries() == 1

    second = _archive(live_cache)
    assert live_cache.requests == 1
    pd.testing.assert_frame_equal(second, first)


def test_different_queries_get_separate_entries_and_fields_share_one(live_cache: LiveCache) -> None:
    snap = _snapshot(live_cache)
    _archive(live_cache)
    assert live_cache.entries() == 2
    assert live_cache.requests == 2

    # `fields` selects columns locally, so a subset reuses the cached response and
    # must not change what a full read returns.
    subset = live_cache.ctx().epidata_snapshot(**NHSN, snapshot_date="2025-06-01", limit=-1).df(fields=["geo_value", "value"])
    assert list(subset.columns) == ["geo_value", "value"]
    assert live_cache.entries() == 2
    assert live_cache.requests == 2
    pd.testing.assert_frame_equal(_snapshot(live_cache), snap)


def test_queries_without_a_fixed_past_version_or_with_a_row_limit_are_not_cached(live_cache: LiveCache) -> None:
    # "Latest" snapshot: no snapshot_date.
    latest = live_cache.ctx().epidata_snapshot(**NHSN, geo_values="ca", limit=-1).df()
    assert len(latest) > 0

    limited = live_cache.ctx().epidata_snapshot(**NHSN, snapshot_date="2025-06-01", limit=10).df()
    assert len(limited) <= 10
    assert live_cache.entries() == 0
