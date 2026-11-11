"""Classic (V4) responses: malformed or error envelopes raise, and promised columns that are missing warn."""

from __future__ import annotations

import json
import warnings
from collections.abc import Callable

import pytest

from epidatpy import (
    DroppedMetaFieldsWarning,
    EpiDataAPIError,
    EpiDataContext,
    EpiDataWarning,
    MalformedResponseError,
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
