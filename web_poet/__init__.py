from .fields import field, item_from_fields, item_from_fields_sync
from .page_inputs import (
    AnyResponse,
    BrowserHtml,
    BrowserResponse,
    HttpClient,
    HttpRequest,
    HttpRequestBody,
    HttpRequestHeaders,
    HttpResponse,
    HttpResponseBody,
    HttpResponseHeaders,
    PageParams,
    RequestUrl,
    ResponseUrl,
    Stats,
)
from .pages import (
    Extractor,
    Injectable,
    ItemPage,
    Returns,
    SelectorExtractor,
    WebPage,
    validates_input,
)
from .requests import request_downloader_var
from .rules import (
    ApplyRule,
    RulesRegistry,
    consume_modules,
)
from .utils import cached_method

__all__ = [
    "AnyResponse",
    "ApplyRule",
    "BrowserHtml",
    "BrowserResponse",
    "Extractor",
    "HttpClient",
    "HttpRequest",
    "HttpRequestBody",
    "HttpRequestHeaders",
    "HttpResponse",
    "HttpResponseBody",
    "HttpResponseHeaders",
    "Injectable",
    "ItemPage",
    "PageParams",
    "RequestUrl",
    "ResponseUrl",
    "Returns",
    "RulesRegistry",
    "SelectorExtractor",
    "Stats",
    "WebPage",
    "cached_method",
    "consume_modules",
    "default_registry",
    "field",
    "handle_urls",
    "item_from_fields",
    "item_from_fields_sync",
    "request_downloader_var",
    "validates_input",
]

default_registry = RulesRegistry()
handle_urls = default_registry.handle_urls
