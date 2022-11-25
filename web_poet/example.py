from asyncio import run
from typing import Any, Dict, List, Optional, Type

from requests import get
from url_matcher import URLMatcher

from . import default_registry
from .page_inputs import HttpResponse, PageParams
from .pages import ItemPage
from .rules import consume_modules


class _HttpClient:
    async def get(self, url: str) -> HttpResponse:
        return _get_http_response(url)


def _get_page_class(url: str) -> Type[ItemPage]:
    url_matcher = URLMatcher(
        {rule.use: rule.for_patterns for rule in default_registry.get_rules()}
    )
    return url_matcher.match(url)


def _get_http_response(url: str) -> HttpResponse:
    response = get(url)
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
    # We make quite a few assumptions here that prevent this function from
    # working in scenarios where those assumptions are wrong. These shortcuts
    # have been taken to save development time, providing the minimum
    # implementation that works well enough for the tutorial.
    http_response = _get_http_response(url)
    kwargs: Dict[str, Any] = {}
    if "http" in page_class.__annotations__:
        kwargs["http"] = _HttpClient()
    if "page_params" in page_class.__annotations__:
        if page_params is None:
            page_params = {}
        kwargs["page_params"] = PageParams(page_params)
    return page_class(response=http_response, **kwargs)  # type: ignore


def get_item(
    url: str,
    *,
    page_modules: List[str],
    page_params: Optional[Dict[Any, Any]] = None,
) -> Any:
    """Returns an item build from the specified URL using a page object class
    from the default registry.

    *page_modules* is a list of the import paths of modules that define page
    object classes, to be imported recursively and hence allow their
    ``@handle_urls`` to take effect.

    This function is an example of a minimal, incomplete web-poet framework
    implementation, intended for use in the web-poet tutorial.
    """
    consume_modules(*page_modules)
    page_class = _get_page_class(url)
    if page_class is None:
        raise ValueError(f"No page object class found for URL: {url}")
    page = _get_page(url, page_class, page_params=page_params)
    return run(page.to_item())
