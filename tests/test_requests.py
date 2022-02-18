from unittest import mock

import pytest
from web_poet.page_inputs import ResponseData
from web_poet.requests import (
    GenericRequest,
    perform_request,
    HttpClient,
    RequestBackendError,
    request_backend_var,
)


@pytest.fixture
def async_mock():
    """workaround since python 3.7 doesn't ship with asyncmock."""

    async def async_test(req):
        return ResponseData(req.url, req.body)

    mock.MagicMock.__await__ = lambda x: async_test().__await__()

    return async_test


def test_generic_request():

    req = GenericRequest("url")
    assert req.url == "url"
    assert req.method == "GET"
    assert req.headers is None
    assert req.body is None

    req = GenericRequest(
        "url", method="POST", headers={"User-Agent": "test agent"}, body=b"body"
    )
    assert req.method == "POST"
    assert req.headers == {"User-Agent": "test agent"}
    assert req.body == b"body"


@pytest.mark.asyncio
async def test_perform_request(async_mock):

    req = GenericRequest("url")

    with pytest.raises(RequestBackendError):
        await perform_request(req)

    request_backend_var.set(async_mock)
    response = await perform_request(req)

    # The async downloader implementation should return the ResponseData
    assert response.url == req.url
    assert type(response) == ResponseData


@pytest.mark.asyncio
async def test_http_client(async_mock):
    client = HttpClient(async_mock)
    assert client.request_downloader == async_mock

    req_1 = GenericRequest("url-1")
    req_2 = GenericRequest("url-2")

    # It should be able to accept arbitrary number of requests
    client.request(req_1)
    responses = await client.request(req_1, req_2)

    assert responses[0].url == req_1.url
    assert responses[1].url == req_2.url
