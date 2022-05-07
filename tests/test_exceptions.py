from web_poet.page_inputs import HttpRequest, HttpResponse
from web_poet.exceptions import HttpError, HttpResponseError

URL = "https://example.com"


def test_http_error_init():

    request = HttpRequest(URL)

    exc = HttpError(request=request)
    assert exc.request == request

def test_http_response_error_init():

    request = HttpRequest(URL)
    response = HttpResponse(URL, b"")

    exc = HttpResponseError(request=request, response=response)
    assert exc.request == request
    assert exc.response == response
