import abc
from typing import Any, Generic, Iterable, Optional, Type, TypeVar

import attr

from web_poet._typing import get_item_cls
from web_poet.fields import FieldsMixin, SelectFields, get_fields_dict, item_from_fields
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


def is_injectable(cls: Any) -> bool:
    """Return True if ``cls`` is a class which inherits
    from :class:`~.Injectable`."""
    return isinstance(cls, type) and issubclass(cls, Injectable)


ItemT = TypeVar("ItemT")


class Returns(Generic[ItemT]):
    """Inherit from this generic mixin to change the item class used by
    :class:`~.ItemPage`"""

    @property
    def item_cls(self) -> Type[ItemT]:
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

        partial_item = await self._partial_item()
        if partial_item:
            return partial_item

        return await item_from_fields(
            self, item_cls=self.item_cls, skip_nonitem_fields=self._skip_nonitem_fields
        )

    # TODO: cache, or maybe not? since users could swap the select_field to
    # reuse the same instance.
    def _get_select_fields(self) -> Optional[SelectFields]:
        # TODO: Should we support other naming conventions? this means we need
        # to iterate over all instance attributes to see if there's an instance
        # of SelectFields. But this should also mean we need to check if there
        # are multiple SelectField instances.
        #
        # for key, param in inspect.signature(self.__init__).parameters.items():

        select_fields = getattr(self, "select_fields", None)
        if not select_fields:
            return None

        if not isinstance(select_fields, SelectFields):
            return None

        return select_fields

    @property
    def fields_to_extract(self) -> Optional[Iterable[str]]:
        """Returns an Iterable of field names which should populate the designated
        ``item_cls``.

        This takes into account the ``include`` and ``excluded`` fields, if
        :class:`web_poet.fields.SelectFields` is available as an instance
        attribute to the page object.
        """
        select_fields = self._get_select_fields()
        if select_fields is None:
            return None

        if isinstance(select_fields.include, list) and len(select_fields.include) == 0:
            return select_fields.include

        page_obj_fields = get_fields_dict(self).keys()
        fields = (set(select_fields.include or []) or page_obj_fields) - set(
            select_fields.exclude or []
        )
        return fields

    async def _partial_item(self) -> Optional[Any]:
        select_fields = self._get_select_fields()
        if not select_fields:
            return None

        return await item_from_fields(
            self,
            item_cls=select_fields.swap_item_cls or self.item_cls,
            skip_nonitem_fields=self._skip_nonitem_fields,
            field_names=self.fields_to_extract,
            on_unknown_field=select_fields.on_unknown_field,
        )


@attr.s(auto_attribs=True)
class WebPage(ItemPage[ItemT], ResponseShortcutsMixin):
    """Base Page Object which requires :class:`~.HttpResponse`
    and provides XPath / CSS shortcuts.
    """

    response: HttpResponse


ItemWebPage = _create_deprecated_class("ItemWebPage", WebPage, warn_once=False)
