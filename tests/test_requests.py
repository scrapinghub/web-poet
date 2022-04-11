from unittest import mock

import pytest
from web_poet.exceptions import RequestBackendError
from web_poet.page_inputs import (
    HttpRequest,
    HttpResponse,
    HttpRequestBody,
    HttpRequestHeaders
)
from web_poet.requests import (
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
