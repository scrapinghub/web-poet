from unittest import mock

import pytest
from web_poet.exceptions import RequestBackendError, HttpRequestError
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
        return HttpResponse(req.url, body=b"")

    mock.MagicMock.__await__ = lambda x: async_test(x).__await__()

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
            mock.call(
                url="url",
                method="GET",
                headers=HttpRequestHeaders(),
                body=HttpRequestBody()
            ),
            mock.call(
                url="url-get",
                method="GET",
                headers=HttpRequestHeaders({"X-Headers": "123"}),
                body=HttpRequestBody(),
            ),
            mock.call(
                url="url-post",
                method="POST",
                headers=HttpRequestHeaders({"X-Headers": "123"}),
                body=HttpRequestBody(b"body value"),
            ),
        ]


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["request", "get", "post"])
async def test_http_client_request_status_err(method_name):
    client = HttpClient(async_mock)

    # Simulate 500 Internal Server Error responses
    async def stub_request_downloader(*args, **kwargs):
        async def stub(req):
            return HttpResponse(req.url, body=b"", status=500)
        return await stub(*args, **kwargs)
    client._request_downloader = stub_request_downloader

    method = getattr(client, method_name)

    await method("url", allow_status=[500])
    with pytest.raises(HttpRequestError):
        await method("url")


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
async def test_http_client_execute(async_mock):
    client = HttpClient(async_mock)

    request = HttpRequest("url-1")
    response = await client.execute(request)

    assert isinstance(response, HttpResponse)
    assert response.url == "url-1"


@pytest.mark.asyncio
async def test_http_client_batch_execute(async_mock):
    client = HttpClient(async_mock)

    requests = [
        HttpRequest("url-1"),
        HttpRequest("url-get", method="GET"),
        HttpRequest("url-post", method="POST"),
    ]
    responses = await client.batch_execute(*requests)

    assert all([isinstance(response, HttpResponse) for response in responses])


@pytest.fixture
def client_that_errs(async_mock):
    client = HttpClient(async_mock)

    # Simulate errors inside the request coroutines
    async def stub_request_downloader(*args, **kwargs):
        async def err():
            raise ValueError("test exception")
        return await err()
    client._request_downloader = stub_request_downloader

    return client


@pytest.mark.asyncio
async def test_http_client_batch_execute_with_exception(client_that_errs):

    requests = [
        HttpRequest("url-1"),
        HttpRequest("url-get", method="GET"),
        HttpRequest("url-post", method="POST"),
    ]
    responses = await client_that_errs.batch_execute(*requests, return_exceptions=True)

    assert len(responses) == 3
    assert isinstance(responses[0], Exception)
    assert isinstance(responses[1], Exception)
    assert isinstance(responses[2], Exception)


@pytest.mark.asyncio
async def test_http_client_batch_execute_with_exception_raised(client_that_errs):
    requests = [
        HttpRequest("url-1"),
    ]
    with pytest.raises(ValueError):
        await client_that_errs.batch_execute(*requests)
