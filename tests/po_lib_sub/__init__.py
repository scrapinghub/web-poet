"""This package is being used by tests/po_lib to validate some behaviors on
external depedencies.
"""
from typing import Dict, Any, Callable

from url_matcher import Patterns

from web_poet import handle_urls


class POBase:
    expected_overrides: Callable
    expected_patterns: Patterns
    expected_meta: Dict[str, Any]


class POLibSubOverriden:
    ...


@handle_urls("sub_example.com", overrides=POLibSubOverriden)
class POLibSub(POBase):
    expected_overrides = POLibSubOverriden
    expected_patterns = Patterns(["sub_example.com"])
    expected_meta = {}  # type: ignore
