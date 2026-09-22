"""Shared fixtures for offline tests that stub the HTTP layer."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import pytest
from requests import Response

import epidatpy._call as call_module

Responder = Callable[[str, Mapping[str, str]], str]


@dataclass
class FakeServer:
    """Records each (url, params) request and answers via `responder`."""

    responder: Responder
    requests: list[tuple[str, dict[str, str]]] = field(default_factory=list)

    def __call__(self, url: str, params: Mapping[str, str], *args: object, **kwargs: object) -> Response:
        self.requests.append((url, dict(params)))
        body = self.responder(url, params)
        r = Response()
        r.status_code = 200
        r._content = body.encode()
        r.headers["Content-Type"] = "application/json" if body.lstrip().startswith(("{", "[")) else "text/csv"
        r.url = url
        return r


@pytest.fixture
def fake_server(monkeypatch: pytest.MonkeyPatch) -> Callable[[Responder], FakeServer]:
    def install(responder: Responder) -> FakeServer:
        server = FakeServer(responder)
        monkeypatch.setattr(call_module, "_request_with_retry", server)
        return server

    return install
