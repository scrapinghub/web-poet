from web_poet import handle_urls

from .base import BasePage


@handle_urls("site_2.com", overrides=BasePage)
class A_Site2:
    ...
