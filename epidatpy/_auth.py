import os
import warnings


def _get_api_key() -> str:
    key = os.environ.get("DELPHI_EPIDATA_KEY", "")

    if not key:
        warnings.warn(
            "DELPHI_EPIDATA_KEY environment variable not set. "
            "Anonymous V5 access is limited to 60 requests/hour, with additional limits of "
            "5 requests/minute on archive queries and 3 requests/minute on snapshot queries. "
            "Some endpoints also require a key. "
            "You can get a free key at: https://api.delphi.cmu.edu/epidata/admin/registration_form"
        )

    return key
