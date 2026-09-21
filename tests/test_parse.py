import datetime

import pytest
from epiweeks import Week

from epidatpy import InvalidArgumentException
from epidatpy._model import EpiRange
from epidatpy._parse import format_report_time_bound, validate_report_time_query


def test_validate_report_time_query_none() -> None:
    assert validate_report_time_query(None) is None
    assert validate_report_time_query("*") is None


def test_validate_report_time_query_operators() -> None:
    assert validate_report_time_query("<2025-10-16") == "<2025-10-16"
    assert validate_report_time_query(">2025-10-16") == ">2025-10-16"
    assert validate_report_time_query("<=2025-10-16") == "<=2025-10-16"
    assert validate_report_time_query(">=2025-10-16") == ">=2025-10-16"


def test_validate_report_time_query_utc_timestamp_bound() -> None:
    assert validate_report_time_query("<=2025-10-16T13:45:00Z") == "<=2025-10-16T13:45:00Z"
    assert validate_report_time_query(">2025-10-16T13:45:30.123Z") == ">2025-10-16T13:45:30.123Z"


def test_validate_report_time_query_epirange() -> None:
    # EpiRange maps to an inclusive server-side range (dates only).
    assert validate_report_time_query(EpiRange(20251001, 20251016)) == "2025-10-01:2025-10-16"


def test_validate_report_time_query_rejects_bare_values() -> None:
    # Bare dates require comparison operators, an EpiRange, or snapshot_date.
    for bare in ("2025-10-16", 20251016, datetime.date(2025, 10, 16), Week(2025, 1)):
        with pytest.raises(InvalidArgumentException):
            validate_report_time_query(bare)


def test_validate_report_time_query_rejects_equality_operator() -> None:
    with pytest.raises(InvalidArgumentException):
        validate_report_time_query("=2025-10-16")


def test_validate_report_time_query_invalid() -> None:
    with pytest.raises(ValueError):
        validate_report_time_query("<garbage")
    # Malformed timestamp string.
    with pytest.raises(InvalidArgumentException):
        validate_report_time_query("<2025-10-16T13:45")


def test_format_report_time_bound() -> None:
    assert format_report_time_bound("2025-10-16") == "2025-10-16"
    assert format_report_time_bound(20251016) == "2025-10-16"
    assert format_report_time_bound(datetime.date(2025, 10, 16)) == "2025-10-16"
    assert format_report_time_bound(Week(2025, 1)) == f"{Week(2025, 1).startdate():%Y-%m-%d}"

    # A UTC timestamp string passes through unchanged.
    assert format_report_time_bound("2025-10-16T13:45:00Z") == "2025-10-16T13:45:00Z"
    # Naive datetimes are assumed UTC; aware ones are converted.
    assert (
        format_report_time_bound(datetime.datetime(2025, 10, 16, 13, 45))  # noqa: DTZ001
        == "2025-10-16T13:45:00Z"
    )
    tz = datetime.timezone(datetime.timedelta(hours=-5))
    assert (
        format_report_time_bound(datetime.datetime(2025, 10, 16, 8, 45, tzinfo=tz)) == "2025-10-16T13:45:00Z"
    )

    # Malformed timestamp returns None.
    assert format_report_time_bound("2025-10-16T13:45") is None
