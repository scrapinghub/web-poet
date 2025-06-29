import abc
import inspect
from contextlib import suppress
from functools import wraps
from types import GenericAlias
from typing import Any, Generic, Optional, TypeVar, overload

import attr
import parsel

from web_poet.fields import FieldsMixin, item_from_fields
from web_poet.mixins import ResponseShortcutsMixin, SelectorShortcutsMixin
from web_poet.page_inputs import HttpResponse
from web_poet.utils import (
    CallableT,
    cached_method,
    get_generic_param,
)


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


def is_injectable(cls: Any) -> bool:
    """Return True if ``cls`` is a class which inherits
    from :class:`~.Injectable`."""
    return (
        isinstance(cls, type)
        and not isinstance(cls, GenericAlias)
        and issubclass(cls, Injectable)
    )


ItemT = TypeVar("ItemT")


class Returns(Generic[ItemT]):
    """Inherit from this generic mixin to change the item class used by
    :class:`~.ItemPage`"""

    @property
    def item_cls(self) -> type:
        """Item class"""
        return get_item_cls(self.__class__, default=dict)


@overload
def get_item_cls(cls: type, default: type) -> type: ...


@overload
def get_item_cls(cls: type, default: None) -> Optional[type]: ...


def get_item_cls(cls: type, default: Optional[type] = None) -> Optional[type]:
    param = get_generic_param(cls, Returns)
    return param or default


_NOT_SET = object()


def validates_input(to_item: CallableT) -> CallableT:
    """Decorator to apply input validation to custom to_item method
    implementations in :class:`~web_poet.pages.ItemPage` subclasses."""

    if inspect.iscoroutinefunction(to_item):

        @wraps(to_item)
        async def _to_item(self, *args, **kwargs):
            validation_item = self._validate_input()
            if validation_item is not None:
                return validation_item
            return await to_item(self, *args, **kwargs)

    else:

        @wraps(to_item)
        def _to_item(self, *args, **kwargs):
            validation_item = self._validate_input()
            if validation_item is not None:
                return validation_item
            return to_item(self, *args, **kwargs)

    return _to_item  # type: ignore[return-value]


class Extractor(Returns[ItemT], FieldsMixin):
    """Base class for field support."""

    _skip_nonitem_fields = _NOT_SET

    def _get_skip_nonitem_fields(self) -> bool:
        value = self._skip_nonitem_fields
        return False if value is _NOT_SET else bool(value)

    def __init_subclass__(
        cls, skip_nonitem_fields: Any = _NOT_SET, **kwargs: Any
    ) -> None:
        super().__init_subclass__(**kwargs)
        if skip_nonitem_fields is _NOT_SET:
            # This is a workaround for attrs issue.
            # See: https://github.com/scrapinghub/web-poet/issues/141
            return
        cls._skip_nonitem_fields = skip_nonitem_fields

    async def to_item(self) -> ItemT:
        """Extract an item"""
        return await item_from_fields(
            self,
            item_cls=self.item_cls,
            skip_nonitem_fields=self._get_skip_nonitem_fields(),
        )


class ItemPage(Extractor[ItemT], Injectable):
    """Base class for page objects."""

    @cached_method
    def _validate_input(self) -> Any:
        """Run self.validate_input if defined."""
        if not hasattr(self, "validate_input"):
            return None
        with suppress(AttributeError):
            if self.__validating_input:
                # We are in a recursive call, i.e. _validate_input is being
                # called from _validate_input itself (likely through a @field
                # method).
                return None

        self.__validating_input: bool = True
        validation_item = self.validate_input()
        self.__validating_input = False
        return validation_item

    @validates_input
    async def to_item(self) -> ItemT:
        """Extract an item from a web page"""
        return await super().to_item()


@attr.s(auto_attribs=True)
class WebPage(ItemPage[ItemT], ResponseShortcutsMixin):
    """Base Page Object which requires :class:`~.HttpResponse`
    and provides XPath / CSS shortcuts.
    """

    response: HttpResponse


@attr.s(auto_attribs=True)
class SelectorExtractor(Extractor[ItemT], SelectorShortcutsMixin):
    """Extractor that takes a :class:`parsel.Selector` and provides shortcuts
    for its methods."""

    selector: parsel.Selector
