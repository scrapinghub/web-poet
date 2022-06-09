from .pages import WebPage, ItemPage, ItemWebPage, Injectable
from .requests import request_backend_var
from .page_inputs import (
    BrowserHtml,
    HttpClient,
    HttpRequest,
    HttpResponse,
    HttpRequestHeaders,
    HttpResponseHeaders,
    HttpRequestBody,
    HttpResponseBody,
    PageParams,
    RequestUrl,
    ResponseUrl,
)
from .overrides import PageObjectRegistry, consume_modules, OverrideRule
from .functional import page_object

default_registry = PageObjectRegistry()
handle_urls = default_registry.handle_urls
