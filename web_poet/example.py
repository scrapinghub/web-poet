"""This is a simplified, incomplete example of a web-poet framework, written as
support material for the web-poet tutorial.

No part of this module is intended for production use, and it may change in a
backward-incompatible way at any point in the future.
"""

from asyncio import run
from typing import Any, Dict, Optional, Type
from warnings import warn

import andi
from requests import get
from url_matcher import URLMatcher

from . import default_registry
from .page_inputs import HttpClient, HttpResponse, PageParams
from .pages import ItemPage, is_injectable
from .utils import ensure_awaitable

warn(
    (
        "You should only be importing web_poet.example to follow the web-poet "
        "tutorial, never as part of production code."
    ),
    UserWarning,
    stacklevel=2,
)


class _HttpClient:
    async def get(self, url: str) -> HttpResponse:
        return _get_http_response(url)


def _get_page_class(url: str, item_class: Type) -> Type[ItemPage]:
    url_matcher = URLMatcher(
        {
            rule.use: rule.for_patterns
            for rule in default_registry.get_rules()
            if rule.to_return == item_class
        }
    )
    return url_matcher.match(url)


def _get_http_response(url: str) -> HttpResponse:
    response = requests.get(url)
    return HttpResponse(
        response.url,
        body=response.content,
        headers=response.headers,
    )


def _get_page(
    url: str,
    page_class: Type[ItemPage],
    *,
    page_params: Optional[Dict[Any, Any]] = None,
) -> ItemPage:
    plan = andi.plan(
        page_class,
        is_injectable=is_injectable,
        externally_provided={
            HttpClient,
            HttpResponse,
            PageParams,
        },
    )
    instances: Dict[Any, Any] = {}
    for fn_or_cls, kwargs_spec in plan:
        if fn_or_cls is HttpResponse:
            instances[fn_or_cls] = _get_http_response(url)
        elif fn_or_cls is HttpClient:
            instances[fn_or_cls] = _HttpClient()
        elif fn_or_cls is PageParams:
            instances[fn_or_cls] = PageParams(page_params or {})
        else:
            instances[fn_or_cls] = fn_or_cls(**kwargs_spec.kwargs(instances))
    return instances[page_class]


def get_item(
    url: str,
    item_class: Type,
    *,
    page_params: Optional[Dict[Any, Any]] = None,
) -> Any:
    """Returns an item built from the specified URL using a page object class
    from the default registry.

    *page_modules* is a list of the import paths of modules that define page
    object classes, to be imported recursively and hence allow their
    ``@handle_urls`` to take effect.

    This function is an example of a minimal, incomplete web-poet framework
    implementation, intended for use in the web-poet tutorial.
    """
    page_class = _get_page_class(url, item_class)
    if page_class is None:
        raise ValueError(f"No page object class found for URL: {url}")
    page = _get_page(url, page_class, page_params=page_params)
    return run(ensure_awaitable(page.to_item()))
