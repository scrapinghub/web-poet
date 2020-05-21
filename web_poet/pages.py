import abc
import attr
import typing

from web_poet.mixins import ResponseShortcutsMixin
from web_poet.page_inputs import ResponseData


class Injectable(abc.ABC):
    """Base Page Object class, which all Page Objects should inherit from
    (probably through Injectable subclasses).

    Frameworks which are using ``web-poet`` Page Objects should use
    :func:`is_injectable` function to detect if an object is an Injectable,
    and if an object is injectable, allow building it automatically
    through dependency injection, using https://github.com/scrapinghub/andi
    library.

    Instead of inheriting you can also use ``Injectable.register(MyWebPage)``.
    ``Injectable.register`` can also be used as a decorator.
    """
    pass


# NoneType is considered as injectable. Required for Optionals to work.
Injectable.register(type(None))


def is_injectable(cls: typing.Any) -> bool:
    """Return True if ``cls`` is a class which inherits
    from :class:`~.Injectable`."""
    return isinstance(cls, type) and issubclass(cls, Injectable)


class ItemPage(Injectable, abc.ABC):
    """Base Page Object with a required :meth:`to_item` method.
    Make sure you're creating Page Objects with ``to_item`` methods
    if their main goal is to extract a single data record from a web page.
    """

    @abc.abstractmethod
    def to_item(self):
        """Extract an item from a web page"""


@attr.s(auto_attribs=True)
class WebPage(Injectable, ResponseShortcutsMixin):
    """Base Page Object which requires :class:`~.ResponseData`
    and provides XPath / CSS shortcuts.

    Use this class as a base class for Page Objects which work on
    HTML downloaded using an HTTP client directly.
    """
    response: ResponseData


@attr.s(auto_attribs=True)
class ItemWebPage(WebPage, ItemPage):
    """:class:`WebPage` that requires the :meth:`to_item` method to
    be implemented.
    """
    pass
