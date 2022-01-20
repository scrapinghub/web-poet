import argparse
import dataclasses

import pytest
from url_matcher import Patterns

from tests.po_lib_sub import POLibSub
from tests.po_lib import (
    POTopLevel1,
    POTopLevel2,
    POTopLevelOverriden2,
    secondary_registry,
)
from tests.po_lib.a_module import POModule
from tests.po_lib.nested_package import PONestedPkg
from tests.po_lib.nested_package.a_nested_module import (
    PONestedModule,
    PONestedModuleOverridenSecondary,
)
from web_poet import PageObjectRegistry, default_registry, registry_pool
from web_poet.overrides import OverrideRule


POS = {POTopLevel1, POTopLevel2, POModule, PONestedPkg, PONestedModule}


def test_override_rule_uniqueness():
    """The same instance of an OverrideRule with the same attribute values should
    have the same hash identity.
    """

    patterns = Patterns(include=["example.com"], exclude=["example.com/blog"])

    rule1 = OverrideRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
        meta={"key_1": 1}
    )
    rule2 = OverrideRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
        meta={"key_2": 2}
    )

    assert hash(rule1) == hash(rule2)


def test_list_page_objects_all():
    rules = default_registry.get_overrides()
    page_objects = {po.use for po in rules}

    # Note that the 'tests_extra.po_lib_sub_not_imported.POLibSubNotImported'
    # Page Object is not included here since it was never imported anywhere in
    # our test package. It would only be included if we run any of the following
    # below. (Note that they should run before `get_overrides` is called.)
    #   - from tests_extra import po_lib_sub_not_imported
    #   - import tests_extra.po_lib_sub_not_imported
    #   - web_poet.consume_modules("tests_extra")
    # Merely having `import tests_extra` won't work since the subpackages and
    # modules needs to be traversed and imported as well.
    assert all(["po_lib_sub_not_imported" not in po.__module__ for po in page_objects])

    # Ensure that ALL Override Rules are returned as long as the given
    # registry's @handle_urls annotation was used.
    assert page_objects == POS.union({POLibSub})
    for rule in rules:
        assert rule.instead_of == rule.use.expected_overrides, rule.use
        assert rule.for_patterns == rule.use.expected_patterns, rule.use
        assert rule.meta == rule.use.expected_meta, rule.use


def test_list_page_objects_all_consume():
    """A test similar to the one above but calls ``consume_modules()`` to properly
    load the @handle_urls annotations from other modules/packages.
    """
    rules = default_registry.get_overrides(consume="tests_extra")
    page_objects = {po.use for po in rules}
    assert any(["po_lib_sub_not_imported" in po.__module__ for po in page_objects])


def test_list_page_objects_from_pkg():
    """Tests that metadata is extracted properly from the po_lib package"""
    rules = default_registry.get_overrides(filters="tests.po_lib")
    page_objects = {po.use for po in rules}

    # Ensure that the "tests.po_lib", which imports another module named
    # "tests.po_lib_sub" which contains @handle_urls decorators, does not
    # retrieve the override rules from the external package.
    assert POLibSub not in page_objects

    assert page_objects == POS
    for rule in rules:
        assert rule.instead_of == rule.use.expected_overrides, rule.use
        assert rule.for_patterns == rule.use.expected_patterns, rule.use
        assert rule.meta == rule.use.expected_meta, rule.use


def test_list_page_objects_from_single():
    rules = default_registry.get_overrides(filters="tests.po_lib.a_module")
    assert len(rules) == 1
    rule = rules[0]
    assert rule.use == POModule
    assert rule.for_patterns == POModule.expected_patterns
    assert rule.instead_of == POModule.expected_overrides


def test_list_page_objects_from_multiple():
    rules = default_registry.get_overrides(
        filters=[
            "tests.po_lib.a_module",
            "tests.po_lib.nested_package.a_nested_module",
        ]
    )
    assert len(rules) == 2

    assert rules[0].use == POModule
    assert rules[0].for_patterns == POModule.expected_patterns
    assert rules[0].instead_of == POModule.expected_overrides

    assert rules[1].use == PONestedModule
    assert rules[1].for_patterns == PONestedModule.expected_patterns
    assert rules[1].instead_of == PONestedModule.expected_overrides


def test_list_page_objects_from_empty_module():
    rules = default_registry.get_overrides(filters="tests.po_lib.an_empty_module")
    assert len(rules) == 0


def test_list_page_objects_from_empty_pkg():
    rules = default_registry.get_overrides(filters="tests.po_lib.an_empty_package")
    assert len(rules) == 0


def test_list_page_objects_from_unknown_module():
    with pytest.raises(ImportError):
        default_registry.get_overrides(filters="tests.po_lib.unknown_module")


def test_list_page_objects_from_imported_registry():
    rules = secondary_registry.get_overrides(filters="tests.po_lib")
    assert len(rules) == 2
    rule_for = {po.use: po for po in rules}

    potop2 = rule_for[POTopLevel2]
    assert potop2.for_patterns == Patterns(["example.org"])
    assert potop2.instead_of == POTopLevelOverriden2

    pones = rule_for[PONestedModule]
    assert pones.for_patterns == Patterns(["example.com"])
    assert pones.instead_of == PONestedModuleOverridenSecondary


def test_registry_name_conflict():
    """Registries can only have valid unique names."""

    PageObjectRegistry("main")

    assert "main" in registry_pool

    with pytest.raises(ValueError):
        PageObjectRegistry("main")  # a duplicate name

    with pytest.raises(TypeError):
        PageObjectRegistry()

    with pytest.raises(ValueError):
        PageObjectRegistry("")


def test_registry_copy_overrides_from():
    combined_registry = PageObjectRegistry("combined")
    combined_registry.copy_overrides_from(default_registry, secondary_registry)

    # Copying overrides from other PageObjectRegistries should have duplicate
    # OverrideRules removed.
    combined_rule_count = combined_registry.get_overrides()
    assert len(combined_rule_count) == 7

    raw_count = len(default_registry.get_overrides()) + len(secondary_registry.get_overrides())
    assert len(combined_rule_count) < raw_count

    # Copying overrides again does not result in duplicates
    combined_registry.copy_overrides_from(default_registry, secondary_registry)
    combined_registry.copy_overrides_from(default_registry, secondary_registry)
    combined_registry.copy_overrides_from(default_registry, secondary_registry)
    assert len(combined_rule_count) == 7


def test_registry_replace_override():
    registry = PageObjectRegistry("replace")
    registry.copy_overrides_from(secondary_registry)
    rules = registry.get_overrides()

    replacement_rule = registry.replace_override(rules[0], instead_of=POTopLevel1)

    new_rules = registry.get_overrides()
    assert len(new_rules) == 2
    assert new_rules[-1].instead_of == POTopLevel1  # newly replace rules at the bottom
    assert replacement_rule.instead_of == POTopLevel1  # newly replace rules at the bottom

    # Replacing a rule not in the registry would result in ValueError
    rule_not_in_registry = dataclasses.replace(new_rules[0], instead_of=POTopLevelOverriden2)
    with pytest.raises(ValueError):
        registry.replace_override(rule_not_in_registry, instead_of=POTopLevel2)


def test_registry_search_overrides():
    registry = PageObjectRegistry("search")
    registry.copy_overrides_from(secondary_registry)

    rules = registry.search_overrides(use=POTopLevel2)
    assert len(rules) == 1
    assert rules[0].use == POTopLevel2

    rules = registry.search_overrides(instead_of=POTopLevelOverriden2)
    assert len(rules) == 1
    assert rules[0].instead_of == POTopLevelOverriden2

    rules = registry.search_overrides(
        instead_of=PONestedModuleOverridenSecondary, use=PONestedModule
    )
    assert len(rules) == 1
    assert rules[0].instead_of == PONestedModuleOverridenSecondary
    assert rules[0].use == PONestedModule

    # These rules doesn't exist
    rules = registry.search_overrides(use=POTopLevel1)
    assert len(rules) == 0

    rules = registry.search_overrides(instead_of=POTopLevel1)
    assert len(rules) == 0


def test_registry_remove_overrides():
    registry = PageObjectRegistry("remove")
    registry.copy_overrides_from(secondary_registry)

    rules = registry.get_overrides()

    registry.remove_overrides(*rules)
    assert len(registry.get_overrides()) == 0

    # Removing non-existing rules won't error out.
    registry.remove_overrides(*rules)
    assert len(registry.get_overrides()) == 0


def test_cli_tool():
    """Ensure that CLI parameters returns the expected results.

    There's no need to check each specific OverrideRule below as we already have
    extensive tests for those above. We can simply count how many rules there are
    for a given registry.
    """

    from web_poet.__main__ import main

    results = main(["tests"])
    assert len(results) == 6

    results = main(["tests", "--registry_name=secondary"])
    assert len(results) == 2

    results = main(["tests", "--registry_name=not_exist"])
    assert not results
