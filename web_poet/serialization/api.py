import os
from functools import singledispatch
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Type, TypeVar, Union

import andi

from web_poet import Injectable
from web_poet.pages import is_injectable

# represents a leaf dependency of any type serialized as a set of files
SerializedLeafData = Dict[str, bytes]
# represents a set of leaf dependencies of different types
SerializedData = Dict[str, SerializedLeafData]
T = TypeVar("T")
InjectableT = TypeVar("InjectableT", bound=Injectable)
SerializeFunction = Callable[[Any], SerializedLeafData]
DeserializeFunction = Callable[[Type[T], SerializedLeafData], T]


def _split_file_name(file_name: str) -> Tuple[str, str]:
    """Extract the type name and the type-specific suffix from a file name.

    >>> _split_file_name("TypeName.ext")
    ('TypeName', 'ext')
    >>> _split_file_name("Qualified.TypeName.ext")
    ('Qualified.TypeName', 'ext')
    >>> _split_file_name("TypeName-component.ext")
    ('TypeName', 'component.ext')
    >>> _split_file_name("Qualified.TypeName-component.ext")
    ('Qualified.TypeName', 'component.ext')
    >>> _split_file_name("Qualified.TypeName-component-with-dashes.ext")
    ('Qualified.TypeName', 'component-with-dashes.ext')
    """
    if "-" in file_name:
        type_name, suffix = file_name.split("-", 1)
    else:
        type_name, suffix = file_name.rsplit(".", 1)
    return type_name, suffix


def read_serialized_data(directory: Union[str, os.PathLike]) -> SerializedData:
    result: SerializedData = {}
    directory = Path(directory)
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        type_name, suffix = _split_file_name(entry.name)
        if type_name not in result:
            result[type_name] = {}
        result[type_name][suffix] = entry.read_bytes()
    return result


def _make_file_name(type_name: str, suffix: str) -> str:
    """Combine the type name and the type-specific suffix into a file name.

    >>> _make_file_name('TypeName', 'ext')
    'TypeName.ext'
    >>> _make_file_name('Qualified.TypeName', 'ext')
    'Qualified.TypeName.ext'
    >>> _make_file_name('TypeName', 'component.ext')
    'TypeName-component.ext'
    >>> _make_file_name('Qualified.TypeName', 'component.ext')
    'Qualified.TypeName-component.ext'
    >>> _make_file_name('Qualified.TypeName', 'component-with-dashes.ext')
    'Qualified.TypeName-component-with-dashes.ext'
    """
    if "." not in suffix:
        # TypeName.ext
        return type_name + "." + suffix
    else:
        # TypeName-component.ext
        return type_name + "-" + suffix


def write_serialized_data(
    data: SerializedData, directory: Union[str, os.PathLike]
) -> None:
    for type_name, leaf in data.items():
        for suffix, contents in leaf.items():
            full_name = _make_file_name(type_name, suffix)
            file_name = Path(directory, full_name)
            file_name.write_bytes(contents)


def serialize_leaf(o: Any) -> SerializedLeafData:
    raise NotImplementedError(f"Serialization for {type(o)} is not implemented")


def _deserialize_leaf_base(cls: Type[Any], data: SerializedLeafData) -> Any:
    raise NotImplementedError(f"Deserialization for {cls} is not implemented")


serialize_leaf.f_deserialize = _deserialize_leaf_base  # type: ignore[attr-defined]
serialize_leaf = singledispatch(serialize_leaf)


def register_serialization(
    f_serialize: SerializeFunction, f_deserialize: DeserializeFunction
) -> None:
    serialize_leaf.register(f_serialize)  # type: ignore[attr-defined]
    f_serialize.f_deserialize = f_deserialize  # type: ignore[attr-defined]


def deserialize_leaf(cls: Type[T], data: SerializedLeafData) -> T:
    f_ser: SerializeFunction = serialize_leaf.dispatch(cls)  # type: ignore[attr-defined]
    return f_ser.f_deserialize(cls, data)  # type: ignore[attr-defined]


def _get_fqname(cls: type) -> str:
    """Return the fully qualified name for a type.

    >>> _get_fqname(Injectable)
    'web_poet.pages.Injectable'
    """
    return f"{cls.__module__}.{cls.__qualname__}"


def serialize(deps: List[Any]) -> SerializedData:
    result: SerializedData = {}
    for dep in deps:
        cls = dep.__class__
        if is_injectable(cls):
            raise ValueError(f"Injectable type {cls} passed to serialize()")
        result[_get_fqname(cls)] = serialize_leaf(dep)
    return result


def _load_type(type_name: str) -> type:
    """Return the type by its fully qualified name.

    >>> _load_type("decimal.Decimal")
    <class 'decimal.Decimal'>
    >>> _load_type("web_poet.pages.WebPage")
    <class 'web_poet.pages.WebPage'>
    >>> _load_type("decimal.foo")
    Traceback (most recent call last):
     ...
    ValueError: Unknown type decimal.foo
    >>> _load_type("foo.bar")
    Traceback (most recent call last):
     ...
    ValueError: Unable to import module foo
    """
    module, name = type_name.rsplit(".", 1)
    try:
        mod = import_module(module)
    except ModuleNotFoundError:
        raise ValueError(f"Unable to import module {module}")
    result = getattr(mod, name, None)
    if not result:
        raise ValueError(f"Unknown type {type_name}")
    return result


def deserialize(cls: Type[InjectableT], data: SerializedData) -> InjectableT:
    deps: Dict[Callable, Any] = {}

    for dep_type_name, dep_data in data.items():
        dep_type = _load_type(dep_type_name)
        deps[dep_type] = deserialize_leaf(dep_type, dep_data)

    plan = andi.plan(cls, is_injectable=is_injectable, externally_provided=deps.keys())
    return cls(**plan.final_kwargs(deps))
