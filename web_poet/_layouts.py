from __future__ import annotations

import inspect
import sys
import types
import typing
from typing import Any

from itemadapter import ItemAdapter

from web_poet.fields import FieldInfo, field, get_fields_dict
from web_poet.pages import ItemPage, get_item_cls
from web_poet.utils import cached_method, ensure_awaitable


def layout_switch(
    cls: type[ItemPage] | None = None,
    *,
    switch_method: str = "get_layout",
    layouts: typing.Iterable[type[ItemPage]] | None = None,
):
    """Decorate a page object class to expose fields from its selected layout.

    The decorated class must define a method named by *switch_method*
    (``"get_layout"`` by default). The method can be synchronous or
    asynchronous and must return an :class:`~web_poet.pages.ItemPage` instance.

    By default, forwarded fields are inferred from the output item type field
    names. This keeps forwarding aligned with the declared item schema.

    For output item types that do not expose field names (for example, plain
    :class:`dict`), pass ``layouts`` explicitly. In that case, forwarded fields
    are the union of fields defined across the provided layout page object
    classes.

    If the decorated class already defines a field with the same name,
    :func:`layout_switch` gives priority to the selected layout field and falls
    back to the decorated class field when the selected layout does not define
    that field.
    """

    def wrap(page_cls: type[ItemPage]) -> type[ItemPage]:
        nonlocal layouts
        if layouts:
            fields_to_forward = _layout_fields(layouts)
        else:
            fields_to_forward = _item_fields_from_page_cls(page_cls)
            layouts = _discover_layout_classes(page_cls)

        helper_names = _install_cached_layout_helpers(page_cls, switch_method)

        page_field_names = set(get_fields_dict(page_cls).keys())
        for field_name in fields_to_forward:
            fallback_attr_name = None
            fallback_attr = None
            if field_name in page_field_names:
                fallback_attr_name = (
                    "_layout_switch_fallback_field__"
                    f"{switch_method.replace('.', '_')}__{field_name}"
                )
                if not hasattr(page_cls, fallback_attr_name):
                    sentinel = object()
                    fallback_attr = inspect.getattr_static(
                        page_cls, field_name, sentinel
                    )
                    if fallback_attr is not sentinel:
                        setattr(page_cls, fallback_attr_name, fallback_attr)
                fallback_attr = getattr(page_cls, fallback_attr_name, None)

            forward_async = _should_forward_async(
                page_cls,
                layouts,
                field_name,
                switch_method,
                fallback_attr=fallback_attr,
            )
            descriptor = _build_forwarding_field(
                field_name,
                async_helper_name=helper_names["async"],
                sync_helper_name=helper_names["sync"],
                forward_async=forward_async,
                fallback_attr_name=fallback_attr_name,
            )
            setattr(page_cls, field_name, descriptor)
            _register_field(page_cls, field_name)

        return page_cls

    if cls is None:
        return wrap
    return wrap(cls)


def _item_fields_from_page_cls(page_cls: type[ItemPage]) -> list[str]:
    item_cls = get_item_cls(page_cls, default=dict)
    item_field_names = ItemAdapter.get_field_names_from_class(item_cls)
    if item_field_names is None:
        raise ValueError(
            "The output item type does not expose field names. "
            "Pass explicit layout classes via layout_switch(layouts=[...])."
        )
    return list(item_field_names)


def _discover_layout_classes(page_cls: type[ItemPage]) -> list[type[ItemPage]]:
    hints = _get_type_hints(page_cls)
    classes: list[type[ItemPage]] = []
    for annotation in hints.values():
        for layout_cls in _get_item_page_classes(annotation):
            if layout_cls not in classes:
                classes.append(layout_cls)
    return classes


def _get_type_hints(page_cls: type) -> dict[str, Any]:
    module = sys.modules.get(page_cls.__module__)
    globalns = vars(module) if module else None
    try:
        return typing.get_type_hints(page_cls, globalns=globalns, include_extras=True)
    except Exception:
        return dict(getattr(page_cls, "__annotations__", {}))


def _get_item_page_classes(annotation: Any) -> list[type[ItemPage]]:
    if isinstance(annotation, str):
        return []

    origin = typing.get_origin(annotation)
    if origin is typing.Annotated:
        return _get_item_page_classes(typing.get_args(annotation)[0])

    if origin in {typing.Union, types.UnionType}:
        result: list[type[ItemPage]] = []
        for arg in typing.get_args(annotation):
            result.extend(_get_item_page_classes(arg))
        return result

    if isinstance(annotation, type) and issubclass(annotation, ItemPage):
        return [annotation]

    return []


def _layout_fields(layout_classes: list[type[ItemPage]]) -> list[str]:
    names: list[str] = []
    for layout_cls in layout_classes:
        for field_name in get_fields_dict(layout_cls):
            if field_name not in names:
                names.append(field_name)
    return names


def _install_cached_layout_helpers(
    page_cls: type[ItemPage], switch_method: str
) -> dict[str, str]:
    method_tag = switch_method.replace(".", "_")
    sync_name = f"_layout_switch_cached_layout_sync__{method_tag}"
    async_name = f"_layout_switch_cached_layout_async__{method_tag}"

    if not hasattr(page_cls, sync_name):

        @cached_method
        def _cached_layout_sync(self):
            return getattr(self, switch_method)()

        setattr(page_cls, sync_name, _cached_layout_sync)

    if not hasattr(page_cls, async_name):

        @cached_method
        async def _cached_layout_async(self):
            return await ensure_awaitable(getattr(self, switch_method)())

        setattr(page_cls, async_name, _cached_layout_async)

    return {"sync": sync_name, "async": async_name}


def _should_forward_async(
    page_cls: type[ItemPage],
    layout_classes: list[type[ItemPage]],
    field_name: str,
    switch_method: str,
    fallback_attr: Any,
) -> bool:
    if inspect.iscoroutinefunction(getattr(page_cls, switch_method)):
        return True

    for layout_cls in layout_classes:
        attr = getattr(layout_cls, field_name, None)
        original_method = getattr(attr, "original_method", None)
        if original_method is not None and inspect.iscoroutinefunction(original_method):
            return True

    fallback_original_method = getattr(fallback_attr, "original_method", None)
    return bool(
        fallback_original_method is not None
        and inspect.iscoroutinefunction(fallback_original_method)
    )


def _build_forwarding_field(
    field_name: str,
    *,
    async_helper_name: str,
    sync_helper_name: str,
    forward_async: bool,
    fallback_attr_name: str | None,
):
    def _resolve_field_target(page, layout):
        layout_fields = get_fields_dict(layout)
        if field_name in layout_fields:
            return layout, field_name
        if fallback_attr_name is not None:
            return page, fallback_attr_name
        raise AttributeError(
            f"Selected layout {layout.__class__.__name__} does not define field "
            f"'{field_name}' and no fallback field is defined in "
            f"{page.__class__.__name__}"
        )

    if forward_async:

        async def forwarded(self):
            layout = await getattr(self, async_helper_name)()
            target, attr_name = _resolve_field_target(self, layout)
            return await ensure_awaitable(getattr(target, attr_name))

    else:

        def forwarded(self):
            layout = getattr(self, sync_helper_name)()
            target, attr_name = _resolve_field_target(self, layout)
            return getattr(target, attr_name)

    forwarded.__name__ = field_name
    return field(forwarded)


def _register_field(page_cls: type[ItemPage], field_name: str) -> None:
    fields = dict(get_fields_dict(page_cls))
    if field_name in fields:
        return
    fields[field_name] = FieldInfo(name=field_name)
    page_cls._web_poet_fields_info = fields
