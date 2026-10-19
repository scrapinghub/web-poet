from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Any

from frostwork import Page, detect_encoding, resolve_label

from web_poet._selectors import _class_cached, _get_selectors_dict

if TYPE_CHECKING:
    from web_poet._selectors import _SelectorDeclaration

_PAGE_ATTRIBUTE = "_web_poet_frostwork_page"

# Selector declaration modes, mapped to the frostwork page method with the same
# cardinality.
_METHODS = {"get": "field", "getall": "field_all"}


def _new_page(names: dict[_SelectorDeclaration, str]) -> Page:
    page = Page()
    for declaration, name in names.items():
        getattr(page, _METHODS[declaration.mode])(
            name, declaration.expression, syntax=declaration.syntax
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
    page = _new_page(names)
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
            f"frostwork cannot extract the selector declarations of "
            f"{cls.__qualname__}:\n  - "
            + "\n  - ".join(problems)
            + "\nWrite some fields as methods to extract them with parsel."
        )
    return page, names


def _get_page(cls: type) -> tuple[Page, dict[_SelectorDeclaration, str]] | None:
    """Return the frostwork page of *cls*, building it on the first call."""
    return _class_cached(cls, _PAGE_ATTRIBUTE, _build_page)


@cache
def _get_combined_page(
    classes: tuple[type, ...],
) -> tuple[Page, dict[_SelectorDeclaration, str]] | None:
    """Return a frostwork page for the declarations of all *classes*, or
    ``None`` if they do not fit in one."""
    names: dict[_SelectorDeclaration, str] = {}
    for cls in classes:
        for declaration in _get_selectors_dict(cls).values():
            names.setdefault(declaration, f"_{len(names)}")
    page = _new_page(names)
    if not page.check().ok:
        return None
    return page, names


def _check_class(cls: type) -> None:
    """Raise :exc:`TypeError` if frostwork cannot extract the selector
    declarations of *cls*."""
    if _get_selectors_dict(cls) and not hasattr(cls, "_selector_document"):
        raise TypeError(
            f"{cls.__qualname__} has selector declarations, but no response to "
            f"extract them from. Inherit from a class that has one, e.g. "
            f"web_poet.WebPage."
        )
    _get_page(cls)


def _supports(document: tuple[bytes | str, str | None]) -> bool:
    """Return whether frostwork can extract values out of *document*."""
    html, encoding = document
    if encoding is not None:
        # frostwork sniffs an encoding out of the document when it does not
        # know the one given to it, and the values of a document that it
        # decodes differently from the parsed one belong to parsel.
        label = resolve_label(encoding)
        if label is None or label != detect_encoding(html, encoding):
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
