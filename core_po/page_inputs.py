import attr


@attr.s(auto_attribs=True)
class ResponseData:
    """Represents a response containing its URL and HTML content."""
    url: str
    html: str
