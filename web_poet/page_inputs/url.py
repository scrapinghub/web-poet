from typing import Union


class _Url:
    """Base URL class."""

    def __init__(self, url: Union[str, "_Url"]):
        if not isinstance(url, (str, _Url)):
            raise TypeError(
                f"`url` must be a str or an instance of _Url, "
                f"got {url.__class__} instance instead"
            )
        self._url = str(url)

    def __str__(self) -> str:
        return self._url

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._url!r})"


class ResponseUrl(_Url):
    """URL of the response"""

    pass


class RequestUrl(_Url):
    """URL of the request"""

    pass
