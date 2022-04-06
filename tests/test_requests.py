from unittest import mock

import pytest
from web_poet.page_inputs import HttpResponse
from web_poet.exceptions import RequestBackendError
from web_poet.requests import (
    HttpRequestHeaders,
    HttpRequestBody,
    HttpRequest,
    HttpClient,
    request_backend_var,
)


@pytest.fixture
def async_mock():
    """Workaround since python 3.7 doesn't ship with asyncmock."""

    async def async_test(req):
        return HttpResponse(req.url, b"")

    mock.MagicMock.__await__ = lambda x: async_test().__await__()

    return async_test


def test_http_request_body_hashable():
    http_body = HttpRequestBody(b"content")
    assert http_body in {http_body}
    assert http_body in {b"content"}
    assert http_body not in {b"foo"}


def test_http_request_body_bytes_api():
    http_body = HttpRequestBody(b"content")
    assert http_body == b"content"
    assert b"ent" in http_body


def test_http_request_body_str_api():
    with pytest.raises(TypeError):
        HttpRequestBody("string content")


def test_http_request_bytes_body():
    request = HttpRequest("http://example.com", body=b"content")
    assert isinstance(request.body, HttpRequestBody)
    assert request.body == HttpRequestBody(b"content")


def test_http_request_body_conversion_str():
    with pytest.raises(TypeError):
        HttpRequest("http://example.com", body="content")


def test_http_request_body_validation_None():
    with pytest.raises(TypeError):
        HttpRequest("http://example.com", body=None)


def test_http_request_headers():
    headers = HttpRequestHeaders({"user-agent": "chrome"})
    assert headers['user-agent'] == "chrome"
    assert headers['User-Agent'] == "chrome"

    with pytest.raises(KeyError):
        headers["user agent"]


def test_http_request_headers_init_dict():
    request = HttpRequest(
        "http://example.com", body=b"", headers={"user-agent": "chrome"}
    )
    assert isinstance(request.headers, HttpRequestHeaders)
    assert request.headers['user-agent'] == "chrome"
    assert request.headers['User-Agent'] == "chrome"


def test_http_request_headers_init_invalid():
    with pytest.raises(TypeError):
        HttpRequest("http://example.com", body=b"", headers=123)


def test_http_request_generic():
    req = HttpRequest("url")
    assert req.url == "url"
    assert req.method == "GET"
    assert isinstance(req.method, str)
    assert not req.headers
    assert isinstance(req.headers, HttpRequestHeaders)
    assert not req.body
    assert isinstance(req.body, HttpRequestBody)


def test_http_request_init():
    req_1 = HttpRequest(
        "url", method="POST", headers={"User-Agent": "test agent"}, body=b"body"
    )
    assert req_1.method == "POST"
    assert isinstance(req_1.method, str)
    assert req_1.headers == {"User-Agent": "test agent"}
    assert req_1.headers.get("user-agent") == "test agent"
    assert isinstance(req_1.headers, HttpRequestHeaders)
    assert req_1.body == b"body"
    assert isinstance(req_1.body, HttpRequestBody)

    http_headers = HttpRequestHeaders({"User-Agent": "test agent"})
    http_body = HttpRequestBody(b"body")
    req_2 = HttpRequest("url", method="POST", headers=http_headers, body=http_body)

    assert req_1.url == req_2.url
    assert req_1.method == req_2.method
    assert req_1.headers == req_2.headers
    assert req_1.body == req_2.body


@pytest.mark.asyncio
async def test_perform_request_from_httpclient(async_mock):

    url = "http://example.com"
    client = HttpClient()

    with pytest.raises(RequestBackendError):
        await client.get(url)

    request_backend_var.set(async_mock)
    response = await client.get(url)

    # The async downloader implementation should return the HttpResponse
    assert response.url == url
    assert isinstance(response, HttpResponse)


@pytest.mark.asyncio
async def test_http_client_single_requests(async_mock):
    client = HttpClient(async_mock)

    with mock.patch("web_poet.requests.HttpRequest") as mock_request:
        response = await client.request("url")
        response.url == "url"

        response = await client.get("url-get", headers={"X-Headers": "123"})
        response.url == "url-get"

        response = await client.post(
            "url-post", headers={"X-Headers": "123"}, body=b"body value"
        )
        response.url == "url-post"

        assert mock_request.call_args_list == [
            mock.call("url", "GET", HttpRequestHeaders(), HttpRequestBody()),
            mock.call(
                "url-get",
                "GET",
                HttpRequestHeaders({"X-Headers": "123"}),
                HttpRequestBody(),
            ),
            mock.call(
                "url-post",
                "POST",
                HttpRequestHeaders({"X-Headers": "123"}),
                HttpRequestBody(b"body value"),
            ),
        ]


@pytest.mark.asyncio
async def test_http_client_keyword_enforcing(async_mock):
    """Only keyword args are allowed after the url param."""

    client = HttpClient(async_mock)

    with pytest.raises(TypeError):
        await client.request("url", "PATCH")

    with pytest.raises(TypeError):
        await client.get("url", {"Content-Encoding": "utf-8"})

    with pytest.raises(TypeError):
        await client.post("url", {"X-Header": "value"}, b"body")


@pytest.mark.asyncio
async def test_http_client_batch_requests(async_mock):
    client = HttpClient(async_mock)

    requests = [
        HttpRequest("url-1"),
        HttpRequest("url-get", method="GET"),
        HttpRequest("url-post", method="POST"),
    ]
    responses = await client.batch_requests(*requests)

    assert all([isinstance(response, HttpResponse) for response in responses])
