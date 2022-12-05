import os
from functools import singledispatch
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

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


def read_serialized_data(directory: Union[str, os.PathLike]) -> SerializedData:
    result: SerializedData = {}
    directory = Path(directory)
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        if "-" in entry.name:
            prefix, name = entry.name.split("-", 1)
        else:
            prefix, name = entry.name.rsplit(".", 1)
        if prefix not in result:
            result[prefix] = {}
        result[prefix][name] = entry.read_bytes()
    return result


def write_serialized_data(
    data: SerializedData, directory: Union[str, os.PathLike]
) -> None:
    for prefix, leaf in data.items():
        for name, contents in leaf.items():
            if "." not in name:
                # TypeName.ext
                full_name = prefix + "." + name
            else:
                # TypeName-component.ext
                full_name = prefix + "-" + name
            file_name = Path(directory, full_name)
            file_name.write_bytes(contents)


def serialize_leaf(o: Any) -> SerializedLeafData:
    raise NotImplementedError(f"Serialization for {type(o)} is not implemented")


def _deserialize_leaf_base(t: Type[Any], data: SerializedLeafData) -> Any:
    raise NotImplementedError(f"Deserialization for {t} is not implemented")


serialize_leaf.f_deserialize = _deserialize_leaf_base
serialize_leaf = singledispatch(serialize_leaf)


def register_serialization(
    f_serialize: SerializeFunction, f_deserialize: DeserializeFunction
) -> None:
    serialize_leaf.register(f_serialize)
    f_serialize.f_deserialize = f_deserialize


def deserialize_leaf(t: Type[T], data: SerializedLeafData) -> T:
    f_ser: SerializeFunction = serialize_leaf.dispatch(t)
    return f_ser.f_deserialize(t, data)


def _get_fqname(t: type) -> str:
    return f"{t.__module__}.{t.__qualname__}"


def serialize(deps: List[Any]) -> SerializedData:
    # we skip injectable classes though the interface should probably not accept them at all
    return {
        _get_fqname(dep.__class__): serialize_leaf(dep)
        for dep in deps
        if not is_injectable(dep.__class__)
    }


def _load_type(type_name: str) -> Optional[type]:
    module, name = type_name.rsplit(".", 1)
    mod = import_module(module)
    return getattr(mod, name, None)


def deserialize(t: Type[InjectableT], data: SerializedData) -> InjectableT:
    deps: Dict[type, Any] = {}

    for dep_type_name, dep_data in data.items():
        dep_type = _load_type(dep_type_name)
        if dep_type is None:
            raise ValueError(f"Unknown serialized type {dep_type_name}")
        deps[dep_type] = deserialize_leaf(dep_type, dep_data)

    plan = andi.plan(t, is_injectable=is_injectable, externally_provided=deps.keys())
    return t(**plan.final_kwargs(deps))
