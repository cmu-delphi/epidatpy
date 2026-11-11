"""Live tests: every test here talks to the real Epidata servers.

They need `DELPHI_EPIDATA_KEY`, and the private classic endpoints also need their own `SECRET_API_AUTH_*` key.
Set `EPIDATPY_CAST_BASE_URL` to point the cast tests at a non-default server. The sections mirror epidatr's
`test-live.R` (classic endpoint table and cast block). The cache tests are in `test_live_cache.py`.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import pandas as pd
import pytest

from epidatpy import EpiDataContext, EpiDataHTTPError, EpiRange, InvalidArgumentException
from epidatpy._constants import CAST_BASE_URL
from epidatpy._model import EpidataFieldType

auth = os.environ.get("DELPHI_EPIDATA_KEY", "")
# Point the cast tests at a non-default server (e.g. dev) without touching the classic endpoints.
cast_base_url = os.environ.get("EPIDATPY_CAST_BASE_URL") or CAST_BASE_URL

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not auth, reason="DELPHI_EPIDATA_KEY not available."),
]

# Classic calls must be warning-free apart from the known endpoint-status notices.
CLASSIC_WARNINGS = pytest.mark.filterwarnings(
    "error",
    "ignore:.*uses the V4 Epidata API",
    "ignore:.*covers a data source that is no longer updated",
    "ignore:.*is in week format",
)

# ---------------------------------------------------------------------------
# Classic endpoints: each call returns rows whose dtypes match the field metadata.
# ---------------------------------------------------------------------------


def _key(name: str) -> str:
    return os.environ.get(f"SECRET_API_AUTH_{name}", "")


def _one(endpoint: str, row_id: str, **kwargs: Any) -> Any:
    """A table row for one fixed call."""
    return pytest.param(lambda c: getattr(c, endpoint)(**kwargs), id=row_id)


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
    _one("pub_covid_hosp_facility_lookup", "pub_covid_hosp_facility_lookup state", state="fl"),
    _one("pub_covid_hosp_facility_lookup", "pub_covid_hosp_facility_lookup city", city="southlake"),
    _one(
        "pub_covid_hosp_facility",
        "pub_covid_hosp_facility week range",
        hospital_pks="100075",
        collection_weeks=EpiRange(202001, 202030),
    ),
    _one(
        "pub_covidcast",
        "pub_covidcast all geo_values",
        data_source="jhu-csse",
        signals="confirmed_7dav_incidence_prop",
        geo_type="state",
        time_type="day",
        geo_values="*",
        time_values=EpiRange(20200601, 20200801),
    ),
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
    *_rows(
        "pvt_norostat",
        "epiweeks",
        201233,
        "NOROSTAT",
        location="Minnesota, Ohio, Oregon, Tennessee, and Wisconsin",
    ),
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


@CLASSIC_WARNINGS
@pytest.mark.parametrize("make_call", ROWS)
def test_endpoint_returns_rows_with_metadata_dtypes(make_call: Callable[[EpiDataContext], Any]) -> None:
    call = make_call(EpiDataContext(use_cache=False))
    df = call.df()
    assert len(df) > 0
    _assert_meta_dtypes(df, call)


@CLASSIC_WARNINGS
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


# ---------------------------------------------------------------------------
# Cast endpoints
# ---------------------------------------------------------------------------

# Rows are capped with `limit` so a query that happens to cover a large geo
# type stays a smoke test rather than a bulk download. The cap is not a filter:
# the query has no stable sort order, so which rows come back varies per call.
CAST_QUERY_LIMIT = 500


def _ctx() -> EpiDataContext:
    return EpiDataContext(cast_base_url=cast_base_url)


# (source, signal, geo_type) — kept in sync with R's `cast_queries`.
# Commented-out rows mirror the R suite's TODOs; uncomment when server-side
# row limits / data backfills allow.
CAST_QUERIES = [
    ("nssp", "pct_ed_visits_influenza", "state"),
    ("nssp", "pct_ed_visits_influenza", "hhs"),
    ("nssp", "pct_ed_visits_covid", "nation"),
    ("nssp", "pct_ed_visits_influenza", "county"),
    ("nhsn", "confirmed_admissions_flu_ew", "state"),
    ("nhsn", "confirmed_admissions_flu_ew", "hhs"),
    ("nhsn", "confirmed_admissions_flu_ew", "nation"),
    ("pophive", "flu_pct_ed", "state"),
    ("pophive", "flu_pct_ed", "hhs"),
    ("pophive", "flu_n_ed", "state"),
    ("pophive", "flu_n_ed", "hhs"),
    ("pophive", "flu_n_ed", "nation"),
    ("nwss", "covid_avg_conc", "sewershed"),
    ("nwss", "flu_avg_conc", "sewershed"),
    # Sources carrying ci_lower/ci_upper, so the confidence bounds get parsed:
    # ("nickel_beta", "covid_ed", "state"),  # Deleted on the server, so it returns 503.
    ("sleepcycle", "pct_cough_2_plus_7dav", "state"),
    # Weekly surveillance sources:
    ("fluview_ilinet", "ili", "state"),
    ("fluview_resp_lab_clinical", "pct_positive", "hhs"),
    ("nchs_mortality", "deaths_covid_incidence_num", "state"),
]


def _assert_cast_frame(ctx: EpiDataContext, source: str, df: pd.DataFrame) -> None:
    """Shared contract for a snapshot/archive result: non-empty, parsed times,
    and no missing key values.

    The key columns come from the source's own `metadata/` declaration (nwss
    adds `nwss_source`/`sample_index`, pophive adds `age_group`), so a schema
    change surfaces here instead of drifting past a hardcoded list. A row with
    a missing key value can't be identified, so it's unusable.
    """
    assert len(df) > 0
    assert pd.api.types.is_datetime64_any_dtype(df["reference_time"])
    assert isinstance(df["report_time"].dtype, pd.DatetimeTZDtype)
    assert str(df["report_time"].dt.tz) == "UTC"

    keys = ctx.epidata_meta(source=source)["key_columns"]
    absent = [c for c in keys if c not in df.columns]
    assert not absent, f"{source}: declared key columns absent from result: {absent}"
    na = df[keys].isna().sum()
    assert not na.any(), f"{source}: missing values in key columns: {na[na > 0].to_dict()}"


def _bound(value: str) -> pd.Timestamp:
    """`value` as a UTC instant, comparable with a `report_time` column."""
    return pd.Timestamp(value, tz="UTC")


class TestCastEndpoints:
    """Live network tests for the CAST API."""

    def test_epidata_meta_all_sources(self) -> None:
        meta = _ctx().epidata_meta()
        assert isinstance(meta, dict)
        assert {q[0] for q in CAST_QUERIES}.issubset(meta)

    def test_epidata_meta_per_source(self) -> None:
        ctx = _ctx()
        for src in sorted({q[0] for q in CAST_QUERIES}):
            source_meta = ctx.epidata_meta(source=src)
            assert isinstance(source_meta, dict), f"metadata response missing source {src!r}"
            assert len(source_meta.get("signals", [])) > 0
            assert len(source_meta.get("geo_types", [])) > 0

    @pytest.mark.parametrize("source,signal,geo_type", CAST_QUERIES)
    def test_epidata_snapshot(self, source: str, signal: str, geo_type: str) -> None:
        ctx = _ctx()
        df = ctx.epidata_snapshot(source=source, signals=signal, geo_type=geo_type, limit=CAST_QUERY_LIMIT).df()
        _assert_cast_frame(ctx, source, df)
        assert df.attrs == {"cast_source": source, "cast_kind": "snapshot"}
        # Sources with an aux schema (currently nwss): merging aux data onto one row keeps
        # that row and appends aux columns.
        try:
            has_aux = bool(ctx._aux_key_columns(source))
        except EpiDataHTTPError:  # the server rejects sources with no aux table
            has_aux = False
        if has_aux:
            small = df.head(1)
            merged = ctx.epidata_aux(small)
            assert isinstance(merged, pd.DataFrame)
            assert len(merged) == 1
            assert len(merged.columns) > len(small.columns)

    @pytest.mark.parametrize("source,signal,geo_type", CAST_QUERIES)
    def test_epidata_archive(self, source: str, signal: str, geo_type: str) -> None:
        ctx = _ctx()
        df = ctx.epidata_archive(source=source, signals=signal, geo_type=geo_type, limit=CAST_QUERY_LIMIT).df()
        _assert_cast_frame(ctx, source, df)
        assert df.attrs == {"cast_source": source, "cast_kind": "archive"}

    def test_epidata_snapshot_key_filters(self) -> None:
        # Extra key filters are applied server-side via `extra_keys`.
        df = (
            _ctx()
            .epidata_snapshot(
                source="nwss",
                signals="covid_avg_conc",
                geo_type="sewershed",
                limit=CAST_QUERY_LIMIT,
                nwss_source="State_Territory",
            )
            .df()
        )
        assert len(df) > 0
        assert set(df["nwss_source"]) == {"State_Territory"}

    def test_epidata_snapshot_multiple_geo_types(self) -> None:
        # nssp has data for both "state" and "hhs"; one request is issued per
        # geo_type and the results are combined into a single DataFrame.
        df = (
            _ctx()
            .epidata_snapshot(
                source="nssp", signals="pct_ed_visits_influenza", geo_type=["state", "hhs"], limit=CAST_QUERY_LIMIT
            )
            .df()
        )
        assert len(df) > 0
        assert set(df["geo_type"].unique()).issubset({"state", "hhs"})
        assert {"state", "hhs"}.issubset(set(df["geo_type"].unique()))

    def test_epidata_router_dispatch(self) -> None:
        # `snapshot_date="*"` routes to archive (no report_time sent);
        # verify the archive's `report_time` column comes back.
        ctx = _ctx()
        df = ctx.epidata(
            source="nssp",
            signals="pct_ed_visits_influenza",
            geo_type="state",
            snapshot_date="*",
            limit=CAST_QUERY_LIMIT,
        ).df()
        assert "report_time" in df.columns

    def test_epidata_mutually_exclusive_report_time_and_snapshot_date(self) -> None:
        with pytest.raises(InvalidArgumentException):
            _ctx().epidata(
                source="nssp",
                signals="pct_ed_visits_influenza",
                geo_type="state",
                snapshot_date="2025-10-16",
                report_time="2025-10-16",
            )

    def test_epidata_snapshot_filters(self) -> None:
        # The geo + reference_time filters are applied by the server.
        df = (
            _ctx()
            .epidata_snapshot(
                source="nssp",
                signals="pct_ed_visits_influenza",
                geo_type="state",
                geo_values="ca,ny",
                reference_time=EpiRange("2025-01-01", "2025-06-01"),
            )
            .df()
        )
        if len(df) > 0:
            assert set(df["geo_value"].str.lower().unique()).issubset({"ca", "ny"})
            assert df["reference_time"].min() >= pd.Timestamp("2025-01-01")
            assert df["reference_time"].max() <= pd.Timestamp("2025-06-01")

    def test_epidata_aux_base_pull(self) -> None:
        # Narrow to a single real site: an unfiltered pull returns the full
        # report-time history for every matching row, which is slow and large.
        df = _ctx().epidata_aux("nwss", sample_index="5886455", pcr_target="sars-cov-2").df()
        assert len(df) > 0
        assert isinstance(df["report_time"].dtype, pd.DatetimeTZDtype)
        assert pd.api.types.is_datetime64_any_dtype(df["reference_time"])
        assert set(df["sample_index"].unique()) == {"5886455"}

    def test_epidata_aux_merge_onto_snapshot(self) -> None:
        # One sewershed keeps the base to a few sample sites, so the merge's
        # inferred key filters keep the aux pull small.
        base = (
            _ctx()
            .epidata_snapshot(
                source="nwss", signals="covid_avg_conc", geo_type="sewershed", geo_values="135", limit=CAST_QUERY_LIMIT
            )
            .df()
        )
        if len(base) == 0:
            pytest.skip("no nwss snapshot data available to merge onto")
        merged = _ctx().epidata_aux(base)
        assert isinstance(merged, pd.DataFrame)
        assert len(merged) == len(base)
        assert set(base.columns).issubset(set(merged.columns))
        # Must actually bring aux columns in: the assertions above all hold when
        # the merge silently no-ops and returns `base` itself.
        assert set(merged.columns) - set(base.columns)
        assert merged["population_served"].notna().any()

    def test_cast_versioning_args_reach_the_server(self) -> None:
        """Mirrors epidatr's "cast versioning args reach the server": the
        `snapshot_date` / `report_time` bounds are applied server-side, not
        silently dropped."""
        ctx = _ctx()

        snap = ctx.epidata_snapshot(
            source="nssp",
            signals="pct_ed_visits_influenza",
            geo_type="state",
            snapshot_date="2025-01-01",
            limit=CAST_QUERY_LIMIT,
        ).df()
        assert len(snap) > 0
        assert (snap["report_time"] <= _bound("2025-01-01")).all()

        lt = ctx.epidata_archive(
            source="nssp",
            signals="pct_ed_visits_influenza",
            geo_type="state",
            report_time="<2025-06-01",
            limit=CAST_QUERY_LIMIT,
        ).df()
        assert len(lt) > 0
        assert (lt["report_time"] < _bound("2025-06-01")).all()

        # A single-day EpiRange pins report_time to that one day.
        one_day = lt["report_time"].max().date()
        eq = ctx.epidata_archive(
            source="nssp",
            signals="pct_ed_visits_influenza",
            geo_type="state",
            report_time=EpiRange(one_day, one_day),
            limit=CAST_QUERY_LIMIT,
        ).df()
        assert len(eq) > 0
        assert (eq["report_time"].dt.date == one_day).all()

        # Both bounds go server-side as an inclusive "from:to" range.
        rng = ctx.epidata_archive(
            source="nssp",
            signals="pct_ed_visits_influenza",
            geo_type="state",
            report_time=EpiRange("2025-01-01", "2025-06-01"),
            limit=CAST_QUERY_LIMIT,
        ).df()
        assert len(rng) > 0
        assert (rng["report_time"] >= _bound("2025-01-01")).all()
        assert (rng["report_time"] <= _bound("2025-06-01")).all()
