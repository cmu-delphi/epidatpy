from __future__ import annotations

from dataclasses import dataclass

from ._model import InvalidArgumentException


def _validate_limit(limit: int | None) -> int | None:
    """Normalize a V5 row limit."""
    if limit is None or limit == -1:
        return None

    # bool is a subclass of int, so reject it explicitly.
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise InvalidArgumentException("`limit` must be -1 (no limit) or a positive integer")

    return limit


@dataclass(frozen=True)
class FetchArgs:
    """Shared options controlling V5 request execution."""

    limit: int | None = None
    return_empty: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "limit", _validate_limit(self.limit))

        if not isinstance(self.return_empty, bool):
            raise InvalidArgumentException("`return_empty` must be a boolean")


def fetch_args(
    *,
    limit: int | None = None,
    return_empty: bool = False,
) -> FetchArgs:
    """Create shared options for V5 Epidata requests."""
    return FetchArgs(
        limit=limit,
        return_empty=return_empty,
    )
