from __future__ import annotations

from typing import TYPE_CHECKING, Any

from frostwork import Page, detect_encoding, resolve_label

from web_poet._selectors import _class_cached, _get_selectors_dict

if TYPE_CHECKING:
    from web_poet._selectors import _SelectorDeclaration

_PAGE_ATTRIBUTE = "_web_poet_frostwork_page"
_COMBINED_PAGES_ATTRIBUTE = "_web_poet_frostwork_combined_pages"

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


def _compile(names: dict[_SelectorDeclaration, str], owner: str) -> Page:
    """Return a frostwork page for *names*, or raise :exc:`TypeError` naming
    *owner* if frostwork cannot extract them."""
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
            f"frostwork cannot extract the selector declarations of {owner}:\n"
            f"  - " + "\n  - ".join(problems) + "\nWrite some fields as methods "
            "to extract them with parsel."
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


def _build_combined_page(
    classes: tuple[type, ...],
) -> tuple[Page, dict[_SelectorDeclaration, str]]:
    names: dict[_SelectorDeclaration, str] = {}
    for cls in classes:
        for declaration in _get_selectors_dict(cls).values():
            names.setdefault(declaration, f"_{len(names)}")
    owner = ", ".join(cls.__qualname__ for cls in classes)
    # Each class fits the frostwork budget, as checked on class definition, but
    # their declarations together may not, in which case this raises on the
    # first field read of the page object.
    return _compile(names, f"{owner} together"), names


def _get_combined_page(
    classes: tuple[type, ...],
) -> tuple[Page, dict[_SelectorDeclaration, str]]:
    """Return a frostwork page for the declarations of all *classes*, building
    it on the first call.

    The page is cached on the first class, so that it lives as long as the
    classes that it combines."""
    pages = _class_cached(classes[0], _COMBINED_PAGES_ATTRIBUTE, lambda cls: {})
    if classes not in pages:
        pages[classes] = _build_combined_page(classes)
    return pages[classes]


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
