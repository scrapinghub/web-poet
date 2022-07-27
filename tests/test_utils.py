import asyncio
import random

import pytest

from web_poet.utils import cached_method, maybe_await


@pytest.mark.asyncio
async def test_maybe_await_sync():
    assert await maybe_await(5) == 5

    def foo():
        return 42

    assert await maybe_await(foo()) == 42


@pytest.mark.asyncio
async def test_maybe_await_async():
    async def foo():
        return 42

    assert await maybe_await(foo()) == 42

    async def bar():
        await asyncio.sleep(0.01)
        return 42

    assert await maybe_await(bar()) == 42


def test_cached_method_basic():
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
async def test_cached_method_async():
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


def test_cached_method_argument():
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
async def test_cached_method_argument_async():
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


def test_cached_method_unhashable():
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
async def test_cached_method_unhashable_async():
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
def test_cached_method_exception():
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
async def test_cached_method_exception_async():
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
async def test_cached_method_async_race():
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
