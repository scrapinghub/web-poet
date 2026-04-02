from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_type_hints

import niquests

from web_poet.page_inputs import HttpClient, HttpResponse, PageParams

if TYPE_CHECKING:
    from collections.abc import Callable

PROVIDERS: dict[type, Callable[..., Any]] = {}


def provider_func(func: Callable[..., Any]):
    hints = get_type_hints(func)
    dep = hints.get("return")
    if dep is None:
        raise ValueError(
            f"provider_func() requires the decorated function to have a "
            f"return type hint: {func!r}"
        )
    if not isinstance(dep, type):
        raise ValueError(
            f"provider_func() return type must be a concrete type, got: {dep!r}"
        )
    PROVIDERS[dep] = func
    return func


def provider_cls(dep: type):
    def _provider(cls: Any) -> Any:
        PROVIDERS[dep] = cls
        return cls()

    return _provider


@provider_func
async def _get_http_response(url: str, **_kwargs) -> HttpResponse:
    response = await niquests.aget(url, timeout=300)
    return HttpResponse(
        response.url or url,
        status=response.status_code,
        body=response.content or b"",
        headers=response.headers,
    )


@provider_func
def get_params(page_params: dict[Any, Any] | None = None, **_kwargs) -> PageParams:
    return PageParams(page_params or {})


@provider_cls(HttpClient)
class HttpClientImplementation:
    def __init__(self, **_kwargs):
        pass

    async def get(self, url: str) -> HttpResponse:
        return await _get_http_response(url)
