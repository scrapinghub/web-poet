import warnings

import pytest
from url_matcher import Patterns

from tests.po_lib import POTopLevel1, POTopLevel2, POTopLevelOverriden2
from tests.po_lib.a_module import POModule, POModuleOverriden
from tests.po_lib.nested_package import PONestedPkg
from tests.po_lib.nested_package.a_nested_module import PONestedModule
from tests.po_lib_sub import POLibSub
from tests.po_lib_to_return import (
    CustomProductPage,
    CustomProductPageDataTypeOnly,
    CustomProductPageNoReturns,
    ImprovedProductPage,
    LessProductPage,
    MoreProductPage,
    Product,
    ProductPage,
    ProductSimilar,
    SimilarProductPage,
)
from web_poet import (
    ApplyRule,
    OverrideRule,
    PageObjectRegistry,
    consume_modules,
    default_registry,
    handle_urls,
)

POS = {
    POTopLevel1,
    POTopLevel2,
    POModule,
    PONestedPkg,
    PONestedModule,
    ProductPage,
    ImprovedProductPage,
    SimilarProductPage,
    MoreProductPage,
    LessProductPage,
    CustomProductPage,
    CustomProductPageNoReturns,
    CustomProductPageDataTypeOnly,
}


def test_apply_rule_uniqueness() -> None:
    """The same instance of an ApplyRule with the same attribute values should
    have the same hash identity.
    """

    patterns = Patterns(include=["example.com"], exclude=["example.com/blog"])

    rule1 = ApplyRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
        meta={"key_1": 1},
    )
    rule2 = ApplyRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
        meta={"key_2": 2},
    )
    # The ``meta`` parameter is ignored in the hash.
    assert hash(rule1) == hash(rule2)

    rule1 = ApplyRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
        to_return=Product,
    )
    rule2 = ApplyRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
        to_return=ProductSimilar,
    )
    # A different data type class results in different hash.
    assert hash(rule1) != hash(rule2)


def test_list_page_objects_all() -> None:
    rules = default_registry.get_rules()
    page_objects = {po.use for po in rules}

    # Note that the 'tests_extra.po_lib_sub_not_imported.POLibSubNotImported'
    # Page Object is not included here since it was never imported anywhere in
    # our test package. It would only be included if we run any of the following
    # below. (Note that they should run before `get_rules` is called.)
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
        # We're ignoring the types below since mypy expects ``Type[ItemPage]``
        # which doesn't contain the ``expected_*`` fields in our tests.
        assert rule.instead_of == rule.use.expected_instead_of, rule.use  # type: ignore[attr-defined]
        assert rule.for_patterns == rule.use.expected_patterns, rule.use  # type: ignore[attr-defined]
        assert rule.to_return == rule.use.expected_to_return, rule.use  # type: ignore[attr-defined]
        assert rule.meta == rule.use.expected_meta, rule.use  # type: ignore[attr-defined]


def test_registry_get_overrides_deprecation() -> None:
    msg = "The 'get_overrides' method is deprecated. Use 'get_rules' instead."
    with pytest.warns(DeprecationWarning, match=msg):
        rules = default_registry.get_overrides()

    # It should still work as usual
    assert len(rules) == 14


def test_consume_module_not_existing() -> None:
    with pytest.raises(ImportError):
        consume_modules("this_does_not_exist")


def test_list_page_objects_all_consume() -> None:
    """A test similar to the one above but calls ``consume_modules()`` to properly
    load the @handle_urls annotations from other modules/packages.
    """
    consume_modules("tests_extra")
    rules = default_registry.get_rules()
    page_objects = {po.use for po in rules}
    assert any(["po_lib_sub_not_imported" in po.__module__ for po in page_objects])


def test_registry_search_rules() -> None:
    rules = default_registry.search_rules(use=POTopLevel2)
    assert len(rules) == 1
    assert rules[0].use == POTopLevel2

    rules = default_registry.search_rules(instead_of=POTopLevelOverriden2)
    assert len(rules) == 1
    assert rules[0].instead_of == POTopLevelOverriden2

    # Such rules doesn't exist
    rules = default_registry.search_rules(use=POModuleOverriden)
    assert len(rules) == 0


def test_registry_search_overrides_deprecation() -> None:
    msg = "The 'search_overrides' method is deprecated. Use 'search_rules' instead."
    with pytest.warns(DeprecationWarning, match=msg):
        rules = default_registry.search_overrides(use=POTopLevel2)

    # It should still work as usual
    assert len(rules) == 1
    assert rules[0].use == POTopLevel2


def test_from_apply_rules() -> None:
    rules = [
        ApplyRule(
            for_patterns=Patterns(include=["sample.com"]),
            use=POTopLevel1,
            instead_of=POTopLevelOverriden2,
        )
    ]

    registry = PageObjectRegistry.from_apply_rules(rules)

    assert registry.get_rules() == rules
    assert default_registry.get_rules() != rules


def test_from_override_rules_deprecation() -> None:
    rules = [
        ApplyRule(
            for_patterns=Patterns(include=["sample.com"]),
            use=POTopLevel1,
            instead_of=POTopLevelOverriden2,
        )
    ]

    msg = (
        "The 'from_override_rules' method is deprecated. "
        "Use 'from_apply_rules' instead."
    )
    with pytest.warns(DeprecationWarning, match=msg):
        registry = PageObjectRegistry.from_override_rules(rules)

    assert registry.get_rules() == rules
    assert default_registry.get_rules() != rules


def test_handle_urls_deprecation() -> None:

    with warnings.catch_warnings(record=True) as w:

        @handle_urls("example.com", overrides=CustomProductPage)
        class PageWithDeprecatedOverrides:
            ...

    w = [x for x in w if x.category is DeprecationWarning]
    assert len(w) == 1
    assert str(w[0].message) == (
        "The 'overrides' parameter in @handle_urls is deprecated. Use the "
        "'instead_of' parameter."
    )


def test_override_rule_deprecation() -> None:
    msg = (
        "web_poet.rules.OverrideRule is deprecated, "
        "instantiate web_poet.rules.ApplyRule instead."
    )
    with pytest.warns(DeprecationWarning, match=msg):
        OverrideRule(for_patterns=None, use=None)
