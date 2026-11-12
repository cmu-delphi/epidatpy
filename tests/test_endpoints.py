"""Offline tests for how EpiDataContext builds cast-API requests."""

from collections.abc import Callable, Mapping
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest

from epidatpy import EmptyResultWarning, EpiDataContext, EpiRange, InvalidArgumentException
from epidatpy._call import EpiDataCall

from .conftest import FakeServer

CSV_HEADER = "signal,report_time,geo_type,geo_value,fill_method,reference_time,value"
META_JSON = (
    '{"nssp": {"signals": ["a", "b"], "geo_types": ["state", "hhs"], '
    '"reference_time_range": {"first": "2022-10-01", "latest": "2026-09-12"}}}'
)


def _params(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def _csv_rows(geo_type: str, signals: str) -> str:
    rows = [f"{s},2025-10-16T00:00:00Z,{geo_type},{geo_type}-x,source,2025-10-01,1.5" for s in signals.split(",")]
    return "\n".join([CSV_HEADER, *rows])


def _meta_or(csv_fn: Callable[[Mapping[str, str]], str]) -> Callable[[str, Mapping[str, str]], str]:
    def responder(url: str, params: Mapping[str, str]) -> str:
        return META_JSON if "metadata" in url else csv_fn(params)

    return responder


def test_empty_result_warns(fake_server: Callable[..., FakeServer]) -> None:
    fake_server(_meta_or(lambda params: ""))
    with pytest.warns(EmptyResultWarning, match="No data returned for source 'nssp'") as record:
        df = EpiDataContext(use_cache=False).epidata_snapshot("nssp", "a", "state").df()
    assert len(df) == 0
    assert "reference_time range: 2022-10-01 to 2026-09-12" in str(record[0].message)


def test_undeclared_columns_warn(fake_server: Callable[..., FakeServer]) -> None:
    def csv(params: Mapping[str, str]) -> str:
        return f"{CSV_HEADER},new_col\na,2025-10-16T00:00:00Z,state,ca,source,2025-10-01,1.5,x"

    fake_server(_meta_or(csv))
    with pytest.warns(UserWarning, match=r"Unspecified fields \['new_col'\]"):
        df = EpiDataContext(use_cache=False).epidata_snapshot("nssp", "a", "state").df()
    assert df["new_col"].iloc[0] == "x"


def test_partially_empty_result_names_missing_signals(fake_server: Callable[..., FakeServer]) -> None:
    fake_server(_meta_or(lambda params: _csv_rows(params["geo_type"], "a")))
    with pytest.warns(EmptyResultWarning, match=r"signals \['b'\]"):
        df = EpiDataContext(use_cache=False).epidata_snapshot("nssp", ["a", "b"], "state").df()
    assert len(df) == 1


def test_unknown_signal_raises(fake_server: Callable[..., FakeServer]) -> None:
    fake_server(_meta_or(lambda params: ""))
    with pytest.raises(InvalidArgumentException, match=r"signals \['zzz'\] are not available"):
        EpiDataContext(use_cache=False).epidata_snapshot("nssp", "zzz", "state").df()


def test_unknown_signal_with_partial_data_warns(fake_server: Callable[..., FakeServer]) -> None:
    fake_server(_meta_or(lambda params: _csv_rows(params["geo_type"], "a")))
    with pytest.warns(EmptyResultWarning, match=r"signals \['zzz'\] are not available"):
        df = EpiDataContext(use_cache=False).epidata_snapshot("nssp", ["a", "zzz"], "state").df()
    assert len(df) == 1


def test_unknown_geo_type_raises(fake_server: Callable[..., FakeServer]) -> None:
    fake_server(_meta_or(lambda params: ""))
    with pytest.raises(InvalidArgumentException, match=r"geo_types \['moon'\] are not available"):
        EpiDataContext(use_cache=False).epidata_archive("nssp", "a", "moon").df()


def test_local_filter_dropping_everything_warns(fake_server: Callable[..., FakeServer]) -> None:
    fake_server(_meta_or(lambda params: _csv_rows(params["geo_type"], params["signal"])))
    with pytest.warns(EmptyResultWarning, match="local `geo_values`/`reference_time` filter"):
        df = EpiDataContext(use_cache=False).epidata_snapshot("nssp", "a", "state", geo_values="zz").df()
    assert len(df) == 0


def test_return_empty_silences_diagnostics(
    fake_server: Callable[..., FakeServer], recwarn: pytest.WarningsRecorder
) -> None:
    fake_server(_meta_or(lambda params: ""))
    df = EpiDataContext(use_cache=False).epidata_snapshot("nssp", "zzz", "state", return_empty=True).df()
    assert len(df) == 0
    assert not [w for w in recwarn if issubclass(w.category, EmptyResultWarning)]


def test_non_empty_result_is_silent(fake_server: Callable[..., FakeServer], recwarn: pytest.WarningsRecorder) -> None:
    server = fake_server(_meta_or(lambda params: _csv_rows(params["geo_type"], params["signal"])))
    EpiDataContext(use_cache=False).epidata_snapshot("nssp", ["a", "b"], ["state", "hhs"]).df()
    assert not [w for w in recwarn if issubclass(w.category, EmptyResultWarning)]
    assert not any("metadata" in url for url, _ in server.requests)


def test_snapshot_request_params() -> None:
    url = EpiDataContext().epidata_snapshot("nssp", ["a", "b"], "state", snapshot_date=20251016).request_url()
    p = _params(url)
    assert p["signal"] == ["a,b"]
    assert p["snapshot_date"] == ["2025-10-16"]
    assert "limit" not in p


@pytest.mark.parametrize("snapshot_date", ["latest", "garbage", "2025-13-01"])
def test_snapshot_invalid_snapshot_date_raises(snapshot_date: str) -> None:
    with pytest.raises(InvalidArgumentException, match="snapshot_date"):
        EpiDataContext().epidata_snapshot("nssp", "a", "state", snapshot_date=snapshot_date)


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


@pytest.mark.filterwarnings("ignore:`pub_covidcast_meta` uses the V4 Epidata API")
def test_pub_covidcast_meta_filters() -> None:
    ctx = EpiDataContext()
    assert _params(ctx.pub_covidcast_meta().request_url()) == {}
    p = _params(ctx.pub_covidcast_meta(signals=["a:b", "c:d"], time_type="day", geo_type="state").request_url())
    assert p == {"signals": ["a:b,c:d"], "time_types": ["day"], "geo_types": ["state"]}


@pytest.mark.filterwarnings("ignore:`pub_covidcast` uses the V4 Epidata API")
def test_pub_covidcast_validation() -> None:
    ctx = EpiDataContext()
    with pytest.raises(InvalidArgumentException, match="time_type"):
        ctx.pub_covidcast("nssp", "pct_ed_visits_covid", "state", "month")  # type: ignore[arg-type]
    with pytest.raises(InvalidArgumentException, match="nssp"):
        ctx.pub_covidcast("nssp", "pct_ed_visits_covid", "state", "day")
    with pytest.raises(InvalidArgumentException, match="nchs-mortality"):
        ctx.pub_covidcast("nchs-mortality", "deaths_covid_incidence_num", "state", "day")
    url = ctx.pub_covidcast("nssp", "pct_ed_visits_covid", "hsa_nci", "week").request_url()
    assert _params(url)["geo_type"] == ["hsa_nci"]


@pytest.mark.filterwarnings("ignore:`pub_covidcast_meta` uses the V4 Epidata API")
def test_pub_covidcast_meta_last_update_is_utc_datetime(fake_server: Callable[..., FakeServer]) -> None:
    body = (
        '{"result": 1, "message": "success", "epidata": ['
        '{"data_source": "s", "signal": "x", "time_type": "day", "geo_type": "state", "last_update": 1760622300}]}'
    )
    fake_server(lambda url, params: body)
    call = EpiDataContext(use_cache=False).pub_covidcast_meta()
    df = call.df()
    assert isinstance(df["last_update"].dtype, pd.DatetimeTZDtype)
    assert df["last_update"][0].isoformat() == "2025-10-16T13:45:00+00:00"
    row = call.classic()["epidata"][0]
    assert row["last_update"].isoformat() == "2025-10-16T13:45:00+00:00"


def test_key_filters_are_sent_as_extra_keys() -> None:
    ctx = EpiDataContext()
    snap = ctx.epidata_snapshot("nwss", "a", "sewershed", pcr_target="sars-cov-2", sample_index=["1", "2"])
    assert _params(snap.request_url())["extra_keys"] == ["pcr_target:sars-cov-2,sample_index:1,sample_index:2"]
    arch = ctx.epidata_archive("nwss", "a", "sewershed", pcr_target="sars-cov-2")
    assert _params(arch.request_url())["extra_keys"] == ["pcr_target:sars-cov-2"]
    for call in (
        ctx.epidata("nwss", "a", "sewershed", pcr_target="sars-cov-2"),
        ctx.epidata("nwss", "a", "sewershed", report_time="<2025-01-01", pcr_target="sars-cov-2"),
    ):
        assert _params(call.request_url())["extra_keys"] == ["pcr_target:sars-cov-2"]
    assert "extra_keys" not in _params(ctx.epidata_snapshot("nwss", "a", "sewershed").request_url())
