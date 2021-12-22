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


class POSubLibOverriden:
    ...


@handle_urls("sub_example.com", POSubLibOverriden)
class POSubLib(POBase):
    expected_overrides = POSubLibOverriden
    expected_patterns = Patterns(["sub_example.com"])
    expected_meta = {}  # type: ignore
