from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

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


def validate_report_time_query(report_time: str | int | date | Week | EpiRange | None) -> str | None:
    """Format the `report_time` argument for the CAST API `report_time` parameter.

    Accepts an exact date, an operator-prefixed string (e.g. ``"<2025-10-16"``),
    or an :class:`EpiRange` (upper bound becomes ``"<to"``; the lower bound is
    filtered locally). Returns ``None`` for ``None`` / ``"*"``.
    """
    from ._model import EpiRange  # avoid circular import

    if report_time is None or report_time == "*":
        return None

    operator = "="
    raw: str | int | date | Week
    if isinstance(report_time, str) and report_time[:2] in ("<=", ">="):
        operator = report_time[:2]
        raw = report_time[2:]
    elif isinstance(report_time, str) and report_time[:1] in ("<", ">", "="):
        operator = report_time[0]
        raw = report_time[1:]
    elif isinstance(report_time, EpiRange):
        operator = "<"
        raw = report_time.end
    else:
        raw = report_time

    parsed: date | None
    if isinstance(raw, date):
        parsed = raw
    elif isinstance(raw, Week):
        parsed = raw.startdate()
    else:
        parsed = parse_api_date(raw)
    if parsed is None:
        raise ValueError(
            "Invalid `report_time` format. Must be a single date, an `EpiRange`, "
            "or a string with an operator (e.g., '<2025-10-16')."
        )
    return f"{operator}{parsed.strftime('%Y-%m-%d')}"


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
