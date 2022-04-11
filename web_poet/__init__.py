from .pages import WebPage, ItemPage, ItemWebPage, Injectable
from .requests import (
    request_backend_var,
    HttpClient,
)
from .page_inputs import (
    Meta,
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
