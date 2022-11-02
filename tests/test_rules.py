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
    SeparateProductPage,
    SimilarProductPage,
    SomePage,
)
from web_poet import (
    ApplyRule,
    OverrideRule,
    RulesRegistry,
    consume_modules,
    default_registry,
    handle_urls,
)

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

    params = [
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

    for change in params[0].keys():
        # Changing any one of the params should result in a hash mismatch
        rule1 = ApplyRule(**params[0])
        kwargs = params[0].copy()
        kwargs.update({change: params[1][change]})
        rule2 = ApplyRule(**kwargs)
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
        include=("example.com",), exclude=(), priority=500
    )

    # Passing Patterns should still work
    rule = ApplyRule(
        for_patterns=Patterns(["example.com"]),
        use=POTopLevel1,
        instead_of=POTopLevelOverriden2,
    )
    assert rule.for_patterns == Patterns(
        include=("example.com",), exclude=(), priority=500
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
                **{k: v for k, v in params.items() if k not in remove}  # type: ignore[arg-type]
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
    assert all(["po_lib_sub_not_imported" not in po.__module__ for po in page_objects])

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


def test_registry_get_overrides_deprecation() -> None:
    msg = "The 'get_overrides' method is deprecated. Use 'get_rules' instead."
    with pytest.warns(DeprecationWarning, match=msg):
        rules = default_registry.get_overrides()

    # It should still work as usual
    assert len(rules) == len(default_registry.get_rules())

    # but the rules from ``.get_overrides()`` should return ``ApplyRule`` and
    # not the old ``OverrideRule``.
    assert all([r for r in rules if isinstance(r, ApplyRule)])


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
    assert any(["po_lib_sub_not_imported" in po.__module__ for po in page_objects])


def test_registry_search() -> None:
    # param: use
    rules = default_registry.search(use=POTopLevel2)
    assert len(rules) == 1
    assert rules[0].use == POTopLevel2

    # param: instead_of
    rules = default_registry.search(instead_of=POTopLevelOverriden2)
    assert len(rules) == 1
    assert rules[0].instead_of == POTopLevelOverriden2

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

    # params: to_return and use
    rules = default_registry.search(to_return=Product, use=ImprovedProductPage)
    assert len(rules) == 1
    assert rules[0].to_return == Product
    assert rules[0].use == ImprovedProductPage

    # Such rules doesn't exist
    rules = default_registry.search(use=POModuleOverriden)
    assert len(rules) == 0


def test_registry_search_overrides_deprecation() -> None:
    msg = "The 'search_overrides' method is deprecated. Use 'search' instead."
    with pytest.warns(DeprecationWarning, match=msg):
        rules = default_registry.search_overrides(use=POTopLevel2)

    # It should still work as usual
    assert len(rules) == 1
    assert rules[0].use == POTopLevel2

    # The rules from ``.get_overrides()`` should return ``ApplyRule`` and
    # not the old ``OverrideRule``.
    assert isinstance(rules[0], ApplyRule)


def test_init_rules() -> None:
    rules = (
        ApplyRule(
            for_patterns=Patterns(include=["sample.com"]),
            use=POTopLevel1,
            instead_of=POTopLevelOverriden2,
        ),
    )

    registry = RulesRegistry(rules=rules)

    # Any type of iterable input should convert it to a list.
    assert registry.get_rules() == list(rules)
    assert default_registry.get_rules() != rules


def test_from_override_rules_deprecation_using_ApplyRule() -> None:
    rules = [
        ApplyRule(
            for_patterns=Patterns(include=["sample.com"]),
            use=POTopLevel1,
            instead_of=POTopLevelOverriden2,
        )
    ]

    msg = "The 'from_override_rules' method is deprecated."
    with pytest.warns(DeprecationWarning, match=msg):
        registry = RulesRegistry.from_override_rules(rules)

    assert registry.get_rules() == rules
    assert default_registry.get_rules() != rules


def test_from_override_rules_deprecation_using_OverrideRule() -> None:
    rules = [
        OverrideRule(
            for_patterns=Patterns(include=["sample.com"]),
            use=POTopLevel1,
            instead_of=POTopLevelOverriden2,
        )
    ]

    msg = "The 'from_override_rules' method is deprecated."
    with pytest.warns(DeprecationWarning, match=msg):
        registry = RulesRegistry.from_override_rules(rules)

    assert registry.get_rules() == rules
    assert default_registry.get_rules() != rules


def test_handle_urls_deprecation() -> None:
    before_count = len(default_registry.get_rules())

    msg = (
        "The 'overrides' parameter in @handle_urls is deprecated. Use the "
        "'instead_of' parameter."
    )
    with pytest.warns(DeprecationWarning, match=msg):

        @handle_urls("example.com", overrides=CustomProductPage)
        class PageWithDeprecatedOverrides:
            ...

    # Despite the deprecation, it should still properly add the rule in the
    # registry.
    after_count = len(default_registry.get_rules())
    assert after_count == before_count + 1

    # The added rule should have its deprecated 'overrides' parameter converted
    # into the new 'instead_of' parameter.
    rules = default_registry.search(
        instead_of=CustomProductPage, use=PageWithDeprecatedOverrides
    )
    assert rules == [
        ApplyRule(
            "example.com",
            instead_of=CustomProductPage,
            # mypy complains here since it's expecting a container class when
            # declared, i.e, ``ItemPage[SomeItem]``
            use=PageWithDeprecatedOverrides,  # type: ignore[arg-type]
        )
    ]


def test_override_rule_deprecation() -> None:
    msg = (
        "web_poet.rules.OverrideRule is deprecated, "
        "instantiate web_poet.rules.ApplyRule instead."
    )
    with pytest.warns(DeprecationWarning, match=msg):
        OverrideRule(for_patterns=None, use=None)
