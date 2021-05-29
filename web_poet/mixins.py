from urllib.parse import urljoin

import parsel
from w3lib.html import get_base_url


class ResponseShortcutsMixin:
    """Common shortcut methods for working with HTML responses.

    It requires "response" attribute to be present.
    """
    _cached_selector = None
    _cached_base_url = None

    @property
    def url(self):
        """Shortcut to HTML Response's URL."""
        return self.response.url

    @property
    def html(self):
        """Shortcut to HTML Response's content."""
        return self.response.html

    @property
    def selector(self) -> parsel.Selector:
        """``parsel.Selector`` instance for the HTML Response."""
        if self._cached_selector is None:
            self._cached_selector = parsel.Selector(self.html)

        return self._cached_selector

    def xpath(self, query, **kwargs):
        """Run an XPath query on a response, using :class:`parsel.Selector`."""
        return self.selector.xpath(query, **kwargs)

    def css(self, query):
        """Run a CSS query on a response, using :class:`parsel.Selector`."""
        return self.selector.css(query)

    @property
    def base_url(self) -> str:
        """Return the base url of the given response"""
        if self._cached_base_url is None:
            text = self.html[:4096]
            self._cached_base_url = get_base_url(text, self.url)
        return self._cached_base_url

    def urljoin(self, url: str) -> str:
        """Convert url to absolute, taking in account
        url and baseurl of the response"""
        return urljoin(self.base_url, url)

