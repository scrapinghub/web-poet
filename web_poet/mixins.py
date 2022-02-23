import json
from urllib.parse import urljoin
from typing import Optional

import parsel
import jmespath
from w3lib.html import get_base_url

from web_poet.page_inputs import ResponseData


class UrlShortcutsMixin:

    response: ResponseData
    _cached_base_url: Optional[str] = None

    @property
    def url(self):
        """Shortcut to HTML Response's URL."""
        return self.response.url

    @property
    def base_url(self) -> str:
        """Return the base url of the given response"""
        if self._cached_base_url is None:
            text = self.response.html[:4096]
            self._cached_base_url = get_base_url(text, self.url)
        return self._cached_base_url

    def urljoin(self, url: str) -> str:
        """Convert url to absolute, taking in account
        url and baseurl of the response"""
        return urljoin(self.base_url, url)


class ResponseShortcutsMixin(UrlShortcutsMixin):
    """Common shortcut methods for working with HTML responses.

    It requires ``response`` attribute to be present.
    """

    response: ResponseData
    _cached_selector: Optional[parsel.Selector] = None

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


class JsonResponseShortcutsMixin(UrlShortcutsMixin):
    """Common shortcut methods for working with JSON responses which usually
    comes from APIs.

    It requires ``response`` attribute to be present.
    """

    response: ResponseData
    _cached_json: Optional[dict] = None

    @property
    def json(self) -> dict:
        """Shortcut to the JSON Response represented in a Python ``dict``."""
        if self._cached_json is None:
            self._cached_json = json.loads(self.response.html)

        return self._cached_json

    def jmespath(self, expression: str) -> dict:
        """Run a jmespath query on the JSON Response."""
        return jmespath.search(expression, self.json)
