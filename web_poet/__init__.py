from .fields import field, item_from_fields, item_from_fields_sync
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
from .pages import Injectable, ItemPage, ItemWebPage, Returns, WebPage
from .requests import request_downloader_var
from .rules import (
    ApplyRule,
    OverrideRule,
    PageObjectRegistry,
    RulesRegistry,
    consume_modules,
)
from .utils import cached_method

default_registry = RulesRegistry()
handle_urls = default_registry.handle_urls
