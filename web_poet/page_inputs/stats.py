from abc import ABC
from typing import Any


class Stats(ABC):
    """Stat collector."""

    def __init__(self):
        self._stats = {}

    def set(self, key: str, value: Any) -> None:
        """Sets the value of stat *key* to *value*."""
        self._stats[key] = value

    def inc(self, key: str, value: int = 1) -> None:
        """Increments the value of stat *key* by *value*, or sets it to *value*
        if *key* has no value."""
        self._stats[key] = self._stats.setdefault(key, 0) + value
