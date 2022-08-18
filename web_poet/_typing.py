"""Utilities for typing"""
import typing


def is_generic_alias(obj) -> bool:
    for attr_name in ["GenericAlias", "_GenericAlias"]:
        if hasattr(typing, attr_name):
            if isinstance(obj, getattr(typing, attr_name)):
                return True
    return False


def get_generic_parameter(cls):
    for base in cls.__orig_bases__:
        if is_generic_alias(base):
            args = typing.get_args(base)
            return args[0]
