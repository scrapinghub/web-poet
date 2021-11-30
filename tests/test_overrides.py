import pytest
from url_matcher import Patterns

from tests.po_lib import POTopLevel1, POTopLevel2, POTopLevelOverriden2
from tests.po_lib.a_module import POModule
from tests.po_lib.nested_package import PONestedPkg
from tests.po_lib.nested_package.a_nested_module import PONestedModule, PONestedModuleOverridenSecondary
from web_poet.overrides import find_page_object_overrides


POS = {POTopLevel1, POTopLevel2, POModule, PONestedPkg, PONestedModule}


def test_list_page_objects_from_pkg():
    """Tests that metadata is extracted properly from the po_lib package"""
    rules = find_page_object_overrides("tests.po_lib")
    assert {po.use for po in rules} == POS

    for rule in rules:
        assert rule.instead_of == rule.use.expected_overrides, rule.use
        assert rule.for_patterns == rule.use.expected_patterns, rule.use
        assert rule.meta == rule.use.expected_meta, rule.use


def test_list_page_objects_from_module():
    rules = find_page_object_overrides("tests.po_lib.a_module")
    assert len(rules) == 1
    rule = rules[0]
    assert rule.use == POModule
    assert rule.for_patterns == POModule.expected_patterns
    assert rule.instead_of == POModule.expected_overrides


def test_list_page_objects_from_empty_module():
    rules = find_page_object_overrides("tests.po_lib.an_empty_module")
    assert len(rules) == 0


def test_list_page_objects_from_empty_pkg():
    rules = find_page_object_overrides("tests.po_lib.an_empty_package")
    assert len(rules) == 0


def test_list_page_objects_from_unknown_module():
    with pytest.raises(ImportError):
        find_page_object_overrides("tests.po_lib.unknown_module")


def test_list_page_objects_from_namespace():
    rules = find_page_object_overrides("tests.po_lib", namespace="secondary")
    assert len(rules) == 2
    rule_for = {po.use: po for po in rules}

    potop2 = rule_for[POTopLevel2]
    assert potop2.for_patterns == Patterns(["example.org"])
    assert potop2.instead_of == POTopLevelOverriden2

    pones = rule_for[PONestedModule]
    assert pones.for_patterns == Patterns(["example.com"])
    assert pones.instead_of == PONestedModuleOverridenSecondary


def test_list_page_objects_from_empty_namespace():
    assert find_page_object_overrides("tests.po_lib", namespace="foo") == []


def test_cmd():
    from  web_poet.__main__ import main
    main(["tests.po_lib"])