import parsel


class ResponseShortcutsMixin:
    """Common shortcut methods for working with HTML responses.

    It requires "response" attribute to be present.
    """
    _cached_selector = None

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
