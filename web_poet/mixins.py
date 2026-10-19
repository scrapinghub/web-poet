from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar
from urllib.parse import urljoin

import parsel
from w3lib.html import get_base_url

from web_poet._frostwork import _check_class as _frostwork_check_class
from web_poet._frostwork import _extract as _frostwork_extract
from web_poet.utils import cached_method

if TYPE_CHECKING:
    from web_poet._selectors import _SelectorDeclaration
    from web_poet.page_inputs.url import RequestUrl, ResponseUrl


class _ResponseLike(Protocol):
    """Protocol for response objects."""

    url: ResponseUrl | str
    text: str


ResponseT = TypeVar("ResponseT", bound=_ResponseLike)


class SelectorShortcutsMixin:
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        _frostwork_check_class(cls)

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

    def _selector_kwargs(self) -> dict[str, Any]:
        return {"text": self._selector_input()}

    @property
    def selector(self) -> parsel.Selector:
        """Cached instance of :external:class:`parsel.selector.Selector`."""
        # caching is implemented in a manual way to avoid issues with
        # non-hashable classes, where memoizemethod_noargs doesn't work
        if self.__cached_selector is not None:
            return self.__cached_selector
        base_url = str(self.url) if hasattr(self, "url") else None
        sel = parsel.Selector(**self._selector_kwargs(), base_url=base_url)
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
        from web_poet.page_inputs.url import RequestUrl  # noqa: PLC0415

        return RequestUrl(urljoin(self._base_url, str(url)))


class ResponseShortcutsMixin(Generic[ResponseT], SelectableMixin, UrlShortcutsMixin):  # noqa: PYI059
    """Common shortcut methods for working with HTML responses.
    This mixin could be used with Page Object base classes.

    It requires "response" attribute to be present.
    """

    response: ResponseT

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

    def _selector_document(self) -> tuple[bytes | str, str | None]:
        """Return the raw document of this object and its encoding, for
        frostwork to scan directly instead of using ``self.selector``."""
        response: Any = self.response
        body = getattr(response, "body", None)
        if body is None:
            # A browser response is HTML that has already been decoded.
            return self.html, None
        return body, getattr(response, "encoding", None)

    @cached_method
    def _frostwork_values(self) -> dict[_SelectorDeclaration, Any] | None:
        return _frostwork_extract(type(self), self._selector_document())

    def _selector_value(self, declaration: _SelectorDeclaration) -> Any:
        """Return the value of *declaration* for this object.

        frostwork extracts every declaration of the object in a single pass,
        on the first call. Documents that frostwork cannot extract, and
        declarations assigned after class creation, are left to parsel."""
        values = self._frostwork_values()
        if values is not None and declaration in values:
            return values[declaration]
        query = getattr(self.selector, declaration.syntax)
        return getattr(query(declaration.expression), declaration.mode)()

    def _selector_kwargs(self) -> dict[str, Any]:
        if isinstance(self.response, SelectableMixin):
            return self.response._selector_kwargs()
        return super()._selector_kwargs()

    @property
    def base_url(self) -> str:
        """Return the base url of the given response"""
        return self._base_url

    def urljoin(self, url: str) -> str:  # type: ignore[override]
        """Convert url to absolute, taking in account
        url and baseurl of the response"""
        return str(super().urljoin(url))
