from typing import Callable, Iterable, Optional, Set, cast

from typing import Union
from datetime import date, datetime
from epiweeks import Week


def parse_api_date(value: Union[str, int, float, None]) -> Optional[date]:
    if value is None:
        return value
    v = str(value)
    if len(v) == 10: # yyyy-mm-dd
        d = datetime.strptime(v, "%Y-%m-%d").date()
    else:
        d = datetime.strptime(v, "%Y%m%d").date()
    return d


def parse_api_week(value: Union[str, int, float, None]) -> Optional[date]:
    if value is None:
        return None
    return cast(date, Week.fromstring(str(value)).startdate())


def parse_api_date_or_week(value: Union[str, int, float, None]) -> Optional[date]:
    if value is None:
        return None
    v = str(value)
    print(len(v))
    if len(v) == 6:
        d = cast(date, Week.fromstring(v).startdate())
    elif len(v) == 10: # yyyy-mm-dd
        d = datetime.strptime(v, "%Y-%m-%d").date()
    else:
        d = datetime.strptime(v, "%Y%m%d").date()
    return d


def fields_to_predicate(
    fields: Optional[Iterable[str]] = None,
) -> Callable[[str], bool]:
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
