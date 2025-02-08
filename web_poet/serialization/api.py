from __future__ import annotations

from functools import singledispatch
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

import andi
from andi.typeutils import strip_annotated

import web_poet
from web_poet import Injectable
from web_poet.annotated import AnnotatedInstance
from web_poet.pages import is_injectable
from web_poet.utils import get_fq_class_name

if TYPE_CHECKING:
    import os
    from collections.abc import Iterable

# represents a leaf dependency of any type serialized as a set of files
SerializedLeafData = dict[str, bytes]
# represents a set of leaf dependencies of different types
SerializedData = dict[str, SerializedLeafData]
T = TypeVar("T")
InjectableT = TypeVar("InjectableT", bound=Injectable)
SerializeFunction = Callable[[T], SerializedLeafData]
DeserializeFunction = Callable[[type[T], SerializedLeafData], T]


class SerializedDataFileStorage:
    def __init__(self, directory: str | os.PathLike[str]) -> None:
        super().__init__()
        self.directory: Path = Path(directory)

    @staticmethod
    def _split_file_name(file_name: str) -> tuple[str, str]:
        """Extract the type name and the type-specific suffix from a file name.

        >>> SerializedDataFileStorage._split_file_name("TypeName.ext")
        ('TypeName', 'ext')
        >>> SerializedDataFileStorage._split_file_name("Qualified.TypeName.ext")
        ('Qualified.TypeName', 'ext')
        >>> SerializedDataFileStorage._split_file_name("TypeName-component.ext")
        ('TypeName', 'component.ext')
        >>> SerializedDataFileStorage._split_file_name("Qualified.TypeName-component.ext")
        ('Qualified.TypeName', 'component.ext')
        >>> SerializedDataFileStorage._split_file_name("Qualified.TypeName-component-with-dashes.ext")
        ('Qualified.TypeName', 'component-with-dashes.ext')
        """
        if "-" in file_name:
            type_name, suffix = file_name.split("-", 1)
        else:
            type_name, suffix = file_name.rsplit(".", 1)
        return type_name, suffix

    @staticmethod
    def _make_file_name(type_name: str, suffix: str) -> str:
        """Combine the type name and the type-specific suffix into a file name.

        >>> SerializedDataFileStorage._make_file_name('TypeName', 'ext')
        'TypeName.ext'
        >>> SerializedDataFileStorage._make_file_name('Qualified.TypeName', 'ext')
        'Qualified.TypeName.ext'
        >>> SerializedDataFileStorage._make_file_name('TypeName', 'component.ext')
        'TypeName-component.ext'
        >>> SerializedDataFileStorage._make_file_name('Qualified.TypeName', 'component.ext')
        'Qualified.TypeName-component.ext'
        >>> SerializedDataFileStorage._make_file_name('Qualified.TypeName', 'component-with-dashes.ext')
        'Qualified.TypeName-component-with-dashes.ext'
        """
        if "." not in suffix:
            # TypeName.ext
            return type_name + "." + suffix
        # TypeName-component.ext
        return type_name + "-" + suffix

    def read(self) -> SerializedData:  # noqa: D102
        result: SerializedData = {}
        for entry in self.directory.iterdir():
            if not entry.is_file():
                continue
            type_name, suffix = self._split_file_name(entry.name)
            if type_name not in result:
                result[type_name] = {}
            result[type_name][suffix] = entry.read_bytes()
        return result

    def write(self, data: SerializedData) -> None:  # noqa: D102
        for type_name, leaf in data.items():
            for suffix, contents in leaf.items():
                full_name = self._make_file_name(type_name, suffix)
                file_name = Path(self.directory, full_name)
                file_name.write_bytes(contents)


def serialize_leaf(o: Any) -> SerializedLeafData:
    raise NotImplementedError(f"Serialization for {type(o)} is not implemented")


def _deserialize_leaf_base(cls: type[Any], data: SerializedLeafData) -> Any:
    raise NotImplementedError(f"Deserialization for {cls} is not implemented")


serialize_leaf.f_deserialize = _deserialize_leaf_base  # type: ignore[attr-defined]
serialize_leaf = singledispatch(serialize_leaf)


def register_serialization(
    f_serialize: SerializeFunction[T], f_deserialize: DeserializeFunction[T]
) -> None:
    serialize_leaf.register(f_serialize)  # type: ignore[attr-defined]
    f_serialize.f_deserialize = f_deserialize  # type: ignore[attr-defined]


def deserialize_leaf(cls: type[T], data: SerializedLeafData) -> T:
    f_ser: SerializeFunction[T] = serialize_leaf.dispatch(cls)  # type: ignore[attr-defined]
    return cast("T", f_ser.f_deserialize(cls, data))  # type: ignore[attr-defined]


def _get_name_for_class(cls: type) -> str:
    """Return the type name that will be used for serialization.

    For classes available in the web_poet module it's the type name,
    for others it's the fully qualified type name.

    >>> _get_name_for_class(Injectable)
    'Injectable'
    >>> from decimal import Decimal
    >>> _get_name_for_class(Decimal)
    'decimal.Decimal'
    """
    if getattr(web_poet, cls.__name__, None) == cls:
        return cls.__name__
    return get_fq_class_name(cls)


def serialize(deps: Iterable[Any]) -> SerializedData:
    result: SerializedData = {}
    for dep in deps:
        cls = dep.__class__
        if is_injectable(cls):
            raise ValueError(f"Injectable type {cls} passed to serialize()")
        if cls is AnnotatedInstance:
            key = f"AnnotatedInstance {_get_name_for_class(dep.result.__class__)}"
        else:
            key = _get_name_for_class(cls)

        if key in result:
            cls_name = cls.__name__
            if cls is AnnotatedInstance:
                cls_name = f"AnnotatedInstance for {dep.result.__class__.__name__}"
            raise ValueError(
                f"Several instances of {cls_name} were passed to serialize()."
            )
        result[key] = serialize_leaf(dep)
    return result


def load_class(type_name: str) -> type:
    """Return the type by its name.

    Requires the fully qualified name unless the type
    is available in the web_poet module.

    >>> load_class("decimal.Decimal")
    <class 'decimal.Decimal'>
    >>> load_class("web_poet.pages.WebPage")
    <class 'web_poet.pages.WebPage'>
    >>> load_class("WebPage")
    <class 'web_poet.pages.WebPage'>
    >>> load_class("decimal.foo")
    Traceback (most recent call last):
     ...
    ValueError: Unknown type decimal.foo
    >>> load_class("foo.bar")
    Traceback (most recent call last):
     ...
    ValueError: Unable to import module foo
    """
    if "." in type_name:
        module, name = type_name.rsplit(".", 1)
    else:
        module = "web_poet"
        name = type_name
    try:
        mod = import_module(module)
    except ModuleNotFoundError as ex:
        raise ValueError(f"Unable to import module {module}") from ex
    result = getattr(mod, name, None)
    if not result:
        raise ValueError(f"Unknown type {type_name}")
    return cast("type", result)


def deserialize(cls: type[InjectableT], data: SerializedData) -> InjectableT:
    deps: dict[Callable, Any] = {}

    for dep_type_name, dep_data in data.items():
        if dep_type_name.startswith("AnnotatedInstance "):
            annotated_result = deserialize_leaf(AnnotatedInstance, dep_data)
            dep_type = annotated_result.get_annotated_cls()
            deserialized_dep = annotated_result.result
        else:
            dep_type = load_class(dep_type_name)
            deserialized_dep = deserialize_leaf(dep_type, dep_data)
        deps[dep_type] = deserialized_dep

    externally_provided = {strip_annotated(cls) for cls in deps}
    plan = andi.plan(
        cls, is_injectable=is_injectable, externally_provided=externally_provided
    )
    for fn_or_cls, kwargs_spec in plan[:-1]:
        if strip_annotated(fn_or_cls) in externally_provided:
            continue
        deps[strip_annotated(fn_or_cls)] = fn_or_cls(**kwargs_spec.kwargs(deps))
    return cls(**plan.final_kwargs(deps))
