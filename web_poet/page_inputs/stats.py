from abc import ABC, abstractmethod
from typing import Any


class Stats(ABC):
    """Stat collector."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Sets the value of stat *key* to *value*."""

    @abstractmethod
    def inc(self, key: str, value: int = 1) -> None:
        """Increments the value of stat *key* by *value*, or sets it to *value*
        if *key* has no value."""
