from typing import Callable, Type

from web_poet.pages import ItemPage


def page_object(func: Callable) -> Type[ItemPage]:
    """
    Decorator to create a Page Object from a function.
    Note that the original function is destroyed, and
    a class is created instead.

    .. code-block:: python

        @web_poet.page_object
        def MyPage(resp: HttpResponse):
            return {"title": resp.css("title::text").get()}

    is a shortcut for

    .. code-block:: python

        class MyPage(web_poet.ItemPage):
            def __init__(self, resp: HttpResponse):
                self.resp = resp

            def to_item(self):
                return {"title": self.resp.css("title::text").get()}

    """
    class PageObject(ItemPage):
        def __init__(self, *args, **kwargs):
            # FIXME: save arguments as properly named attributes
            # FIXME: __init__ method doesn't fail if parameters are wrong
            self.args = args
            self.kwargs = kwargs
            super().__init__()

        # TODO: async def support
        def to_item(self):
            return func(*self.args, **self.kwargs)

    # FIXME: robustness, edge cases
    PageObject.__module__ = func.__module__
    PageObject.__name__ = func.__name__
    PageObject.__qualname__ = func.__qualname__
    PageObject.__doc__ = func.__doc__
    PageObject.__init__.__annotations__ = func.__annotations__

    # TODO: check that type annotations work properly
    # TODO: preserve the original function as an attribute?
    return PageObject

