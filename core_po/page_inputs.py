import attr


@attr.s(auto_attribs=True)
class ResponseData:
    """Represents response containing its URL and HTML content."""
    url: str
    html: str
