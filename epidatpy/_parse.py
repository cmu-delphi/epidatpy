from datetime import date, datetime
from typing import Callable, Literal, Optional, Sequence, Set, Union

from epiweeks import Week


def parse_api_date(value: Union[str, int, float, None]) -> Optional[date]:
    if value is None:
        return value
    v = str(value)
    return datetime.strptime(v, "%Y%m%d").date()


def parse_api_week(value: Union[str, int, float, None]) -> Optional[date]:
    if value is None:
        return None
    return Week.fromstring(str(value)).startdate()


def parse_api_date_or_week(value: Union[str, int, float, None]) -> Optional[date]:
    if value is None:
        return None
    v = str(value)
    if len(v) == 6:
        d = Week.fromstring(v).startdate()
    else:
        d = datetime.strptime(v, "%Y%m%d").date()
    return d


def parse_user_date_or_week(
    value: Union[str, int, date, Week], out_type: Literal["day", "week", None] = None
) -> Union[date, Week]:
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


def fields_to_predicate(fields: Optional[Sequence[str]] = None) -> Callable[[str], bool]:
    if not fields:
        return lambda _: True
    to_include: Set[str] = set()
    to_exclude: Set[str] = set()
    for f in fields:
        if f.startswith("-"):
            to_exclude.add(f[1:])
        else:
            to_include.add(f)
    return lambda f: (f not in to_exclude and (not to_include or f in to_include))
