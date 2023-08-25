import os
import warnings
from typing import Optional


def get_api_key() -> Optional[str]:
    key = os.environ.get("DELPHI_EPIDATA_KEY", None)

    if not key:
        warnings.warn(
            "DELPHI_EPIDATA_KEY environment variable not set. "
            "Please set it to your Epidata API key to avoid rate limits. "
            "You can get a free key at: https://api.delphi.cmu.edu/epidata/admin/registration_form"
        )

    return key
