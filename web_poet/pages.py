import abc
from typing import Any, Generic, Iterable, Optional, Set, Type, TypeVar
from warnings import warn

import attr

from web_poet._typing import get_item_cls
from web_poet.fields import (
    FieldsMixin,
    SelectFields,
    UnknownFieldActions,
    get_fields_dict,
    item_from_fields,
)
from web_poet.mixins import ResponseShortcutsMixin
from web_poet.page_inputs import HttpResponse
from web_poet.utils import _create_deprecated_class, get_fq_class_name


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
        return await item_from_fields(
            self,
            item_cls=self.item_cls,
            skip_nonitem_fields=self._skip_nonitem_fields,
            field_names=self.fields_to_extract,
        )

    def _get_select_fields(self) -> Optional[SelectFields]:
        select_fields = getattr(self, "select_fields", None)
        if not select_fields:
            return None

        if not isinstance(select_fields, SelectFields):
            return None

        return select_fields

    @property
    def fields_to_extract(self) -> Iterable[str]:
        """Returns an Iterable of field names which should populate the designated
        ``item_cls``.

        If :class:`web_poet.fields.SelectFields` is set, this takes into account
        the fields that are marked as included or excluded alongside any field
        that are marked as enabled/disabled by default.
        """
        select_fields = self._get_select_fields()
        if select_fields is None:
            return list(get_fields_dict(self))

        fields = select_fields.fields

        if fields is None or len(fields) == 0:
            return list(get_fields_dict(self))

        page_obj_fields = get_fields_dict(self, include_disabled=True)

        unknown_fields = set(fields) - set(page_obj_fields.keys()).union({"*"})
        if unknown_fields:
            self._handle_unknown_field(unknown_fields, select_fields.on_unknown_field)

        fields_to_extract = []
        for name, field_info in page_obj_fields.items():
            if fields.get("*") is False and fields.get(name) is not True:
                continue
            if (
                fields.get("*") is True
                or fields.get(name) is True
                or field_info.disabled is False
            ) and fields.get(name) is not False:
                fields_to_extract.append(name)

        return fields_to_extract

    def _handle_unknown_field(
        self, name: Set[str], action: UnknownFieldActions = "raise"
    ) -> None:
        if action == "ignore":
            return None

        msg = (
            f"The {name} fields isn't available in {get_fq_class_name(self.__class__)}."
        )

        if action == "raise":
            raise AttributeError(msg)
        elif action == "warn":
            warn(msg)
        else:
            raise ValueError(
                f"web_poet.SelectFields only accepts 'ignore', 'warn', and 'raise' "
                f"values. Received unrecognized '{action}' value which it treats as "
                f"'ignore'."
            )


@attr.s(auto_attribs=True)
class WebPage(ItemPage[ItemT], ResponseShortcutsMixin):
    """Base Page Object which requires :class:`~.HttpResponse`
    and provides XPath / CSS shortcuts.
    """

    response: HttpResponse


ItemWebPage = _create_deprecated_class("ItemWebPage", WebPage, warn_once=False)
