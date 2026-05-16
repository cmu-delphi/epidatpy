from importlib.metadata import version
from typing import Final

__version__: Final = version("epidatpy")
HTTP_HEADERS: Final = {"User-Agent": f"epidatpy/{__version__}"}
BASE_URL: Final = "https://api.delphi.cmu.edu/epidata/"
CAST_BASE_URL: Final = "https://delphi.cmu.edu/epidata/v5/"
