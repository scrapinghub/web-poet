from typing import Union

import attrs

from web_poet.page_inputs.browser import BrowserResponse
from web_poet.page_inputs.http import HttpResponse
from web_poet.page_inputs.url import ResponseUrl


@attrs.define
class AnyResponse:
    """A container that holds either :class:`~.BrowserResponse` or :class:`~.HttpResponse.`"""

    response: Union[BrowserResponse, HttpResponse]

    @property
    def url(self) -> ResponseUrl:
        """URL of the response."""
        return self.response.url

    @property
    def text(self) -> str:
        """Contents of the response."""
        if isinstance(self.response, BrowserResponse):
            return self.response.html
        return self.response.text
