from .overrides import OverrideRule, PageObjectRegistry, consume_modules
from .page_inputs import (
    BrowserHtml,
    HttpClient,
    HttpRequest,
    HttpRequestBody,
    HttpRequestHeaders,
    HttpResponse,
    HttpResponseBody,
    HttpResponseHeaders,
    Meta,
)
from .pages import Injectable, ItemPage, ItemWebPage, WebPage
from .requests import request_backend_var

default_registry = PageObjectRegistry()
handle_urls = default_registry.handle_urls
