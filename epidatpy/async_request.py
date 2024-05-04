from datetime import date
from typing import (
    AsyncGenerator,
    Callable,
    Coroutine,
    Dict,
    Final,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)
from json import loads

from asyncio import get_event_loop, gather
from aiohttp import TCPConnector, ClientSession, ClientResponse
from pandas import DataFrame

from ._model import (
    EpiRangeLike,
    AEpiDataCall,
    EpiDataFormatType,
    EpiDataResponse,
    EpiRange,
    EpidataFieldInfo,
    OnlySupportsClassicFormatException,
    add_endpoint_to_url,
)
from ._endpoints import AEpiDataEndpoints
from ._constants import HTTP_HEADERS, BASE_URL
from ._covidcast import CovidcastDataSources, define_covidcast_fields


async def _async_request(
    url: str, params: Mapping[str, str], session: Optional[ClientSession] = None
) -> ClientResponse:
    async def call_impl(s: ClientSession) -> ClientResponse:
        res = await s.get(url, params=params, headers=HTTP_HEADERS)
        if res.status == 414:
            return await s.post(url, params=params, headers=HTTP_HEADERS)
        return res

    if session:
        return await call_impl(session)

    async with ClientSession() as s:
        return await call_impl(s)


class EpiDataAsyncCall(AEpiDataCall):
    """
    async version of an epidata call
    """

    _session: Final[Optional[ClientSession]]

    def __init__(
        self,
        base_url: str,
        session: Optional[ClientSession],
        endpoint: str,
        params: Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]],
        meta: Optional[Sequence[EpidataFieldInfo]] = None,
        only_supports_classic: bool = False,
    ) -> None:
        super().__init__(base_url, endpoint, params, meta, only_supports_classic)
        self._session = session

    def with_base_url(self, base_url: str) -> "EpiDataAsyncCall":
        return EpiDataAsyncCall(base_url, self._session, self._endpoint, self._params)

    def with_session(self, session: ClientSession) -> "EpiDataAsyncCall":
        return EpiDataAsyncCall(self._base_url, session, self._endpoint, self._params)

    async def _call(
        self,
        format_type: Optional[EpiDataFormatType] = None,
        fields: Optional[Iterable[str]] = None,
    ) -> ClientResponse:
        url, params = self.request_arguments(format_type, fields)
        return await _async_request(url, params, self._session)

    async def classic(
        self,
        fields: Optional[Iterable[str]] = None,
        disable_date_parsing: Optional[bool] = False,
    ) -> EpiDataResponse:
        """Request and parse epidata in CLASSIC message format."""
        self._verify_parameters()
        try:
            response = await self._call(None, fields)
            r = cast(EpiDataResponse, await response.json())
            epidata = r.get("epidata")
            if epidata and isinstance(epidata, list) and len(epidata) > 0 and isinstance(epidata[0], dict):
                r["epidata"] = [self._parse_row(row, disable_date_parsing=disable_date_parsing) for row in epidata]
            return r
        except Exception as e:  # pylint: disable=broad-except
            return {"result": 0, "message": f"error: {e}", "epidata": []}

    async def __call__(
        self,
        fields: Optional[Iterable[str]] = None,
        disable_date_parsing: Optional[bool] = False,
    ) -> EpiDataResponse:
        """Request and parse epidata in CLASSIC message format."""
        return await self.classic(fields, disable_date_parsing=disable_date_parsing)

    async def json(
        self,
        fields: Optional[Iterable[str]] = None,
        disable_date_parsing: Optional[bool] = False,
    ) -> List[Mapping[str, Union[str, int, float, date, None]]]:
        """Request and parse epidata in JSON format"""
        self._verify_parameters()
        if self.only_supports_classic:
            raise OnlySupportsClassicFormatException()
        response = await self._call(EpiDataFormatType.json, fields)
        response.raise_for_status()
        return [
            self._parse_row(row, disable_date_parsing)
            for row in cast(List[Mapping[str, Union[str, int, float, None]]], await response.json())
        ]

    async def df(
        self,
        fields: Optional[Iterable[str]] = None,
        disable_date_parsing: Optional[bool] = False,
    ) -> DataFrame:
        """Request and parse epidata as a pandas data frame"""
        self._verify_parameters()
        if self.only_supports_classic:
            raise OnlySupportsClassicFormatException()
        r = await self.json(fields, disable_date_parsing=disable_date_parsing)
        return self._as_df(r, fields, disable_date_parsing)

    async def csv(self, fields: Optional[Iterable[str]] = None) -> str:
        """Request and parse epidata in CSV format"""
        self._verify_parameters()
        if self.only_supports_classic:
            raise OnlySupportsClassicFormatException()
        response = await self._call(EpiDataFormatType.csv, fields)
        response.raise_for_status()
        return await response.text()

    async def iter(
        self,
        fields: Optional[Iterable[str]] = None,
        disable_date_parsing: Optional[bool] = False,
    ) -> AsyncGenerator[Mapping[str, Union[str, int, float, date, None]], None]:
        """Request and streams epidata rows"""
        self._verify_parameters()
        if self.only_supports_classic:
            raise OnlySupportsClassicFormatException()
        response = await self._call(EpiDataFormatType.jsonl, fields)
        response.raise_for_status()
        async for line in response.content:
            yield self._parse_row(loads(line), disable_date_parsing=disable_date_parsing)

    async def __(
        self,
    ) -> AsyncGenerator[Mapping[str, Union[str, int, float, date, None]], None]:
        return self.iter()


class EpiDataAsyncContext(AEpiDataEndpoints[EpiDataAsyncCall]):
    """
    sync epidata call class
    """

    _base_url: Final[str]
    _session: Final[Optional[ClientSession]]

    def __init__(self, base_url: str = BASE_URL, session: Optional[ClientSession] = None) -> None:
        super().__init__()
        self._base_url = base_url
        self._session = session

    def with_base_url(self, base_url: str) -> "EpiDataAsyncContext":
        return EpiDataAsyncContext(base_url, self._session)

    def with_session(self, session: ClientSession) -> "EpiDataAsyncContext":
        return EpiDataAsyncContext(self._base_url, session)

    def _create_call(
        self,
        endpoint: str,
        params: Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]],
        meta: Optional[Sequence[EpidataFieldInfo]] = None,
        only_supports_classic: bool = False,
    ) -> EpiDataAsyncCall:
        return EpiDataAsyncCall(self._base_url, self._session, endpoint, params, meta, only_supports_classic)

    @staticmethod
    def all(
        calls: Iterable[EpiDataAsyncCall],
        call_api: Callable[[EpiDataAsyncCall, ClientSession], Coroutine],
        batch_size: int = 50,
    ) -> List:
        loop = get_event_loop()

        async def impl() -> List:
            tasks: List[Coroutine] = []
            connector = TCPConnector(limit=batch_size)
            async with ClientSession(connector=connector) as session:
                for call in calls:
                    co_routine = call_api(call, session)
                    tasks.append(co_routine)
                return list(await gather(*tasks))

        future = impl()
        return loop.run_until_complete(future)

    def all_classic(
        self,
        calls: Iterable[EpiDataAsyncCall],
        fields: Optional[Iterable[str]] = None,
        batch_size: int = 50,
    ) -> List[EpiDataResponse]:
        """
        runs the given calls in a batch asynchronously and return their responses
        """

        def call_api(call: EpiDataAsyncCall, session: ClientSession) -> Coroutine:
            return call.with_session(session).classic(fields)

        return self.all(calls, call_api, batch_size)

    def all_json(
        self,
        calls: Iterable[EpiDataAsyncCall],
        fields: Optional[Iterable[str]] = None,
        batch_size: int = 50,
    ) -> List[List[Dict]]:
        """
        runs the given calls in a batch asynchronously and return their responses
        """

        def call_api(call: EpiDataAsyncCall, session: ClientSession) -> Coroutine:
            return call.with_session(session).json(fields)

        return self.all(calls, call_api, batch_size)

    def all_csv(
        self,
        calls: Iterable[EpiDataAsyncCall],
        fields: Optional[Iterable[str]] = None,
        batch_size: int = 50,
    ) -> List[str]:
        """
        runs the given calls in a batch asynchronously and return their responses
        """

        def call_api(call: EpiDataAsyncCall, session: ClientSession) -> Coroutine:
            return call.with_session(session).csv(fields)

        return self.all(calls, call_api, batch_size)


Epidata = EpiDataAsyncContext()


async def CovidcastEpidata(
    base_url: str = BASE_URL, session: Optional[ClientSession] = None
) -> CovidcastDataSources[EpiDataAsyncCall]:
    url = add_endpoint_to_url(base_url, "covidcast/meta")
    meta_data_res = await _async_request(url, {}, session)
    meta_data_res.raise_for_status()
    meta_data = await meta_data_res.json()

    def create_call(
        params: Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]],
    ) -> EpiDataAsyncCall:
        return EpiDataAsyncCall(base_url, session, "covidcast", params, define_covidcast_fields())

    return CovidcastDataSources.create(meta_data, create_call)


__all__ = [
    "Epidata",
    "EpiDataAsyncCall",
    "EpiDataAsyncContext",
    "EpiRange",
    "CovidcastEpidata",
]
