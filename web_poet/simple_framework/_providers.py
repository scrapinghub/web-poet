from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_type_hints

import niquests

from web_poet.page_inputs import HttpClient, HttpResponse, PageParams

if TYPE_CHECKING:
    from collections.abc import Callable

PROVIDERS: dict[type, Callable[..., Any]] = {}


def _provider_func(func: Callable[..., Any]):
    dep = get_type_hints(func).get("return")
    PROVIDERS[dep] = func
    return func


def _provider_cls(dep: type):
    def _provider(cls: Any) -> Any:
        PROVIDERS[dep] = cls
        return cls()

    return _provider


@_provider_func
async def _get_http_response(url: str, **_kwargs) -> HttpResponse:
    response = await niquests.aget(url, timeout=300)
    return HttpResponse(
        response.url or url,
        status=response.status_code,
        body=response.content or b"",
        headers=response.headers,
    )


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
        return await _get_http_response(url)
