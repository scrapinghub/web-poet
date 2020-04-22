import attr


@attr.s(auto_attribs=True)
class HTMLResponse:
    """Represents a basic Response.

    Every response should contain an URL and have a text content.
    """
    url: str
    content: str
