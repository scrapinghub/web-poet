from __future__ import annotations

from typing import TYPE_CHECKING, Any

try:
    from frostwork import Page, detect_encoding, resolve_label
except ImportError:
    Page = None  # type: ignore[assignment,misc]

from web_poet._selectors import _class_cached, _get_selectors_dict

if TYPE_CHECKING:
    from web_poet._selectors import _SelectorDeclaration

_PAGE_ATTRIBUTE = "_web_poet_frostwork_page"

# Selector declaration modes, mapped to the frostwork page method with the same
# cardinality. A declaration whose mode is missing here is left to parsel:
# frostwork extracts values, so it cannot build a selector list.
_METHODS = {"get": "field", "getall": "field_all"}

# frostwork supports neither JMESPath nor every CSS and XPath expression; the
# expressions that it does not support are reported by check().
_SYNTAXES = {"css", "xpath"}


def _build_page(cls: type) -> tuple[Page, dict[_SelectorDeclaration, str]] | None:
    """Return a frostwork page for the declarations of *cls* that frostwork
    extracts, mapped to the name that they have on it, or ``None`` if there are
    none.

    Declarations that are equal are extracted once, under the first attribute
    name that uses one."""
    names: dict[_SelectorDeclaration, str] = {}
    for name, declaration in _get_selectors_dict(cls).items():
        if declaration.mode in _METHODS and declaration.syntax in _SYNTAXES:
            names.setdefault(declaration, name)
    if not names:
        return None
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
            f"frostwork cannot extract the selector declarations of "
            f"{cls.__qualname__}:\n  - "
            + "\n  - ".join(problems)
            + "\nWrite some fields as methods to extract them with parsel."
        )
    return page, names


def _get_page(cls: type) -> tuple[Page, dict[_SelectorDeclaration, str]] | None:
    """Return the frostwork page of *cls*, building it on the first call."""
    return _class_cached(cls, _PAGE_ATTRIBUTE, _build_page)


def _check_class(cls: type) -> None:
    """Raise an exception if frostwork cannot extract the selector declarations
    of *cls*."""
    if Page is None:
        raise ImportError(
            f"{cls.__qualname__} sets declarative_backend='frostwork'. Install "
            f"web-poet[frostwork]."
        )
    if not hasattr(cls, "_selector_document"):
        raise TypeError(
            f"{cls.__qualname__} sets declarative_backend='frostwork', but it "
            f"has no response for frostwork to extract from. Inherit from a "
            f"class that does, e.g. web_poet.WebPage."
        )
    _get_page(cls)


def _extract(
    cls: type,
    declaration: _SelectorDeclaration,
    document: tuple[bytes | str, str | None],
) -> dict[_SelectorDeclaration, Any] | None:
    """Return the value of every declaration of *cls* that frostwork extracts
    out of *document*, provided that *declaration* is among them.

    Return an empty mapping otherwise, or ``None`` if frostwork cannot extract
    any declaration out of *document*."""
    result = _get_page(cls)
    if result is None:
        return {}
    page, names = result
    if declaration not in names:
        return {}
    html, encoding = document
    if encoding is not None:
        # frostwork sniffs an encoding out of the document when it does not
        # know the one given to it, and the values of a document that it
        # decodes differently from the parsed one belong to parsel.
        label = resolve_label(encoding)
        if label is None or label != detect_encoding(html, encoding):
            return None
    values = page.extract(html, encoding).to_dict()
    return {declaration: values[name] for declaration, name in names.items()}
