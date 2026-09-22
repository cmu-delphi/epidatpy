import pytest
from requests import Response

from epidatpy import EpiDataHTTPError
from epidatpy._call import _check_response, _error_body_message


def _response(status: int, body: str, content_type: str) -> Response:
    r = Response()
    r.status_code = status
    r._content = body.encode()
    r.headers["Content-Type"] = content_type
    r.url = "https://example.test/epidata/v5/snapshot/"
    return r


def test_error_body_message_json_message() -> None:
    r = _response(400, '{"message": "unknown source"}', "application/json; charset=utf-8")
    assert _error_body_message(r) == "unknown source"


def test_error_body_message_fastapi_detail() -> None:
    r = _response(422, '{"detail": [{"msg": "field required"}, {"loc": ["x"]}]}', "application/json")
    assert _error_body_message(r) == "field required; invalid value"
    r = _response(422, '{"detail": "not found"}', "application/json")
    assert _error_body_message(r) == "not found"


def test_error_body_message_html() -> None:
    r = _response(
        500, "<html><body><h1>Oops</h1><p>Server <b>exploded</b></p><p>Try later</p></body></html>", "text/html"
    )
    assert _error_body_message(r) == "Server exploded Try later"


def test_error_body_message_unparseable() -> None:
    assert _error_body_message(_response(500, "not json", "application/json")) is None
    assert _error_body_message(_response(500, "plain", "text/plain")) is None


def test_check_response_raises_with_message() -> None:
    r = _response(400, '{"message": "unknown source"}', "application/json")
    with pytest.raises(EpiDataHTTPError, match="HTTP 400: unknown source") as excinfo:
        _check_response(r)
    assert excinfo.value.status_code == 400
    assert excinfo.value.message == "unknown source"


def test_check_response_passes_success() -> None:
    r = _response(200, "ok", "text/plain")
    assert _check_response(r) is r
