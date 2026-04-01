from __future__ import annotations

from asyncio import run
from typing import Any

import andi
import requests

from web_poet.page_inputs import HttpClient, HttpResponse, PageParams
from web_poet.pages import ItemPage, is_injectable
from web_poet.rules import RulesRegistry
from web_poet.utils import ensure_awaitable


class _HttpClient:
    async def get(self, url: str) -> HttpResponse:
        return _get_http_response(url)


def _get_http_response(url: str) -> HttpResponse:
    response = requests.get(url, timeout=300)
    return HttpResponse(
        response.url,
        status=response.status_code,
        body=response.content,
        headers=response.headers,
    )


def _get_page(
    url: str,
    page_cls: type[ItemPage],
    *,
    page_params: dict[Any, Any] | None = None,
) -> ItemPage:
    plan = andi.plan(
        page_cls,
        is_injectable=is_injectable,
        externally_provided={
            HttpClient,
            HttpResponse,
            PageParams,
        },
    )
    instances: dict[Any, Any] = {}
    for fn_or_cls, kwargs_spec in plan:
        if fn_or_cls is HttpResponse:
            instances[fn_or_cls] = _get_http_response(url)
        elif fn_or_cls is HttpClient:
            instances[fn_or_cls] = _HttpClient()
        elif fn_or_cls is PageParams:
            instances[fn_or_cls] = PageParams(page_params or {})
        else:
            instances[fn_or_cls] = fn_or_cls(**kwargs_spec.kwargs(instances))
    return instances[page_cls]


def get_item(
    url: str,
    item_cls: type,
    *,
    page_params: dict[Any, Any] | None = None,
    registry: RulesRegistry | None = None,
) -> Any:
    """Returns an item built from the specified URL using a page object class
    from the default registry.

    This function is an example of a minimal, incomplete web-poet framework
    implementation, intended for use in the web-poet tutorial.
    """
    if registry is None:  # pragma: no cover
        from web_poet import default_registry  # noqa: PLC0415

        registry = default_registry

    page_cls = registry.page_cls_for_item(url, item_cls)
    if page_cls is None:
        raise ValueError(f"No page object class found for URL: {url}")
    page = _get_page(url, page_cls, page_params=page_params)
    return run(ensure_awaitable(page.to_item()))
