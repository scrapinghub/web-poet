from __future__ import annotations

import attrs

from web_poet.mixins import SelectableMixin, UrlShortcutsMixin

from .url import ResponseUrl


class BrowserHtml(SelectableMixin, str):  # noqa: SLOT000
    """HTML returned by a web browser,
    i.e. snapshot of the DOM tree in HTML format.
    """

    def _selector_input(self) -> str:
        return self


@attrs.define(auto_attribs=False, slots=False, eq=False)
class BrowserResponse(SelectableMixin, UrlShortcutsMixin):
    """Browser response: url, HTML and status code.

    ``url`` should be browser's window.location, not a URL of the request,
    if possible.

    ``html`` contains the HTML returned by the browser,
    i.e. a snapshot of DOM tree in HTML format.

    The following are optional since it would depend on the source of the
    ``BrowserResponse`` if these are available or not:

    ``status`` should represent the int status code of the HTTP response.
    """

    url: ResponseUrl = attrs.field(converter=ResponseUrl)
    html: BrowserHtml = attrs.field(converter=BrowserHtml)
    status: int | None = attrs.field(default=None, kw_only=True)

    def _selector_input(self) -> str:
        return self.html
