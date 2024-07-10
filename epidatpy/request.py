from typing import (
    Any,
    Dict,
    Final,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

from pandas import CategoricalDtype, DataFrame, Series
from requests import Response, Session
from requests.auth import HTTPBasicAuth
from tenacity import retry, stop_after_attempt

from ._auth import _get_api_key
from ._constants import BASE_URL, HTTP_HEADERS
from ._covidcast import CovidcastDataSources, define_covidcast_fields
from ._endpoints import AEpiDataEndpoints
from ._model import (
    AEpiDataCall,
    EpidataFieldInfo,
    EpidataFieldType,
    EpiDataResponse,
    EpiRange,
    EpiRangeParam,
    OnlySupportsClassicFormatException,
    add_endpoint_to_url,
)
from ._parse import fields_to_predicate

# Make the linter happy about the unused variables
__all__ = ["Epidata", "EpiDataCall", "EpiDataContext", "EpiRange", "CovidcastEpidata"]


@retry(reraise=True, stop=stop_after_attempt(2))
def _request_with_retry(
    url: str,
    params: Mapping[str, str],
    session: Optional[Session] = None,
    stream: bool = False,
) -> Response:
    """Make request with a retry if an exception is thrown."""
    basic_auth = HTTPBasicAuth("epidata", _get_api_key())

    def call_impl(s: Session) -> Response:
        res = s.get(url, params=params, headers=HTTP_HEADERS, stream=stream, auth=basic_auth)
        if res.status_code == 414:
            return s.post(url, params=params, headers=HTTP_HEADERS, stream=stream, auth=basic_auth)
        return res

    if session:
        return call_impl(session)

    with Session() as s:
        return call_impl(s)


class EpiDataCall(AEpiDataCall):
    """
    epidata call representation
    """

    _session: Final[Optional[Session]]

    def __init__(
        self,
        base_url: str,
        session: Optional[Session],
        endpoint: str,
        params: Mapping[str, Optional[EpiRangeParam]],
        meta: Optional[Sequence[EpidataFieldInfo]] = None,
        only_supports_classic: bool = False,
    ) -> None:
        super().__init__(base_url, endpoint, params, meta, only_supports_classic)
        self._session = session

    def with_base_url(self, base_url: str) -> "EpiDataCall":
        return EpiDataCall(base_url, self._session, self._endpoint, self._params)

    def with_session(self, session: Session) -> "EpiDataCall":
        return EpiDataCall(self._base_url, session, self._endpoint, self._params)

    def _call(
        self,
        fields: Optional[Sequence[str]] = None,
        stream: bool = False,
    ) -> Response:
        url, params = self.request_arguments(fields)
        return _request_with_retry(url, params, self._session, stream)

    def classic(
        self,
        fields: Optional[Sequence[str]] = None,
        disable_date_parsing: Optional[bool] = False,
        disable_type_parsing: Optional[bool] = False,
    ) -> EpiDataResponse:
        """Request and parse epidata in CLASSIC message format."""
        self._verify_parameters()
        try:
            response = self._call(fields)
            r = cast(EpiDataResponse, response.json())
            if disable_type_parsing:
                return r
            epidata = r.get("epidata")
            if epidata and isinstance(epidata, list) and len(epidata) > 0 and isinstance(epidata[0], dict):
                r["epidata"] = [self._parse_row(row, disable_date_parsing=disable_date_parsing) for row in epidata]
            return r
        except Exception as e:  # pylint: disable=broad-except
            return {"result": 0, "message": f"error: {e}", "epidata": []}

    def __call__(
        self,
        fields: Optional[Sequence[str]] = None,
        disable_date_parsing: Optional[bool] = False,
    ) -> Union[EpiDataResponse, DataFrame]:
        """Request and parse epidata in df message format."""
        if self.only_supports_classic:
            return self.classic(fields, disable_date_parsing=disable_date_parsing, disable_type_parsing=False)
        return self.df(fields, disable_date_parsing=disable_date_parsing)

    def df(
        self,
        fields: Optional[Sequence[str]] = None,
        disable_date_parsing: Optional[bool] = False,
    ) -> DataFrame:
        """Request and parse epidata as a pandas data frame"""
        if self.only_supports_classic:
            raise OnlySupportsClassicFormatException()
        self._verify_parameters()
        json = self.classic(fields, disable_type_parsing=True)
        rows = json.get("epidata", [])
        pred = fields_to_predicate(fields)
        columns: List[str] = [info.name for info in self.meta if pred(info.name)]
        df = DataFrame(rows, columns=columns or None)

        data_types: Dict[str, Any] = {}
        for info in self.meta:
            if not pred(info.name) or df[info.name].isnull().all():
                continue
            if info.type == EpidataFieldType.bool:
                data_types[info.name] = bool
            elif info.type == EpidataFieldType.categorical:
                data_types[info.name] = CategoricalDtype(
                    categories=Series(info.categories) if info.categories else None, ordered=True
                )
            elif info.type == EpidataFieldType.int:
                data_types[info.name] = "Int64"
            elif info.type in (
                EpidataFieldType.date,
                EpidataFieldType.epiweek,
                EpidataFieldType.date_or_epiweek,
            ):
                data_types[info.name] = "Int64" if disable_date_parsing else "datetime64[ns]"
            elif info.type == EpidataFieldType.float:
                data_types[info.name] = "Float64"
            else:
                data_types[info.name] = "string"
        if data_types:
            df = df.astype(data_types)
        return df


class EpiDataContext(AEpiDataEndpoints[EpiDataCall]):
    """
    sync epidata call class
    """

    _base_url: Final[str]
    _session: Final[Optional[Session]]

    def __init__(self, base_url: str = BASE_URL, session: Optional[Session] = None) -> None:
        super().__init__()
        self._base_url = base_url
        self._session = session

    def with_base_url(self, base_url: str) -> "EpiDataContext":
        return EpiDataContext(base_url, self._session)

    def with_session(self, session: Session) -> "EpiDataContext":
        return EpiDataContext(self._base_url, session)

    def _create_call(
        self,
        endpoint: str,
        params: Mapping[str, Optional[EpiRangeParam]],
        meta: Optional[Sequence[EpidataFieldInfo]] = None,
        only_supports_classic: bool = False,
    ) -> EpiDataCall:
        return EpiDataCall(self._base_url, self._session, endpoint, params, meta, only_supports_classic)


Epidata = EpiDataContext()


def CovidcastEpidata(base_url: str = BASE_URL, session: Optional[Session] = None) -> CovidcastDataSources[EpiDataCall]:
    url = add_endpoint_to_url(base_url, "covidcast/meta")
    meta_data_res = _request_with_retry(url, {}, session, False)
    meta_data_res.raise_for_status()
    meta_data = meta_data_res.json()

    def create_call(
        params: Mapping[str, Optional[EpiRangeParam]],
    ) -> EpiDataCall:
        return EpiDataCall(base_url, session, "covidcast", params, define_covidcast_fields())

    return CovidcastDataSources.create(meta_data, create_call)
