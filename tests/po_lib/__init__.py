"""
This package is just for overrides testing purposes.
"""
from typing import Any, Dict, List, Type, Union

from url_matcher import Patterns

from web_poet import ItemPage, handle_urls

# NOTE: this module contains a PO with @handle_rules
from .. import po_lib_sub  # noqa: F401


class POBase(ItemPage):
    expected_instead_of: Union[Type[ItemPage], List[Type[ItemPage]]]
    expected_patterns: Patterns
    expected_to_return: Any = None
    expected_meta: Dict[str, Any]


class POTopLevelOverriden1(ItemPage):
    ...


class POTopLevelOverriden2(ItemPage):
    ...


@handle_urls("example.com", instead_of=POTopLevelOverriden1)
@handle_urls(
    "example.com", instead_of=POTopLevelOverriden1, exclude="/*.jpg|", priority=300
)
class POTopLevel1(POBase):
    expected_instead_of = [POTopLevelOverriden1, POTopLevelOverriden1]
    expected_patterns = [
        Patterns(["example.com"], ["/*.jpg|"], priority=300),
        Patterns(["example.com"]),
    ]
    expected_to_return = [None, None]
    expected_meta = [{}, {}]  # type: ignore


@handle_urls("example.com", instead_of=POTopLevelOverriden2)
class POTopLevel2(POBase):
    expected_instead_of = POTopLevelOverriden2
    expected_patterns = Patterns(["example.com"])
    expected_to_return = None
    expected_meta = {}  # type: ignore
