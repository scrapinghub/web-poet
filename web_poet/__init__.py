from .fields import field, item_from_fields, item_from_fields_sync
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
    PageParams,
    RequestUrl,
    ResponseUrl,
)
from .pages import Injectable, ItemPage, ItemWebPage, WebPage
from .requests import request_downloader_var
from .utils import cached_method

default_registry = PageObjectRegistry()
handle_urls = default_registry.handle_urls
