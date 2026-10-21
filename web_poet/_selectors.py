from __future__ import annotations

import copy
import inspect
import sys
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable

    # typing.Self requires Python 3.11
    from typing_extensions import Self

_SELECTORS_DICT_ATTRIBUTE = "_web_poet_selectors_dict"

_ValueT = TypeVar("_ValueT")

_SelectorSyntax = Literal["css", "xpath"]

# Whether the value of a selector declaration is the value of its first match,
# or the values of all its matches, named after the parsel selector list method
# that does the same.
_SelectorMode = Literal["get", "getall"]


class _SelectorDeclaration(Generic[_ValueT]):
    def __init__(
        self,
        expression: str,
        syntax: _SelectorSyntax,
        mode: _SelectorMode,
    ):
        self.expression = expression
        self.syntax = syntax
        self.mode = mode

    def __repr__(self) -> str:
        return f"{self.syntax}_{self.mode}({self.expression!r})"

    @property
    def _key(self) -> tuple[str, _SelectorSyntax, _SelectorMode]:
        return self.expression, self.syntax, self.mode

    # Declarations are dictionary keys, both to map them to their value on an
    # object and to extract each of them once, and two declarations of the same
    # query always have the same value.
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _SelectorDeclaration):
            return NotImplemented
        return self._key == other._key

    def __hash__(self) -> int:
        return hash(self._key)

    def __set_name__(self, owner: type, name: str) -> None:
        _check_unannotated(owner, name, "declaration")

    @overload
    def __get__(
        self, instance: None, owner: type | None = None
    ) -> _SelectorDeclaration[_ValueT]: ...

    @overload
    def __get__(self, instance: object, owner: type | None = None) -> _ValueT: ...

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            selector_value = instance._selector_value
        except AttributeError:
            raise TypeError(
                f"{type(instance).__name__} does not support selector declarations: "
                f"it provides no response. Inherit from a class that does, e.g. "
                f"web_poet.WebPage."
            ) from None
        return selector_value(self)


def _check_unannotated(owner: type, name: str, kind: str) -> None:
    """Raise :exc:`TypeError` if *name*, a selector *kind*, is annotated in the
    body of *owner*.

    attrs turns annotated class attributes into instance attributes that
    default to the class attribute value, hiding what its descriptor returns."""
    if sys.version_info >= (3, 14):
        from annotationlib import Format, get_annotations  # noqa: PLC0415

        annotations = get_annotations(owner, format=Format.FORWARDREF)
    else:
        annotations = inspect.get_annotations(owner)
    if name in annotations:
        raise TypeError(
            f"{owner.__qualname__}.{name} is a selector {kind} with a type "
            f"annotation. Remove the annotation."
        )


def css_get(expression: str) -> _SelectorDeclaration[str | None]:
    """Return a declaration of the CSS *expression*, to be used as a class
    attribute of a page object class, either on its own or through
    :func:`~web_poet.field`.

    Its value is that of the first match, or ``None``.

    See :ref:`declarative-selectors`.
    """
    return _SelectorDeclaration(expression, "css", "get")


def css_getall(expression: str) -> _SelectorDeclaration[list[str]]:
    """Return a declaration of the CSS *expression* whose value is the list of
    the values of all its matches.

    See :func:`~web_poet.css_get`.
    """
    return _SelectorDeclaration(expression, "css", "getall")


def xpath_get(expression: str) -> _SelectorDeclaration[str | None]:
    """Return a declaration of the XPath *expression*.

    See :func:`~web_poet.css_get`.
    """
    return _SelectorDeclaration(expression, "xpath", "get")


def xpath_getall(expression: str) -> _SelectorDeclaration[list[str]]:
    """Return a declaration of the XPath *expression* whose value is the list
    of the values of all its matches.

    See :func:`~web_poet.css_get`.
    """
    return _SelectorDeclaration(expression, "xpath", "getall")


class SelectorGroup:
    """Base class for a group of :ref:`selector declarations
    <declarative-selectors>` that page object classes can share, by assigning
    an instance of it as a class attribute.

    See :ref:`sharing-selectors`."""

    _owner: Any = None

    def __set_name__(self, owner: type, name: str) -> None:
        _check_unannotated(owner, name, "group")

    def __get__(self, instance: object | None, owner: type | None = None) -> Self:
        if instance is None:
            return self
        group = copy.copy(self)
        group._owner = instance
        return group

    def _selector_value(self, declaration: _SelectorDeclaration) -> Any:
        if self._owner is None:
            raise TypeError(
                f"{type(self).__name__} can only be read through the page object "
                f"class that it is assigned to."
            )
        return self._owner._selector_value(declaration)


def _get_declaration(value: Any) -> _SelectorDeclaration | None:
    if not isinstance(value, _SelectorDeclaration):
        value = getattr(value, "selector_declaration", None)
    return value if isinstance(value, _SelectorDeclaration) else None


_MISSING = object()


def _class_cached(cls: type, attribute: str, build: Callable[[type], Any]) -> Any:
    """Return ``build(cls)``, caching it in *attribute* of *cls*.

    Only *cls* itself is looked up, so that each subclass builds its own
    value."""
    value = cls.__dict__.get(attribute, _MISSING)
    if value is _MISSING:
        value = build(cls)
        setattr(cls, attribute, value)
    return value


def _build_selectors_dict(cls: type) -> dict[str, _SelectorDeclaration]:
    result: dict[str, _SelectorDeclaration] = {}
    for klass in reversed(cls.__mro__):
        for name, value in vars(klass).items():
            # A subclass shadowing a declaration or a group with something
            # else, e.g. a regular @field method, drops it from the schema.
            for key in [k for k in result if k == name or k.startswith(f"{name}.")]:
                del result[key]
            if isinstance(value, SelectorGroup):
                for inner_name, inner in _get_selectors_dict(type(value)).items():
                    result[f"{name}.{inner_name}"] = inner
            elif (declaration := _get_declaration(value)) is not None:
                result[name] = declaration
    return result


def _get_selectors_dict(cls: type) -> dict[str, _SelectorDeclaration]:
    """Return a dictionary with the selector declarations of *cls*: keys are
    attribute names, dotted for declarations of a group, e.g. ``skus.meta``,
    and values are declaration objects."""
    return _class_cached(cls, _SELECTORS_DICT_ATTRIBUTE, _build_selectors_dict)
