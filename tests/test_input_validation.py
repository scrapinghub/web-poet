"""Test page object input validation scenarios."""

from __future__ import annotations

import attrs
import pytest

from web_poet import ItemPage, Returns, field, validates_input
from web_poet.exceptions import Retry, UseFallback


@attrs.define
class Item:
    a: str
    is_valid: bool = True


EXPECTED_ITEM = Item(a="a", is_valid=True)


class BasePage(ItemPage[Item]):
    @field
    def a(self):
        return "a"


# Valid input


class BaseValidInputPage(BasePage):
    def validate_input(self):
        pass


def test_valid_input_sync_to_item():
    class Page(BaseValidInputPage):
        def to_item(self):
            return Item(a=self.a)

    assert Page().to_item() == EXPECTED_ITEM


@pytest.mark.asyncio
async def test_valid_input_async_to_item():
    assert await BaseValidInputPage().to_item() == EXPECTED_ITEM


def test_valid_input_sync_field():
    assert BaseValidInputPage().a == "a"


@pytest.mark.asyncio
async def test_valid_input_async_field():
    class Page(BaseValidInputPage):
        @field
        async def a(self):
            return "a"

    assert await Page().a == "a"


# Retry


class BaseRetryPage(BasePage):
    def validate_input(self):
        raise Retry


def test_retry_sync_to_item():
    class Page(BaseRetryPage):
        def to_item(self):
            return Item(a=self.a)

    page = Page()
    with pytest.raises(Retry):
        page.to_item()


@pytest.mark.asyncio
async def test_retry_async_to_item():
    page = BaseRetryPage()
    with pytest.raises(Retry):
        await page.to_item()


def test_retry_sync_field():
    page = BaseRetryPage()
    with pytest.raises(Retry):
        page.a


@pytest.mark.asyncio
async def test_retry_async_field():
    class Page(BaseRetryPage):
        @field
        async def a(self):
            return "a"

    page = Page()
    with pytest.raises(Retry):
        await page.a


# Use fallback


class BaseUseFallbackPage(BasePage):
    def validate_input(self):
        if self.a is None:
            raise UseFallback

    @field
    def a(self):
        return None


def test_use_fallback_sync_to_item():
    class Page(BaseUseFallbackPage):
        def to_item(self):
            return Item(a=self.a)

    page = Page()
    with pytest.raises(UseFallback):
        page.to_item()


@pytest.mark.asyncio
async def test_use_fallback_async_to_item():
    page = BaseUseFallbackPage()
    with pytest.raises(UseFallback):
        await page.to_item()


def test_use_fallback_sync_field():
    page = BaseUseFallbackPage()
    with pytest.raises(UseFallback):
        page.a


@pytest.mark.asyncio
async def test_use_fallback_async_field():
    class Page(BaseUseFallbackPage):
        def validate_input(self):
            # Cannot use async self.a
            raise UseFallback

        @field
        async def a(self):
            return "a"

    page = Page()
    with pytest.raises(UseFallback):
        await page.a


# Invalid input


INVALID_ITEM = Item(a="invalid", is_valid=False)


class BaseInvalidInputPage(ItemPage[Item]):
    def validate_input(self):
        return INVALID_ITEM

    @field
    def a(self):
        raise RuntimeError("This exception should never be raised")


def test_invalid_input_sync_to_item():
    class Page(BaseInvalidInputPage):
        @validates_input
        def to_item(self):
            return Item(a=self.a)

    assert Page().to_item() == INVALID_ITEM


@pytest.mark.asyncio
async def test_invalid_input_async_to_item():
    assert await BaseInvalidInputPage().to_item() == INVALID_ITEM


def test_invalid_input_sync_field():
    assert BaseInvalidInputPage().a == "invalid"


@pytest.mark.asyncio
async def test_invalid_input_async_field():
    class Page(BaseInvalidInputPage):
        @field
        async def a(self):
            raise RuntimeError("This exception should never be raised")

    assert await Page().a == "invalid"


# Unvalidated input


def test_unvalidated_input_sync_to_item():
    class Page(BasePage):
        def to_item(self):
            return Item(a=self.a)

    assert Page().to_item() == EXPECTED_ITEM


@pytest.mark.asyncio
async def test_unvalidated_input_async_to_item():
    assert await BasePage().to_item() == EXPECTED_ITEM


def test_unvalidated_input_sync_field():
    assert BasePage().a == "a"


@pytest.mark.asyncio
async def test_unvalidated_input_async_field():
    class Page(BasePage):
        @field
        async def a(self):
            return "a"

    assert await Page().a == "a"


# Caching


class BaseCachingPage(BasePage):
    _raise = False

    def validate_input(self):
        if self._raise:
            raise UseFallback
        self._raise = True


def test_invalid_input_sync_to_item_caching():
    class Page(BaseCachingPage):
        def to_item(self):
            return Item(a=self.a)

    page = Page()
    page.to_item()
    page.to_item()


@pytest.mark.asyncio
async def test_invalid_input_async_to_item_caching():
    page = BaseCachingPage()
    await page.to_item()
    await page.to_item()


def test_invalid_input_sync_field_caching():
    page = BaseCachingPage()
    page.a
    page.a


@pytest.mark.asyncio
async def test_invalid_input_async_field_caching():
    class Page(BaseCachingPage):
        @field
        async def a(self):
            return "a"

    page = Page()
    await page.a
    await page.a


@pytest.mark.asyncio
async def test_invalid_input_cross_api_caching():
    @attrs.define
    class _Item(Item):
        b: str | None = None

    class Page(BaseCachingPage, Returns[_Item]):
        @field
        async def b(self):
            return "b"

    page = Page()
    page.a
    await page.b
    await page.to_item()


# Recursion


@pytest.mark.asyncio
async def test_recursion():
    """Make sure that using fields within the validate_input method does not
    result in a recursive call to the validate_input method."""

    class Page(BasePage):
        _raise = False

        def validate_input(self):
            if self._raise:
                raise UseFallback
            self._raise = True
            assert self.a == "a"

    page = Page()
    assert page.a == "a"
