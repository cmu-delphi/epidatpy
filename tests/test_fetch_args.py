from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from epidatpy import FetchArgs, InvalidArgumentException, fetch_args


def test_fetch_args_defaults() -> None:
    args = fetch_args()

    assert args == FetchArgs()
    assert args.limit is None
    assert args.return_empty is False


@pytest.mark.parametrize("limit", [None, -1])
def test_fetch_args_normalizes_no_limit(limit: int | None) -> None:
    assert fetch_args(limit=limit).limit is None


@pytest.mark.parametrize("limit", [1, 10, 100])
def test_fetch_args_accepts_positive_limit(limit: int) -> None:
    assert fetch_args(limit=limit).limit == limit


@pytest.mark.parametrize("limit", [0, -2, 1.5, True])
def test_fetch_args_rejects_invalid_limit(limit: object) -> None:
    with pytest.raises(InvalidArgumentException):
        fetch_args(limit=limit)  # type: ignore[arg-type]


def test_fetch_args_validates_return_empty() -> None:
    assert fetch_args(return_empty=True).return_empty is True

    with pytest.raises(InvalidArgumentException):
        fetch_args(return_empty=1)  # type: ignore[arg-type]


def test_fetch_args_is_immutable() -> None:
    args = fetch_args(limit=10)

    with pytest.raises(FrozenInstanceError):
        # Deliberately violate the static contract to test runtime immutability.
        args.limit = 20  # type: ignore[misc]
