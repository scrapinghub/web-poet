"""
This package quite is similar to tests/po_lib_sub in terms of code contents.

What we're ultimately trying to test here is to see if the `default_registry`
captures the rules annotated in this module if it was not imported.
"""
from typing import Dict, Any, Callable

from url_matcher import Patterns

from web_poet import handle_urls


class POBase:
    expected_overrides: Callable
    expected_patterns: Patterns
    expected_meta: Dict[str, Any]


class POLibSubOverridenNotImported:
    ...


@handle_urls("sub_example_not_imported.com", overrides=POLibSubOverridenNotImported)
class POLibSubNotImported(POBase):
    expected_overrides = POLibSubOverridenNotImported
    expected_patterns = Patterns(["sub_example_not_imported.com"])
    expected_meta = {}  # type: ignore
