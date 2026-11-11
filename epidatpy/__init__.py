"""Fetch data from Delphi's API."""

# Make the linter happy about the unused variables
__all__ = [
    "CovidcastEpidata",
    "DroppedMetaFieldsWarning",
    "EmptyResultWarning",
    "EpiDataAPIError",
    "EpiDataContext",
    "EpiDataHTTPError",
    "EpiDataWarning",
    "EpiRange",
    "InvalidArgumentException",
    "MalformedResponseError",
    "__version__",
    "available_endpoints",
]
__author__ = "Delphi Research Group"


from ._constants import __version__
from ._model import (
    DroppedMetaFieldsWarning,
    EmptyResultWarning,
    EpiDataAPIError,
    EpiDataHTTPError,
    EpiDataWarning,
    EpiRange,
    InvalidArgumentException,
    MalformedResponseError,
)
from .request import CovidcastEpidata, EpiDataContext, available_endpoints
