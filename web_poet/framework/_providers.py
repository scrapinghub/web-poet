from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, get_type_hints

import niquests
from playwright.async_api import async_playwright

from web_poet.exceptions import HttpRequestError
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
    Stats,
)
from web_poet.page_inputs.stats import StatCollector

if TYPE_CHECKING:
    from collections.abc import Callable

DEFAULT_PLAYWRIGHT_ENGINE = "chromium"
PROVIDERS: dict[type, Callable[..., Any]] = {}
logger = logging.getLogger(__name__)


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
    try:
        response = await niquests.aget(str(request.url), timeout=300)
    except Exception as exc:
        raise HttpRequestError(str(exc), request=request) from exc
    return _get_http_response_from_nirequests_response(request, response)


async def _get_browser_response_from_http_request(
    request: HttpRequest, playwright_engine: str | None = None
) -> BrowserResponse:
    if request.method.upper() != "GET":
        raise HttpRequestError(
            "Browser provider only supports plain GET requests with a URL (no "
            "headers or body)",
            request=request,
        )
    if request.headers and len(request.headers):
        header_names = ", ".join(map(str, list(request.headers.keys())))
        logger.warning(
            "Browser provider does not support requests with headers; ignoring headers: %s",
            header_names,
        )
    if request.body and len(request.body):
        raise HttpRequestError(
            "Browser provider does not support requests with a body; only "
            "plain GET with a URL is supported",
            request=request,
        )

    engine_name = playwright_engine or DEFAULT_PLAYWRIGHT_ENGINE
    try:
        async with async_playwright() as playwright:
            engine = getattr(playwright, engine_name)
            browser_obj = await engine.launch()
            try:
                page = await browser_obj.new_page()
                goto_response = await page.goto(str(request.url))
                html = await page.content()
                return BrowserResponse(
                    url=page.url or str(request.url),
                    html=html,
                    status=None if goto_response is None else goto_response.status,
                )
            finally:
                await browser_obj.close()
    except Exception as exc:
        raise HttpRequestError(str(exc), request=request) from exc


class ResponseFetcher:
    def __init__(
        self,
        required_deps: set[type] | None = None,
        default_playwright_engine: str | None = None,
    ) -> None:
        self.http_response: HttpResponse | None = None
        self._browser_responses: dict[str, BrowserResponse] = {}
        self.default_playwright_engine = default_playwright_engine
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

    async def get_browser_response(
        self, request: HttpRequest, playwright_engine: str | None = None
    ) -> BrowserResponse:
        engine_name = (
            playwright_engine
            or self.default_playwright_engine
            or DEFAULT_PLAYWRIGHT_ENGINE
        )
        if engine_name not in self._browser_responses:
            self._browser_responses[
                engine_name
            ] = await _get_browser_response_from_http_request(
                request, playwright_engine=engine_name
            )
        return self._browser_responses[engine_name]

    async def get_any_response(
        self, request: HttpRequest, playwright_engine: str | None = None
    ) -> AnyResponse:
        if self._needs_browser_response:
            browser_response = await self.get_browser_response(
                request, playwright_engine=playwright_engine
            )
            return AnyResponse(response=browser_response)
        http_response = await self.get_http_response(request)
        return AnyResponse(response=http_response)


def _provider(func: Callable[..., Any]):
    dep = get_type_hints(func).get("return")
    assert isinstance(dep, type)
    PROVIDERS[dep] = func
    return func


@_provider
async def _get_http_response(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> HttpResponse:
    return await response_fetcher.get_http_response(request)


@_provider
async def _get_browser_response(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> BrowserResponse:
    return await response_fetcher.get_browser_response(
        request, playwright_engine=_kwargs.get("playwright_engine")
    )


@_provider
async def _get_browser_html(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> BrowserHtml:
    response = await response_fetcher.get_browser_response(
        request, playwright_engine=_kwargs.get("playwright_engine")
    )
    return response.html


@_provider
def _get_request_body(request: HttpRequest, **_kwargs) -> HttpRequestBody:
    return HttpRequestBody(request.body)


@_provider
def _get_request_headers(request: HttpRequest, **_kwargs) -> HttpRequestHeaders:
    return request.headers


@_provider
async def _get_response_body(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> HttpResponseBody:
    response = await response_fetcher.get_http_response(request)
    return response.body


@_provider
async def _get_response_headers(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> HttpResponseHeaders:
    response = await response_fetcher.get_http_response(request)
    return response.headers


@_provider
async def _get_response_url(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> ResponseUrl:
    response = await response_fetcher.get_any_response(
        request, playwright_engine=_kwargs.get("playwright_engine")
    )
    return response.url


@_provider
async def _get_any_response(
    request: HttpRequest, response_fetcher: ResponseFetcher, **_kwargs
) -> AnyResponse:
    return await response_fetcher.get_any_response(
        request, playwright_engine=_kwargs.get("playwright_engine")
    )


@_provider
def _get_request_url(request: HttpRequest, **_kwargs) -> RequestUrl:
    return request.url


@_provider
def _get_page_params(
    page_params: dict[Any, Any] | None = None, **_kwargs
) -> PageParams:
    return PageParams(page_params or {})


@_provider
def _get_request(request: HttpRequest, **_kwargs) -> HttpRequest:
    return request


@_provider
def _get_stats(stats: StatCollector | None = None, **_kwargs) -> Stats:
    return Stats(stat_collector=stats)


@_provider
def _get_http_client(**_kwargs) -> HttpClient:
    return HttpClient(request_downloader=_get_http_response_from_http_request)
