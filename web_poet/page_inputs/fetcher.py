from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

T = TypeVar("T")


class Fetcher:
    """Injectable for fetching additional page objects for different URLs at
    run time with full dependency injection support.

    Example::

        @define
        class RelatedPage(ItemPage):
            response: BrowserResponse

            def title(self) -> str:
                return self.css("h1::text").get()

        @define
        class ProductPage(ItemPage):
            response: HttpResponse
            fetcher: Fetcher

            async def to_item(self):
                related_url = self.css("a.related::attr(href)").get()
                related: RelatedPage = await self.fetcher.get_page(
                    related_url, RelatedPage
                )
                return {"title": ..., "related_title": related.title()}
    """

    def __init__(
        self,
        _get_page: Callable[..., Awaitable[Any]],
        _get_item: Callable[..., Awaitable[Any]],
    ) -> None:
        self._get_page = _get_page
        self._get_item = _get_item

    async def get_page(
        self,
        request: Any,
        page_cls: type[T],
        *,
        page_params: dict[Any, Any] | None = None,
    ) -> T:
        """Return a page object instance built from *request* and *page_cls*.

        *page_cls* is resolved with full dependency injection, supporting all
        page object dependencies the framework provides.

        *page_params* is a dict accessible inside the page object through the
        :class:`~web_poet.page_inputs.PageParams` dependency.
        """
        return await self._get_page(request, page_cls, page_params=page_params)

    async def get_item(
        self,
        request: Any,
        item_or_page_cls: type,
        *,
        page_params: dict[Any, Any] | None = None,
    ) -> Any:
        """Return an item built from *request*.

        *item_or_page_cls* is either an item class or a page object class.
        If it is an item class, the page class to use is determined by the
        framework's registry.

        *page_params* is a dict accessible inside the page object through the
        :class:`~web_poet.page_inputs.PageParams` dependency.
        """
        return await self._get_item(request, item_or_page_cls, page_params=page_params)
