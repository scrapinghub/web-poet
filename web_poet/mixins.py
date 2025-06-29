from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Protocol
from urllib.parse import urljoin

import parsel
from w3lib.html import get_base_url

from web_poet.page_inputs.url import RequestUrl, ResponseUrl

if TYPE_CHECKING:
    from web_poet.page_inputs.http import HttpResponse


class SelectorShortcutsMixin:
    def xpath(self, query, **kwargs) -> parsel.SelectorList:
        """A shortcut to ``.selector.xpath()``."""
        return self.selector.xpath(query, **kwargs)  # type: ignore[attr-defined]

    def css(self, query) -> parsel.SelectorList:
        """A shortcut to ``.selector.css()``."""
        return self.selector.css(query)  # type: ignore[attr-defined]

    def jmespath(self, query: str, **kwargs) -> parsel.SelectorList:
        """A shortcut to ``.selector.jmespath()``."""
        if not hasattr(self.selector, "jmespath"):  # type: ignore[attr-defined]
            raise AttributeError(
                "Please install parsel >= 1.8.1 to get jmespath support"
            )
        return self.selector.jmespath(query, **kwargs)  # type: ignore[attr-defined]


class SelectableMixin(abc.ABC, SelectorShortcutsMixin):
    """
    Inherit from this mixin, implement ``._selector_input`` method,
    get ``.selector`` property and ``.xpath`` / ``.css`` / ``.jmespath``
    methods.
    """

    __cached_selector = None

    @abc.abstractmethod
    def _selector_input(self) -> str:
        raise NotImplementedError  # pragma: nocover

    @property
    def selector(self) -> parsel.Selector:
        """Cached instance of :external:class:`parsel.selector.Selector`."""
        # caching is implemented in a manual way to avoid issues with
        # non-hashable classes, where memoizemethod_noargs doesn't work
        if self.__cached_selector is not None:
            return self.__cached_selector
        base_url = str(self.url) if hasattr(self, "url") else None
        sel = parsel.Selector(text=self._selector_input(), base_url=base_url)
        self.__cached_selector = sel
        return sel


class UrlShortcutsMixin:
    _cached_base_url = None

    def _url_shortcuts_input(self) -> str:
        return self._selector_input()  # type: ignore[attr-defined]

    @property
    def _base_url(self) -> str:
        if self._cached_base_url is None:
            text = self._url_shortcuts_input()[:4096]
            self._cached_base_url = get_base_url(text, str(self.url))  # type: ignore[attr-defined]
        return self._cached_base_url

    def urljoin(self, url: str | RequestUrl | ResponseUrl) -> RequestUrl:
        """Return *url* as an absolute URL.

        If *url* is relative, it is made absolute relative to the base URL of
        *self*."""
        return RequestUrl(urljoin(self._base_url, str(url)))


class ResponseProtocol(Protocol):
    response: HttpResponse


class ResponseShortcutsMixin(ResponseProtocol, SelectableMixin, UrlShortcutsMixin):
    """Common shortcut methods for working with HTML responses.
    This mixin could be used with Page Object base classes.

    It requires "response" attribute to be present.
    """

    _cached_base_url = None

    @property
    def url(self) -> str:
        """Shortcut to HTML Response's URL, as a string."""
        return str(self.response.url)

    @property
    def html(self) -> str:
        """Shortcut to HTML Response's content."""
        return self.response.text

    def _selector_input(self) -> str:
        return self.html

    @property
    def base_url(self) -> str:
        """Return the base url of the given response"""
        return self._base_url

    def urljoin(self, url: str) -> str:  # type: ignore[override]
        """Convert url to absolute, taking in account
        url and baseurl of the response"""
        return str(super().urljoin(url))
