"""Live tests for the CAST API endpoints.

Mirrors the `epidata_* (cast API)` block in epidatr's `tests/testthat/test-live.R`.
Gated on `DELPHI_EPIDATA_KEY` so it only runs against the live server when
a key is present.
"""

import os

import pandas as pd
import pytest

from epidatpy import EpiDataContext, EpiRange, InvalidArgumentException

auth = os.environ.get("DELPHI_EPIDATA_KEY", "")

# (source, signal, geo_type) — kept in sync with R's `cast_queries`.
# Commented-out rows mirror the R suite's TODOs; uncomment when server-side
# row limits / data backfills allow.
CAST_QUERIES = [
    ("nssp", "pct_ed_visits_influenza", "state"),
    ("nssp", "pct_ed_visits_influenza", "hhs"),
    # ("nssp", "pct_ed_visits_influenza", "county"),  # ignored: row limit
    # ("nhsn", "confirmed_admissions_flu_ew", "state"),  # ignored: no data
    # ("nhsn", "confirmed_admissions_flu_ew", "hhs"),
    # ("nhsn", "confirmed_admissions_flu_ew", "national"),
    ("pophive", "flu_pct_ed", "state"),
    ("pophive", "flu_pct_ed", "hhs"),
    ("pophive", "flu_n_ed", "state"),
    ("pophive", "flu_n_ed", "hhs"),
    ("pophive", "flu_n_ed", "nation"),
    ("nwss", "covid_avg_conc", "sewershed"),
]


@pytest.mark.live
@pytest.mark.skipif(not auth, reason="DELPHI_EPIDATA_KEY not available.")
class TestCastEndpoints:
    """Live network tests for the CAST API."""

    def test_epidata_meta_per_source(self) -> None:
        ctx = EpiDataContext()
        for src in sorted({q[0] for q in CAST_QUERIES}):
            meta = ctx.epidata_meta(source=src)
            assert src in meta, f"metadata response missing source {src!r}"
            source_meta = meta[src]
            assert isinstance(source_meta, dict)
            assert len(source_meta.get("signals", [])) > 0
            assert len(source_meta.get("geo_types", [])) > 0

    @pytest.mark.parametrize("source,signal,geo_type", CAST_QUERIES)
    def test_epidata_snapshot(self, source: str, signal: str, geo_type: str) -> None:
        df = EpiDataContext().epidata_snapshot(source=source, signals=signal, geo_type=geo_type).df()
        assert len(df) > 0
        assert pd.api.types.is_datetime64_any_dtype(df["reference_time"])
        assert pd.api.types.is_datetime64_any_dtype(df["report_time"])

    @pytest.mark.parametrize("source,signal,geo_type", CAST_QUERIES)
    def test_epidata_archive(self, source: str, signal: str, geo_type: str) -> None:
        df = EpiDataContext().epidata_archive(source=source, signals=signal, geo_type=geo_type).df()
        assert len(df) > 0
        assert pd.api.types.is_datetime64_any_dtype(df["reference_time"])
        assert pd.api.types.is_datetime64_any_dtype(df["report_time"])

    def test_epidata_router_dispatch(self) -> None:
        # `snapshot_date="*"` routes to archive (no report_time sent);
        # verify the archive's `report_time` column comes back.
        ctx = EpiDataContext()
        df = ctx.epidata(
            source="nssp",
            signals="pct_ed_visits_influenza",
            geo_type="state",
            snapshot_date="*",
        ).df()
        assert "report_time" in df.columns

    def test_epidata_mutually_exclusive_report_time_and_snapshot_date(self) -> None:
        with pytest.raises(InvalidArgumentException):
            EpiDataContext().epidata(
                source="nssp",
                signals="pct_ed_visits_influenza",
                geo_type="state",
                snapshot_date="2025-10-16",
                report_time="2025-10-16",
            )

    def test_epidata_snapshot_local_filters(self) -> None:
        # Local geo + reference_time filter should narrow rows without hitting the server twice.
        df = (
            EpiDataContext()
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
