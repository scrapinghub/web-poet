import attr
from typing import List, Dict

@attr.s(auto_attribs=True)
class ResponseData:
    """A container for URL and HTML content of a response, downloaded
    directly using an HTTP client.

    ``url`` should be an URL of the response (after all redirects),
    not an URL of the request, if possible.

    ``html`` should be content of the HTTP body, converted to unicode
    using the detected encoding of the response, preferably according
    to the web browser rules (respecting Content-Type header, etc.)
    """
    url: str
    html: str


@attr.s(auto_attribs=True)
class SplashResponseData:
    """A container for a response, rendered using Splash browser.

    ``url`` should be an URL of the response (after all redirects),
    not an URL of the request, if possible.

    ``html`` should be content of the HTTP body, converted to unicode
    using the detected encoding of the response, preferably according
    to the web browser rules (respecting Content-Type header, etc.)
    """
    url: str
    sourceUrl: str
    html: str
    jpeg: bytes
    httpStatus: int


@attr.s(auto_attribs=True)
class AutoextractProductResponse:
    name: str
    description: str
    mainImage: str
    images: List[str]
    url: str
    additionalProperty: List[Dict[str, str]]
    sku: str
    brand: str
    breadcrumbs: List[Dict[str, str]]
    probability: float
    mpn: str
    gtin: List[Dict[str, str]]
    aggregateRating: Dict[str, str]
