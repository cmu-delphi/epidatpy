"""Mirrors epidatr's "fetch surfaces http errors": API errors carry the
server's own message for both the classic (V4) and cast (V5) APIs."""

from __future__ import annotations

import pytest
from requests import HTTPError, Response

from epidatpy._call import _raise_for_status
from epidatpy.request import EpiDataContext


def _response(body: str, status_code: int, content_type: str) -> Response:
    res = Response()
    res.status_code = status_code
    res._content = body.encode()
    res.headers["Content-Type"] = content_type
    res.url = "https://api.delphi.cmu.edu/epidata/test"
    return res


@pytest.mark.parametrize(
    ("body", "content_type", "expected"),
    [
        ('{"message": "invalid signal"}', "application/json", "invalid signal"),
        ('{"detail": "no such source"}', "application/json", "no such source"),
        # FastAPI's own validation errors put a list of objects under "detail"
        # rather than a plain string; this must not itself crash while formatting.
        (
            '{"detail": [{"loc": ["query", "source"], "msg": "Input should be \'nssp\'"}]}',
            "application/json",
            "Input should be 'nssp'",
        ),
        ("<html><body><p>database error</p></body></html>", "text/html", "database error"),
        # Unusable bodies fall back to requests' own message.
        ("not json", "application/json", "422"),
        ("oops", "text/plain", "422"),
    ],
)
def test_raise_for_status_surfaces_server_message(body: str, content_type: str, expected: str) -> None:
    with pytest.raises(HTTPError, match=expected):
        _raise_for_status(_response(body, 422, content_type))


def test_classic_surfaces_server_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """A classic (V4) HTTP error raises rather than returning an empty frame."""
    res = _response("<html><body><p>Internal Server Error</p></body></html>", 500, "text/html")
    monkeypatch.setattr("epidatpy._call._request_with_retry", lambda *a, **k: res)
    call = EpiDataContext().pub_flusurv("network", "202001")
    with pytest.raises(HTTPError, match="Internal Server Error"):
        call.classic()
    with pytest.raises(HTTPError, match="Internal Server Error"):
        call.df()


def test_df_cast_surfaces_server_message(monkeypatch: pytest.MonkeyPatch) -> None:
    res = _response('{"message": "invalid signal"}', 422, "application/json")
    monkeypatch.setattr("epidatpy._call._request_with_retry", lambda *a, **k: res)
    with pytest.raises(HTTPError, match="invalid signal"):
        EpiDataContext().epidata_snapshot("nssp", "bad_sig", "state").df()
