from web_poet import handle_urls

from .base import BasePage


@handle_urls("site_3.com", overrides=BasePage)
class B_Site3:
    ...
