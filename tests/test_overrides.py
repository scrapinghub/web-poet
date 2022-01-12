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
from web_poet.overrides import PageObjectRegistry, default_registry


POS = {POTopLevel1, POTopLevel2, POModule, PONestedPkg, PONestedModule}


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


def test_registry_data_from():
    data = default_registry.data_from("tests.po_lib.nested_package")

    assert len(data) == 2
    assert PONestedModule in data
    assert PONestedPkg in data


def test_cmd():
    from web_poet.__main__ import main

    assert main(["tests.po_lib"]) is None
