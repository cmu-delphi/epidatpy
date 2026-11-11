"""Classic (V4) responses: malformed or error envelopes raise, and promised columns that are missing warn."""

from __future__ import annotations

import json
import warnings
from collections.abc import Callable

import pandas as pd
import pytest

from epidatpy import (
    DroppedMetaFieldsWarning,
    EpiDataAPIError,
    EpiDataContext,
    EpiDataWarning,
    MalformedResponseError,
    UnknownCategoryWarning,
)
from epidatpy._call import EpiDataCall

from .conftest import FakeServer

pytestmark = pytest.mark.filterwarnings("ignore:`pub_fluview` uses the V4 Epidata API")

ROW = {"release_date": "2020-01-01", "region": "nat", "issue": 202001, "epiweek": 202001, "lag": 0}


def _call(fake_server: Callable[..., FakeServer], body: object) -> EpiDataCall:
    text = body if isinstance(body, str) else json.dumps(body)
    fake_server(lambda url, params: text)
    return EpiDataContext(use_cache=False).pub_fluview("nat", [202001])


@pytest.mark.parametrize(
    "body",
    [
        "<html>oops</html>",
        [1, 2],
        {"message": "success", "epidata": []},
        {"result": 1, "epidata": []},
        {"result": "1", "message": "success", "epidata": []},
        {"result": 1, "message": "success"},
        {"result": 2, "message": "truncated"},
    ],
)
def test_malformed_envelopes_raise(fake_server: Callable[..., FakeServer], body: object) -> None:
    with pytest.raises(MalformedResponseError, match=r"https://[^?]*$|\(request: https://[^?]*\)"):
        _call(fake_server, body).df()


def test_api_error_raises_from_df_but_classic_returns_the_envelope(fake_server: Callable[..., FakeServer]) -> None:
    call = _call(fake_server, {"result": -1, "message": "bad param", "epidata": []})
    with pytest.raises(EpiDataAPIError, match="bad param") as info:
        call.df()
    assert info.value.result == -1
    assert call.classic()["result"] == -1


def test_no_results_is_an_empty_frame_with_the_servers_message(fake_server: Callable[..., FakeServer]) -> None:
    with pytest.warns(EpiDataWarning, match="no results"):
        df = _call(fake_server, {"result": -2, "message": "no results", "epidata": []}).df()
    assert len(df) == 0


def test_truncated_result_warns_and_keeps_the_rows(fake_server: Callable[..., FakeServer]) -> None:
    with pytest.warns(EpiDataWarning, match="truncated"):
        df = _call(fake_server, {"result": 2, "message": "too many results, data truncated", "epidata": [ROW]}).df()
    assert len(df) == 1


def test_epidata_warning_points_at_the_callers_line(fake_server: Callable[..., FakeServer]) -> None:
    call = _call(fake_server, {"result": 2, "message": "truncated", "epidata": [ROW]})
    with pytest.warns(EpiDataWarning) as record:
        call.df()
    assert record[0].filename == __file__


def test_missing_promised_columns_warn(fake_server: Callable[..., FakeServer]) -> None:
    body = {"result": 1, "message": "success", "epidata": [ROW]}
    with pytest.warns(DroppedMetaFieldsWarning, match="num_ili"):
        _call(fake_server, body).df()
    # Asking for specific `fields` explains the absence, so there is no warning.
    with warnings.catch_warnings():
        warnings.simplefilter("error", DroppedMetaFieldsWarning)
        _call(fake_server, body).df(fields=["region", "epiweek"])


def test_complete_response_is_silent(fake_server: Callable[..., FakeServer]) -> None:
    full: dict[str, object] = {k: 1 for k in _call(fake_server, "x").meta_by_name}
    full.update(ROW)
    with warnings.catch_warnings():
        warnings.simplefilter("error", (DroppedMetaFieldsWarning, EpiDataWarning))
        df = _call(fake_server, {"result": 1, "message": "success", "epidata": [full]}).df()
    assert len(df) == 1


@pytest.mark.filterwarnings("ignore:.*V4 Epidata API")
@pytest.mark.parametrize(
    ("issues", "is_date"),
    [(["201719", "202615"], False), (["20240311", "20240503"], True), (["20240311", "202615"], False)],
)
def test_date_or_epiweek_column_parses_by_what_it_holds(
    fake_server: Callable[..., FakeServer], issues: list[str], is_date: bool
) -> None:
    rows = [{"issue": i, "epiweek": 201701, "location": "CA"} for i in issues]
    fake_server(lambda url, params: json.dumps({"result": 1, "message": "success", "epidata": rows}))
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        df = EpiDataContext(use_cache=False).pub_flusurv("CA", "201701").df()
    assert not [w for w in record if "Could not infer format" in str(w.message)]
    assert pd.api.types.is_datetime64_any_dtype(df["issue"]) is is_date


@pytest.mark.filterwarnings("ignore:.*V4 Epidata API", "ignore::epidatpy.DroppedMetaFieldsWarning")
def test_unknown_categorical_value_warns_and_is_kept(fake_server: Callable[..., FakeServer]) -> None:
    rows = [{"time_type": "day", "geo_type": "state"}, {"time_type": "hour", "geo_type": "state"}]
    fake_server(lambda url, params: json.dumps({"result": 1, "message": "success", "epidata": rows}))
    call = EpiDataContext(use_cache=False).pub_covidcast("src", "sig", "state", "day", "ca", [20200101])
    with pytest.warns(UnknownCategoryWarning, match=r"`time_type`.*\['hour'\]"):
        df = call.df()
    assert df["time_type"].tolist() == ["day", "hour"]
