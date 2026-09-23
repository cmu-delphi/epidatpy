"""Offline tests for `epidata_aux` -- no live API calls.

Mirrors the coverage of epidatr's `test-endpoints.R` "epidata_aux" block: call
construction (key filters via `...`/`**kwargs`, typed values, multi-value
filters), the version-aware merge (archive per-row vs. snapshot uniform, using
the same fixture), filter inference/forwarding, and the connected-path
validation errors.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from epidatpy import EpiDataContext, InvalidArgumentException
from epidatpy._endpoints import EpiDataContext as _EpiDataContext
from epidatpy._endpoints import _serialize_key_filters


def test_serialize_key_filters_empty() -> None:
    assert _serialize_key_filters({}) is None


def test_serialize_key_filters_scalar_and_sequence() -> None:
    assert _serialize_key_filters({"pcr_target": "sars-cov-2"}) == "pcr_target:sars-cov-2"
    assert _serialize_key_filters({"geo_value": ["ca", "ny"]}) == "geo_value:ca,geo_value:ny"


def test_serialize_key_filters_formats_dates_as_iso() -> None:
    assert _serialize_key_filters({"reference_time": date(2024, 1, 1)}) == "reference_time:2024-01-01"


def test_serialize_key_filters_warns_over_max_vals() -> None:
    with pytest.warns(UserWarning, match="more than 10 values"):
        _serialize_key_filters({"geo_value": [str(i) for i in range(11)]})


def test_epidata_aux_base_pull_builds_call() -> None:
    """Mirrors epidatr's "base-pull builds the call, serializes key filters via
    ..." test: report_time operator, columns, an arbitrary named filter, and a
    typed filter value serializing as ISO -- not a day-count."""
    ctx = EpiDataContext()
    call = ctx.epidata_aux(
        "nwss",
        report_time="<2024-06-01",
        pcr_target="SARS-CoV-2",
        ref_date=date(2024, 1, 1),  # a typed key value -> ISO, not day-count
        columns=["geo_value", "population_served"],
    )
    _, params = call.request_arguments()
    assert params["source"] == "nwss"
    assert params["report_time_query"] == "<2024-06-01"
    assert params["columns"] == "geo_value,population_served"
    assert "pcr_target:SARS-CoV-2" in params["filtered_keys"]
    assert "ref_date:2024-01-01" in params["filtered_keys"]


def test_epidata_aux_base_pull_snapshot_date() -> None:
    ctx = EpiDataContext()
    call = ctx.epidata_aux("nwss", snapshot_date="2024-06-01")
    _, params = call.request_arguments()
    assert params["snapshot_date"] == "2024-06-01"
    assert "report_time_query" not in params


def test_epidata_aux_df_keeps_undeclared_value_columns() -> None:
    """Ensure aux value columns survive df() even if undeclared in _aux_fields()."""
    csv = "report_time,geo_value,pcr_target,population_served,county_fips\n2024-05-20,ca,sars-cov-2,1000,06001\n"

    def fake_request(url: str, params: Any, *_a: Any, **_k: Any) -> Any:
        resp = MagicMock()
        resp.status_code = 200
        resp.text = csv
        return resp

    with patch("epidatpy._call._request_with_retry", fake_request), warnings.catch_warnings():
        # Aux value columns are open-ended, so they don't trigger the undeclared-columns warning.
        warnings.simplefilter("error")
        df = EpiDataContext().epidata_aux("nwss", report_time="<2024-06-01").df()

    assert "population_served" in df.columns
    assert "county_fips" in df.columns
    assert df["population_served"].iloc[0] == "1000"


def test_epidata_aux_base_pull_snapshot_date_latest() -> None:
    """snapshot_date="latest" resolves to today's date."""
    ctx = EpiDataContext()
    call = ctx.epidata_aux("nwss", snapshot_date="latest")
    _, params = call.request_arguments()
    assert params["snapshot_date"] == datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
    assert "report_time_query" not in params


def test_epidata_aux_snapshot_date_and_report_time_are_exclusive() -> None:
    ctx = EpiDataContext()
    with pytest.raises(InvalidArgumentException):
        ctx.epidata_aux("nwss", snapshot_date="2024-06-01", report_time="<2024-06-01")


def test_epidata_aux_base_pull_multi_value_filter_repeats_terms() -> None:
    ctx = EpiDataContext()
    call = ctx.epidata_aux("nwss", geo_value=["ca", "ny"])
    _, params = call.request_arguments()
    assert params["filtered_keys"] == "geo_value:ca,geo_value:ny"


def test_epidata_aux_rejects_untagged_dataframe() -> None:
    ctx = EpiDataContext()
    with pytest.raises(InvalidArgumentException):
        ctx.epidata_aux(pd.DataFrame({"geo_value": ["a"]}))


def test_epidata_aux_rejects_report_time_with_dataframe_source() -> None:
    base = pd.DataFrame({"geo_value": ["a"]})
    base.attrs["cast_source"] = "nwss"
    ctx = EpiDataContext()
    with pytest.raises(InvalidArgumentException):
        ctx.epidata_aux(base, report_time="2024-01-01")


def test_epidata_aux_merge_empty_base_passthrough() -> None:
    base = pd.DataFrame({"geo_value": pd.array([], dtype="object")})
    base.attrs["cast_source"] = "nwss"
    ctx = EpiDataContext()
    assert ctx.epidata_aux(base) is base


def test_epidata_aux_merge_no_shared_keys_raises() -> None:
    base = pd.DataFrame({"unrelated_column": [1]})
    base.attrs["cast_source"] = "nwss"
    ctx = EpiDataContext()
    with (
        patch.object(_EpiDataContext, "_aux_key_columns", return_value=["report_time", "geo_value"]),
        pytest.raises(InvalidArgumentException),
    ):
        ctx.epidata_aux(base)


def test_epidata_aux_merge_columns_excluding_key_raises() -> None:
    base = pd.DataFrame({"geo_value": ["ca"], "report_time": pd.to_datetime(["2024-02-01"])})
    base.attrs["cast_source"] = "nwss"
    ctx = EpiDataContext()
    with (
        patch.object(_EpiDataContext, "_aux_key_columns", return_value=["report_time", "geo_value"]),
        pytest.raises(InvalidArgumentException, match="geo_value"),
    ):
        ctx.epidata_aux(base, columns=["population_served"])


def _fake_aux_fetch(aux: pd.DataFrame, calls: list[dict[str, Any]] | None = None) -> Callable[..., Any]:
    """Patch `epidata_aux`'s recursive base-pull call to return `aux` directly.

    When `calls` is given, each base-pull invocation's kwargs are recorded so
    tests can assert on the filters/report_time forwarded by merge mode.
    """
    original = _EpiDataContext.epidata_aux

    class _FakeCall:
        def df(self) -> pd.DataFrame:
            return aux

    def fake(self: _EpiDataContext, source: Any, **kwargs: Any) -> Any:
        if isinstance(source, pd.DataFrame):
            return original(self, source, **kwargs)
        if calls is not None:
            calls.append(kwargs)
        return _FakeCall()

    return fake


# Shared aux table for the merge tests below: three keys (geo_value,
# reference_time, sample_index), some with two revisions whose report_time
# straddles the base rows' own report_time (so archive/as-of vs. snapshot/
# uniform diverge), plus a non-key `county_fips` to check shared columns
# aren't clobbered. Mirrors epidatr's `aux_versions_csv` fixture exactly, so
# the expected values below are directly comparable to the R test.
_AUX_VERSIONS = pd.DataFrame(
    {
        "report_time": pd.to_datetime(["2024-02-01", "2024-05-01", "2024-02-01", "2024-01-01", "2024-04-01"]),
        "geo_value": ["ca", "ca", "ca", "ny", "ny"],
        "reference_time": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-08", "2024-01-01", "2024-01-01"]),
        "sample_index": ["A", "A", "A", "B", "B"],
        "county_fips": ["001"] * 5,
        "population_served": [100, 200, 300, 350, 400],
        "label": ["p1", "p2", "p3", "p0", "p4"],
    }
)
_AUX_KEYS = ["report_time", "geo_value", "reference_time", "sample_index"]


def test_epidata_aux_merge_archive_is_version_aware_per_row() -> None:
    """Each archive row is matched as-of its own report_time -- mirrors
    epidatr's "merge is version-aware: archive per-row" case."""
    base = pd.DataFrame(
        {
            "geo_value": ["ca", "ca", "ca", "ny", "tx"],
            "reference_time": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-08", "2024-01-01", "2024-01-01"]),
            "sample_index": ["A", "A", "A", "B", "C"],
            "report_time": pd.to_datetime(["2024-01-15", "2024-03-01", "2024-06-01", "2024-03-01", "2024-03-01"]),
            "county_fips": ["999"] * 5,
            "value": [1, 2, 3, 4, 5],
        }
    )
    base.attrs["cast_source"] = "nwss"
    base.attrs["cast_kind"] = "archive"

    ctx = EpiDataContext()
    with (
        patch.object(_EpiDataContext, "_aux_key_columns", return_value=_AUX_KEYS),
        patch.object(_EpiDataContext, "epidata_aux", _fake_aux_fetch(_AUX_VERSIONS)),
    ):
        result = ctx.epidata_aux(base)

    assert isinstance(result, pd.DataFrame)
    # row0 (01-15) predates the earliest ca/01-01/A revision (02-01) -> NaN.
    assert pd.isna(result["population_served"].iloc[0])
    assert pd.isna(result["label"].iloc[0])
    # row1 (03-01) -> the 02-01 revision (100), not the newer 05-01 one (200).
    assert result["population_served"].iloc[1] == 100
    assert result["label"].iloc[1] == "p1"
    # row2 (06-01, reference_time=01-08, a different key) -> its only revision (300).
    assert result["population_served"].iloc[2] == 300
    assert result["label"].iloc[2] == "p3"
    # row3 (ny, 03-01) -> the 01-01 revision (350), not the newer 04-01 one (400).
    assert result["population_served"].iloc[3] == 350
    assert result["label"].iloc[3] == "p0"
    # row4 (tx) has no matching key in aux at all -> NaN.
    assert pd.isna(result["population_served"].iloc[4])
    assert pd.isna(result["label"].iloc[4])
    # A shared non-key column is never clobbered; base rows/order/other columns are kept.
    assert result["county_fips"].tolist() == ["999"] * 5
    assert result["value"].tolist() == [1, 2, 3, 4, 5]


def test_epidata_aux_merge_snapshot_uses_uniform_cutoff() -> None:
    """A snapshot base is a single-version view, so every row is matched
    as-of the base's overall latest report_time -- mirrors epidatr's "snapshot
    uniform" case, and diverges from the archive result above on the same aux."""
    base = pd.DataFrame(
        {
            "geo_value": ["ca", "ca", "ny"],
            "reference_time": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-01"]),
            "sample_index": ["A", "A", "B"],
            "report_time": pd.to_datetime(["2024-03-01", "2024-06-01", "2024-03-01"]),
            "value": [1, 2, 3],
        }
    )
    base.attrs["cast_source"] = "nwss"
    base.attrs["cast_kind"] = "snapshot"

    ctx = EpiDataContext()
    with (
        patch.object(_EpiDataContext, "_aux_key_columns", return_value=_AUX_KEYS),
        patch.object(_EpiDataContext, "epidata_aux", _fake_aux_fetch(_AUX_VERSIONS)),
    ):
        result = ctx.epidata_aux(base)

    assert isinstance(result, pd.DataFrame)
    # Cutoff = max(base report_time) = 06-01 for every row.
    # ca/01-01/A -> the newer 05-01 revision now qualifies (200).
    # ca/01-08/A -> its only revision (300). ny/01-01/B -> the newer 04-01 revision (400).
    assert result["population_served"].tolist() == [200, 300, 400]


def test_epidata_aux_merge_infers_and_forwards_multi_value_filters() -> None:
    """Mirrors epidatr's "infers multi-value key filters from the base"
    test: a key with 2 distinct values (under the 10-value cap) is pinned and
    forwarded to the recursive base-pull call."""
    base = pd.DataFrame(
        {
            "geo_value": ["ca", "ny"],
            "report_time": pd.to_datetime(["2024-03-01", "2024-03-01"]),
            "value": [1, 2],
        }
    )
    base.attrs["cast_source"] = "nwss"
    base.attrs["cast_kind"] = "snapshot"
    aux = pd.DataFrame(
        {
            "report_time": pd.to_datetime(["2024-02-01", "2024-02-01"]),
            "geo_value": ["ca", "ny"],
            "population_served": [100, 200],
        }
    )

    calls: list[dict[str, Any]] = []
    ctx = EpiDataContext()
    with (
        patch.object(_EpiDataContext, "_aux_key_columns", return_value=["report_time", "geo_value"]),
        patch.object(_EpiDataContext, "epidata_aux", _fake_aux_fetch(aux, calls)),
    ):
        ctx.epidata_aux(base)

    assert len(calls) == 1
    assert sorted(calls[0]["geo_value"]) == ["ca", "ny"]


def test_epidata_aux_merge_forwards_explicit_filters_and_caps_report_time() -> None:
    """Explicit key filters are forwarded and report_time is capped at base's max."""
    base = pd.DataFrame(
        {
            "geo_value": ["ca", "ca"],
            "reference_time": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "report_time": pd.to_datetime(["2024-01-10", "2024-05-20"]),
            "value": [1, 2],
        }
    )
    base.attrs["cast_source"] = "nwss"
    base.attrs["cast_kind"] = "archive"
    empty_aux = pd.DataFrame({"report_time": pd.to_datetime([]), "geo_value": pd.array([], dtype="object")})

    calls: list[dict[str, Any]] = []
    ctx = EpiDataContext()
    with (
        patch.object(_EpiDataContext, "_aux_key_columns", return_value=["report_time", "geo_value"]),
        patch.object(_EpiDataContext, "epidata_aux", _fake_aux_fetch(empty_aux, calls)),
        pytest.warns(UserWarning, match="pcr_target"),
    ):
        ctx.epidata_aux(base, pcr_target="x")

    assert len(calls) == 1
    assert calls[0]["pcr_target"] == "x"
    assert calls[0]["report_time"] == "<=2024-05-20T00:00:00Z"


def test_epidata_aux_merge_snapshot_base_requests_snapshot_date() -> None:
    """Snapshot base queries snapshot_date using the base's max report_time."""
    base = pd.DataFrame(
        {
            "geo_value": ["ca", "ca"],
            "report_time": pd.to_datetime(["2024-03-01", "2024-05-20"]),
            "value": [1, 2],
        }
    )
    base.attrs["cast_source"] = "nwss"
    base.attrs["cast_kind"] = "snapshot"
    empty_aux = pd.DataFrame({"report_time": pd.to_datetime([]), "geo_value": pd.array([], dtype="object")})

    calls: list[dict[str, Any]] = []
    ctx = EpiDataContext()
    with (
        patch.object(_EpiDataContext, "_aux_key_columns", return_value=["report_time", "geo_value"]),
        patch.object(_EpiDataContext, "epidata_aux", _fake_aux_fetch(empty_aux, calls)),
    ):
        ctx.epidata_aux(base)

    assert len(calls) == 1
    assert calls[0]["snapshot_date"] == pd.Timestamp("2024-05-20")
    assert "report_time" not in calls[0]
