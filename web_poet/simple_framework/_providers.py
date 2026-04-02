from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_type_hints

import niquests

from web_poet.page_inputs import (
    HttpClient,
    HttpRequest,
    HttpRequestBody,
    HttpResponse,
    HttpResponseBody,
    PageParams,
    RequestUrl,
    ResponseUrl,
)

if TYPE_CHECKING:
    from collections.abc import Callable

PROVIDERS: dict[type, Callable[..., Any]] = {}


def _get_http_response_from_nirequests_response(
    request: HttpRequest, response: niquests.Response
) -> HttpResponse:
    return HttpResponse(
        response.url or request.url,
        status=response.status_code,
        body=response.content or b"",
        headers=response.headers,
    )


async def _get_http_response_from_http_request(request: HttpRequest) -> HttpResponse:
    response = await niquests.aget(request.url, timeout=300)
    return _get_http_response_from_nirequests_response(request, response)


class ResponseFetcher:
    def __init__(self) -> None:
        self.response: niquests.Response | None = None

    async def fetch(self, request: HttpRequest) -> HttpResponse:
        if self.response is None:
            self.response = await _get_http_response_from_http_request(request)
        return self.response


def _provider_func(func: Callable[..., Any]):
    dep = get_type_hints(func).get("return")
    PROVIDERS[dep] = func
    return func


def _provider_cls(dep: type):
    def _provider(cls: Any) -> Any:
        PROVIDERS[dep] = cls
        return cls

    return _provider


@_provider_func
async def _get_http_response(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> HttpResponse:
    return await response_fetcher.fetch(request)


@_provider_func
def _get_request_body(request: HttpRequest, **_kwargs) -> HttpRequestBody:
    return HttpRequestBody(request.body)


@_provider_func
async def _get_response_body(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> HttpResponseBody:
    response = await response_fetcher.fetch(request)
    return response.body


@_provider_func
async def _get_response_url(
    request: HttpRequest, response_fetcher: ResponseFetcher | None = None, **_kwargs
) -> ResponseUrl:
    response = await response_fetcher.fetch(request)
    return response.url


@_provider_func
def _get_request_url(request: HttpRequest, **_kwargs) -> RequestUrl:
    return request.url


@_provider_func
def _get_page_params(
    page_params: dict[Any, Any] | None = None, **_kwargs
) -> PageParams:
    return PageParams(page_params or {})


@_provider_cls(HttpClient)
class _HttpClient:
    def __init__(self, **_kwargs):
        pass

    async def get(self, url: str) -> HttpResponse:
        return await _get_http_response_from_http_request(HttpRequest(url=url))
