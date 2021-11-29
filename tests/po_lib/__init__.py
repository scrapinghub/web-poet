from url_matcher import Patterns

from web_poet.meta import handle_urls


class POTopLevelOverriden1:
    ...


class POTopLevelOverriden2:
    ...


# This first annotation is ignored. A single annotation per namespace per class is allowed
@handle_urls("example.com", POTopLevelOverriden1)
@handle_urls("example.com", POTopLevelOverriden1, exclude="/*.jpg|", priority=300)
class POTopLevel1:
    expected_overrides = POTopLevelOverriden1
    expected_patterns = Patterns(["example.com"], ["/*.jpg|"], priority=300)


# The second annotation is for a different namespace
@handle_urls("example.com", POTopLevelOverriden2)
@handle_urls("example.org", POTopLevelOverriden2, namespace="secondary")
class POTopLevel2:
    expected_overrides = POTopLevelOverriden2
    expected_patterns = Patterns(["example.com"])
