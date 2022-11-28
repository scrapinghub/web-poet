import os
from functools import singledispatch
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

T = TypeVar("T")
SerializedData = Dict[str, Union[bytes, "SerializedData"]]
SerializeFunction = Callable[[Any], SerializedData]
DeserializeFunction = Callable[[Type[T], SerializedData], T]


def read_serialized_data(directory: Union[str, os.PathLike]) -> SerializedData:
    result: SerializedData = {}
    directory = Path(directory)
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        *keys, ext = entry.name.split(".")
        node = result
        for key in keys:
            if key not in node:
                node[key] = {}
            node = node[key]
        node[ext] = entry.read_bytes()
    return result


def write_serialized_data(
    data: SerializedData,
    directory: Union[str, os.PathLike],
    prefix: Optional[str] = None,
) -> None:
    for k, v in data.items():
        new_prefix = prefix + "." + k if prefix else k
        if isinstance(v, bytes):
            file_name = Path(directory, new_prefix)
            file_name.write_bytes(v)
        elif isinstance(v, dict):
            write_serialized_data(v, directory, new_prefix)


def serialize(o: Any) -> SerializedData:
    raise NotImplementedError(f"Serialization for {type(o)} is not implemented")


def _deserialize_base(t: Type[Any], data: SerializedData) -> Any:
    raise NotImplementedError(f"Deserialization for {t} is not implemented")


serialize.f_deserialize = _deserialize_base
serialize = singledispatch(serialize)


def register_serialization(
    f_serialize: SerializeFunction, f_deserialize: DeserializeFunction
) -> None:
    serialize.register(f_serialize)
    f_serialize.f_deserialize = f_deserialize


def deserialize(t: Type[T], data: SerializedData) -> T:
    f_ser: SerializeFunction = serialize.dispatch(t)
    return f_ser.f_deserialize(t, data)


def get_bytes(d: dict, key: str) -> bytes:
    if key not in d:
        raise ValueError(f"Expected key {key} not found")
    value = d[key]
    if not isinstance(value, bytes):
        raise ValueError(f"Expected key {key} contains {type(value)} instead of bytes.")
    return value
