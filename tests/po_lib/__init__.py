"""
This package is just for overrides testing purposes.
"""
from typing import Dict, Any, Callable

from url_matcher import Patterns

from .. import po_lib_sub # NOTE: this module contains a PO with @handle_rules
from web_poet import handle_urls, PageObjectRegistry


class POBase:
    expected_overrides: Callable
    expected_patterns: Patterns
    expected_meta: Dict[str, Any]


class POTopLevelOverriden1:
    ...


class POTopLevelOverriden2:
    ...


secondary_registry = PageObjectRegistry(name="secondary")


# This first annotation is ignored. A single annotation per registry is allowed
@handle_urls("example.com", POTopLevelOverriden1)
@handle_urls("example.com", POTopLevelOverriden1, exclude="/*.jpg|", priority=300)
class POTopLevel1(POBase):
    expected_overrides = POTopLevelOverriden1
    expected_patterns = Patterns(["example.com"], ["/*.jpg|"], priority=300)
    expected_meta = {}  # type: ignore


# The second annotation is for a different registry
@handle_urls("example.com", POTopLevelOverriden2)
@secondary_registry.handle_urls("example.org", POTopLevelOverriden2)
class POTopLevel2(POBase):
    expected_overrides = POTopLevelOverriden2
    expected_patterns = Patterns(["example.com"])
    expected_meta = {}  # type: ignore
