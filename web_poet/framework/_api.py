from __future__ import annotations

from typing import Annotated, Any, TypeAlias, get_args, get_origin

import andi
from andi.typeutils import strip_annotated
from playwright.async_api import async_playwright

from web_poet import default_registry
from web_poet.annotated import annotation_encode
from web_poet.page_inputs import (
    BrowserHtml,
    BrowserResponse,
    HttpRequest,
)
from web_poet.page_inputs.stats import DictStatCollector, StatCollector
from web_poet.page_inputs.url import RequestUrl, ResponseUrl
from web_poet.pages import ItemPage, is_injectable
from web_poet.rules import RulesRegistry
from web_poet.utils import ensure_awaitable

from ._providers import DEFAULT_BROWSER, PROVIDERS, ResponseFetcher

ANNOTATION_PREFIX = "browser."


def browser(name: str) -> str:
    """Helper to create a hashable metadata value for Annotated browser names.

    Example usage:

    .. code-block:: python

        Annotated[BrowserResponse, browser("firefox")]
    """
    return annotation_encode(f"{ANNOTATION_PREFIX}{name}")


RequestLike: TypeAlias = HttpRequest | RequestUrl | ResponseUrl | str


def _normalize_request(request: RequestLike) -> HttpRequest:
    if not isinstance(request, HttpRequest):
        request = HttpRequest(url=request)
    return request


class Poet:
    """Manager of the :ref:`built-in framework <framework>`.

    *registry* is the :class:`~web_poet.rules.RulesRegistry` from where page
    objects resolve their dependencies. If ``None``,
    :data:`~web_poet.default_registry` is used.

    *default_browser* is the Playwright browser engine to use when browser
    inputs do not specify one. Examples: ``"chromium"``, ``"firefox"``,
    ``"webkit"``.

    *stats* is a :class:`~web_poet.page_inputs.stats.StatCollector` instance to
    collect stats written by the page object through the
    :class:`~web_poet.page_inputs.stats.Stats` dependency. If not specified, a
    :class:`~web_poet.page_inputs.stats.DictStatCollector` is used. You can
    access the collector throught the :attr:`stats` attribute, e.g. to read its
    data.
    """

    def __init__(
        self,
        *,
        registry: RulesRegistry | None = None,
        default_browser: str | None = None,
        stats: StatCollector | None = None,
    ) -> None:
        self._registry = registry or default_registry
        self._default_browser = default_browser
        self.stats: StatCollector = stats or DictStatCollector()

    async def get_page(
        self,
        request: RequestLike,
        page_cls: type[ItemPage],
        *,
        page_params: dict[Any, Any] | None = None,
    ) -> ItemPage:
        """Return a page object built from *request* and *page_cls*.

        *page_params* is a dict that the page object may access through the
        :class:`~web_poet.page_inputs.PageParams` dependency.
        """
        request = _normalize_request(request)
        plan = andi.plan(
            page_cls,
            is_injectable=is_injectable,
            externally_provided=set(PROVIDERS),
        )
        instances: dict[Any, Any] = {}
        required_deps: set[type] = set()
        for fn_or_cls, _ in plan:
            base = strip_annotated(fn_or_cls)
            assert isinstance(base, type)
            required_deps.add(base)
        response_fetcher = ResponseFetcher(
            required_deps=required_deps, default_browser=self._default_browser
        )

        # first pass: collect explicit browser names from Annotated browser deps
        explicit_browsers: set[str] = set()
        for fn_or_cls, _ in plan:
            base = strip_annotated(fn_or_cls)
            if (
                base in {BrowserResponse, BrowserHtml}
                and get_origin(fn_or_cls) is Annotated
            ):
                meta = get_args(fn_or_cls)[1:]
                if meta and isinstance(meta[0], str):
                    m = meta[0]
                    if m.startswith(ANNOTATION_PREFIX):
                        explicit_browsers.add(m.split(".", 1)[1])

        # choose browser for un-annotated browser deps per rules
        if not explicit_browsers:
            chosen_browser_for_unannotated = self._default_browser or DEFAULT_BROWSER
        elif self._default_browser and self._default_browser in explicit_browsers:
            chosen_browser_for_unannotated = self._default_browser
        else:
            chosen_browser_for_unannotated = min(explicit_browsers)

        # validate requested browsers are available in playwright before doing work
        needed_browsers = set(explicit_browsers)
        # include chosen browser for unannotated deps if there are any browser deps
        if required_deps & {BrowserResponse, BrowserHtml}:
            needed_browsers.add(chosen_browser_for_unannotated)
        if needed_browsers:
            async with async_playwright() as playwright:
                for b in needed_browsers:
                    if getattr(playwright, b, None) is None:
                        raise ValueError(f"Playwright does not provide engine '{b}'")

        # second pass: instantiate dependencies, forwarding browser kwarg when needed
        for fn_or_cls, kwargs_spec in plan:
            kwargs = kwargs_spec.kwargs(instances)
            base = strip_annotated(fn_or_cls)
            assert isinstance(base, type)
            browser_kw: str | None = None
            if (
                base in {BrowserResponse, BrowserHtml}
                and get_origin(fn_or_cls) is Annotated
            ):
                meta = get_args(fn_or_cls)[1:]
                if meta and isinstance(meta[0], str):
                    m = meta[0]
                    if m.startswith(ANNOTATION_PREFIX):
                        browser_kw = m.split(".", 1)[1]
            elif base in {BrowserResponse, BrowserHtml}:
                browser_kw = chosen_browser_for_unannotated

            provider = PROVIDERS.get(base)
            if provider is not None:
                call_kwargs = {
                    "request": request,
                    "page_params": page_params,
                    "page_cls": page_cls,
                    "registry": self._registry,
                    "response_fetcher": response_fetcher,
                    "stats": self.stats,
                    **kwargs,
                }
                if browser_kw is not None:
                    call_kwargs["browser"] = browser_kw
                value = await ensure_awaitable(provider(**call_kwargs))
            else:
                value = await ensure_awaitable(base(**kwargs))

            instances[fn_or_cls] = value
        return instances[page_cls]

    async def get_item(
        self,
        request: RequestLike,
        item_or_page_cls: type,
        *,
        page_params: dict[Any, Any] | None = None,
    ) -> Any:
        """Return an item built from *request*.

        *item_or_page_cls* is either an item class or a page object class. If
        it is an item class, the page class to use is determined by the
        :class:`~web_poet.rules.RulesRegistry` passed to
        :class:`~web_poet.framework.Poet`.

        *page_params* is a dict that the page object may access through the
        :class:`~web_poet.page_inputs.PageParams` dependency
        """
        request = _normalize_request(request)
        if issubclass(item_or_page_cls, ItemPage):
            page_cls = item_or_page_cls
        else:
            page_cls = self._registry.page_cls_for_item(request.url, item_or_page_cls)
            if page_cls is None:
                raise ValueError(f"No page object class found for URL: {request.url}")
        page = await self.get_page(request, page_cls, page_params=page_params)
        return await ensure_awaitable(page.to_item())
