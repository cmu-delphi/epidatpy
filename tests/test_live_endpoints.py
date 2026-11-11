"""Live calls to every classic endpoint, with and without a wildcard time range.

Mirrors the `endpoint_calls()` table in epidatr's `helper-endpoints.R`. Each call must return rows,
raise no warning beyond the known endpoint-status notices, and give every column the dtype its
field metadata promises. Private endpoints need their own `SECRET_API_AUTH_*` key and are skipped without it.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import pandas as pd
import pytest

from epidatpy import EpiDataContext, EpiRange
from epidatpy._model import EpidataFieldType

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.environ.get("DELPHI_EPIDATA_KEY"), reason="DELPHI_EPIDATA_KEY not available."),
    pytest.mark.filterwarnings(
        "error",
        "ignore:.*uses the V4 Epidata API",
        "ignore:.*covers a data source that is no longer updated",
        "ignore:.*is in week format",
    ),
]


def _key(name: str) -> str:
    return os.environ.get(f"SECRET_API_AUTH_{name}", "")


def _rows(endpoint: str, time_arg: str, time_range: Any, secret: str | None = None, **kwargs: Any) -> list[Any]:
    """Two table rows for one endpoint: an explicit time range, then `*`. Private endpoints skip without their key."""
    if secret is not None:
        kwargs["auth"] = _key(secret)
    marks = [pytest.mark.skipif(not _key(secret), reason=f"{secret} key not available.")] if secret else []
    return [
        pytest.param(
            lambda c, t=t: getattr(c, endpoint)(**{time_arg: t}, **kwargs),
            id=f"{endpoint} {suffix}".strip(),
            marks=marks,
        )
        for t, suffix in ((time_range, ""), ("*", "wildcard"))
    ]


ROWS: list[Any] = [
    *_rows("pub_covid_hosp_facility", "collection_weeks", EpiRange(20200101, 20200501), hospital_pks="100075"),
    *_rows("pub_covid_hosp_state_timeseries", "dates", EpiRange(20200101, 20200501), states="fl"),
    *_rows(
        "pub_covidcast",
        "time_values",
        EpiRange(20200601, 20200801),
        data_source="jhu-csse",
        signals="confirmed_7dav_incidence_prop",
        geo_type="state",
        time_type="day",
        geo_values="ca,fl",
    ),
    *_rows("pub_dengue_nowcast", "epiweeks", EpiRange(201401, 202301), locations="pr"),
    *_rows("pub_ecdc_ili", "epiweeks", EpiRange(201901, 202001), regions="austria"),
    *_rows("pub_flusurv", "epiweeks", EpiRange(201701, 201801), locations="CA"),
    *_rows("pub_fluview_clinical", "epiweeks", EpiRange(201601, 201701), regions="nat"),
    *_rows("pub_fluview", "epiweeks", EpiRange(201201, 202005), regions="nat"),
    *_rows("pub_gft", "epiweeks", EpiRange(201201, 202001), locations="hhs1"),
    *_rows("pub_kcdc_ili", "epiweeks", 200436, regions="ROK"),
    *_rows("pub_nidss_dengue", "epiweeks", EpiRange(201201, 201301), locations="taipei"),
    *_rows("pub_nidss_flu", "epiweeks", EpiRange(201501, 201601), regions="taipei"),
    *_rows("pub_nowcast", "epiweeks", EpiRange(201201, 201301), locations="ca"),
    *_rows("pub_paho_dengue", "epiweeks", EpiRange(201401, 201501), regions="ca"),
    *_rows("pub_wiki", "time_values", EpiRange(201501, 201601), articles="avian_influenza", time_type="week"),
    *_rows("pub_wiki", "time_values", EpiRange(20150101, 20200101), articles="avian_influenza", time_type="day"),
    *_rows("pvt_cdc", "epiweeks", EpiRange(201501, 201601), "CDC", locations="fl,ca"),
    *_rows("pvt_dengue_sensors", "epiweeks", EpiRange(201501, 202001), "SENSORS", names="ght", locations="ag"),
    *_rows("pvt_ght", "epiweeks", EpiRange(199301, 202304), "GHT", locations="ma", query="how to get over the flu"),
    *_rows("pvt_quidel", "epiweeks", EpiRange(201201, 202001), "QUIDEL", locations="hhs1"),
    *_rows("pvt_sensors", "epiweeks", EpiRange(201501, 202001), "SENSORS", names="sar3", locations="nat"),
    *_rows("pvt_twitter", "time_values", EpiRange(201501, 202001), "TWITTER", locations="CA", time_type="week"),
    *_rows("pvt_twitter", "time_values", EpiRange(20150101, 20200101), "TWITTER", locations="CA", time_type="day"),
]


def _assert_meta_dtypes(df: pd.DataFrame, call: Any) -> None:
    """Every returned column has the dtype its field type promises. Dates may stay strings if unparseable."""
    for info in call.meta:
        if info.name not in df.columns:
            continue
        col = df[info.name]
        match info.type:
            case EpidataFieldType.int:
                ok = str(col.dtype) == "Int64"
            case EpidataFieldType.float:
                ok = str(col.dtype) == "Float64"
            case EpidataFieldType.bool:
                ok = str(col.dtype) == "bool"
            case EpidataFieldType.categorical:
                ok = isinstance(col.dtype, pd.CategoricalDtype)
            case EpidataFieldType.date | EpidataFieldType.date_or_epiweek:
                ok = str(col.dtype) == "string" or pd.api.types.is_datetime64_any_dtype(col)
            case EpidataFieldType.epoch_seconds | EpidataFieldType.datetimetz:
                ok = pd.api.types.is_datetime64_any_dtype(col)
            case _:
                ok = str(col.dtype) == "string"
        assert ok, f"column `{info.name}` has dtype {col.dtype}, not what type {info.type.name} promises"


@pytest.mark.parametrize("make_call", ROWS)
def test_endpoint_returns_rows_with_metadata_dtypes(make_call: Callable[[EpiDataContext], Any]) -> None:
    call = make_call(EpiDataContext(use_cache=False))
    df = call.df()
    assert len(df) > 0
    _assert_meta_dtypes(df, call)


@pytest.mark.parametrize(
    "make_call",
    [
        pytest.param(lambda c: c.pub_delphi(system="ec", epiweek=201501), id="pub_delphi"),
        pytest.param(lambda c: c.pub_meta(), id="pub_meta"),
        pytest.param(lambda c: c.pub_fluview_meta(), id="pub_fluview_meta"),
        pytest.param(lambda c: c.pub_covidcast_meta(), id="pub_covidcast_meta"),
    ],
)
def test_metadata_endpoint_returns_rows(make_call: Callable[[EpiDataContext], Any]) -> None:
    call = make_call(EpiDataContext(use_cache=False))
    result = call.classic() if call.only_supports_classic else call.df()
    assert len(result) > 0
