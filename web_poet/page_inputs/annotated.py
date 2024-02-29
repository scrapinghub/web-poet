from dataclasses import dataclass
from typing import Any, Tuple


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
    metadata: Tuple[Any, ...]

    def get_annotated_cls(self):
        """Returns a re-created :class:`typing.Annotated` type."""
        from typing import Annotated

        return Annotated[(type(self.result), *self.metadata)]
