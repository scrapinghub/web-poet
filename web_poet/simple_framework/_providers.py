from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_type_hints

import niquests
from playwright.async_api import async_playwright

from web_poet.page_inputs import (
    AnyResponse,
    BrowserHtml,
    BrowserResponse,
    HttpClient,
    HttpRequest,
    HttpRequestBody,
    HttpRequestHeaders,
    HttpResponse,
    HttpResponseBody,
    HttpResponseHeaders,
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


async def _get_browser_response_from_http_request(
    request: HttpRequest,
) -> BrowserResponse:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            page = await browser.new_page()
            goto_response = await page.goto(str(request.url))
            html = await page.content()
            return BrowserResponse(
                url=page.url or str(request.url),
                html=html,
                status=None if goto_response is None else goto_response.status,
            )
        finally:
            await browser.close()


class ResponseFetcher:
    def __init__(self, required_deps: set[type] | None = None) -> None:
        self.http_response: HttpResponse | None = None
        self.browser_response: BrowserResponse | None = None
        required_deps = required_deps or set()
        self._needs_http_response = bool(
            required_deps & {HttpResponse, HttpResponseBody, HttpResponseHeaders}
        )
        self._needs_browser_response = bool(
            required_deps & {BrowserResponse, BrowserHtml}
        )

    async def get_http_response(self, request: HttpRequest) -> HttpResponse:
        if self.http_response is None:
            self.http_response = await _get_http_response_from_http_request(request)
        return self.http_response

    async def get_browser_response(self, request: HttpRequest) -> BrowserResponse:
        if self.browser_response is None:
            self.browser_response = await _get_browser_response_from_http_request(
                request
            )
        return self.browser_response

    async def get_any_response(self, request: HttpRequest) -> AnyResponse:
        if self._needs_browser_response:
            browser_response = await self.get_browser_response(request)
            return AnyResponse(response=browser_response)
        http_response = await self.get_http_response(request)
        return AnyResponse(response=http_response)


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
    return await response_fetcher.get_http_response(request)


@_provider_func
async def _get_browser_response(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> BrowserResponse:
    return await response_fetcher.get_browser_response(request)


@_provider_func
async def _get_browser_html(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> BrowserHtml:
    response = await response_fetcher.get_browser_response(request)
    return response.html


@_provider_func
def _get_request_body(request: HttpRequest, **_kwargs) -> HttpRequestBody:
    return HttpRequestBody(request.body)


@_provider_func
def _get_request_headers(request: HttpRequest, **_kwargs) -> HttpRequestHeaders:
    return request.headers


@_provider_func
async def _get_response_body(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> HttpResponseBody:
    response = await response_fetcher.get_http_response(request)
    return response.body


@_provider_func
async def _get_response_headers(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> HttpResponseHeaders:
    response = await response_fetcher.get_http_response(request)
    return response.headers


@_provider_func
async def _get_response_url(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> ResponseUrl:
    response = await response_fetcher.get_any_response(request)
    return response.url


@_provider_func
def _get_request_url(request: HttpRequest, **_kwargs) -> RequestUrl:
    return request.url


@_provider_func
def _get_page_params(
    page_params: dict[Any, Any] | None = None, **_kwargs
) -> PageParams:
    return PageParams(page_params or {})


@_provider_func
def _get_request(request: HttpRequest, **_kwargs) -> HttpRequest:
    return request


@_provider_cls(HttpClient)
class _HttpClient:
    def __init__(self, **_kwargs):
        pass

    async def get(self, url: str) -> HttpResponse:
        return await _get_http_response_from_http_request(HttpRequest(url=url))
