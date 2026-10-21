from ._layouts import layout_switch
from ._selectors import SelectorGroup, css_get, css_getall, xpath_get, xpath_getall
from .annotated import AnnotatedInstance, annotation_decode, annotation_encode
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
    BrowserPage,
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
    "AnnotatedInstance",
    "AnyResponse",
    "ApplyRule",
    "BrowserHtml",
    "BrowserPage",
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
    "SelectorGroup",
    "Stats",
    "WebPage",
    "annotation_decode",
    "annotation_encode",
    "cached_method",
    "consume_modules",
    "css_get",
    "css_getall",
    "default_registry",
    "field",
    "handle_urls",
    "item_from_fields",
    "item_from_fields_sync",
    "layout_switch",
    "request_downloader_var",
    "validates_input",
    "xpath_get",
    "xpath_getall",
]

default_registry = RulesRegistry()
handle_urls = default_registry.handle_urls
