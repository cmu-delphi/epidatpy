import os
import warnings


def _get_api_key() -> str:
    key = os.environ.get("DELPHI_EPIDATA_KEY", "")

    if not key:
        warnings.warn(
            "DELPHI_EPIDATA_KEY environment variable not set. "
            "Please set it to your Epidata API key to avoid rate limits. "
            "You can get a free key at: https://api.delphi.cmu.edu/epidata/admin/registration_form"
        )

    return key
