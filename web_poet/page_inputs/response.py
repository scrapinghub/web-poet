from __future__ import annotations

import attrs

from web_poet.mixins import SelectableMixin, UrlShortcutsMixin
from web_poet.page_inputs.browser import BrowserResponse
from web_poet.page_inputs.http import HttpResponse
from web_poet.page_inputs.url import ResponseUrl


@attrs.define
class AnyResponse(SelectableMixin, UrlShortcutsMixin):
    """A container that holds either :class:`~.BrowserResponse` or :class:`~.HttpResponse`."""

    response: BrowserResponse | HttpResponse

    @property
    def url(self) -> ResponseUrl:
        """URL of the response."""
        return self.response.url

    @property
    def text(self) -> str:
        """Text or HTML contents of the response."""
        if isinstance(self.response, BrowserResponse):
            return self.response.html
        return self.response.text

    @property
    def status(self) -> int | None:
        """The int status code of the HTTP response, if available."""
        return self.response.status

    def _selector_input(self) -> str:
        return self.text
