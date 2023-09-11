from abc import ABC, abstractmethod
from typing import Any, Dict

StatNum = int | float


class StatCollector(ABC):
    """Base class for web-poet to implement the storing of data written through
    :class:`~web_poet.page_inputs.stats.Stats`."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set the value of stat *key* to *value*."""

    @abstractmethod
    def inc(self, key: str, value: StatNum = 1) -> None:
        """Increment the value of stat *key* by *value*, or set it to *value*
        if *key* has no value."""


class DummyStatCollector(StatCollector):
    """:class:`~web_poet.page_inputs.stats.StatCollector` implementation that
    does not persist stats. It is used when running automatic tests, where stat
    storage is not necessary."""

    def __init__(self):
        self._stats: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:  # noqa: D102
        self._stats[key] = value

    def inc(self, key: str, value: StatNum = 1) -> None:  # noqa: D102
        if key in self._stats:
            assert isinstance(self._stats[key], StatNum)  # type: ignore[arg-type,misc]
            self._stats[key] += value
        else:
            self._stats[key] = value


class Stats:
    """Page input class to write key-value data pairs during parsing that you
    can inspect later. See :ref:`stats`.

    Stats can be set to a fixed value or, if numeric, incremented.

    Stats are write-only.

    Storage and read access of stats depends on the web-poet framework that you
    are using. Check the documentation of your web-poet framework to find out
    if it supports stats, and if so, how to read stored stats.
    """

    def __init__(self, stat_collector=None):
        self._stats = stat_collector or DummyStatCollector()

    def set(self, key: str, value: Any) -> None:
        """Set the value of stat *key* to *value*."""
        self._stats.set(key, value)

    def inc(self, key: str, value: StatNum = 1) -> None:
        """Increment the value of stat *key* by *value*, or set it to *value*
        if *key* has no value."""
        self._stats.inc(key, value)
