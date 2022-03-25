"""This POP simply wants to repackage POP "A" and "B" into one unifying package."""

from web_poet import PageObjectRegistry

from . import improved_A_package
from . import base_B_package

rules_A_improved = improved_A_package.REGISTRY.search_overrides(
    use=improved_A_package.site_1.A_Improved_Site1  # type:ignore
)
rules_B = base_B_package.REGISTRY.search_overrides(
    use=base_B_package.site_3.B_Site3  # type: ignore
)

combined_rules = rules_A_improved + rules_B
REGISTRY = PageObjectRegistry.from_override_rules(combined_rules)
