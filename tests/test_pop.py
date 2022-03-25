"""This tests the expected behavior of importing multiple different POPs such
that they don't leak the OverrideRules from other POPs that use the same
``default_registry``.

Packacking and exporting a given POP should be resilient from such cases.

In particular, this tests the :meth:`PageObjectRegistry.export` functionality.
"""

def test_base_A():
    from tests_pop import base_A_package

    reg = base_A_package.REGISTRY

    assert len(reg) == 2
    assert base_A_package.site_1.A_Site1 in reg
    assert base_A_package.site_2.A_Site2 in reg


def test_base_B():
    from tests_pop import base_B_package

    reg = base_B_package.REGISTRY

    assert len(reg) == 2
    assert base_B_package.site_2.B_Site2 in reg
    assert base_B_package.site_3.B_Site3 in reg


def test_improved_A():
    from tests_pop import improved_A_package, base_A_package

    reg = improved_A_package.REGISTRY

    assert len(reg) == 3
    assert improved_A_package.site_1.A_Improved_Site1 in reg
    assert improved_A_package.base_A_package.site_1.A_Site1 in reg
    assert improved_A_package.base_A_package.site_2.A_Site2 in reg


def test_combine_A_B():
    from tests_pop import combine_A_B_package, base_A_package, base_B_package

    reg = combine_A_B_package.REGISTRY

    assert len(reg) == 4
    assert combine_A_B_package.base_A_package.site_1.A_Site1 in reg
    assert combine_A_B_package.base_A_package.site_2.A_Site2 in reg
    assert combine_A_B_package.base_B_package.site_2.B_Site2 in reg
    assert combine_A_B_package.base_B_package.site_3.B_Site3 in reg


def test_combine_A_B_subset():
    from tests_pop import combine_A_B_subset_package, improved_A_package, base_B_package

    reg = combine_A_B_subset_package.REGISTRY

    assert len(reg) == 2
    assert combine_A_B_subset_package.improved_A_package.site_1.A_Improved_Site1 in reg
    assert combine_A_B_subset_package.base_B_package.site_3.B_Site3 in reg
