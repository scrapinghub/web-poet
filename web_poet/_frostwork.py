from __future__ import annotations

import types
import typing
import weakref
from typing import TYPE_CHECKING, Any

from frostwork import Page, detect_encoding, resolve_label

from web_poet._selectors import (
    _SELECTORS_DICT_ATTRIBUTE,
    _class_cached,
    _get_selectors_dict,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from web_poet._selectors import _SelectorDeclaration

_PAGE_ATTRIBUTE = "_web_poet_frostwork_page"
_UNION_PAGES_ATTRIBUTE = "_web_poet_frostwork_union_pages"
_DEPENDENCIES_ATTRIBUTE = "_web_poet_selector_dependencies"

# Selector declaration modes, mapped to the frostwork page method with the same
# cardinality.
_METHODS = {"get": "field", "getall": "field_all"}


def _compile(names: dict[_SelectorDeclaration, str], owner: str) -> Page:
    """Return a frostwork page for *names*, or raise :exc:`TypeError` naming
    *owner* if frostwork cannot extract them."""
    page = Page()
    for declaration, name in names.items():
        getattr(page, _METHODS[declaration.mode])(
            name, declaration.expression, syntax=declaration.syntax
        )
    report = page.check()
    if not report.ok:
        problems = [
            f"{field.name} = {field.selector!r}: {field.reason}"
            for field in report.unsupported
        ]
        if report.over_budget:
            problems.append(
                f"over budget: {report.members}/{report.max_members} member "
                f"selectors, {report.sib_bits}/{report.max_sib_bits} "
                f"sibling-combinator bits"
            )
        raise TypeError(
            f"frostwork cannot extract the selector declarations of {owner}:\n"
            f"  - " + "\n  - ".join(problems) + "\nRewrite them within the "
            "frostwork selector contract "
            "(https://github.com/scrapy/frostwork/blob/main/docs/COMPATIBILITY.md), "
            "or write some of them as methods to extract them with parsel."
        )
    return page


def _build_page(cls: type) -> tuple[Page, dict[_SelectorDeclaration, str]] | None:
    """Return a frostwork page for the declarations of *cls*, mapped to the
    name that they have on it, or ``None`` if there are none.

    Declarations that are equal are extracted once, under the first attribute
    name that uses one."""
    names: dict[_SelectorDeclaration, str] = {}
    for name, declaration in _get_selectors_dict(cls).items():
        names.setdefault(declaration, name)
    if not names:
        return None
    return _compile(names, cls.__qualname__), names


def _get_page(cls: type) -> tuple[Page, dict[_SelectorDeclaration, str]] | None:
    """Return the frostwork page of *cls*, building it on the first call."""
    return _class_cached(cls, _PAGE_ATTRIBUTE, _build_page)


def _get_union_page(
    classes: Iterable[type],
) -> tuple[Page, dict[_SelectorDeclaration, str]] | None:
    """Return a frostwork page for the declarations of all *classes*, or
    ``None`` if none of them has any, building it on the first call."""
    declaring = sorted(
        {cls for cls in classes if _get_selectors_dict(cls)},
        key=lambda cls: (cls.__module__, cls.__qualname__, id(cls)),
    )
    if not declaring:
        return None
    if len(declaring) == 1:
        return _get_page(declaring[0])
    # The page is cached on the first class, and keeps the other classes alive
    # for as long as that one lives.
    pages = _class_cached(declaring[0], _UNION_PAGES_ATTRIBUTE, lambda cls: {})
    key = tuple(declaring)
    if key not in pages:
        names: dict[_SelectorDeclaration, str] = {}
        for cls in declaring:
            for declaration in _get_selectors_dict(cls).values():
                names.setdefault(declaration, f"_{len(names)}")
        owner = ", ".join(cls.__qualname__ for cls in declaring)
        pages[key] = _compile(names, f"{owner} together"), names
    return pages[key]


def _annotation_classes(annotation: Any) -> list[type]:
    if typing.get_origin(annotation) in {typing.Union, types.UnionType}:
        return [
            cls
            for arg in typing.get_args(annotation)
            for cls in _annotation_classes(arg)
        ]
    return [annotation] if isinstance(annotation, type) else []


def _build_dependency_classes(cls: type) -> tuple[type, ...]:
    try:
        hints = typing.get_type_hints(cls)
    except Exception:
        return ()
    result: dict[type, None] = {}
    for annotation in hints.values():
        for dependency in _annotation_classes(annotation):
            # Only classes that web-poet has checked can have declarations.
            if dependency is cls or not hasattr(dependency, _SELECTORS_DICT_ATTRIBUTE):
                continue
            if _get_selectors_dict(dependency):
                result[dependency] = None
            result.update(dict.fromkeys(_dependency_classes(dependency)))
    result.pop(cls, None)
    return tuple(result)


def _dependency_classes(cls: type) -> tuple[type, ...]:
    """Return the classes with selector declarations among the annotated
    dependencies of *cls*, direct or not.

    Annotations that cannot be resolved when *cls* is defined are left out."""
    return _class_cached(cls, _DEPENDENCIES_ATTRIBUTE, _build_dependency_classes)


def _response_kind(cls: type) -> str | None:
    """Return ``"http"`` or ``"browser"`` for a class that reads that kind of
    response, or ``None`` if it could read either."""
    from web_poet.pages import BrowserPage, WebPage  # noqa: PLC0415

    if issubclass(cls, BrowserPage):
        return "browser"
    if issubclass(cls, WebPage):
        return "http"
    return None


def _check_class(cls: type) -> None:
    """Raise :exc:`TypeError` if frostwork cannot extract the selector
    declarations of *cls*, or those of *cls* and of its dependencies that read
    the same kind of response, in a single pass."""
    if _get_selectors_dict(cls) and not hasattr(cls, "_selector_document"):
        raise TypeError(
            f"{cls.__qualname__} has selector declarations, but no response to "
            f"extract them from. Inherit from a class that has one, e.g. "
            f"web_poet.WebPage."
        )
    _get_page(cls)
    classes = [cls, *_dependency_classes(cls)]
    if len(classes) == 1:
        return
    kinds = {_response_kind(klass) for klass in classes}
    for kind in (kinds - {None}) or {None}:
        _get_union_page(
            klass for klass in classes if _response_kind(klass) in {kind, None}
        )


def _decodes_as_declared(document: tuple[bytes | str, str | None]) -> bool:
    """Return whether frostwork decodes *document* with its declared
    encoding."""
    html, encoding = document
    if encoding is not None:
        # frostwork sniffs an encoding out of the document when it does not
        # know the one given to it, and decodes encodings that WHATWG maps to
        # "replacement" into a single replacement character.
        label = resolve_label(encoding)
        if label in {None, "replacement"} or label != detect_encoding(html, encoding):
            return False
    return True


def _extract(
    compiled: tuple[Page, dict[_SelectorDeclaration, str]],
    document: tuple[bytes | str, str | None],
) -> dict[_SelectorDeclaration, Any]:
    """Return the value of every declaration of *compiled*, a frostwork page
    mapped to the names of its declarations, out of *document*."""
    page, names = compiled
    values = page.extract(*document).to_dict()
    return {declaration: values[name] for declaration, name in names.items()}


# Objects with selector declarations that have not extracted them yet, by id,
# since page objects are often unhashable attrs classes. Objects are registered
# before they have a response, so they start in _unsorted, and move to the
# bucket of their response the first time that _pending_objects() sees them
# with one, so that each lookup only scans the objects registered since the
# previous one and those over the same response.
_unsorted: dict[int, weakref.ref[Any]] = {}
_by_response: dict[int, dict[int, weakref.ref[Any]]] = {}
_response_keys: dict[int, int] = {}


def _register(obj: Any) -> None:
    """Register *obj* to extract its declarations in the same pass as any
    other registered object that reads the same response."""
    key = id(obj)

    def forget(_: weakref.ref[Any]) -> None:
        _forget(key)

    _unsorted[key] = weakref.ref(obj, forget)


def _forget(key: int) -> None:
    _unsorted.pop(key, None)
    response_key = _response_keys.pop(key, None)
    if response_key is not None:
        bucket = _by_response[response_key]
        del bucket[key]
        if not bucket:
            del _by_response[response_key]


def _unregister(obj: Any) -> None:
    _forget(id(obj))


def _any_pending() -> bool:
    """Return whether any registered object has yet to extract its
    declarations."""
    return bool(_unsorted or _response_keys)


def _response_or_none(obj: Any) -> Any:
    # An object whose __init__ failed before setting its response can still be
    # registered until it is garbage-collected.
    try:
        return obj._selector_response()
    except AttributeError:
        return None


def _pending_objects(response: Any) -> list[Any]:
    """Return the registered objects that read *response*."""
    for key, ref in list(_unsorted.items()):
        if (obj := ref()) is None or (obj_response := _response_or_none(obj)) is None:
            continue
        del _unsorted[key]
        _response_keys[key] = id(obj_response)
        _by_response.setdefault(id(obj_response), {})[key] = ref
    bucket = _by_response.get(id(response), {})
    # A response attribute set again after sorting can point elsewhere.
    return [
        obj
        for ref in list(bucket.values())
        if (obj := ref()) is not None and _response_or_none(obj) is response
    ]
