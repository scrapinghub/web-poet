from __future__ import annotations

try:
    import instructor  # noqa: F401
except ImportError as exception:
    message = "Could not import web_poet.llm dependencies. Install web-poet[llm]."
    raise ImportError(message) from exception

import asyncio
import inspect
from types import NoneType, UnionType
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from itemadapter import ItemAdapter
from pydantic import RootModel, field_validator, model_serializer

if TYPE_CHECKING:
    from collections.abc import Hashable

    from instructor import AsyncInstructor
    from instructor.cache import BaseCache

T = TypeVar("T")


def _structure(schema: Any, value: Any) -> Any:
    """Build a *schema* value out of the JSON-like *value*."""
    origin, args = get_origin(schema), get_args(schema)
    if (
        origin is None
        and isinstance(schema, type)
        and ItemAdapter.is_item_class(schema)
    ):
        hints = get_type_hints(schema)
        parameters = inspect.signature(schema).parameters.values()
        if not any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters):
            names = {p.name for p in parameters}
            value = {name: item for name, item in value.items() if name in names}
        return schema(
            **{name: _structure(hints.get(name), item) for name, item in value.items()}
        )
    if not args or value is None:
        return value
    if origin in (Union, UnionType):
        args = tuple(arg for arg in args if arg is not NoneType)
        return _structure(args[0], value) if len(args) == 1 else value
    if isinstance(value, dict):
        return {key: _structure(args[1], item) for key, item in value.items()}
    if isinstance(value, list):
        return [_structure(args[0], item) for item in value]
    return value


def _response_model(item_class: type[T]) -> type[RootModel[T]]:
    """Return a Pydantic model that instructor can request and cache, and that
    holds an instance of *item_class* as its root value."""
    json_schema = {
        "title": item_class.__name__,
        **ItemAdapter.get_json_schema(item_class),
    }

    class Response(RootModel[T]):
        @classmethod
        def model_json_schema(cls, *args: Any, **kwargs: Any) -> dict[str, Any]:
            return json_schema

        @field_validator("root", mode="before")
        @classmethod
        def _structure(cls, value: Any) -> T:
            try:
                return _structure(item_class, value)
            except TypeError as exception:
                raise ValueError(exception) from exception

        @model_serializer
        def _serialize(self) -> dict[str, Any]:
            return ItemAdapter(self.root).asdict()

    return Response


class LLMClient:
    """Parse text into :ref:`item classes <items>` with a large language
    model.

    *client* is an asynchronous instructor client, such as the return value
    of :func:`instructor.from_provider` with ``async_client=True``. *cache*,
    an instructor cache backend such as :class:`instructor.cache.DiskCache`,
    makes parsing identical text into the same item class again free.
    """

    def __init__(self, client: AsyncInstructor, cache: BaseCache | None = None):
        self.client = client
        self.cache = cache
        self._in_flight: dict[Hashable, asyncio.Future[Any]] = {}

    async def parse(self, text: str, item_class: type[T], *, key: Hashable = None) -> T:
        """Return an instance of *item_class*, any class that itemadapter_
        supports, with the data found in *text*.

        Concurrent calls with the same *key*, which defaults to *item_class*
        and *text*, share a single request.

        .. _itemadapter: https://github.com/scrapy/itemadapter
        """
        if key is None:
            key = (item_class, text)
        task = self._in_flight.get(key)
        if task is None:
            task = self._in_flight[key] = asyncio.ensure_future(
                self._parse(text, item_class)
            )
            task.add_done_callback(lambda _: self._in_flight.pop(key, None))
        return await asyncio.shield(task)

    async def _parse(self, text: str, item_class: type[T]) -> T:
        # Instructor scopes its cache to a random namespace by default, which
        # would keep a disk cache from surviving a restart.
        kwargs: dict[str, Any] = (
            {"cache": self.cache, "cache_namespace": "web_poet"} if self.cache else {}
        )
        response = await self.client.create(
            response_model=_response_model(item_class),
            messages=[{"role": "user", "content": text}],
            **kwargs,
        )
        return response.root
