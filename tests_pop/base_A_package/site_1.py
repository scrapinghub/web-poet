from web_poet import handle_urls

from .base import BasePage


@handle_urls("site_1.com", overrides=BasePage)
class A_Site1:
    ...
