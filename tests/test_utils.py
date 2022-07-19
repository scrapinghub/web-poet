import inspect
import warnings
from unittest import mock

import pytest

from web_poet.utils import _create_deprecated_class


class SomeBaseClass:
    pass


class NewName(SomeBaseClass):
    pass


def _mywarnings(w):
    return [x for x in w if x.category is DeprecationWarning]


def test_no_warning_on_definition():
    with warnings.catch_warnings(record=True) as w:
        _create_deprecated_class("Deprecated", NewName)

    w = _mywarnings(w)
    assert w == []


def test_subclassing_warning_message():
    Deprecated = _create_deprecated_class("Deprecated", NewName)

    with warnings.catch_warnings(record=True) as w:

        class UserClass(Deprecated):
            pass

    w = _mywarnings(w)
    assert len(w) == 1
    expected = (
        f"{__name__}.UserClass inherits from deprecated class "
        f"{__name__}.Deprecated, please inherit from {__name__}.NewName. "
        f"(warning only on first subclass, there may be others)"
    )
    assert str(w[0].message) == expected
    assert w[0].lineno == inspect.getsourcelines(UserClass)[1]


def test_custom_class_paths():
    Deprecated = _create_deprecated_class(
        "Deprecated", NewName, new_class_path="foo.NewClass", old_class_path="bar.OldClass"
    )

    with warnings.catch_warnings(record=True) as w:

        class UserClass(Deprecated):
            pass

        _ = Deprecated()

    w = _mywarnings(w)
    assert len(w) == 2
    assert "foo.NewClass" in str(w[0].message)
    assert "bar.OldClass" in str(w[0].message)
    assert "foo.NewClass" in str(w[1].message)
    assert "bar.OldClass" in str(w[1].message)


def test_subclassing_warns_only_on_direct_childs():
    Deprecated = _create_deprecated_class("Deprecated", NewName, warn_once=False)

    with warnings.catch_warnings(record=True) as w:

        class UserClass(Deprecated):
            pass

        class NoWarnOnMe(UserClass):
            pass

    w = _mywarnings(w)
    assert len(w) == 1
    assert "UserClass" in str(w[0].message)


def test_subclassing_warns_once_by_default():
    Deprecated = _create_deprecated_class("Deprecated", NewName)

    with warnings.catch_warnings(record=True) as w:

        class UserClass(Deprecated):
            pass

        class FooClass(Deprecated):
            pass

        class BarClass(Deprecated):
            pass

    w = _mywarnings(w)
    assert len(w) == 1
    assert "UserClass" in str(w[0].message)


def test_warning_on_instance():
    Deprecated = _create_deprecated_class("Deprecated", NewName)

    # ignore subclassing warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        class UserClass(Deprecated):
            pass

    with warnings.catch_warnings(record=True) as w:
        _, lineno = Deprecated(), inspect.getlineno(inspect.currentframe())
        _ = UserClass()  # subclass instances don't warn

    w = _mywarnings(w)
    assert len(w) == 1
    expected = f"{__name__}.Deprecated is deprecated, instantiate " f"{__name__}.NewName instead."
    assert str(w[0].message) == expected
    assert w[0].lineno == lineno


def test_warning_auto_message():
    with warnings.catch_warnings(record=True) as w:
        Deprecated = _create_deprecated_class("Deprecated", NewName)

        class UserClass2(Deprecated):
            pass

    msg = str(w[0].message)
    assert f"{__name__}.NewName" in msg
    assert f"{__name__}.Deprecated" in msg


def test_issubclass():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        DeprecatedName = _create_deprecated_class("DeprecatedName", NewName)

        class UpdatedUserClass1(NewName):
            pass

        class UpdatedUserClass1a(NewName):
            pass

        class OutdatedUserClass1(DeprecatedName):
            pass

        class OutdatedUserClass1a(DeprecatedName):
            pass

        class UnrelatedClass:
            pass

        class OldStyleClass:
            pass

    assert issubclass(UpdatedUserClass1, NewName)
    assert issubclass(UpdatedUserClass1a, NewName)
    assert issubclass(UpdatedUserClass1, DeprecatedName)
    assert issubclass(UpdatedUserClass1a, DeprecatedName)
    assert issubclass(OutdatedUserClass1, DeprecatedName)
    assert not issubclass(UnrelatedClass, DeprecatedName)
    assert not issubclass(OldStyleClass, DeprecatedName)
    assert not issubclass(OldStyleClass, DeprecatedName)
    assert not issubclass(OutdatedUserClass1, OutdatedUserClass1a)
    assert not issubclass(OutdatedUserClass1a, OutdatedUserClass1)

    with pytest.raises(TypeError):
        issubclass(object(), DeprecatedName)


def test_isinstance():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        DeprecatedName = _create_deprecated_class("DeprecatedName", NewName)

        class UpdatedUserClass2(NewName):
            pass

        class UpdatedUserClass2a(NewName):
            pass

        class OutdatedUserClass2(DeprecatedName):
            pass

        class OutdatedUserClass2a(DeprecatedName):
            pass

        class UnrelatedClass:
            pass

        class OldStyleClass:
            pass

    assert isinstance(UpdatedUserClass2(), NewName)
    assert isinstance(UpdatedUserClass2a(), NewName)
    assert isinstance(UpdatedUserClass2(), DeprecatedName)
    assert isinstance(UpdatedUserClass2a(), DeprecatedName)
    assert isinstance(OutdatedUserClass2(), DeprecatedName)
    assert isinstance(OutdatedUserClass2a(), DeprecatedName)
    assert not isinstance(OutdatedUserClass2a(), OutdatedUserClass2)
    assert not isinstance(OutdatedUserClass2(), OutdatedUserClass2a)
    assert not isinstance(UnrelatedClass(), DeprecatedName)
    assert not isinstance(OldStyleClass(), DeprecatedName)


def test_clsdict():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        Deprecated = _create_deprecated_class("Deprecated", NewName, {"foo": "bar"})

    assert Deprecated.foo == "bar"


def test_deprecate_a_class_with_custom_metaclass():
    Meta1 = type("Meta1", (type,), {})
    New = Meta1("New", (), {})
    _create_deprecated_class("Deprecated", New)


def test_deprecate_subclass_of_deprecated_class():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        Deprecated = _create_deprecated_class("Deprecated", NewName)
        AlsoDeprecated = _create_deprecated_class("AlsoDeprecated", Deprecated, new_class_path="foo.Bar")

    w = _mywarnings(w)
    assert len(w) == 0, str(map(str, w))

    with warnings.catch_warnings(record=True) as w:
        AlsoDeprecated()

        class UserClass(AlsoDeprecated):
            pass

    w = _mywarnings(w)
    assert len(w) == 2
    assert "AlsoDeprecated" in str(w[0].message)
    assert "foo.Bar" in str(w[0].message)
    assert "AlsoDeprecated" in str(w[1].message)
    assert "foo.Bar" in str(w[1].message)


def test_inspect_stack():
    with mock.patch("inspect.stack", side_effect=IndexError):
        with warnings.catch_warnings(record=True) as w:
            DeprecatedName = _create_deprecated_class("DeprecatedName", NewName)

            class SubClass(DeprecatedName):
                pass

    assert "Error detecting parent module" in str(w[0].message)
