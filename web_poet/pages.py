import abc
import typing

import attr

from web_poet._typing import get_item_cls
from web_poet.fields import FieldsMixin, item_from_fields
from web_poet.mixins import ResponseShortcutsMixin
from web_poet.page_inputs import HttpResponse
from web_poet.utils import _create_deprecated_class


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


class Returns(typing.Generic[ItemT]):
    """Inherit from this generic mixin to change the item class used by
    :class:`~.ItemPage`"""

    @property
    def item_cls(self) -> typing.Type[ItemT]:
        """Item class"""
        return get_item_cls(self.__class__, default=dict)


class ItemPage(Injectable, Returns[ItemT]):
    """Base Page Object, with a default :meth:`to_item` implementation
    which supports web-poet fields.
    """

    _skip_nonitem_fields: bool

    def __init_subclass__(cls, skip_nonitem_fields: bool = False, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._skip_nonitem_fields = skip_nonitem_fields

    async def to_item(self) -> ItemT:
        """Extract an item from a web page"""
        return await item_from_fields(
            self, item_cls=self.item_cls, skip_nonitem_fields=self._skip_nonitem_fields
        )


class MultiLayoutPage(ItemPage[ItemT]):
    """Base class for :ref:`multi-layout page object classes <multi-layout>`.

    Subclasses must reimplement the :meth:`layout` method.
    """

    @abc.abstractmethod
    async def get_layout(self) -> ItemPage[ItemT]:
        """Return the :ref:`page object <page-objects>` to use based on the
        received input (e.g. :class:`~.HttpResponse`)."""

    async def to_item(self) -> ItemT:
        """Return the output of the :meth:`~web_poet.pages.ItemPage.to_item`
        method of the :ref:`page object <page-objects>` that :meth:`layout`
        returns."""
        page_object = await self.get_layout()
        return await page_object.to_item()


@attr.s(auto_attribs=True)
class WebPage(ItemPage[ItemT], ResponseShortcutsMixin):
    """Base Page Object which requires :class:`~.HttpResponse`
    and provides XPath / CSS shortcuts.
    """

    response: HttpResponse


ItemWebPage = _create_deprecated_class("ItemWebPage", WebPage, warn_once=False)
