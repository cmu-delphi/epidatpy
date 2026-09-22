# The API deals in naive civil dates (e.g. "20210101"), not timestamps, so
# `datetime.strptime()` without a timezone is intentional throughout this file.
# ruff: noqa: DTZ007
from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Literal

from epiweeks import Week

if TYPE_CHECKING:
    from ._model import EpiRange

# cast-API UTC timestamp bound, e.g. "2025-10-16T13:45:00Z" or "...:45:00.123Z".
_UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?Z$")


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


def format_report_time_bound(value: str | int | date | datetime | Week) -> str | None:
    """Format a date or UTC timestamp bound for cast-API queries.

    Returns None for invalid timestamp strings.
    """
    if isinstance(value, str) and _UTC_TIMESTAMP_RE.match(value):
        return value
    if isinstance(value, str) and "T" in value:
        return None
    if isinstance(value, datetime):
        aware = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return aware.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, Week):
        value = value.startdate()
    parsed = value if isinstance(value, date) else parse_api_date(value)
    return parsed.strftime("%Y-%m-%d") if parsed is not None else None


def validate_report_time_query(report_time: str | int | date | datetime | Week | EpiRange | None) -> str | None:
    """Format the `report_time` argument for the CAST API `report_time_query` parameter.

    Accepts an operator-prefixed string (e.g. ``"<2025-10-16"``,
    ``">=2025-10-16T13:45:00Z"``) or an :class:`EpiRange` (dates only), which
    maps to an inclusive server-side range (``"from:to"``). Bare dates and the
    ``"="`` operator are rejected
    Returns ``None`` for ``None`` / ``"*"``.
    """
    from ._model import EpiRange, InvalidArgumentException  # avoid circular import

    if report_time is None or report_time == "*":
        return None

    if isinstance(report_time, EpiRange):
        start = report_time.start.startdate() if isinstance(report_time.start, Week) else report_time.start
        end = report_time.end.startdate() if isinstance(report_time.end, Week) else report_time.end
        return f"{start.strftime('%Y-%m-%d')}:{end.strftime('%Y-%m-%d')}"

    operator: str | None = None
    raw: str | int | date | datetime | Week = report_time
    if isinstance(report_time, str):
        for op in ("<=", ">=", "<", ">", "="):
            if report_time.startswith(op):
                operator = op
                raw = report_time[len(op) :]
                break

    if operator is None:
        raise InvalidArgumentException(
            "A bare date is not a valid `report_time` value. Use a comparison "
            "operator (e.g. '<2025-10-16') or an `EpiRange`. For data as it "
            "appeared on a specific date, use `snapshot_date` instead."
        )
    if operator == "=":
        raise InvalidArgumentException(
            "The `=` operator is not supported for `report_time`. Use a "
            "comparison operator (e.g. '<2025-10-16') or an `EpiRange`. For "
            "data as it appeared on a specific date, use `snapshot_date` instead."
        )

    formatted = format_report_time_bound(raw)
    if formatted is None:
        raise InvalidArgumentException(
            "Invalid `report_time` format. Must be a comparison string with an "
            "operator (e.g., '<2025-10-16', '>=2025-10-16', or "
            "'<=2025-10-16T13:45:00Z') or an `EpiRange`."
        )
    return f"{operator}{formatted}"


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
