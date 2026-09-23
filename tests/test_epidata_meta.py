"""Unit tests for `EpiDataContext.epidata_meta` response handling (no network).

Mirrors epidatr's `epidata_meta` unlisting behavior: a named `source` returns
that source's dict directly, while no argument returns the full keyed mapping.
"""

from typing import Any

import pytest
from pytest import MonkeyPatch

import epidatpy._endpoints as endpoints
from epidatpy import EpiDataContext

META_PAYLOAD = {
    "nssp": {"signals": ["pct_ed_visits_influenza"], "geo_types": ["state"]},
    "nwss": {"signals": ["covid_avg_conc"], "geo_types": ["sewershed"]},
}


class _FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> Any:
        return self._payload


@pytest.fixture(autouse=True)
def _stub_request(monkeypatch: MonkeyPatch) -> None:
    def fake_request(url: str, params: Any, *args: Any, **kwargs: Any) -> _FakeResponse:
        source = params.get("source")
        if source is None:
            return _FakeResponse(META_PAYLOAD)
        return _FakeResponse({source: META_PAYLOAD[source]} if source in META_PAYLOAD else {})

    monkeypatch.setattr(endpoints, "_request_with_retry", fake_request)


def test_no_source_returns_full_mapping() -> None:
    meta = EpiDataContext().epidata_meta()
    assert set(meta) == {"nssp", "nwss"}


def test_named_source_is_unwrapped() -> None:
    meta = EpiDataContext().epidata_meta(source="nssp")
    assert meta == META_PAYLOAD["nssp"]
    assert meta["signals"] == ["pct_ed_visits_influenza"]


def test_unknown_source_returns_raw_response() -> None:
    # No `source` key to unwrap — pass the payload through untouched rather than raising.
    assert EpiDataContext().epidata_meta(source="does-not-exist") == {}
