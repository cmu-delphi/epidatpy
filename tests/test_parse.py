import datetime

import pytest
from epiweeks import Week

from epidatpy._model import EpiRange, InvalidArgumentException
from epidatpy._parse import format_report_time_bound, parse_api_datetimetz, validate_report_time_query


def test_parse_api_datetimetz() -> None:
    parsed = parse_api_datetimetz("2025-10-16T13:45:00Z")
    assert parsed == datetime.datetime(2025, 10, 16, 13, 45, tzinfo=datetime.timezone.utc)
    assert parse_api_datetimetz(None) is None


def test_format_report_time_bound_dates() -> None:
    assert format_report_time_bound("2025-10-16") == "2025-10-16"
    assert format_report_time_bound("20251016") == "2025-10-16"
    assert format_report_time_bound(20251016) == "2025-10-16"
    assert format_report_time_bound(datetime.date(2025, 10, 16)) == "2025-10-16"
    assert format_report_time_bound(Week(2025, 1)) == f"{Week(2025, 1).startdate():%Y-%m-%d}"


def test_format_report_time_bound_instants() -> None:
    assert format_report_time_bound("2025-10-16T13:45:00Z") == "2025-10-16T13:45:00Z"
    assert format_report_time_bound("2025-10-16T13:45Z") == "2025-10-16T13:45Z"
    naive = datetime.datetime(2025, 10, 16, 13, 45, 0)  # noqa: DTZ001 - naive means UTC here
    assert format_report_time_bound(naive) == "2025-10-16T13:45:00Z"
    est = datetime.datetime(2025, 10, 16, 8, 45, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
    assert format_report_time_bound(est) == "2025-10-16T13:45:00Z"


def test_format_report_time_bound_invalid() -> None:
    with pytest.raises(InvalidArgumentException):
        format_report_time_bound("not-a-date")
    with pytest.raises(InvalidArgumentException):
        format_report_time_bound("2025-10-16T13:45:00")  # missing Z


def test_validate_report_time_query_none() -> None:
    assert validate_report_time_query(None) is None
    assert validate_report_time_query("*") is None


def test_validate_report_time_query_operators() -> None:
    assert validate_report_time_query("<2025-10-16") == "<2025-10-16"
    assert validate_report_time_query(">2025-10-16") == ">2025-10-16"
    assert validate_report_time_query("<=2025-10-16") == "<=2025-10-16"
    assert validate_report_time_query(">=2025-10-16") == ">=2025-10-16"
    assert validate_report_time_query("<=20251016") == "<=2025-10-16"
    assert validate_report_time_query("<=2025-10-16T13:45:00Z") == "<=2025-10-16T13:45:00Z"


def test_validate_report_time_query_epirange() -> None:
    assert validate_report_time_query(EpiRange(20251001, 20251016)) == "2025-10-01:2025-10-16"
    assert validate_report_time_query(EpiRange("2025-10-16", "2025-10-01")) == "2025-10-01:2025-10-16"


def test_validate_report_time_query_rejects_bare_date_and_equals() -> None:
    with pytest.raises(InvalidArgumentException, match="bare date"):
        validate_report_time_query("2025-10-16")
    with pytest.raises(InvalidArgumentException, match="bare date"):
        validate_report_time_query(20251016)  # type: ignore[arg-type]
    with pytest.raises(InvalidArgumentException, match="'='"):
        validate_report_time_query("=2025-10-16")


def test_validate_report_time_query_invalid() -> None:
    with pytest.raises(InvalidArgumentException):
        validate_report_time_query("not-a-date")
    with pytest.raises(InvalidArgumentException):
        validate_report_time_query("<garbage")
