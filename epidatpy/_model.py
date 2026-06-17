from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Final,
    Literal,
    TypedDict,
    Union,
    cast,
)

if TYPE_CHECKING:
    from pandas import DataFrame

from epiweeks import Week

from ._parse import parse_user_date_or_week

GeoType = Literal["nation", "msa", "hrr", "hhs", "state", "county"]
TimeType = Literal["day", "week"]
EpiDateLike = Union[int, str, date, Week]
EpiRangeDict = TypedDict("EpiRangeDict", {"from": EpiDateLike, "to": EpiDateLike})
EpiRangeLike = Union[int, str, "EpiRange", EpiRangeDict, date, Week]
EpiRangeParam = Union[EpiRangeLike, Sequence[EpiRangeLike]]
StringParam = Union[str, Sequence[str]]
IntParam = Union[int, Sequence[int]]


class EpiDataResponse(TypedDict):
    """response from the API"""

    result: int
    message: str
    epidata: list


def format_date(d: EpiDateLike) -> str:
    if isinstance(d, date):
        # YYYYMMDD
        return d.strftime("%Y%m%d")
    if isinstance(d, Week):
        # YYYYww
        return d.cdcformat()
    return str(d)


def format_item(value: EpiRangeLike) -> str:
    """Cast values and/or range to a string."""
    if isinstance(value, (date, Week)):
        return format_date(value)
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, EpiRange):
        return str(value)
    if isinstance(value, dict) and "from" in value and "to" in value:
        return f"{format_date(value['from'])}-{format_date(value['to'])}"
    return str(value)


def format_list(values: EpiRangeParam) -> str:
    """Turn a list/tuple of values/ranges into a comma-separated string."""
    if isinstance(values, Sequence) and not isinstance(values, str):
        # ty drops the element type when narrowing a Sequence via isinstance,
        # widening it to `object`; cast restores what we already know here.
        seq = cast("Sequence[EpiRangeLike]", values)
        return ",".join([format_item(value) for value in seq])
    return format_item(values)


class EpiRange:
    """Range object for dates/epiweeks"""

    def __init__(self, start: EpiDateLike, end: EpiDateLike) -> None:
        # check if types are correct
        self.start = parse_user_date_or_week(start)
        self.end = parse_user_date_or_week(end)
        # swap if wrong order
        # complicated construct for typing inference
        if self.end < self.start:
            self.start, self.end = self.end, self.start

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{format_date(self.start)}-{format_date(self.end)}"


class InvalidArgumentException(Exception):
    """exception for an invalid argument"""


class OnlySupportsClassicFormatException(Exception):
    """the endpoint only supports the classic message format, due to an non-standard behavior"""


class EpidataFieldType(Enum):
    """field type"""

    text = 0
    int = 1
    float = 2
    date = 3
    epiweek = 4
    categorical = 5
    bool = 6
    date_or_epiweek = 7


@dataclass
class EpidataFieldInfo:
    """meta data information about an return field"""

    name: Final[str] = ""
    type: Final[EpidataFieldType] = EpidataFieldType.text
    description: Final[str] = ""
    categories: Final[Sequence[str]] = field(default_factory=list)


def add_endpoint_to_url(url: str, endpoint: str) -> str:
    if not url.endswith("/"):
        url += "/"
    url += endpoint
    return url


ApiVersion = Literal["classic", "cast"]

# (geo_values, reference_time, report_time) — passed straight to cast_filter.
CastPostFilter = tuple[
    Union[str, Sequence[str]],
    Union[str, "EpiRangeParam"],
    Union[str, "EpiRange", None],
]


def cast_filter(
    df: DataFrame,
    geo_values: str | Sequence[str] = "*",
    reference_time: str | EpiRangeParam = "*",
    report_time: str | EpiRange | None = None,
) -> DataFrame:
    """Local post-filter for CAST-API responses.

    The CAST endpoints return data that's only weakly filtered server-side.
    Apply geo, reference_time, and EpiRange report_time-lower-bound filters locally.
    """
    from pandas import to_datetime

    if not hasattr(df, "columns"):
        return df

    if geo_values != "*" and "geo_value" in df.columns:
        if isinstance(geo_values, str):
            wanted = [g.strip().lower() for g in geo_values.split(",")]
        else:
            wanted = [str(g).strip().lower() for g in geo_values]
        df = df[df["geo_value"].str.lower().isin(wanted)]

    if reference_time != "*" and "reference_time" in df.columns:
        df = _filter_by_timeset(df, "reference_time", reference_time, to_datetime)

    if isinstance(report_time, EpiRange) and "report_time" in df.columns:
        df = _filter_by_timeset(df, "report_time", report_time, to_datetime)

    return df


def _filter_by_timeset(
    df: DataFrame,
    column: str,
    timeset: str | EpiRangeParam | EpiRange,
    to_datetime: Callable,
) -> DataFrame:
    values = df[column]
    if isinstance(timeset, EpiRange):
        lo = to_datetime(format_date(timeset.start))
        hi = to_datetime(format_date(timeset.end))
        return df[(values >= lo) & (values <= hi)]

    if isinstance(timeset, (str, int, date, Week)):
        wanted = to_datetime([format_item(timeset)])
    else:
        wanted = to_datetime([format_item(v) for v in timeset])
    return df[values.isin(wanted)]
