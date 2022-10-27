"""This package is being used by tests/po_lib to validate some behaviors on
external depedencies.
"""
from typing import Any, Dict, Type

from url_matcher import Patterns

from web_poet import ItemPage, handle_urls


class POBase(ItemPage):
    expected_instead_of: Type[ItemPage]
    expected_patterns: Patterns
    expected_meta: Dict[str, Any]


class POLibSubOverriden(ItemPage):
    ...


@handle_urls("sub.example", instead_of=POLibSubOverriden)
class POLibSub(POBase):
    expected_instead_of = POLibSubOverriden
    expected_patterns = Patterns(["sub.example"])
    expected_to_return = None
    expected_meta = {}  # type: ignore
