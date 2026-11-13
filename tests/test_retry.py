"""Which responses are retried, how long we wait, and that a long Retry-After is never waited on."""

from __future__ import annotations

from typing import Any

import pytest
from requests import ConnectionError as RequestsConnectionError
from requests import Response

from epidatpy import EpiDataHTTPError, _call
from epidatpy._call import _raise_for_status, _request_with_retry, _retry_after_seconds


def _response(status: int, retry_after: str | None = None, body: str = "{}") -> Response:
    res = Response()
    res.status_code = status
    res._content = body.encode()
    res.headers["Content-Type"] = "application/json"
    if retry_after is not None:
        res.headers["Retry-After"] = retry_after
    res.url = "https://x/y"
    return res


class ScriptedSession:
    """Answers each GET with the next item of `script`: a Response, or an exception to raise."""

    def __init__(self, *script: Response | Exception) -> None:
        self.script = list(script)
        self.calls = 0

    def get(self, *args: Any, **kwargs: Any) -> Response:
        self.calls += 1
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    monkeypatch.delenv("EPIDATPY_MAX_RETRY_WAIT", raising=False)
    waited: list[float] = []
    monkeypatch.setattr(_call, "_sleep", waited.append)
    return waited


def _send(*script: Response | Exception) -> tuple[Response, ScriptedSession]:
    session = ScriptedSession(*script)
    return _request_with_retry("https://x/y", {}, session), session  # type: ignore[arg-type]


def test_transient_server_error_is_retried_with_backoff(sleeps: list[float]) -> None:
    res, session = _send(_response(503), _response(502), _response(200))
    assert res.status_code == 200
    assert session.calls == 3
    assert sleeps == [1, 2]


def test_gives_up_after_three_tries_and_returns_the_last_response(sleeps: list[float]) -> None:
    res, session = _send(_response(500), _response(500), _response(500))
    assert res.status_code == 500
    assert session.calls == 3


def test_short_retry_after_is_honoured(sleeps: list[float]) -> None:
    res, _ = _send(_response(503, "5"), _response(200))
    assert res.status_code == 200
    assert sleeps == [5]


def test_long_retry_after_is_never_waited_on(sleeps: list[float]) -> None:
    res, session = _send(_response(503, "3600"))
    assert res.status_code == 503
    assert session.calls == 1
    assert sleeps == []


def test_max_retry_wait_is_configurable(sleeps: list[float], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EPIDATPY_MAX_RETRY_WAIT", "2")
    _, session = _send(_response(503, "5"))
    assert session.calls == 1


def test_429_is_retried_only_when_the_server_says_when(sleeps: list[float]) -> None:
    _, session = _send(_response(429))
    assert session.calls == 1
    res, session = _send(_response(429, "3"), _response(200))
    assert res.status_code == 200
    assert sleeps == [3]


@pytest.mark.parametrize("status", [400, 401, 404, 422])
def test_client_errors_are_not_retried(status: int, sleeps: list[float]) -> None:
    _, session = _send(_response(status))
    assert session.calls == 1


def test_connection_errors_are_retried_then_raised(sleeps: list[float]) -> None:
    res, _ = _send(RequestsConnectionError("boom"), _response(200))
    assert res.status_code == 200
    with pytest.raises(RequestsConnectionError):
        _send(*[RequestsConnectionError("boom")] * 3)


@pytest.mark.parametrize(
    ("value", "expected"), [("10", 10.0), ("-5", 0.0), ("soon", None), ("nan", None), ("inf", None), (None, None)]
)
def test_retry_after_parsing(value: str | None, expected: float | None) -> None:
    assert _retry_after_seconds(_response(503, value)) == expected


def test_http_error_says_when_the_server_suggests_retrying() -> None:
    body = '{"detail": "Try again in an hour."}'
    with pytest.raises(
        EpiDataHTTPError, match=r"Try again in an hour\. The server suggests retrying in about 60 minutes\."
    ):
        _raise_for_status(_response(503, "3600", body))
