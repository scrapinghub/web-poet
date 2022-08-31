from typing import Callable, Union
from unittest import mock

import pytest

from web_poet.exceptions import HttpResponseError, RequestDownloaderVarError
from web_poet.page_inputs import (
    HttpClient,
    HttpRequest,
    HttpRequestBody,
    HttpRequestHeaders,
    HttpResponse,
)
from web_poet.requests import request_downloader_var


@pytest.fixture
def async_mock():
    """Workaround since python 3.7 doesn't ship with asyncmock."""

    async def async_test(req):
        return HttpResponse(str(req.url), body=b"")

    mock.MagicMock.__await__ = lambda x: async_test(x).__await__()

    return async_test


@pytest.mark.asyncio
async def test_perform_request_from_httpclient(async_mock) -> None:

    url = "http://example.com"
    client = HttpClient()

    with pytest.raises(RequestDownloaderVarError):
        await client.get(url)

    request_downloader_var.set(async_mock)
    response = await client.get(url)

    # The async downloader implementation should return the HttpResponse
    assert str(response.url) == str(url)
    assert isinstance(response, HttpResponse)


@pytest.mark.asyncio
async def test_http_client_single_requests(async_mock) -> None:
    client = HttpClient(async_mock)

    with mock.patch("web_poet.page_inputs.client.HttpRequest") as mock_request:
        await client.request("url")
        await client.get("url-get", headers={"X-Headers": "123"})
        await client.post("url-post", headers={"X-Headers": "123"}, body=b"body value")
        assert mock_request.call_args_list == [
            mock.call(
                url="url",
                method="GET",
                headers=HttpRequestHeaders(),
                body=HttpRequestBody(),
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


@pytest.fixture
def client_with_status() -> Callable:
    def _param_wrapper(status_code: int):
        async def stub_request_downloader(*args, **kwargs):
            async def stub(req):
                return HttpResponse(req.url, body=b"", status=status_code)

            return await stub(*args, **kwargs)

        return stub_request_downloader

    return _param_wrapper


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["request", "get", "post", "execute"])
async def test_http_client_allow_status(
    async_mock, client_with_status, method_name
) -> None:
    client = HttpClient(async_mock)

    # Simulate 500 Internal Server Error responses
    client._request_downloader = client_with_status(500)

    method = getattr(client, method_name)

    url_or_request: Union[str, HttpRequest] = "url"
    if method_name == "execute":
        # NOTE: We're ignoring the type below due to the following mypy bugs:
        #   - https://github.com/python/mypy/issues/10187
        #   - https://github.com/python/mypy/issues/5313
        #   - https://github.com/python-attrs/attrs/issues/889
        # Currently, the said bugs causes mypy to raise the following error:
        #   'Incompatible types in assignment (expression has type "ResponseUrl",
        #   variable has type "Optional[str]")'
        url_or_request = HttpRequest(url_or_request)  # type: ignore[arg-type]

    # Should handle single and multiple values
    await method(url_or_request, allow_status=500)
    response = await method(url_or_request, allow_status=[500, 503])
    assert isinstance(response, HttpResponse)
    assert response.status == 500

    # As well as strings
    await method(url_or_request, allow_status="500")
    await method(url_or_request, allow_status=["500", "503"])

    with pytest.raises(HttpResponseError) as excinfo:
        await method(url_or_request)
    assert isinstance(excinfo.value.request, HttpRequest)
    assert isinstance(excinfo.value.response, HttpResponse)
    assert str(excinfo.value).startswith("500 INTERNAL_SERVER_ERROR response for")

    with pytest.raises(HttpResponseError):
        await method(url_or_request, allow_status=406)
    assert isinstance(excinfo.value.request, HttpRequest)
    assert isinstance(excinfo.value.response, HttpResponse)
    assert str(excinfo.value).startswith("500 INTERNAL_SERVER_ERROR response for")

    # As long as "*" is present, then no errors would be raised
    await method(url_or_request, allow_status="*")
    await method(url_or_request, allow_status=[500, "*"])

    # Globbing isn't supported
    with pytest.raises(HttpResponseError):
        await method(url_or_request, allow_status="5*")
    assert isinstance(excinfo.value.request, HttpRequest)
    assert isinstance(excinfo.value.response, HttpResponse)
    assert str(excinfo.value).startswith("500 INTERNAL_SERVER_ERROR response for")


@pytest.mark.asyncio
async def test_http_client_keyword_enforcing(async_mock) -> None:
    """Only keyword args are allowed after the url param."""

    client = HttpClient(async_mock)

    with pytest.raises(TypeError):
        await client.request("url", "PATCH")  # type: ignore[misc]

    with pytest.raises(TypeError):
        await client.get("url", {"Content-Encoding": "utf-8"})  # type: ignore[misc]

    with pytest.raises(TypeError):
        await client.post("url", {"X-Header": "value"}, b"body")  # type: ignore[misc]


@pytest.mark.asyncio
async def test_http_client_execute(async_mock) -> None:
    client = HttpClient(async_mock)

    request = HttpRequest("url-1")
    response = await client.execute(request)

    assert isinstance(response, HttpResponse)
    assert str(response.url) == "url-1"


@pytest.mark.asyncio
async def test_http_client_batch_execute(async_mock) -> None:
    client = HttpClient(async_mock)

    requests = [
        HttpRequest("url-1"),
        HttpRequest("url-get", method="GET"),
        HttpRequest("url-post", method="POST"),
    ]
    responses = await client.batch_execute(*requests)

    assert all([isinstance(response, HttpResponse) for response in responses])


@pytest.fixture
def client_that_errs(async_mock) -> HttpClient:
    client = HttpClient(async_mock)

    # Simulate errors inside the request coroutines
    async def stub_request_downloader(*args, **kwargs):
        async def err():
            raise ValueError("test exception")

        return await err()

    client._request_downloader = stub_request_downloader

    return client


@pytest.mark.asyncio
async def test_http_client_batch_execute_with_exception(client_that_errs) -> None:

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
async def test_http_client_batch_execute_with_exception_raised(
    client_that_errs,
) -> None:
    requests = [
        HttpRequest("url-1"),
    ]
    with pytest.raises(ValueError):
        await client_that_errs.batch_execute(*requests)


@pytest.mark.asyncio
async def test_http_client_batch_execute_allow_status(
    async_mock, client_with_status
) -> None:
    client = HttpClient(async_mock)

    # Simulate 400 Bad Request
    client._request_downloader = client_with_status(400)

    requests = [HttpRequest("url-1"), HttpRequest("url-2"), HttpRequest("url-3")]

    await client.batch_execute(*requests, allow_status=400)
    await client.batch_execute(*requests, allow_status=[400, 403])
    await client.batch_execute(*requests, allow_status="400")
    responses = await client.batch_execute(*requests, allow_status=["400", "403"])

    for r in responses:
        assert isinstance(r, HttpResponse) and r.status == 400

    with pytest.raises(HttpResponseError) as excinfo:
        await client.batch_execute(*requests)
    assert isinstance(excinfo.value.request, HttpRequest)
    assert isinstance(excinfo.value.response, HttpResponse)
    assert str(excinfo.value).startswith("400 BAD_REQUEST response for")

    with pytest.raises(HttpResponseError) as excinfo:
        await client.batch_execute(*requests, allow_status=406)
    assert isinstance(excinfo.value.request, HttpRequest)
    assert isinstance(excinfo.value.response, HttpResponse)
    assert str(excinfo.value).startswith("400 BAD_REQUEST response for")

    await client.batch_execute(*requests, return_exceptions=True, allow_status=400)
    await client.batch_execute(
        *requests, return_exceptions=True, allow_status=[400, 403]
    )
    await client.batch_execute(*requests, return_exceptions=True, allow_status="400")
    await client.batch_execute(
        *requests, return_exceptions=True, allow_status=["400", "403"]
    )

    responses = await client.batch_execute(*requests, return_exceptions=True)
    for r in responses:
        assert (
            isinstance(r, HttpResponseError)
            and isinstance(r.request, HttpRequest)
            and isinstance(r.response, HttpResponse)
        )
    assert all([str(r).startswith("400 BAD_REQUEST response for") for r in responses])

    responses = await client.batch_execute(
        *requests, return_exceptions=True, allow_status=408
    )
    for r in responses:
        assert (
            isinstance(r, HttpResponseError)
            and isinstance(r.request, HttpRequest)
            and isinstance(r.response, HttpResponse)
        )
    assert all([str(r).startswith("400 BAD_REQUEST response for") for r in responses])

    # These have no assertions since they're used to see if mypy raises an
    # error against them.
    for r in responses:
        if isinstance(r, HttpResponseError):
            r.request
            r.response
        else:
            r.url
            r.body
            r.status
            r.headers
