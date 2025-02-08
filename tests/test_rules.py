import warnings
from typing import Any

import attrs
import pytest
from url_matcher import Patterns

from tests.po_lib import (
    POTopLevel1,
    POTopLevel2,
    POTopLevelOverriden1,
    POTopLevelOverriden2,
)
from tests.po_lib.a_module import POModule, POModuleOverriden
from tests.po_lib.nested_package import PONestedPkg, PONestedPkgOverriden
from tests.po_lib.nested_package.a_nested_module import (
    PONestedModule,
    PONestedModuleOverriden,
)
from tests.po_lib_sub import POLibSub
from tests.po_lib_to_return import (
    CustomProductPage,
    CustomProductPageDataTypeOnly,
    CustomProductPageNoReturns,
    ImprovedProductPage,
    LessProductPage,
    MoreProductPage,
    Product,
    ProductFewerFields,
    ProductMoreFields,
    ProductPage,
    ProductSeparate,
    ProductSimilar,
    SeparateProductPage,
    SimilarProductPage,
    SomePage,
)
from web_poet import (
    ApplyRule,
    RulesRegistry,
    consume_modules,
    default_registry,
)
from web_poet.page_inputs.url import RequestUrl, ResponseUrl

POS = {
    CustomProductPage,
    CustomProductPageNoReturns,
    CustomProductPageDataTypeOnly,
    ImprovedProductPage,
    LessProductPage,
    MoreProductPage,
    POTopLevel1,
    POTopLevel2,
    POModule,
    PONestedPkg,
    PONestedModule,
    ProductPage,
    SeparateProductPage,
    SimilarProductPage,
    SomePage,
}


def test_apply_rule_uniqueness() -> None:
    """The same instance of an ApplyRule with the same attribute values should
    have the same hash identity.
    """

    patterns = Patterns(include=["example.com"], exclude=["example.com/blog"])
    patterns_b = Patterns(include=["example.com/b"])

    rule1 = ApplyRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden1,
        meta={"key_1": 1},
    )
    rule2 = ApplyRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden1,
        meta={"key_2": 2},
    )
    # The ``meta`` parameter is ignored in the hash.
    assert hash(rule1) == hash(rule2)

    params: list[dict[str, Any]] = [
        {
            "for_patterns": patterns,
            "use": POTopLevel1,
            "instead_of": POTopLevelOverriden1,
            "to_return": Product,
        },
        {
            "for_patterns": patterns_b,
            "use": POTopLevel2,
            "instead_of": POTopLevelOverriden2,
            "to_return": ProductSimilar,
        },
    ]

    for change in params[0]:
        # Changing any one of the params should result in a hash mismatch
        rule1 = ApplyRule(**params[0])  # type: ignore[arg-type]
        kwargs = params[0].copy()
        kwargs.update({change: params[1][change]})
        rule2 = ApplyRule(**kwargs)  # type: ignore[arg-type]
        assert hash(rule1) != hash(rule2)


def test_apply_rule_immutability() -> None:
    patterns = Patterns(include=["example.com"], exclude=["example.com/blog"])

    rule = ApplyRule(
        for_patterns=patterns,
        use=POTopLevel1,
        instead_of=POTopLevelOverriden1,
    )

    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        rule.for_patterns = Patterns(include=["example.com/"])  # type: ignore[misc]

    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        rule.use = POTopLevel2  # type: ignore[misc]

    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        rule.instead_of = POTopLevelOverriden2  # type: ignore[misc]


def test_apply_rule_converter_on_pattern() -> None:
    # passing strings should auto-converter into Patterns
    rule = ApplyRule("example.com", use=POTopLevel1, instead_of=POTopLevelOverriden2)
    assert rule.for_patterns == Patterns(
        include=["example.com"], exclude=[], priority=500
    )

    # Passing Patterns should still work
    rule = ApplyRule(
        for_patterns=Patterns(["example.com"]),
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
    )
    assert rule.for_patterns == Patterns(
        include=["example.com"], exclude=[], priority=500
    )


def test_apply_rule_kwargs_only() -> None:
    params = {
        "use": POTopLevel1,
        "instead_of": POTopLevelOverriden2,
        "to_return": Product,
        "meta": {"key_2": 2},
    }
    remove = set()

    for param_name in params:
        remove.add(param_name)
        with pytest.raises(TypeError):
            ApplyRule(
                "example.com",
                *[params[r] for r in remove],
                **{k: v for k, v in params.items() if k not in remove},  # type: ignore[arg-type]
            )


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
    assert all("po_lib_sub_not_imported" not in po.__module__ for po in page_objects)

    # Ensure that ALL Override Rules are returned as long as the given
    # registry's @handle_urls decorator was used.
    assert page_objects == POS.union({POLibSub})

    for rule in rules:
        # We're ignoring the types below since mypy expects ``Type[ItemPage]``
        # which doesn't contain the ``expected_*`` fields in our tests.

        # Special case since this PO has 2 ``@handle_urls`` decorators.
        # See ``test_multiple_handle_urls()`` test case below.
        if rule.use == POTopLevel1:
            continue

        assert rule.instead_of == rule.use.expected_instead_of, rule.use  # type: ignore[attr-defined]
        assert rule.for_patterns == rule.use.expected_patterns, rule.use  # type: ignore[attr-defined]
        assert rule.to_return == rule.use.expected_to_return, rule.use  # type: ignore[attr-defined]
        assert rule.meta == rule.use.expected_meta, rule.use  # type: ignore[attr-defined]


def test_multiple_handle_urls_annotations() -> None:
    """Using multiple ``@handle_urls`` annotations on a single Page Object
    should work.
    """
    rules = default_registry.search(use=POTopLevel1)
    assert len(rules) == 2

    for i, rule in enumerate(rules):
        assert rule.instead_of == rule.use.expected_instead_of[i], rule.use  # type: ignore[attr-defined]
        assert rule.for_patterns == rule.use.expected_patterns[i], rule.use  # type: ignore[attr-defined]
        assert rule.to_return == rule.use.expected_to_return[i], rule.use  # type: ignore[attr-defined]
        assert rule.meta == rule.use.expected_meta[i], rule.use  # type: ignore[attr-defined]


def test_consume_module_not_existing() -> None:
    with pytest.raises(ImportError):
        consume_modules("this_does_not_exist")


def test_list_page_objects_all_consume() -> None:
    """A test similar to the one above but calls ``consume_modules()`` to properly
    load the ``@handle_urls`` decorators from other modules/packages.
    """
    consume_modules("tests_extra")
    rules = default_registry.get_rules()
    page_objects = {po.use for po in rules}
    assert any("po_lib_sub_not_imported" in po.__module__ for po in page_objects)


def test_registry_search() -> None:
    # param: use
    rules = default_registry.search(use=POTopLevel2)
    assert len(rules) == 1
    assert rules[0].use == POTopLevel2

    # param: instead_of
    rules = default_registry.search(instead_of=POTopLevelOverriden2)
    assert len(rules) == 1
    assert rules[0].instead_of == POTopLevelOverriden2

    rules = default_registry.search(instead_of=None)
    for rule in rules:
        assert rule.instead_of is None

    # param: to_return
    rules = default_registry.search(to_return=Product)
    assert rules == [
        ApplyRule("example.com", use=ProductPage, to_return=Product),
        ApplyRule(
            "example.com",
            use=ImprovedProductPage,
            instead_of=ProductPage,
            to_return=Product,
        ),
        ApplyRule(
            "example.com",
            # mypy complains here since it's expecting a container class when
            # declared, i.e, ``ItemPage[SomeItem]``
            use=CustomProductPageDataTypeOnly,  # type: ignore[arg-type]
            to_return=Product,
        ),
    ]

    rules = default_registry.search(to_return=None)
    for rule in rules:
        assert rule.to_return is None

    # params: to_return and use
    rules = default_registry.search(to_return=Product, use=ImprovedProductPage)
    assert len(rules) == 1
    assert rules[0].to_return == Product
    assert rules[0].use == ImprovedProductPage

    # params: to_return and instead_of
    rules = default_registry.search(to_return=Product, instead_of=None)
    assert len(rules) == 2
    assert rules[0].to_return == Product
    assert rules[0].instead_of is None
    assert rules[1].to_return == Product
    assert rules[1].instead_of is None

    rules = default_registry.search(to_return=None, instead_of=ProductPage)
    for rule in rules:
        assert rule.to_return is None
        assert rule.instead_of is None

    rules = default_registry.search(to_return=None, instead_of=None)
    assert len(rules) == 1
    assert rules[0].to_return is None
    assert rules[0].instead_of is None

    # Such rules doesn't exist
    rules = default_registry.search(use=POModuleOverriden)
    assert len(rules) == 0


def test_init_rules() -> None:
    rules = (
        ApplyRule(
            for_patterns=Patterns(include=["example.com"]),
            use=POTopLevel1,
            instead_of=POTopLevelOverriden2,
        ),
    )

    registry = RulesRegistry(rules=rules)

    # Any type of iterable input should convert it to a list.
    assert registry.get_rules() == list(rules)
    assert default_registry.get_rules() != rules


def test_add_rule() -> None:
    registry = RulesRegistry()

    # Basic case of adding a rule
    rule_1 = ApplyRule(
        for_patterns=Patterns(include=["example.com"]),
        use=POTopLevel1,
        instead_of=POTopLevelOverriden1,
        to_return=Product,
    )
    registry.add_rule(rule_1)
    assert registry.get_rules() == [rule_1]

    # Adding a second rule should not emit a warning as long as both the URL
    # pattern and `.to_return` value is not the same.
    rule_2 = ApplyRule(
        for_patterns=Patterns(include=["example.com"]),
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
        to_return=ProductSimilar,
    )
    with warnings.catch_warnings(record=True) as warnings_emitted:
        registry.add_rule(rule_2)
    assert not warnings_emitted
    assert registry.get_rules() == [rule_1, rule_2]

    # Warnings should be raised for this case since it's the same URL pattern
    # and `.to_return` value from one of the past rules.
    rule_3 = ApplyRule(
        for_patterns=Patterns(include=["example.com"]),
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
        to_return=Product,
    )
    with pytest.warns(UserWarning, match="conflicting rules"):
        registry.add_rule(rule_3)

    assert registry.get_rules() == [rule_1, rule_2, rule_3]


def test_overrides_for() -> None:
    for cls in [str, RequestUrl, ResponseUrl]:
        assert default_registry.overrides_for(cls("https://example.com")) == {
            POTopLevelOverriden1: POTopLevel1,
            POTopLevelOverriden2: POTopLevel2,
            POModuleOverriden: POModule,
            PONestedPkgOverriden: PONestedPkg,
            PONestedModuleOverriden: PONestedModule,
            ProductPage: CustomProductPageNoReturns,
        }

        assert default_registry.overrides_for(cls("https://example.org")) == {
            PONestedModuleOverriden: PONestedModule,
            PONestedPkgOverriden: PONestedPkg,
        }


def test_page_cls_for_item() -> None:
    # This is not associated with any rule.
    class FakeItem:
        pass

    method = default_registry.page_cls_for_item

    for cls in [str, RequestUrl, ResponseUrl]:
        url = cls("https://example.com")
        assert method(url, ProductSimilar) == CustomProductPageNoReturns
        assert method(url, Product) == CustomProductPageDataTypeOnly
        assert method(url, ProductSeparate) == SeparateProductPage
        assert method(url, ProductFewerFields) == LessProductPage
        assert method(url, ProductMoreFields) == MoreProductPage

        # Type is ignored since item_cls shouldn't be None
        assert method(url, None) is None  # type: ignore[arg-type]

        # When there's no rule specifying to return this FakeItem
        assert method(url, FakeItem) is None

        # When the URL itself doesn't have any ``to_return`` in any of its rules
        assert method(cls("https://example.org"), FakeItem) is None


def test_top_rules_for_item() -> None:
    registry = RulesRegistry()

    assert list(registry.top_rules_for_item("https://example.com", Product)) == []

    @registry.handle_urls("https://a.example", priority=1000)
    class A1(ProductPage):
        pass

    @registry.handle_urls("https://a.example", priority=900)
    class A2(ProductPage):
        pass

    assert {
        rule.use for rule in registry.top_rules_for_item("https://a.example", Product)
    } == {A1}

    @registry.handle_urls("https://b.example")
    class B1(ProductPage):
        pass

    @registry.handle_urls("https://b.example")
    class B2(ProductPage):
        pass

    assert {
        rule.use for rule in registry.top_rules_for_item("https://b.example", Product)
    } == {B1, B2}
