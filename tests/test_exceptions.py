import pytest

from web_poet.exceptions import HttpError, HttpRequestError, HttpResponseError
from web_poet.page_inputs import HttpRequest, HttpResponse

URL = "https://example.com"


def test_http_error_init() -> None:
    exc = HttpError()
    assert exc.request is None
    assert exc.args

    request = HttpRequest(URL)
    exc = HttpError(request=request)
    assert exc.request == request


def test_http_request_error_init() -> None:
    exc = HttpRequestError()
    assert exc.request is None
    assert exc.args

    request = HttpRequest(URL)
    exc = HttpRequestError(request=request)
    assert exc.request == request

    response = HttpResponse(URL, b"")
    with pytest.raises(TypeError):
        HttpRequestError(request=request, response=response)  # type: ignore[call-arg]


def test_http_response_error_init() -> None:
    exc = HttpResponseError()
    assert exc.request is None
    assert exc.response is None
    assert exc.args

    request = HttpRequest(URL)
    response = HttpResponse(URL, b"")

    exc = HttpResponseError(request=request, response=response)
    assert exc.request == request
    assert exc.response == response
