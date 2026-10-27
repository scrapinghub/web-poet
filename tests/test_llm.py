import asyncio
import dataclasses
import json
from typing import Literal

import attrs
import pytest

pytest.importorskip("instructor")

from instructor import AsyncInstructor, Mode, patch
from instructor.cache import AutoCache
from instructor.core.exceptions import InstructorRetryException
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_function_tool_call import (
    ChatCompletionMessageFunctionToolCall,
    Function,
)
from pydantic import BaseModel
from zyte_common_items import Brand, Breadcrumb, Product, ProductMetadata

from web_poet.llm import LLMClient


class FakeCompletions:
    """OpenAI-like chat completions that answer every tool call with *data*."""

    def __init__(self, data):
        self.data = data
        self.calls = 0

    async def create(self, *, messages, tools, **kwargs):
        self.calls += 1
        await asyncio.sleep(0)
        function = Function(
            name=tools[0]["function"]["name"], arguments=json.dumps(self.data)
        )
        tool_call = ChatCompletionMessageFunctionToolCall(
            id="1", type="function", function=function
        )
        message = ChatCompletionMessage(role="assistant", tool_calls=[tool_call])
        choice = Choice(index=0, finish_reason="tool_calls", message=message)
        return ChatCompletion(
            id="1", created=0, model="fake", object="chat.completion", choices=[choice]
        )


def make_client(data, cache=None):
    fake = FakeCompletions(data)
    instructor_client = AsyncInstructor(
        client=fake, create=patch(create=fake.create, mode=Mode.TOOLS), mode=Mode.TOOLS
    )
    return LLMClient(instructor_client, cache=cache), fake


class Shipping(BaseModel):
    days: int
    free: bool


@attrs.define
class Offer:
    price: str
    tags: list[str] = attrs.Factory(list)
    currency: str | None = None
    condition: Literal["new", "used"] | None = None
    summary: str = attrs.field(init=False, default="")


@dataclasses.dataclass
class Listing:
    title: str
    offers: list[Offer]
    best: Offer | None = None


@pytest.mark.asyncio
async def test_pydantic():
    client, fake = make_client({"days": 3, "free": True})
    shipping = await client.parse("Ships in 3 days, free.", Shipping)
    assert isinstance(shipping, Shipping)
    assert shipping.model_dump() == {"days": 3, "free": True}
    assert fake.calls == 1


@pytest.mark.asyncio
async def test_attrs():
    data = {"price": "10", "condition": "used", "summary": "Ten"}
    client, fake = make_client(data)
    assert await client.parse("$10, used", Offer) == Offer(price="10", condition="used")
    assert fake.calls == 1


@pytest.mark.asyncio
async def test_dataclass_nested():
    data = {"title": "Foo", "offers": [{"price": "10"}], "best": {"price": "10"}}
    client, _ = make_client(data)
    assert await client.parse("Foo, $10", Listing) == Listing(
        title="Foo", offers=[Offer(price="10")], best=Offer(price="10")
    )


@pytest.mark.asyncio
async def test_missing_required_field_is_retried():
    client, fake = make_client({"tags": ["a"]})
    with pytest.raises(InstructorRetryException):
        await client.parse("No price here", Offer)
    assert fake.calls > 1


@pytest.mark.asyncio
async def test_attrs_nested():
    data = {
        "url": "https://example.com/foo",
        "name": "Foo",
        "brand": {"name": "Bar"},
        "breadcrumbs": [{"name": "Home", "url": "https://example.com"}],
        "metadata": {"validationMessages": {"name": ["Too short"]}},
    }
    client, _ = make_client(data)
    product = await client.parse("Foo by Bar", Product)
    assert product == Product(
        url="https://example.com/foo",
        name="Foo",
        brand=Brand(name="Bar"),
        breadcrumbs=[Breadcrumb(name="Home", url="https://example.com")],
        metadata=ProductMetadata(validationMessages={"name": ["Too short"]}),
    )


@pytest.mark.asyncio
async def test_cache():
    cache = AutoCache()
    client, fake = make_client({"days": 3, "free": True}, cache=cache)
    await client.parse("Ships in 3 days, free.", Shipping)
    await client.parse("Ships in 3 days, free.", Shipping)
    await client.parse("Ships in 5 days.", Shipping)
    assert fake.calls == 2

    other_client, other_fake = make_client({}, cache=cache)
    shipping = await other_client.parse("Ships in 3 days, free.", Shipping)
    assert shipping.model_dump() == {"days": 3, "free": True}
    assert other_fake.calls == 0


@pytest.mark.asyncio
async def test_coalesce():
    client, fake = make_client({"days": 3, "free": True})
    results = await asyncio.gather(
        *(client.parse("Ships in 3 days, free.", Shipping) for _ in range(5))
    )
    assert [shipping.model_dump() for shipping in results] == [
        {"days": 3, "free": True}
    ] * 5
    assert fake.calls == 1
    assert not client._in_flight

    await asyncio.gather(
        *(client.parse("Ships in 3 days, free.", Shipping, key=i) for i in range(3))
    )
    assert fake.calls == 4


@pytest.mark.asyncio
async def test_coalesce_survives_cancellation():
    client, fake = make_client({"days": 3, "free": True})
    first = asyncio.ensure_future(client.parse("Ships in 3 days, free.", Shipping))
    second = asyncio.ensure_future(client.parse("Ships in 3 days, free.", Shipping))
    await asyncio.sleep(0)
    first.cancel()
    assert (await second).model_dump() == {"days": 3, "free": True}
    assert fake.calls == 1
