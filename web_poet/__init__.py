from .pages import WebPage, ItemPage, ItemWebPage, Injectable
from .requests import request_backend_var
from .page_inputs import (
    Meta,
    HttpClient,
    HttpRequest,
    HttpResponse,
    HttpRequestHeaders,
    HttpResponseHeaders,
    HttpRequestBody,
    HttpResponseBody,
)
from .overrides import PageObjectRegistry, consume_modules, OverrideRule


default_registry = PageObjectRegistry()
handle_urls = default_registry.handle_urls
