import datetime

import pytest
from epiweeks import Week

from epidatpy._model import EpiRange
from epidatpy._parse import validate_report_time_query


def test_validate_report_time_query_none() -> None:
    assert validate_report_time_query(None) is None
    assert validate_report_time_query("*") is None


def test_validate_report_time_query_exact() -> None:
    assert validate_report_time_query("2025-10-16") == "=2025-10-16"
    assert validate_report_time_query(20251016) == "=2025-10-16"
    assert validate_report_time_query(datetime.date(2025, 10, 16)) == "=2025-10-16"
    assert validate_report_time_query("=2025-10-16") == "=2025-10-16"


def test_validate_report_time_query_week() -> None:
    # Week resolves to its start date.
    assert validate_report_time_query(Week(2025, 1)) == f"={Week(2025, 1).startdate():%Y-%m-%d}"


def test_validate_report_time_query_operators() -> None:
    assert validate_report_time_query("<2025-10-16") == "<2025-10-16"
    assert validate_report_time_query(">2025-10-16") == ">2025-10-16"
    assert validate_report_time_query("<=2025-10-16") == "<=2025-10-16"
    assert validate_report_time_query(">=2025-10-16") == ">=2025-10-16"


def test_validate_report_time_query_epirange() -> None:
    # EpiRange upper bound becomes "<to"; lower bound filtered locally.
    assert validate_report_time_query(EpiRange(20251001, 20251016)) == "<2025-10-16"


def test_validate_report_time_query_invalid() -> None:
    with pytest.raises(ValueError):
        validate_report_time_query("not-a-date")
    with pytest.raises(ValueError):
        validate_report_time_query("<garbage")
