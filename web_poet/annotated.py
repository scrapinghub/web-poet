from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any


@dataclass
class AnnotatedInstance:
    """Wrapper for instances of annotated dependencies.

    It is used when both the dependency value and the dependency annotation are
    needed.

    :param result: The wrapped dependency instance.
    :type result: Any

    :param metadata: The copy of the annotation.
    :type metadata: Tuple[Any, ...]
    """

    result: Any
    metadata: tuple[Any, ...]

    def get_annotated_cls(self) -> Annotated[Any, ...]:
        """Returns a re-created :class:`typing.Annotated` type."""
        return Annotated[(type(self.result), *self.metadata)]
