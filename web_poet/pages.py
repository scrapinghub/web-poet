import abc
from typing import Any, Generic, List, Type, TypeVar

import attrs

from web_poet._typing import get_item_cls
from web_poet.fields import (
    FieldsMixin,
    SelectFields,
    _validate_select_fields,
    get_fields_dict,
    item_from_fields,
)
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


_NOT_SET = object()


@attrs.define
class ItemPage(Injectable, Returns[ItemT]):
    """Base Page Object, with a default :meth:`to_item` implementation
    which supports web-poet fields.
    """

    select_fields: SelectFields = attrs.field(
        converter=lambda x: SelectFields(x) if not isinstance(x, SelectFields) else x,
        kw_only=True,
        default=None,
    )
    _skip_nonitem_fields = _NOT_SET

    def _get_skip_nonitem_fields(self) -> bool:
        value = self._skip_nonitem_fields
        return False if value is _NOT_SET else bool(value)

    def __init_subclass__(cls, skip_nonitem_fields=_NOT_SET, **kwargs):
        super().__init_subclass__(**kwargs)
        if skip_nonitem_fields is _NOT_SET:
            # This is a workaround for attrs issue.
            # See: https://github.com/scrapinghub/web-poet/issues/141
            return
        cls._skip_nonitem_fields = skip_nonitem_fields

    async def to_item(self) -> ItemT:
        """Extract an item from a web page"""
        return await item_from_fields(
            self,
            item_cls=self.item_cls,
            skip_nonitem_fields=self._get_skip_nonitem_fields(),
        )

    @property
    def fields_to_ignore(self) -> List[str]:
        """Returns a list of field names which should **NOT** populate the
        designated :meth:`~.Returns.item_cls`.

        This is takes into account the fields inside the :class:`~.SelectFields`
        instance as well as fields that are marked as disabled by default (i.e.
        ``@field(disabled=True)``).
        """
        _validate_select_fields(self)

        fields = self.select_fields.fields
        page_obj_fields = get_fields_dict(self, include_disabled=True)

        fields_to_ignore = []
        for name, field_info in page_obj_fields.items():
            if fields.get("*") is True and fields.get(name) is not False:
                continue
            if (
                field_info.disabled is True
                or fields.get(name) is False
                or (fields.get("*") is False and fields.get(name) is not True)
            ):
                fields_to_ignore.append(name)

        for name in fields:
            if (
                fields.get(name) is False
                and name != "*"
                and name not in fields_to_ignore
            ):
                fields_to_ignore.append(name)

        return fields_to_ignore


@attrs.define
class WebPage(ItemPage[ItemT], ResponseShortcutsMixin):
    """Base Page Object which requires :class:`~.HttpResponse`
    and provides XPath / CSS shortcuts.
    """

    response: HttpResponse


ItemWebPage = _create_deprecated_class("ItemWebPage", WebPage, warn_once=False)
