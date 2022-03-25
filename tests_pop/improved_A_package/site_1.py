from web_poet import handle_urls

from .base_A_package.base import BasePage
from .base_A_package.site_1 import A_Site1


@handle_urls("site_1.com", overrides=BasePage)
class A_Improved_Site1(A_Site1):
    ...  # some improvements here after subclassing the original one.
