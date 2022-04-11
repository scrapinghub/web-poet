import pytest
from url_matcher import Patterns

from tests.po_lib_sub import POLibSub
from tests.po_lib import (
    POTopLevel1,
    POTopLevel2,
    POTopLevelOverriden2,
)
from tests.po_lib.a_module import POModule, POModuleOverriden
from tests.po_lib.nested_package import PONestedPkg
from tests.po_lib.nested_package.a_nested_module import PONestedModule
from web_poet import (
    default_registry,
    consume_modules,
    OverrideRule,
    PageObjectRegistry,
)


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
        meta={"key_1": 1},
    )
    rule2 = OverrideRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
        meta={"key_2": 2},
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


def test_consume_module_not_existing():
    with pytest.raises(ImportError):
        consume_modules("this_does_not_exist")


def test_list_page_objects_all_consume():
    """A test similar to the one above but calls ``consume_modules()`` to properly
    load the @handle_urls annotations from other modules/packages.
    """
    consume_modules("tests_extra")
    rules = default_registry.get_overrides()
    page_objects = {po.use for po in rules}
    assert any(["po_lib_sub_not_imported" in po.__module__ for po in page_objects])


def test_registry_search_overrides():
    rules = default_registry.search_overrides(use=POTopLevel2)
    assert len(rules) == 1
    assert rules[0].use == POTopLevel2

    rules = default_registry.search_overrides(instead_of=POTopLevelOverriden2)
    assert len(rules) == 1
    assert rules[0].instead_of == POTopLevelOverriden2

    # Such rules doesn't exist
    rules = default_registry.search_overrides(use=POModuleOverriden)
    assert len(rules) == 0


def test_from_override_rules():
    rules = [
        OverrideRule(
            for_patterns=Patterns(include=["sample.com"]),
            use=POTopLevel1,
            instead_of=POTopLevelOverriden2,
        )
    ]

    registry = PageObjectRegistry.from_override_rules(rules)

    assert registry.get_overrides() == rules
    assert default_registry.get_overrides() != rules
