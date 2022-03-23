from .pages import WebPage, ItemPage, ItemWebPage, Injectable
from .page_inputs import ResponseData
from .overrides import PageObjectRegistry, consume_modules, OverrideRule

default_registry = PageObjectRegistry()
handle_urls = default_registry.handle_urls
