import abc
import attr


class PageObjectResponse(abc.ABC):
    """Represents a basic response.

    Responses are used by PageObjects to serialize data.
    """
    pass


@attr.s(auto_attribs=True)
class ResponseData(PageObjectResponse):
    """Represents an HTML response.

    Every HTML response should contain a URL and a textual content.
    """
    url: str
    content: str
