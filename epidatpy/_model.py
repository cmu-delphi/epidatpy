from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import (
    Any,
    Dict,
    Final,
    Generic,
    Iterable,
    List,
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
from pandas import CategoricalDtype, DataFrame

from ._parse import (
    fields_to_predicate,
    parse_api_date,
    parse_api_date_or_week,
    parse_api_week,
)

EpiDateLike = Union[int, str, date, Week]
EpiRangeDict = TypedDict("EpiRangeDict", {"from": EpiDateLike, "to": EpiDateLike})
EpiRangeLike = Union[int, str, "EpiRange", EpiRangeDict, date, Week]


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


def format_list(values: Union[EpiRangeLike, Iterable[EpiRangeLike]]) -> str:
    """Turn a list/tuple of values/ranges into a comma-separated string."""
    list_values = values if isinstance(values, (list, tuple, set)) else [values]
    return ",".join([format_item(value) for value in list_values])


EPI_RANGE_TYPE = TypeVar("EPI_RANGE_TYPE", int, date, str, Week)


@dataclass(repr=False)
class EpiRange(Generic[EPI_RANGE_TYPE]):
    """
    Range object for dates/epiweeks
    """

    start: EPI_RANGE_TYPE
    end: EPI_RANGE_TYPE

    def __post_init__(self) -> None:
        # swap if wrong order
        # complicated construct for typing inference
        if self.end < self.start:
            self.start, self.end = self.end, self.start

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{format_date(self.start)}-{format_date(self.end)}"


EpiDataResponse = TypedDict("EpiDataResponse", {"result": int, "message": str, "epidata": List})


EpiRangeParam = Union[EpiRangeLike, Iterable[EpiRangeLike]]
StringParam = Union[str, Iterable[str]]
IntParam = Union[int, Iterable[int]]


class EpiDataFormatType(str, Enum):
    """
    possible formatting options for API calls
    """

    json = "json"
    classic = "classic"
    csv = "csv"
    jsonl = "jsonl"


class InvalidArgumentException(Exception):
    """
    exception for an invalid argument
    """


class OnlySupportsClassicFormatException(Exception):
    """
    the endpoint only supports the classic message format, due to an non-standard behavior
    """


class EpidataFieldType(Enum):
    """
    field type
    """

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
    """
    meta data information about an return field
    """

    name: Final[str] = ""
    type: Final[EpidataFieldType] = EpidataFieldType.text
    description: Final[str] = ""
    categories: Final[Sequence[str]] = field(default_factory=list)


CALL_TYPE = TypeVar("CALL_TYPE")


def add_endpoint_to_url(url: str, endpoint: str) -> str:
    if not url.endswith("/"):
        url += "/"
    url += endpoint
    return url


class AEpiDataCall:
    """
    base epidata call class
    """

    _base_url: Final[str]
    _endpoint: Final[str]
    _params: Final[Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]]]
    meta: Final[Sequence[EpidataFieldInfo]]
    meta_by_name: Final[Mapping[str, EpidataFieldInfo]]
    only_supports_classic: Final[bool]

    def __init__(
        self,
        base_url: str,
        endpoint: str,
        params: Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]],
        meta: Optional[Sequence[EpidataFieldInfo]] = None,
        only_supports_classic: bool = False,
    ) -> None:
        self._base_url = base_url
        self._endpoint = endpoint
        self._params = params
        self.only_supports_classic = only_supports_classic
        self.meta = meta or []
        self.meta_by_name = {k.name: k for k in self.meta}

    def _verify_parameters(self) -> None:
        # hook for verifying parameters before sending
        pass

    def _formatted_parameters(
        self,
        format_type: Optional[EpiDataFormatType] = None,
        fields: Optional[Iterable[str]] = None,
    ) -> Mapping[str, str]:
        """
        format this call into a [URL, Params] tuple
        """
        all_params = dict(self._params)
        if format_type and format_type != EpiDataFormatType.classic:
            all_params["format"] = format_type
        if fields:
            all_params["fields"] = fields
        return {k: format_list(v) for k, v in all_params.items() if v is not None}

    def request_arguments(
        self,
        format_type: Optional[EpiDataFormatType] = None,
        fields: Optional[Iterable[str]] = None,
    ) -> Tuple[str, Mapping[str, str]]:
        """
        format this call into a [URL, Params] tuple
        """
        formatted_params = self._formatted_parameters(format_type, fields)
        full_url = self._full_url()
        return full_url, formatted_params

    def _full_url(self) -> str:
        """
        combines the endpoint with the given base url
        """
        return add_endpoint_to_url(self._base_url, self._endpoint)

    def request_url(
        self,
        format_type: Optional[EpiDataFormatType] = None,
        fields: Optional[Iterable[str]] = None,
    ) -> str:
        """
        format this call into a full HTTP request url with encoded parameters
        """
        self._verify_parameters()
        u, p = self.request_arguments(format_type, fields)
        query = urlencode(p)
        if query:
            return f"{u}?{query}"
        return u

    def __repr__(self) -> str:
        return f"EpiDataCall(endpoint={self._endpoint}, params={self._formatted_parameters()})"

    def __str__(self) -> str:
        return self.request_url()

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

    def _as_df(
        self,
        rows: Sequence[Mapping[str, Union[str, float, int, date, None]]],
        fields: Optional[Iterable[str]] = None,
        disable_date_parsing: Optional[bool] = False,
    ) -> DataFrame:
        pred = fields_to_predicate(fields)
        columns: List[str] = [info.name for info in self.meta if pred(info.name)]
        df = DataFrame(rows, columns=columns or None)

        data_types: Dict[str, Any] = {}
        for info in self.meta:
            if not pred(info.name) or df[info.name].isnull().values.all():
                continue
            if info.type == EpidataFieldType.bool:
                data_types[info.name] = bool
            elif info.type == EpidataFieldType.categorical:
                data_types[info.name] = CategoricalDtype(categories=info.categories or None, ordered=True)
            elif info.type == EpidataFieldType.int:
                data_types[info.name] = int
            elif info.type in (
                EpidataFieldType.date,
                EpidataFieldType.epiweek,
                EpidataFieldType.date_or_epiweek,
            ):
                data_types[info.name] = int if disable_date_parsing else "datetime64[ns]"
            elif info.type == EpidataFieldType.float:
                data_types[info.name] = float
            else:
                data_types[info.name] = str
        if data_types:
            df = df.astype(data_types)
        return df
