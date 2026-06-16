from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import (
    Any,
    Final,
)

from pandas import DataFrame
from requests import Session

from ._call import EpiDataCall, _request_with_retry
from ._constants import BASE_URL, CAST_BASE_URL
from ._covidcast import CovidcastDataSources, define_covidcast_fields
from ._endpoints import AEpiDataEndpoints
from ._model import (
    ApiVersion,
    CastPostFilter,
    EpidataFieldInfo,
    EpiRangeParam,
    add_endpoint_to_url,
)


class EpiDataContext(AEpiDataEndpoints):
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
        return EpiDataContext(
            base_url,
            self._session,
            self.use_cache,
            self.cache_max_age_days,
            cast_base_url=self._cast_base_url,
        )

    def with_session(self, session: Session) -> EpiDataContext:
        return EpiDataContext(
            self._base_url,
            session,
            self.use_cache,
            self.cache_max_age_days,
            cast_base_url=self._cast_base_url,
        )

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
) -> CovidcastDataSources:
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
