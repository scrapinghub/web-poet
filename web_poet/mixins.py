import parsel


class ResponseShortcutsMixin:
    """Common shortcut methods for working with HTML responses.

    It requires "response" attribute to be present.
    """
    _cached_selector = None

    @property
    def selector(self) -> parsel.Selector:
        """``parsel.Selector`` instance for the HTML Response."""
        if self._cached_selector is None:
            self._cached_selector = parsel.Selector(self.html)

        return self._cached_selector

    @property
    def url(self):
        """Shortcut to HTML Response's URL."""
        return self.response.url

    @property
    def html(self):
        """Shortcut to HTML Response's content."""
        return self.response.html

    def xpath(self, query, **kwargs):
        """Shortcut to XPath selector."""
        return self.selector.xpath(query, **kwargs)

    def css(self, query):
        """Shortcut to CSS selector."""
        return self.selector.css(query)
