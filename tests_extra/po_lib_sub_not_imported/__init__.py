"""
This package quite is similar to tests/po_lib_sub in terms of code contents.

What we're ultimately trying to test here is to see if the `default_registry`
captures the rules annotated in this module if it was not imported.
"""

from __future__ import annotations

from typing import Any

from url_matcher import Patterns

from web_poet import ItemPage, handle_urls


class POBase:
    expected_instead_of: type[ItemPage]
    expected_patterns: Patterns
    expected_meta: dict[str, Any]


class POLibSubOverridenNotImported: ...


@handle_urls("sub_not_imported.example", instead_of=POLibSubOverridenNotImported)
class POLibSubNotImported(POBase):
    expected_instead_of = POLibSubOverridenNotImported
    expected_patterns = Patterns(["sub_not_imported.example"])
    expected_to_return = None
    expected_meta = {}
