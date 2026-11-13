from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from io import StringIO
from os import environ
from re import DOTALL, IGNORECASE, compile, findall, sub
from time import sleep as _sleep
from typing import (
    Any,
    Final,
    cast,
)
from urllib.parse import urlencode

from appdirs import user_cache_dir
from diskcache import Cache
from pandas import CategoricalDtype, DataFrame, Series, concat, read_csv, to_datetime
from requests import ConnectionError as RequestsConnectionError
from requests import Response, Session, Timeout
from requests.auth import HTTPBasicAuth

from ._auth import _get_api_key
from ._constants import HTTP_HEADERS, __version__
from ._model import (
    ApiVersion,
    CastPostFilter,
    DroppedMetaFieldsWarning,
    EmptyResultWarning,
    EpiDataAPIError,
    EpidataFieldInfo,
    EpidataFieldType,
    EpiDataHTTPError,
    EpiDataResponse,
    EpiDataWarning,
    EpiRangeParam,
    InvalidArgumentException,
    MalformedResponseError,
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

_ISO_DATE_RE = compile(r"(?<![\d.])\d{4}-\d{2}-\d{2}(?!\d)")


def _version_dates(text: str) -> list[date]:
    """The valid `YYYY-MM-DD` dates in a version bound such as ``<2025-01-01T13:45:00Z``."""
    dates = []
    for token in _ISO_DATE_RE.findall(text):
        try:
            dates.append(datetime.strptime(token, "%Y-%m-%d").date())
        except ValueError:
            continue
    return dates


def _is_fixed_past_version(params: Mapping[str, Any]) -> bool:
    """Whether a cast request asks for a version that can no longer change, so its result may be cached.

    That means a `snapshot_date`, or a `report_time_query` that is `<date` or a `from:to` range,
    at least two days ago in UTC. "Latest", open-ended, and row-limited requests are never cached.
    """
    if params.get("limit") not in (None, -1, "-1"):
        return False
    snapshot_date = params.get("snapshot_date")
    report_time = params.get("report_time_query")
    if snapshot_date:
        dates = _version_dates(str(snapshot_date))
    elif report_time:
        text = str(report_time)
        dates = _version_dates(text)
        if text.startswith(">") or len(dates) < (1 if text.startswith("<") else 2):
            return False
    else:
        return False
    return bool(dates) and max(dates) < datetime.now(UTC).date() - timedelta(days=1)


# Total attempts per request, counting the first.
MAX_TRIES = 3
# Server errors worth retrying. A 429 is retried only when the server says when to come back.
_RETRY_STATUSES = frozenset({500, 502, 503, 504})
# (connect, read) timeouts in seconds; the read timeout matches epidatr's 15 minutes.
REQUEST_TIMEOUT = (30, 15 * 60)


def _max_retry_wait() -> float:
    """The longest server-requested wait to honour, in seconds (`EPIDATPY_MAX_RETRY_WAIT`, default 60)."""
    try:
        value = float(environ.get("EPIDATPY_MAX_RETRY_WAIT", "60"))
    except ValueError:
        return 60.0
    return value if value >= 0 and value != float("inf") else 60.0


def _retry_after_seconds(response: Response) -> float | None:
    """The `Retry-After` header as seconds from now, or None if it is missing or unusable."""
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        try:
            seconds = (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
        except (TypeError, ValueError):
            return None
    return max(seconds, 0.0) if seconds == seconds and seconds != float("inf") else None  # noqa: PLR0124 - NaN check


def _is_transient(response: Response, max_wait: float) -> bool:
    """Whether a response is worth retrying: a transient server error, unless it asks for a long wait."""
    after = _retry_after_seconds(response)
    if after is not None and after > max_wait:
        return False
    if response.status_code == 429:
        return after is not None
    return response.status_code in _RETRY_STATUSES


def _retry_hint(response: Response) -> str | None:
    """A sentence saying when the server suggests retrying, or None if it gave no usable `Retry-After`."""
    after = _retry_after_seconds(response)
    if after is None or after <= 0 or after > 24 * 60 * 60:
        return None
    seconds = max(1, round(after))
    minutes = round(after / 60)
    if seconds < 60:
        wait = f"{seconds} second{'s' if seconds != 1 else ''}"
    elif minutes < 90:
        wait = f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = round(minutes / 60)
        wait = f"{hours} hour{'s' if hours != 1 else ''}"
    return f"The server suggests retrying in about {wait}."


def _request_with_retry(
    url: str,
    params: Mapping[str, str],
    session: Session | None = None,
    stream: bool = False,
    api_version: ApiVersion = "classic",
) -> Response:
    """Make a request, retrying connection failures and transient server errors up to `MAX_TRIES` times.

    The wait between tries is the server's `Retry-After`, else 1 then 2 seconds. A
    `Retry-After` longer than `EPIDATPY_MAX_RETRY_WAIT` (60 seconds) is never waited
    on: the response is returned at once so the caller can report the server's message.
    """
    key = _get_api_key()
    if api_version == "cast":
        # CAST API uses a token header instead of HTTP basic auth.
        headers = {**HTTP_HEADERS, "token": key} if key else HTTP_HEADERS
        auth = None
    else:
        headers = HTTP_HEADERS
        auth = HTTPBasicAuth("epidata", key)

    def call_impl(s: Session) -> Response:
        res = s.get(url, params=params, headers=headers, stream=stream, auth=auth, timeout=REQUEST_TIMEOUT)
        if res.status_code == 414:
            # The URL was too long, so send the parameters in the form body instead.
            return s.post(url, data=params, headers=headers, stream=stream, auth=auth, timeout=REQUEST_TIMEOUT)
        return res

    def attempt_all(s: Session) -> Response:
        max_wait = _max_retry_wait()
        for attempt in range(1, MAX_TRIES + 1):
            try:
                res = call_impl(s)
            except (RequestsConnectionError, Timeout):
                if attempt == MAX_TRIES:
                    raise
                _sleep(2 ** (attempt - 1))
                continue
            if attempt == MAX_TRIES or not _is_transient(res, max_wait):
                return res
            after = _retry_after_seconds(res)
            _sleep(after if after is not None else 2 ** (attempt - 1))
        raise AssertionError("unreachable")  # pragma: no cover

    if session:
        return attempt_all(session)

    with Session() as s:
        return attempt_all(s)


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
        message = _error_body_message(response)
        hint = _retry_hint(response)
        raise EpiDataHTTPError(response, " ".join(part for part in (message, hint) if part) or None)


def _parse_classic_envelope(response: Response) -> EpiDataResponse:
    """Parse a classic response body, raising `MalformedResponseError` if it is not a valid envelope."""
    # The query string is dropped because it can hold the API key.
    url = response.url.split("?")[0]
    try:
        body = response.json()
    except ValueError as e:
        raise MalformedResponseError(f"The API response could not be parsed as JSON (request: {url}): {e}") from e
    if not isinstance(body, dict):
        raise MalformedResponseError(f"Malformed response envelope: expected a JSON object (request: {url})")
    result, message = body.get("result"), body.get("message")
    if isinstance(result, bool) or not isinstance(result, int) or not isinstance(message, str):
        raise MalformedResponseError(
            f"Malformed response envelope: `result` must be an integer and `message` a string (request: {url})"
        )
    if result in (1, 2) and body.get("epidata") is None:
        raise MalformedResponseError(
            f"Malformed response envelope: `result` is {result} but `epidata` is missing (request: {url})"
        )
    return cast(EpiDataResponse, body)


def _check_epidata_result(envelope: EpiDataResponse) -> None:
    """Raise on an API-level error and warn on a non-success message; "no results" (-2) is not an error."""
    result, message = envelope["result"], envelope["message"]
    if result not in (1, 2, -2):
        raise EpiDataAPIError(result, message)
    if message != "success":
        warnings.warn(f"epidata warning: {message}", EpiDataWarning, stacklevel=3)


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
        # The cast API rejects unknown parameters; `df()` selects the columns locally instead.
        if fields and self._api_version != "cast":
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
            return datetime.fromtimestamp(float(value), tz=UTC)
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

    @staticmethod
    def _unknown_cast_keys(
        meta: Mapping[str, Any] | None, source: str, signals: list[str], geo_types: list[str]
    ) -> list[str]:
        """Sentences naming the requested signals and geo types that `source`'s metadata does not list."""
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

        meta = self._cast_source_meta(source) if empty_signals or empty_geo_types or len(fetched) == 0 else None
        unknown = self._unknown_cast_keys(meta, source, empty_signals, empty_geo_types)
        if len(result) == 0 and unknown:
            raise InvalidArgumentException(" ".join(unknown))

        if len(fetched) == 0:
            message = f"No data returned for source {source!r}, signals {signals}, geo_type {geo_types}."
            ref_range = meta.get("reference_time_range") if meta else None
            if isinstance(ref_range, dict) and ref_range.get("first") and ref_range.get("latest"):
                message += f" Source {source!r}'s reference_time range: {ref_range['first']} to {ref_range['latest']}."
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

    def _get_cache_key(self, method: str, fields: Sequence[str] | None = None, variant: str = "") -> str:
        cache_key = f"{__version__} | {self._base_url} | {self._endpoint} | {self._api_version} | {method} | {fields!s} | {variant}"
        if self._params:
            cache_key += f" | {dict(sorted(self._params.items()))!s}"
        return cache_key

    def _cast_csv_body(self, fields: Sequence[str] | None, refresh_cache: bool = False) -> str:
        """Fetch a cast response as CSV text, from the cache when the request is a fixed past version."""
        cacheable = self.use_cache and _is_fixed_past_version(self._params)
        cache_key = self._get_cache_key("csv")
        if cacheable and not refresh_cache:
            with Cache(CACHE_DIRECTORY) as cache:
                cached = cache.get(cache_key)
            if cached is not None:
                return cast(str, cached)
        response = self._call(fields, extra_params={"format": "csv"})
        _raise_for_status(response)
        body = response.text
        if cacheable and body.strip():
            with Cache(CACHE_DIRECTORY) as cache:
                cache.set(cache_key, body, expire=self.cache_max_age_days * 24 * 60 * 60)
        return body

    def classic(
        self,
        fields: Sequence[str] | None = None,
        disable_date_parsing: bool | None = False,
        disable_type_parsing: bool | None = False,
        refresh_cache: bool = False,
    ) -> EpiDataResponse:
        """Request and parse epidata in CLASSIC message format.

        With ``refresh_cache=True`` the cache is not read, but the fresh result still replaces the cached entry.
        """
        if self.use_cache and not refresh_cache:
            with Cache(CACHE_DIRECTORY) as cache:
                cache_key = self._get_cache_key("classic", fields, str(disable_date_parsing))
                if cache_key in cache:
                    return cast(EpiDataResponse, cache[cache_key])
        response = self._call(fields)
        # Raised, not buried in the result dict: an HTTP error means no data came
        # back, and df() would otherwise hand back a silently empty frame.
        _raise_for_status(response)
        r = _parse_classic_envelope(response)
        try:
            if disable_type_parsing:
                return r
            epidata = r.get("epidata")
            if epidata and isinstance(epidata, list) and len(epidata) > 0 and isinstance(epidata[0], dict):
                r["epidata"] = [self._parse_row(row, disable_date_parsing=disable_date_parsing) for row in epidata]
            if self.use_cache:
                with Cache(CACHE_DIRECTORY) as cache:
                    cache_key = self._get_cache_key("classic", fields, str(disable_date_parsing))
                    cache.set(cache_key, r, expire=self.cache_max_age_days * 24 * 60 * 60)
            return r
        except Exception as e:  # noqa: BLE001 - intentional catch-all
            return {"result": 0, "message": f"error: {e}", "epidata": []}

    def __call__(
        self,
        fields: Sequence[str] | None = None,
        disable_date_parsing: bool | None = False,
        refresh_cache: bool = False,
    ) -> EpiDataResponse | DataFrame:
        """Request and parse epidata in df message format."""
        if self.only_supports_classic:
            return self.classic(
                fields,
                disable_date_parsing=disable_date_parsing,
                disable_type_parsing=False,
                refresh_cache=refresh_cache,
            )
        return self.df(fields, disable_date_parsing=disable_date_parsing, refresh_cache=refresh_cache)

    def df(
        self,
        fields: Sequence[str] | None = None,
        disable_date_parsing: bool | None = False,
        refresh_cache: bool = False,
    ) -> DataFrame:
        """Request and parse epidata as a pandas data frame.

        With ``refresh_cache=True`` the cache is not read, but the fresh result still replaces the cached entry.
        """
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
                        fields, disable_date_parsing=disable_date_parsing, refresh_cache=refresh_cache
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

        # Classic results are cached as parsed frames; cast results cache the raw CSV below.
        df_cache_key = self._get_cache_key("df", fields, str(disable_date_parsing))
        if self.use_cache and not refresh_cache and self._api_version != "cast":
            with Cache(CACHE_DIRECTORY) as cache:
                if df_cache_key in cache:
                    return cast(DataFrame, cache[df_cache_key])

        pred = fields_to_predicate(fields)
        columns: list[str] = [info.name for info in self.meta if pred(info.name)]
        fetched: DataFrame | None = None
        if self._api_version == "cast":
            # CAST endpoints only speak CSV.
            body = self._cast_csv_body(fields, refresh_cache)
            if body.strip():
                df = read_csv(StringIO(body), dtype=str)
                # Keep meta columns in order, plus any undeclared response columns (e.g. aux values).
                meta_names = {info.name for info in self.meta}
                cols_in_df = [c for c in columns if c in df.columns]
                extras = [c for c in df.columns if c not in meta_names and pred(c)]
                if extras and self._endpoint != "aux_data/":
                    # Aux value columns are open-ended, so only warn for snapshot/archive.
                    warnings.warn(
                        f"Not all return columns are specified as expected epidata fields. "
                        f"Unspecified fields {extras} are returned as strings and may need manual conversion.",
                        UserWarning,
                        stacklevel=2,
                    )
                df = df[cols_in_df + extras]
            else:
                df = DataFrame(columns=columns or None)
            fetched = df
        else:
            json = self.classic(fields, disable_type_parsing=True, refresh_cache=refresh_cache)
            _check_epidata_result(json)
            rows = json.get("epidata", [])
            if rows and not fields and isinstance(rows[0], dict):
                present = {key for row in rows for key in row}
                dropped = [info.name for info in self.meta if info.name not in present]
                if dropped:
                    warnings.warn(
                        f"Expected fields {dropped} were not in the response. "
                        "The API may have changed; they are filled with missing values.",
                        DroppedMetaFieldsWarning,
                        stacklevel=2,
                    )
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

        if self.use_cache and self._api_version != "cast":
            with Cache(CACHE_DIRECTORY) as cache:
                cache.set(df_cache_key, df, expire=self.cache_max_age_days * 24 * 60 * 60)

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
