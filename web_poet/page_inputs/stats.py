from typing import Any, Dict, Protocol


class StatCollectorProtocol(Protocol):
    def set(self, key: str, value: Any) -> None:  # noqa: D102
        pass

    def inc(self, key: str, value: int = 1) -> None:  # noqa: D102
        pass


class DummyStatCollector:
    def __init__(self):
        self._stats: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:  # noqa: D102
        self._stats[key] = value

    def inc(self, key: str, value: int = 1) -> None:  # noqa: D102
        if key in self._stats:
            assert isinstance(self._stats[key], int)
            self._stats[key] += value
        else:
            self._stats[key] = value


class Stats:
    """Stat collector."""

    def __init__(self, stat_collector=None):
        self._stats = stat_collector or DummyStatCollector()

    def set(self, key: str, value: Any) -> None:
        """Sets the value of stat *key* to *value*."""
        self._stats.set(key, value)

    def inc(self, key: str, value: int = 1) -> None:
        """Increments the value of stat *key* by *value*, or sets it to *value*
        if *key* has no value."""
        self._stats.inc(key, value)
