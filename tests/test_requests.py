from unittest import mock

import pytest
from web_poet.page_inputs import HttpResponse
from web_poet.requests import (
    Request,
    HttpClient,
    RequestBackendError,
    request_backend_var,
)


@pytest.fixture
def async_mock():
    """workaround since python 3.7 doesn't ship with asyncmock."""

    async def async_test(req):
        return HttpResponse(req.url, req.body)

    mock.MagicMock.__await__ = lambda x: async_test().__await__()

    return async_test


def test_generic_request():

    req = Request("url")
    assert req.url == "url"
    assert req.method == "GET"
    assert req.headers is None
    assert req.body is None

    req = Request(
        "url", method="POST", headers={"User-Agent": "test agent"}, body=b"body"
    )
    assert req.method == "POST"
    assert req.headers == {"User-Agent": "test agent"}
    assert req.body == b"body"


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
    assert type(response) == HttpResponse


@pytest.mark.asyncio
async def test_http_client_single_requests(async_mock):
    client = HttpClient(async_mock)
    assert client.request_downloader == async_mock

    with mock.patch("web_poet.requests.Request") as mock_request:
        response = await client.request("url")
        response.url == "url"

        response = await client.get("url-get")
        response.url == "url-get"

        response = await client.post("url-post")
        response.url == "url-post"

        assert mock_request.call_args_list == [
            mock.call("url", "GET", None, None),
            mock.call("url-get", "GET", None, None),
            mock.call("url-post", "POST", None, None),
        ]


@pytest.mark.asyncio
async def test_http_client_batch_requests(async_mock):
    client = HttpClient(async_mock)

    requests = [
        Request("url-1"),
        Request("url-get", method="GET"),
        Request("url-post", method="POST"),
    ]
    responses = await client.batch_requests(*requests)

    assert all([isinstance(response, HttpResponse) for response in responses])
