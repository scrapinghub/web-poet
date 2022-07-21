import asyncio

import pytest

from web_poet.utils import maybe_await


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
