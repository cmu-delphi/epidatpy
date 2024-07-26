"""Fetch data from Delphi's API."""

# Make the linter happy about the unused variables
__all__ = ["__version__", "Epidata", "CovidcastEpidata", "EpiRange"]
__author__ = "Delphi Research Group"


from ._constants import __version__
from .request import CovidcastEpidata, EpiDataContext, EpiRange
