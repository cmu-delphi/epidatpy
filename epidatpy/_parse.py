# The API deals in naive civil dates (e.g. "20210101"), not timestamps, so
# `datetime.strptime()` without a timezone is intentional throughout this file.
# ruff: noqa: DTZ007
from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Literal, Union

from epiweeks import Week

if TYPE_CHECKING:
    from ._model import EpiRange


def parse_api_date(value: str | float | None) -> date | None:
    if value is None:
        return value
    v = str(value)
    if len(v) == 10:  # yyyy-mm-dd
        d = datetime.strptime(v, "%Y-%m-%d").date()
    else:
        d = datetime.strptime(v, "%Y%m%d").date()
    return d


def parse_api_week(value: str | float | None) -> date | None:
    if value is None:
        return None
    return Week.fromstring(str(value)).startdate()


def parse_api_datetimetz(value: str | None) -> datetime | None:
    """Parse a CAST-API UTC timestamp such as ``2025-10-16T13:45:00Z`` to an aware datetime."""
    if value is None:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def parse_api_date_or_week(value: str | float | None) -> date | None:
    if value is None:
        return None
    v = str(value)
    if len(v) == 6:
        d = Week.fromstring(v).startdate()
    elif len(v) == 10:  # yyyy-mm-dd
        d = datetime.strptime(v, "%Y-%m-%d").date()
    else:
        d = datetime.strptime(v, "%Y%m%d").date()
    return d


def parse_user_date_or_week(
    value: str | int | date | Week, out_type: Literal["day", "week"] | None = None
) -> date | Week:
    if isinstance(value, Week):
        if out_type == "day":
            return value.startdate()
        return value

    if isinstance(value, date):
        if out_type == "week":
            return Week.fromdate(value)
        return value

    value = str(value)
    if out_type == "week":
        if len(value) == 6:
            return Week.fromstring(value)
        if len(value) == 8:
            return Week.fromdate(datetime.strptime(value, "%Y%m%d").date())
        if len(value) == 10:
            return Week.fromdate(datetime.strptime(value, "%Y-%m-%d").date())
    if out_type == "day":
        if len(value) == 8:
            return datetime.strptime(value, "%Y%m%d").date()
        if len(value) == 10:
            return datetime.strptime(value, "%Y-%m-%d").date()
    if out_type is None:
        if len(value) == 6:
            return Week.fromstring(value)
        if len(value) == 8:
            return datetime.strptime(value, "%Y%m%d").date()
        if len(value) == 10:
            return datetime.strptime(value, "%Y-%m-%d").date()

    raise ValueError(f"Cannot parse date or week from {value}")


_UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?Z$")

ReportTimeBound = Union[str, int, date, datetime, Week]


def format_report_time_bound(value: ReportTimeBound) -> str:
    """Format a `report_time` bound or `snapshot_date` the way the CAST API accepts it.

    Dates (``date``, ``YYYYMMDD``, ``YYYY-MM-DD``, ``Week``) become ``YYYY-MM-DD``;
    instants (``datetime`` or a trailing-``Z`` UTC timestamp string) become
    ``YYYY-MM-DDTHH:MM:SSZ``.
    """
    from ._model import InvalidArgumentException  # avoid circular import

    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc)
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Week):
        return value.startdate().strftime("%Y-%m-%d")
    raw = str(value)
    if _UTC_TIMESTAMP_RE.match(raw):
        return raw
    try:
        parsed = parse_api_date(raw)
    except ValueError:
        parsed = None
    if parsed is None:
        raise InvalidArgumentException(
            f"Invalid date or timestamp {value!r}. Use YYYY-MM-DD, YYYYMMDD, a `date`, "
            "a `datetime`, or a UTC timestamp like '2025-10-16T13:45:00Z'."
        )
    return parsed.strftime("%Y-%m-%d")


def validate_report_time_query(report_time: str | EpiRange | None) -> str | None:
    """Format the `report_time` argument for the CAST API `report_time_query` parameter.

    Accepts an operator-prefixed string (``<``, ``<=``, ``>``, ``>=`` followed by a
    date or UTC timestamp, e.g. ``"<2025-10-16"`` or ``"<=2025-10-16T13:45:00Z"``)
    or an :class:`EpiRange`, sent as an inclusive ``from:to`` date range.
    Returns ``None`` for ``None`` / ``"*"``. Bare dates and ``=`` are rejected:
    use `snapshot_date` for point-in-time data.
    """
    from ._model import EpiRange, InvalidArgumentException  # avoid circular import

    if report_time is None or report_time == "*":
        return None

    if isinstance(report_time, EpiRange):
        return f"{format_report_time_bound(report_time.start)}:{format_report_time_bound(report_time.end)}"

    hint = (
        " Use a comparison like '<2025-10-16' or an `EpiRange` for a date range; "
        "for data as it appeared on a specific date, use `snapshot_date` instead."
    )
    if not isinstance(report_time, str):
        raise InvalidArgumentException(f"A bare date is not a valid `report_time` value.{hint}")
    match = re.match(r"^(<=|>=|<|>|=)", report_time)
    if match is None:
        raise InvalidArgumentException(f"A bare date is not a valid `report_time` value.{hint}")
    operator = match.group(1)
    if operator == "=":
        raise InvalidArgumentException(f"The '=' operator is not supported for `report_time`.{hint}")
    return f"{operator}{format_report_time_bound(report_time[len(operator) :])}"


def fields_to_predicate(
    fields: Sequence[str] | None = None,
) -> Callable[[str], bool]:
    if not fields:
        return lambda _: True
    to_include: set[str] = set()
    to_exclude: set[str] = set()
    for f in fields:
        if f.startswith("-"):
            to_exclude.add(f[1:])
        else:
            to_include.add(f)
    return lambda f: f not in to_exclude and (not to_include or f in to_include)
