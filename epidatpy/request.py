from __future__ import annotations

import inspect
from collections.abc import Mapping

from pandas import DataFrame
from requests import Session

from ._call import EpiDataCall, _request_with_retry
from ._constants import BASE_URL
from ._covidcast import CovidcastDataSources, define_covidcast_fields
from ._endpoints import EpiDataContext
from ._model import EpiRangeParam, add_endpoint_to_url

__all__ = [
    "CovidcastEpidata",
    "EpiDataCall",
    "EpiDataContext",
    "available_endpoints",
]


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
    endpoints = [x for x in inspect.getmembers(EpiDataContext) if x[0].startswith("pvt_") or x[0].startswith("pub_")]
    data = {e[0]: e[1].__doc__.split("\n")[0] if e[1].__doc__ else "None" for e in endpoints}
    return DataFrame(data.items(), columns=["Endpoint", "Description"])
