from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from html import unescape
from io import StringIO
from os import environ
from re import DOTALL, IGNORECASE, findall, sub
from typing import (
    Any,
    Final,
    cast,
)
from urllib.parse import urlencode

from appdirs import user_cache_dir
from diskcache import Cache
from pandas import CategoricalDtype, DataFrame, Series, concat, read_csv, to_datetime
from requests import Response, Session
from requests.auth import HTTPBasicAuth
from tenacity import retry, stop_after_attempt

from ._auth import _get_api_key
from ._constants import HTTP_HEADERS
from ._model import (
    ApiVersion,
    CastPostFilter,
    EmptyResultWarning,
    EpidataFieldInfo,
    EpidataFieldType,
    EpiDataHTTPError,
    EpiDataResponse,
    EpiRangeParam,
    InvalidArgumentException,
    OnlySupportsClassicFormatException,
    StringParam,
    add_endpoint_to_url,
    cast_filter,
    format_list,
    split_list,
)
from ._parse import (
    fields_to_predicate,
    parse_api_date,
    parse_api_date_or_week,
    parse_api_datetimetz,
    parse_api_week,
)

CACHE_DIRECTORY = user_cache_dir(appname="epidatpy", appauthor="delphi")

if environ.get("USE_EPIDATPY_CACHE", None):
    warnings.warn(
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


def _error_body_message(response: Response) -> str | None:
    """Extract the server's own error message from an error response body.

    Whatever format was requested, error bodies come back either as JSON --
    ``{"message": ...}``, or FastAPI's automatic validation errors under
    ``"detail"`` -- or as an HTML error page from the web server.
    """
    content_type = response.headers.get("Content-Type", "").lower()
    try:
        if content_type.startswith("application/json"):
            body = response.json()
            message = body.get("message") or body.get("detail")
            if isinstance(message, list):
                # FastAPI validation errors: a list of {"loc", "msg", ...} objects.
                message = "; ".join(d["msg"] for d in message if isinstance(d, dict) and isinstance(d.get("msg"), str))
        elif content_type.startswith("text/html"):
            # grab the error information out of the returned HTML document
            message = " ".join(
                unescape(sub(r"<[^>]+>", "", p)).strip()
                for p in findall(r"<p>(.*?)</p>", response.text, DOTALL | IGNORECASE)
            )
        else:
            return None
    except (AttributeError, TypeError, ValueError):  # body isn't the shape we expected
        return None
    return str(message) if message else None


def _raise_for_status(response: Response) -> None:
    """Raise `EpiDataHTTPError`, carrying the server's own message, on an HTTP error status."""
    if response.status_code >= 400:
        raise EpiDataHTTPError(response, _error_body_message(response))


def fetch_cast_meta(base_url: str, session: Session | None, source: str | None = None) -> Any:
    """Fetch cast-API metadata: every source keyed by name, or `source`'s own entry.

    If the response has no entry for `source`, it is returned as is.
    """
    params = {"source": source} if source is not None else {}
    response = _request_with_retry(add_endpoint_to_url(base_url, "metadata/"), params, session, api_version="cast")
    _raise_for_status(response)
    res = response.json()
    if source is not None and isinstance(res, dict) and source in res:
        return res[source]
    return res


class EpiDataCall:
    """epidata call representation"""

    _base_url: Final[str]
    _endpoint: Final[str]
    _params: Final[Mapping[str, EpiRangeParam | None]]
    _api_version: Final[ApiVersion]
    _post_filter: Final[CastPostFilter | None]
    _return_empty: Final[bool]
    _session: Final[Session | None]
    meta: Final[Sequence[EpidataFieldInfo]]
    meta_by_name: Final[Mapping[str, EpidataFieldInfo]]
    only_supports_classic: Final[bool]
    use_cache: Final[bool]

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
        return_empty: bool = False,
    ) -> None:
        self._base_url = base_url
        self._endpoint = endpoint
        self._params = params
        self._api_version = api_version
        self._post_filter = post_filter
        self._return_empty = return_empty
        self._session = session
        self.only_supports_classic = only_supports_classic
        self.meta = meta or []
        self.meta_by_name = {k.name: k for k in self.meta}
        # Set use_cache from the constructor if present; otherwise check
        # USE_EPIDATPY_CACHE, accepting various "truthy" values.
        self.use_cache = (
            use_cache
            if use_cache is not None
            else (environ.get("USE_EPIDATPY_CACHE", "").lower() in ["true", "t", "1"])
        )
        if cache_max_age_days is not None:
            self.cache_max_age_days = cache_max_age_days
        else:
            env_days = environ.get("EPIDATPY_CACHE_MAX_AGE_DAYS", "7")
            self.cache_max_age_days = int(env_days) if env_days.isdigit() else 7

    def _formatted_parameters(
        self,
        fields: Sequence[str] | None = None,
    ) -> Mapping[str, str]:
        all_params = dict(self._params)
        if fields:
            all_params["fields"] = fields
        return {k: format_list(v) for k, v in all_params.items() if v is not None}

    def request_arguments(
        self,
        fields: Sequence[str] | None = None,
    ) -> tuple[str, Mapping[str, str]]:
        """Format this call into a (URL, params) tuple."""
        formatted_params = self._formatted_parameters(fields)
        full_url = add_endpoint_to_url(self._base_url, self._endpoint)
        return full_url, formatted_params

    def request_url(
        self,
        fields: Sequence[str] | None = None,
    ) -> str:
        """Format this call into a full HTTP request url with encoded parameters."""
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
        value: str | float | None,
        disable_date_parsing: bool | None = False,
    ) -> str | float | int | date | None:
        meta = self.meta_by_name.get(key)
        if not meta or value is None:
            return value
        if meta.type == EpidataFieldType.date_or_epiweek and not disable_date_parsing:
            return parse_api_date_or_week(value)
        if meta.type == EpidataFieldType.date and not disable_date_parsing:
            return parse_api_date(value)
        if meta.type == EpidataFieldType.epiweek and not disable_date_parsing:
            return parse_api_week(value)
        if meta.type == EpidataFieldType.epoch_seconds and not disable_date_parsing:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        if meta.type == EpidataFieldType.datetimetz and not disable_date_parsing:
            return parse_api_datetimetz(str(value))
        if meta.type == EpidataFieldType.bool:
            return bool(value)
        return value

    def _parse_row(
        self,
        row: Mapping[str, str | float | int | None],
        disable_date_parsing: bool | None = False,
    ) -> Mapping[str, str | float | int | date | None]:
        if not self.meta:
            return row
        return {k: self._parse_value(k, v, disable_date_parsing) for k, v in row.items()}

    def with_base_url(self, base_url: str) -> EpiDataCall:
        return EpiDataCall(
            base_url,
            self._session,
            self._endpoint,
            self._params,
            meta=self.meta,
            only_supports_classic=self.only_supports_classic,
            use_cache=self.use_cache,
            cache_max_age_days=self.cache_max_age_days,
            api_version=self._api_version,
            post_filter=self._post_filter,
            return_empty=self._return_empty,
        )

    def with_session(self, session: Session) -> EpiDataCall:
        return EpiDataCall(
            self._base_url,
            session,
            self._endpoint,
            self._params,
            meta=self.meta,
            only_supports_classic=self.only_supports_classic,
            use_cache=self.use_cache,
            cache_max_age_days=self.cache_max_age_days,
            api_version=self._api_version,
            post_filter=self._post_filter,
            return_empty=self._return_empty,
        )

    def _with_param(self, key: str, value: EpiRangeParam | None, *, return_empty: bool | None = None) -> EpiDataCall:
        return EpiDataCall(
            self._base_url,
            self._session,
            self._endpoint,
            {**self._params, key: value},
            meta=self.meta,
            only_supports_classic=self.only_supports_classic,
            use_cache=self.use_cache,
            cache_max_age_days=self.cache_max_age_days,
            api_version=self._api_version,
            post_filter=self._post_filter,
            return_empty=self._return_empty if return_empty is None else return_empty,
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

    def _requested_values(self, name: str) -> list[str]:
        """The distinct comma-separated values of a request parameter, in order."""
        value = self._params.get(name)
        if value is None:
            return []
        return list(dict.fromkeys(v.strip() for v in format_list(value).split(",") if v.strip()))

    def _cast_source_meta(self, source: str) -> Mapping[str, Any] | None:
        try:
            entry = fetch_cast_meta(self._base_url, self._session, source)
        except Exception:  # noqa: BLE001 - diagnostics must never mask the real result
            return None
        # An unknown source comes back as the raw response, not its entry.
        return entry if isinstance(entry, dict) and "signals" in entry else None

    def _unknown_cast_keys(self, source: str, signals: list[str], geo_types: list[str]) -> list[str]:
        """Sentences naming the requested signals and geo types that `source`'s metadata does not list."""
        meta = self._cast_source_meta(source) if signals or geo_types else None
        if meta is None:
            return []
        problems = []
        for kind, requested in (("signals", signals), ("geo_types", geo_types)):
            known = meta.get(kind, [])
            unknown = [v for v in requested if v not in known]
            if unknown:
                problems.append(f"For source {source!r}, {kind} {unknown} are not available (known: {known}).")
        return problems

    def _check_cast_empty(self, fetched: DataFrame, result: DataFrame) -> None:
        """Warn about empty or partially empty cast results, the way epidatr does.

        Signals or geo types missing from the source's metadata are an error
        only when nothing came back at all; alongside real data they are
        mentioned in the warning instead.
        """
        source = format_list(cast("EpiRangeParam", self._params.get("source", "")))
        signals = self._requested_values("signal")
        geo_types = self._requested_values("geo_type")
        returned_signals = set(fetched["signal"]) if "signal" in fetched.columns else set()
        returned_geo_types = set(fetched["geo_type"]) if "geo_type" in fetched.columns else set()
        empty_signals = [s for s in signals if s not in returned_signals]
        empty_geo_types = [g for g in geo_types if g not in returned_geo_types]
        if not empty_signals and not empty_geo_types and len(result) > 0:
            return

        unknown = self._unknown_cast_keys(source, empty_signals, empty_geo_types)
        if len(result) == 0 and unknown:
            raise InvalidArgumentException(" ".join(unknown))

        if len(fetched) == 0:
            message = f"No data returned for source {source!r}, signals {signals}, geo_type {geo_types}."
        elif len(result) == 0:
            message = (
                f"The server returned {len(fetched)} rows but the local `geo_values`/`reference_time` "
                "filter dropped them all."
            )
        else:
            parts = [f"signals {empty_signals}"] if empty_signals else []
            parts += [f"geo_types {empty_geo_types}"] if empty_geo_types else []
            message = f"No data returned for {' and '.join(parts)} from source {source!r}."
        warnings.warn(
            " ".join([message, *unknown, "Pass return_empty=True to silence this."]),
            EmptyResultWarning,
            stacklevel=3,
        )

    def _get_cache_key(self, method: str) -> str:
        cache_key = f"{self._endpoint} | {self._api_version} | {method}"
        if self._params:
            cache_key += f" | {dict(sorted(self._params.items()))!s}"
        return cache_key

    def classic(
        self,
        fields: Sequence[str] | None = None,
        disable_date_parsing: bool | None = False,
        disable_type_parsing: bool | None = False,
    ) -> EpiDataResponse:
        """Request and parse epidata in CLASSIC message format."""
        if self.use_cache:
            with Cache(CACHE_DIRECTORY) as cache:
                cache_key = self._get_cache_key("classic")
                if cache_key in cache:
                    return cast(EpiDataResponse, cache[cache_key])
        response = self._call(fields)
        # Raised, not buried in the result dict: an HTTP error means no data came
        # back, and df() would otherwise hand back a silently empty frame.
        _raise_for_status(response)
        try:
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
        except Exception as e:  # noqa: BLE001 - intentional catch-all
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

        if self._api_version == "cast" and self._endpoint in ("snapshot/", "archive/"):
            # The cast-API accepts only one geo_type per request; signals are
            # already comma-joined into one request each. Fetch one request
            # per geo_type and combine, mirroring epidatr's `epidata_snapshot`/
            # `epidata_archive`.
            geo_types = split_list(cast(StringParam, self._params.get("geo_type") or ""))
            if len(geo_types) > 1:
                frames = [
                    self._with_param("geo_type", g, return_empty=True).df(
                        fields, disable_date_parsing=disable_date_parsing
                    )
                    for g in geo_types
                ]
                combined = concat(frames, ignore_index=True)
                combined.attrs = frames[0].attrs
                if not self._return_empty:
                    # Per-request frames are already locally filtered, so the
                    # combined frame stands in for both the fetched and the
                    # filtered result here.
                    self._check_cast_empty(combined, combined)
                return combined

        if self.use_cache:
            with Cache(CACHE_DIRECTORY) as cache:
                cache_key = self._get_cache_key("df")
                if cache_key in cache:
                    return cast(DataFrame, cache[cache_key])

        pred = fields_to_predicate(fields)
        columns: list[str] = [info.name for info in self.meta if pred(info.name)]
        fetched: DataFrame | None = None
        if self._api_version == "cast":
            # CAST endpoints only speak CSV.
            response = self._call(fields, extra_params={"format": "csv"})
            _raise_for_status(response)
            body = response.text
            if body.strip():
                df = read_csv(StringIO(body), dtype=str)
                # Keep meta columns in order, plus any undeclared response columns (e.g. aux values).
                meta_names = {info.name for info in self.meta}
                cols_in_df = [c for c in columns if c in df.columns]
                extras = [c for c in df.columns if c not in meta_names and pred(c)]
                df = df[cols_in_df + extras]
            else:
                df = DataFrame(columns=columns or None)
            fetched = df
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
                EpidataFieldType.datetimetz,
            ):
                data_types[info.name] = "string"
                time_fields.append(info)
            elif info.type == EpidataFieldType.epoch_seconds:
                data_types[info.name] = "Int64"
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
                if info.type == EpidataFieldType.epoch_seconds:
                    df[info.name] = to_datetime(df[info.name], unit="s", utc=True)
                    continue
                if info.type == EpidataFieldType.datetimetz:
                    df[info.name] = to_datetime(df[info.name], format="ISO8601", utc=True)
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

        if self.use_cache:
            with Cache(CACHE_DIRECTORY) as cache:
                cache_key = self._get_cache_key("df")
                cache.set(cache_key, df, expire=self.cache_max_age_days * 24 * 60 * 60)

        if self._post_filter is not None:
            geo_values, reference_time = self._post_filter
            df = cast_filter(df, geo_values=geo_values, reference_time=reference_time)

        if fetched is not None and not self._return_empty:
            self._check_cast_empty(fetched, df)

        if self._api_version == "cast" and self._endpoint in ("snapshot/", "archive/"):
            # Lets `EpiDataContext.epidata_aux()` recover the source/kind from a
            # materialized snapshot/archive result and merge aux data onto it.
            df.attrs["cast_source"] = self._params.get("source")
            df.attrs["cast_kind"] = "snapshot" if self._endpoint == "snapshot/" else "archive"

        return df
