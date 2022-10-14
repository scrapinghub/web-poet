"""Utilities for typing"""
import typing

if hasattr(typing, "get_args"):
    _get_args = typing.get_args
else:

    def _get_args(base):
        return getattr(base, "__args__", ())


def is_generic_alias(obj) -> bool:
    for attr_name in ["GenericAlias", "_GenericAlias"]:
        if hasattr(typing, attr_name):
            if isinstance(obj, getattr(typing, attr_name)):
                return True
    return False


def get_generic_parameter(cls):
    for base in getattr(cls, "__orig_bases__", []):
        if is_generic_alias(base):
            args = _get_args(base)
            return args[0]


def get_item_cls(cls, default=None):
    param = get_generic_parameter(cls)
    if param is None or isinstance(param, typing.TypeVar):  # class is not parametrized
        return default
    return param
