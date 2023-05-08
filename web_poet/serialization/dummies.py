from typing import Any, Dict, Type

from web_poet.page_inputs.stats import Stats
from web_poet.pages import Injectable


class DummyStats(Stats):
    def set(self, key: str, value: Any) -> None:  # noqa: D102
        pass

    def inc(self, key: str, value: int = 1) -> None:  # noqa: D102
        pass


DUMMY_MAP: Dict[Type[Injectable], Type[Injectable]] = {
    Stats: DummyStats,
}
