from typing import Dict

from .pages import WebPage, ItemPage, ItemWebPage, Injectable
from .page_inputs import ResponseData
from .overrides import (
    PageObjectRegistry,
    consume_modules,
    registry_pool,
)


# For ease of use, we'll create a default registry so that users can simply
# use its `handle_urls()` method directly by `from web_poet import handle_urls`
default_registry = PageObjectRegistry(name="default")
handle_urls = default_registry.handle_urls
