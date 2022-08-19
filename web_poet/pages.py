import abc
import typing

import attr

from web_poet._typing import get_generic_parameter
from web_poet.fields import FieldsMixin, item_from_fields
from web_poet.mixins import ResponseShortcutsMixin
from web_poet.page_inputs import HttpResponse


class Injectable(abc.ABC, FieldsMixin):
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


ItemT = typing.TypeVar("ItemT")


class ItemPage(Injectable, typing.Generic[ItemT]):
    """Base Page Object, with a default :meth:`to_item` implementation
    which supports web-poet fields.
    """

    def __init_subclass__(cls, skip_nonitem_fields: bool = False, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._skip_nonitem_fields = skip_nonitem_fields

    @property
    def item_cls(self) -> typing.Type[ItemT]:
        """Item class"""
        param = get_generic_parameter(self.__class__)
        if isinstance(param, typing.TypeVar):  # class is not parametrized
            return dict  # type: ignore[return-value]
        return param

    async def to_item(self) -> ItemT:
        """Extract an item from a web page"""
        return await item_from_fields(
            self, item_cls=self.item_cls, item_cls_fields=self._skip_nonitem_fields
        )


@attr.s(auto_attribs=True)
class WebPage(Injectable, ResponseShortcutsMixin):
    """Base Page Object which requires :class:`~.HttpResponse`
    and provides XPath / CSS shortcuts.

    Use this class as a base class for Page Objects which work on
    HTML downloaded using an HTTP client directly.
    """

    response: HttpResponse


@attr.s(auto_attribs=True)
class ItemWebPage(WebPage, ItemPage):
    """:class:`WebPage` that requires the :meth:`to_item` method to
    be implemented.
    """

    pass
