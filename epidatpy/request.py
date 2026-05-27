from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from io import StringIO
from os import environ
from typing import (
    Any,
    Final,
    cast,
)

from appdirs import user_cache_dir
from diskcache import Cache
from pandas import CategoricalDtype, DataFrame, Series, read_csv, to_datetime
from requests import Response, Session
from requests.auth import HTTPBasicAuth
from tenacity import retry, stop_after_attempt

from ._auth import _get_api_key
from ._constants import BASE_URL, CAST_BASE_URL, HTTP_HEADERS
from ._covidcast import CovidcastDataSources, define_covidcast_fields
from ._endpoints import AEpiDataEndpoints
from ._model import (
    AEpiDataCall,
    ApiVersion,
    CastPostFilter,
    EpidataFieldInfo,
    EpidataFieldType,
    EpiDataResponse,
    EpiRangeParam,
    OnlySupportsClassicFormatException,
    add_endpoint_to_url,
    cast_filter,
)
from ._parse import fields_to_predicate

# Make the linter happy about the unused variables
CACHE_DIRECTORY = user_cache_dir(appname="epidatpy", appauthor="delphi")

if environ.get("USE_EPIDATPY_CACHE", None):
    print(
        f"diskcache is being used (unset USE_EPIDATPY_CACHE if not intended). "
        f"The cache directory is {CACHE_DIRECTORY}. "
        f"The TTL is set to {environ.get('EPIDATPY_CACHE_MAX_AGE_DAYS', '7')} days."
    )


@retry(reraise=True, stop=stop_after_attempt(2))
def _request_with_retry(
    url: str,
    params: Mapping[str, str],
    session: Session | None = None,
    stream: bool = False,
    api_version: ApiVersion = "classic",
) -> Response:
    """Make request with a retry if an exception is thrown."""
    key = _get_api_key()
    if api_version == "cast":
        # CAST API uses a token header instead of HTTP basic auth.
        headers = {**HTTP_HEADERS, "token": key} if key else HTTP_HEADERS
        auth = None
    else:
        headers = HTTP_HEADERS
        auth = HTTPBasicAuth("epidata", key)

    def call_impl(s: Session) -> Response:
        res = s.get(url, params=params, headers=headers, stream=stream, auth=auth)
        if res.status_code == 414:
            return s.post(url, params=params, headers=headers, stream=stream, auth=auth)
        return res

    if session:
        return call_impl(session)

    with Session() as s:
        return call_impl(s)


class EpiDataCall(AEpiDataCall):
    """epidata call representation"""

    _session: Final[Session | None]

    def __init__(
        self,
        base_url: str,
        session: Session | None,
        endpoint: str,
        params: Mapping[str, EpiRangeParam | None],
        meta: Sequence[EpidataFieldInfo] | None = None,
        only_supports_classic: bool = False,
        use_cache: bool | None = None,
        cache_max_age_days: int | None = None,
        api_version: ApiVersion = "classic",
        post_filter: CastPostFilter | None = None,
    ) -> None:
        super().__init__(
            base_url,
            endpoint,
            params,
            meta,
            only_supports_classic,
            use_cache,
            cache_max_age_days,
            api_version=api_version,
            post_filter=post_filter,
        )
        self._session = session

    def with_base_url(self, base_url: str) -> EpiDataCall:
        return EpiDataCall(
            base_url,
            self._session,
            self._endpoint,
            self._params,
            api_version=self._api_version,
            post_filter=self._post_filter,
        )

    def with_session(self, session: Session) -> EpiDataCall:
        return EpiDataCall(
            self._base_url,
            session,
            self._endpoint,
            self._params,
            api_version=self._api_version,
            post_filter=self._post_filter,
        )

    def _call(
        self,
        fields: Sequence[str] | None = None,
        stream: bool = False,
        extra_params: Mapping[str, str] | None = None,
    ) -> Response:
        url, params = self.request_arguments(fields)
        if extra_params:
            params = {**params, **extra_params}
        return _request_with_retry(url, params, self._session, stream, api_version=self._api_version)

    def _get_cache_key(self, method: str) -> str:
        cache_key = f"{self._endpoint} | {self._api_version} | {method}"
        if self._params:
            cache_key += f" | {str(dict(sorted(self._params.items())))}"
        return cache_key

    def classic(
        self,
        fields: Sequence[str] | None = None,
        disable_date_parsing: bool | None = False,
        disable_type_parsing: bool | None = False,
    ) -> EpiDataResponse:
        """Request and parse epidata in CLASSIC message format."""
        self._verify_parameters()
        try:
            if self.use_cache:
                with Cache(CACHE_DIRECTORY) as cache:
                    cache_key = self._get_cache_key("classic")
                    if cache_key in cache:
                        return cast(EpiDataResponse, cache[cache_key])
            response = self._call(fields)
            r = cast(EpiDataResponse, response.json())
            if disable_type_parsing:
                return r
            epidata = r.get("epidata")
            if epidata and isinstance(epidata, list) and len(epidata) > 0 and isinstance(epidata[0], dict):
                r["epidata"] = [self._parse_row(row, disable_date_parsing=disable_date_parsing) for row in epidata]
            if self.use_cache:
                with Cache(CACHE_DIRECTORY) as cache:
                    cache_key = self._get_cache_key("classic")
                    cache.set(cache_key, r, expire=self.cache_max_age_days * 24 * 60 * 60)
            return r
        except Exception as e:
            return {"result": 0, "message": f"error: {e}", "epidata": []}

    def __call__(
        self,
        fields: Sequence[str] | None = None,
        disable_date_parsing: bool | None = False,
    ) -> EpiDataResponse | DataFrame:
        """Request and parse epidata in df message format."""
        if self.only_supports_classic:
            return self.classic(
                fields,
                disable_date_parsing=disable_date_parsing,
                disable_type_parsing=False,
            )
        return self.df(fields, disable_date_parsing=disable_date_parsing)

    def df(
        self,
        fields: Sequence[str] | None = None,
        disable_date_parsing: bool | None = False,
    ) -> DataFrame:
        """Request and parse epidata as a pandas data frame"""
        if self.only_supports_classic:
            raise OnlySupportsClassicFormatException()
        self._verify_parameters()

        if self.use_cache:
            with Cache(CACHE_DIRECTORY) as cache:
                cache_key = self._get_cache_key("df")
                if cache_key in cache:
                    return cast(DataFrame, cache[cache_key])

        pred = fields_to_predicate(fields)
        columns: list[str] = [info.name for info in self.meta if pred(info.name)]
        if self._api_version == "cast":
            # CAST endpoints only speak CSV.
            response = self._call(fields, extra_params={"format": "csv"})
            response.raise_for_status()
            body = response.text
            if body.strip():
                df = read_csv(StringIO(body), dtype=str)
                # Keep only fields in meta that exist in the response, in meta order.
                cols_in_df = [c for c in columns if c in df.columns]
                df = df[cols_in_df] if cols_in_df else df
            else:
                df = DataFrame(columns=columns or None)
        else:
            json = self.classic(fields, disable_type_parsing=True)
            rows = json.get("epidata", [])
            df = DataFrame(rows, columns=columns or None)

        data_types: dict[str, Any] = {}
        time_fields: list[EpidataFieldInfo] = []
        for info in self.meta:
            if not pred(info.name):
                continue
            if info.name not in df.columns:
                # CAST responses may omit source-specific columns; skip them.
                continue
            if info.type == EpidataFieldType.bool:
                data_types[info.name] = bool
            elif info.type == EpidataFieldType.categorical:
                data_types[info.name] = CategoricalDtype(
                    categories=Series(info.categories) if info.categories else None,
                    ordered=True,
                )
            elif info.type == EpidataFieldType.int:
                data_types[info.name] = "Int64"
            elif info.type in (
                EpidataFieldType.date,
                EpidataFieldType.epiweek,
                EpidataFieldType.date_or_epiweek,
            ):
                data_types[info.name] = "string"
                time_fields.append(info)
            elif info.type == EpidataFieldType.float:
                data_types[info.name] = "Float64"
            else:
                data_types[info.name] = "string"
        if data_types:
            df = df.astype(data_types)
        if not disable_date_parsing:
            for info in time_fields:
                if info.type == EpidataFieldType.epiweek:
                    continue
                # Try known date formats in priority order; keep as string if all
                # fail. The try/except is needed because the time field might be
                # date_or_epiweek, and the CAST CSV path returns timestamps
                # (e.g. "2024-04-18 00:00:00").
                parsed = False
                for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S"):
                    try:
                        df[info.name] = to_datetime(df[info.name], format=fmt)
                        parsed = True
                        break
                    except ValueError:
                        continue
                if not parsed:
                    # Last resort: let pandas infer (slower but flexible).
                    try:
                        df[info.name] = to_datetime(df[info.name])
                    except (ValueError, TypeError):
                        pass

        if self._post_filter is not None:
            geo_values, reference_time, report_time = self._post_filter
            df = cast_filter(df, geo_values=geo_values, reference_time=reference_time, report_time=report_time)

        if self.use_cache:
            with Cache(CACHE_DIRECTORY) as cache:
                cache_key = self._get_cache_key("df")
                cache.set(cache_key, df, expire=self.cache_max_age_days * 24 * 60 * 60)

        return df


class EpiDataContext(AEpiDataEndpoints[EpiDataCall]):
    """sync epidata call class"""

    _base_url: Final[str]
    _cast_base_url: Final[str]
    _session: Final[Session | None]

    def __init__(
        self,
        base_url: str = BASE_URL,
        session: Session | None = None,
        use_cache: bool | None = None,
        cache_max_age_days: int | None = None,
        cast_base_url: str = CAST_BASE_URL,
    ) -> None:
        super().__init__()
        self._base_url = base_url
        self._cast_base_url = cast_base_url
        self._session = session
        self.use_cache = use_cache
        self.cache_max_age_days = cache_max_age_days

    def with_base_url(self, base_url: str) -> EpiDataContext:
        return EpiDataContext(base_url, self._session, cast_base_url=self._cast_base_url)

    def with_session(self, session: Session) -> EpiDataContext:
        return EpiDataContext(self._base_url, session, cast_base_url=self._cast_base_url)

    def _create_call(
        self,
        endpoint: str,
        params: Mapping[str, EpiRangeParam | None],
        meta: Sequence[EpidataFieldInfo] | None = None,
        only_supports_classic: bool = False,
        api_version: ApiVersion = "classic",
        post_filter: CastPostFilter | None = None,
    ) -> EpiDataCall:
        base_url = self._cast_base_url if api_version == "cast" else self._base_url
        return EpiDataCall(
            base_url,
            self._session,
            endpoint,
            params,
            meta,
            only_supports_classic,
            self.use_cache,
            self.cache_max_age_days,
            api_version=api_version,
            post_filter=post_filter,
        )

    def epidata_meta(self, source: str) -> Any:
        """Fetch source-level metadata from the CAST API.

        Returns the parsed JSON (a list of signal/geo descriptors) for `source`.
        """
        url = add_endpoint_to_url(self._cast_base_url, "metadata/")
        response = _request_with_retry(
            url,
            {"source": source},
            self._session,
            stream=False,
            api_version="cast",
        )
        response.raise_for_status()
        return response.json()


def CovidcastEpidata(
    base_url: str = BASE_URL,
    session: Session | None = None,
    use_cache: bool | None = None,
    cache_max_age_days: int | None = None,
) -> CovidcastDataSources[EpiDataCall]:
    url = add_endpoint_to_url(base_url, "covidcast/meta")
    meta_data_res = _request_with_retry(url, {}, session, False)
    meta_data_res.raise_for_status()
    meta_data = meta_data_res.json()

    def create_call(
        params: Mapping[str, EpiRangeParam | None],
    ) -> EpiDataCall:
        return EpiDataCall(
            base_url,
            session,
            "covidcast",
            params,
            define_covidcast_fields(),
            use_cache=use_cache,
            cache_max_age_days=cache_max_age_days,
        )

    return CovidcastDataSources.create(meta_data, create_call)


def available_endpoints() -> DataFrame:
    """Get a DataFrame of available endpoints and their descriptions."""
    endpoints = [x for x in inspect.getmembers(AEpiDataEndpoints) if x[0].startswith("pvt_") or x[0].startswith("pub_")]
    data = {e[0]: e[1].__doc__.split("\n")[0] if e[1].__doc__ else "None" for e in endpoints}
    return DataFrame(data.items(), columns=["Endpoint", "Description"])
