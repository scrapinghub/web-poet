import asyncio
import inspect
import random
import warnings
from typing import Any
from unittest import mock

import pytest

from web_poet.utils import _create_deprecated_class, cached_method, ensure_awaitable


class SomeBaseClass:
    pass


class NewName(SomeBaseClass):
    pass


def _mywarnings(w):
    return [x for x in w if x.category is DeprecationWarning]


def test_no_warning_on_definition() -> None:
    with warnings.catch_warnings(record=True) as w:
        _create_deprecated_class("Deprecated", NewName)

    w = _mywarnings(w)
    assert w == []


def test_subclassing_warning_message() -> None:
    # https://github.com/python/mypy/issues/2477#issuecomment-262734005
    # Annotating it with Any helps prevent mypy issues for dynamic classes
    Deprecated: Any = _create_deprecated_class("Deprecated", NewName)

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


def test_custom_class_paths() -> None:
    Deprecated: Any = _create_deprecated_class(
        "Deprecated",
        NewName,
        new_class_path="foo.NewClass",
        old_class_path="bar.OldClass",
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


def test_subclassing_warns_only_on_direct_childs() -> None:
    Deprecated: Any = _create_deprecated_class("Deprecated", NewName, warn_once=False)

    with warnings.catch_warnings(record=True) as w:

        class UserClass(Deprecated):
            pass

        class NoWarnOnMe(UserClass):
            pass

    w = _mywarnings(w)
    assert len(w) == 1
    assert "UserClass" in str(w[0].message)


def test_subclassing_warns_once_by_default() -> None:
    Deprecated: Any = _create_deprecated_class("Deprecated", NewName)

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


def test_warning_on_instance() -> None:
    Deprecated: Any = _create_deprecated_class("Deprecated", NewName)

    # ignore subclassing warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        class UserClass(Deprecated):
            pass

    with warnings.catch_warnings(record=True) as w:
        _, lineno = Deprecated(), inspect.getlineno(inspect.currentframe())  # type: ignore[arg-type]
        _ = UserClass()  # subclass instances don't warn

    w = _mywarnings(w)
    assert len(w) == 1
    expected = (
        f"{__name__}.Deprecated is deprecated, instantiate "
        f"{__name__}.NewName instead."
    )
    assert str(w[0].message) == expected
    assert w[0].lineno == lineno


def test_warning_auto_message() -> None:
    with warnings.catch_warnings(record=True) as w:
        Deprecated: Any = _create_deprecated_class("Deprecated", NewName)

        class UserClass2(Deprecated):
            pass

    msg = str(w[0].message)
    assert f"{__name__}.NewName" in msg
    assert f"{__name__}.Deprecated" in msg


def test_issubclass() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        DeprecatedName: Any = _create_deprecated_class("DeprecatedName", NewName)

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
        issubclass(object(), DeprecatedName)  # type: ignore[arg-type]


def test_isinstance() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        DeprecatedName: Any = _create_deprecated_class("DeprecatedName", NewName)

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


def test_clsdict() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        Deprecated: Any = _create_deprecated_class(
            "Deprecated", NewName, {"foo": "bar"}
        )

    assert Deprecated.foo == "bar"


def test_deprecate_a_class_with_custom_metaclass() -> None:
    Meta1 = type("Meta1", (type,), {})
    New = Meta1("New", (), {})
    _create_deprecated_class("Deprecated", New)


def test_deprecate_subclass_of_deprecated_class() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        Deprecated: Any = _create_deprecated_class("Deprecated", NewName)
        AlsoDeprecated: Any = _create_deprecated_class(
            "AlsoDeprecated", Deprecated, new_class_path="foo.Bar"
        )

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


def test_inspect_stack() -> None:
    with mock.patch("inspect.stack", side_effect=IndexError):
        with warnings.catch_warnings(record=True) as w:
            DeprecatedName: Any = _create_deprecated_class("DeprecatedName", NewName)

            class SubClass(DeprecatedName):
                pass

    assert "Error detecting parent module" in str(w[0].message)


@pytest.mark.asyncio
async def test_ensure_awaitable_sync() -> None:
    assert await ensure_awaitable(5) == 5

    def foo():
        return 42

    assert await ensure_awaitable(foo()) == 42


@pytest.mark.asyncio
async def test_ensure_awaitable_async() -> None:
    async def foo():
        return 42

    assert await ensure_awaitable(foo()) == 42

    async def bar():
        await asyncio.sleep(0.01)
        return 42

    assert await ensure_awaitable(bar()) == 42


def test_cached_method_basic() -> None:
    class Foo:
        n_called = 0

        def __init__(self, name):
            self.name = name

        @cached_method
        def meth(self):
            self.n_called += 1
            return self.n_called, self.name

    foo = Foo("first")
    assert foo.meth() == (1, "first")
    assert foo.meth() == (1, "first")

    bar = Foo("second")
    assert bar.meth() == (1, "second")
    assert bar.meth() == (1, "second")


@pytest.mark.asyncio
async def test_cached_method_async() -> None:
    class Foo:
        n_called = 0

        def __init__(self, name):
            self.name = name

        @cached_method
        async def meth(self):
            self.n_called += 1
            return self.n_called, self.name

    foo = Foo("first")
    assert await foo.meth() == (1, "first")
    assert await foo.meth() == (1, "first")

    bar = Foo("second")
    assert await bar.meth() == (1, "second")
    assert await bar.meth() == (1, "second")


def test_cached_method_argument() -> None:
    class Foo:
        n_called = 0

        def __init__(self, name):
            self.name = name

        @cached_method
        def meth(self, x):
            self.n_called += 1
            return self.n_called, self.name, x

    foo = Foo("first")
    assert foo.meth(5) == (1, "first", 5)
    assert foo.meth(5) == (1, "first", 5)
    assert foo.meth(6) == (2, "first", 6)
    assert foo.meth(6) == (2, "first", 6)


@pytest.mark.asyncio
async def test_cached_method_argument_async() -> None:
    class Foo:
        n_called = 0

        def __init__(self, name):
            self.name = name

        @cached_method
        async def meth(self, x):
            self.n_called += 1
            return self.n_called, self.name, x

    foo = Foo("first")
    assert await foo.meth(5) == (1, "first", 5)
    assert await foo.meth(5) == (1, "first", 5)
    assert await foo.meth(6) == (2, "first", 6)
    assert await foo.meth(6) == (2, "first", 6)


def test_cached_method_unhashable() -> None:
    class Foo(list):
        n_called = 0

        @cached_method
        def meth(self):
            self.n_called += 1
            return self.n_called

    foo = Foo()
    assert foo.meth() == 1
    assert foo.meth() == 1


@pytest.mark.asyncio
async def test_cached_method_unhashable_async() -> None:
    class Foo(list):
        n_called = 0

        @cached_method
        async def meth(self):
            self.n_called += 1
            return self.n_called

    foo = Foo()
    assert await foo.meth() == 1
    assert await foo.meth() == 1


@pytest.mark.xfail
def test_cached_method_exception() -> None:
    class Error(Exception):
        pass

    class Foo(list):
        n_called = 0

        @cached_method
        def meth(self):
            self.n_called += 1
            raise Error()

    foo = Foo()

    for _ in range(2):
        with pytest.raises(Error):
            foo.meth()
        assert foo.n_called == 1


@pytest.mark.asyncio
async def test_cached_method_exception_async() -> None:
    class Error(Exception):
        pass

    class Foo(list):
        n_called = 0

        @cached_method
        async def meth(self):
            self.n_called += 1
            raise Error()

    foo = Foo()

    for _ in range(2):
        with pytest.raises(Error):
            await foo.meth()
        assert foo.n_called == 1


@pytest.mark.asyncio
async def test_cached_method_async_race() -> None:
    class Foo:
        _n_called = 0

        @cached_method
        async def n_called(self):
            await asyncio.sleep(random.randint(0, 10) / 100.0)
            self._n_called += 1
            return self._n_called

    foo = Foo()
    results = await asyncio.gather(
        foo.n_called(),
        foo.n_called(),
        foo.n_called(),
        foo.n_called(),
        foo.n_called(),
    )
    assert results == [1, 1, 1, 1, 1]
