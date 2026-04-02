from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_type_hints

import niquests

from web_poet.page_inputs import HttpClient, HttpResponse, PageParams, ResponseUrl

if TYPE_CHECKING:
    from collections.abc import Callable

PROVIDERS: dict[type, Callable[..., Any]] = {}


class ResponseFetcher:
    def __init__(self) -> None:
        self._responses: dict[str, Any] = {}

    async def get(self, url: str) -> Any:
        if url not in self._responses:
            self._responses[url] = await niquests.aget(url, timeout=300)
        return self._responses[url]


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
    url: str, response_fetcher: ResponseFetcher, **_kwargs
) -> HttpResponse:
    response = await response_fetcher.get(url)
    return HttpResponse(
        response.url or url,
        status=response.status_code,
        body=response.content or b"",
        headers=response.headers,
    )


@_provider_func
async def _get_response_url(
    url: str, response_fetcher: ResponseFetcher | None = None, **_kwargs
) -> ResponseUrl:
    response = await response_fetcher.get(url)
    return ResponseUrl(response.url or url)


@_provider_func
def _get_page_params(
    page_params: dict[Any, Any] | None = None, **_kwargs
) -> PageParams:
    return PageParams(page_params or {})


@_provider_cls(HttpClient)
class _HttpClient:
    def __init__(self, response_fetcher: ResponseFetcher, **_kwargs):
        self._response_fetcher = response_fetcher

    async def get(self, url: str) -> HttpResponse:
        return await _get_http_response(url, response_fetcher=self._response_fetcher)
