from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from os import environ
from typing import (
    Final,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    cast,
)
from urllib.parse import urlencode

from epiweeks import Week

from ._parse import (
    parse_api_date,
    parse_api_date_or_week,
    parse_api_week,
    parse_user_date_or_week,
)

GeoType = Literal["nation", "msa", "hrr", "hhs", "state", "county"]
TimeType = Literal["day", "week"]
EpiDateLike = Union[int, str, date, Week]
EpiRangeDict = TypedDict("EpiRangeDict", {"from": EpiDateLike, "to": EpiDateLike})
EpiRangeLike = Union[int, str, "EpiRange", EpiRangeDict, date, Week]
EpiRangeParam = Union[EpiRangeLike, Sequence[EpiRangeLike]]
StringParam = Union[str, Sequence[str]]
IntParam = Union[int, Sequence[int]]
ParamType = Union[StringParam, IntParam, EpiRangeParam]
CALL_TYPE = TypeVar("CALL_TYPE")


class EpiDataResponse(TypedDict):
    """response from the API"""

    result: int
    message: str
    epidata: List


def format_date(d: EpiDateLike) -> str:
    if isinstance(d, date):
        # YYYYMMDD
        return d.strftime("%Y%m%d")
    if isinstance(d, Week):
        # YYYYww
        return cast(str, d.cdcformat())
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
        return ",".join([format_item(value) for value in values])
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


class AEpiDataCall:
    """base epidata call class"""

    _base_url: Final[str]
    _endpoint: Final[str]
    _params: Final[Mapping[str, Optional[EpiRangeParam]]]
    meta: Final[Sequence[EpidataFieldInfo]]
    meta_by_name: Final[Mapping[str, EpidataFieldInfo]]
    only_supports_classic: Final[bool]
    use_cache: Final[bool]

    def __init__(
        self,
        base_url: str,
        endpoint: str,
        params: Mapping[str, Optional[EpiRangeParam]],
        meta: Optional[Sequence[EpidataFieldInfo]] = None,
        only_supports_classic: bool = False,
        use_cache: Optional[bool] = None,
        cache_max_age_days: Optional[int] = None,
    ) -> None:
        self._base_url = base_url
        self._endpoint = endpoint
        self._params = params
        self.only_supports_classic = only_supports_classic
        self.meta = meta or []
        self.meta_by_name = {k.name: k for k in self.meta}
        # Set the use_cache value from the constructor if present.
        # Otherwise check the USE_EPIDATPY_CACHE variable, accepting various "truthy" values.
        self.use_cache = (
            use_cache
            if use_cache is not None
            else (environ.get("USE_EPIDATPY_CACHE", "").lower() in ["true", "t", "1"])
        )
        # Set cache_max_age_days from the constructor, fall back to environment variable.
        if cache_max_age_days:
            self.cache_max_age_days = cache_max_age_days
        else:
            env_days = environ.get("EPIDATPY_CACHE_MAX_AGE_DAYS", "7")
            if env_days.isdigit():
                self.cache_max_age_days = int(env_days)
            else:  # handle string / negative / invalid enviromment variable
                self.cache_max_age_days = 7

    def _verify_parameters(self) -> None:
        # hook for verifying parameters before sending
        pass

    def _formatted_parameters(
        self,
        fields: Optional[Sequence[str]] = None,
    ) -> Mapping[str, str]:
        """Format this call into a [URL, Params] tuple"""
        all_params = dict(self._params)
        if fields:
            all_params["fields"] = fields
        return {k: format_list(v) for k, v in all_params.items() if v is not None}

    def request_arguments(
        self,
        fields: Optional[Sequence[str]] = None,
    ) -> Tuple[str, Mapping[str, str]]:
        """Format this call into a [URL, Params] tuple"""
        formatted_params = self._formatted_parameters(fields)
        full_url = add_endpoint_to_url(self._base_url, self._endpoint)
        return full_url, formatted_params

    def request_url(
        self,
        fields: Optional[Sequence[str]] = None,
    ) -> str:
        """Format this call into a full HTTP request url with encoded parameters"""
        self._verify_parameters()
        u, p = self.request_arguments(fields)
        query = urlencode(p)
        if query:
            return f"{u}?{query}"
        return u

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"EpiDataCall(endpoint={self._endpoint}, params={self._formatted_parameters()})"

    def _parse_value(
        self,
        key: str,
        value: Union[str, float, int, None],
        disable_date_parsing: Optional[bool] = False,
    ) -> Union[str, float, int, date, None]:
        meta = self.meta_by_name.get(key)
        if not meta or value is None:
            return value
        if meta.type == EpidataFieldType.date_or_epiweek and not disable_date_parsing:
            return parse_api_date_or_week(value)
        if meta.type == EpidataFieldType.date and not disable_date_parsing:
            return parse_api_date(value)
        if meta.type == EpidataFieldType.epiweek and not disable_date_parsing:
            return parse_api_week(value)
        if meta.type == EpidataFieldType.bool:
            return bool(value)
        return value

    def _parse_row(
        self,
        row: Mapping[str, Union[str, float, int, None]],
        disable_date_parsing: Optional[bool] = False,
    ) -> Mapping[str, Union[str, float, int, date, None]]:
        if not self.meta:
            return row
        return {k: self._parse_value(k, v, disable_date_parsing) for k, v in row.items()}
