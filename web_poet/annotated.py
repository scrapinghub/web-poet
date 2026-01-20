from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any


def annotation_encode(obj: Any) -> Any:
    """Encodes *obj* for :obj:`~typing.Annotated`.

    Annotated params must be hashable. This function converts dicts and lists
    into hashable alternatives (tuples and frozensets).

    For example:

    .. code-block:: python

        foo = Annotated(Bar, annotation_encode({"a": [1, 2, 3]}))

    *obj* must not contain tuples or frozensets, or unhashable data besides
    dicts and lists.
    """
    if isinstance(obj, (tuple, list)):
        return tuple(annotation_encode(e) for e in obj)
    if isinstance(obj, dict):
        return frozenset(
            (annotation_encode(k), annotation_encode(v)) for k, v in obj.items()
        )
    return obj


def annotation_decode(obj: Any) -> Any:
    """Converts a result of :func:`annotation_encode` back to original form."""
    if isinstance(obj, tuple):
        return [annotation_decode(o) for o in obj]
    if isinstance(obj, frozenset):
        return {annotation_decode(k): annotation_decode(v) for k, v in obj}
    return obj


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


__all__: list[str] = []  # Prefer imports from web_poet.__init__.py
