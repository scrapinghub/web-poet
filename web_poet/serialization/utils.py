from __future__ import annotations

import json
from typing import Any, cast

from web_poet.page_inputs.url import _Url
from web_poet.serialization.api import _get_name_for_class, load_class


def _exception_to_dict(ex: Exception) -> dict[str, Any]:
    """Serialize an exception.

    Only the exception type and the first argument are saved.
    """
    return {
        "import_path": _get_name_for_class(type(ex)),
        "msg": ex.args[0] if ex.args else None,
    }


def _exception_from_dict(data: dict[str, Any]) -> Exception:
    """Deserialize an exception.

    Only the exception type and the first argument are restored.
    """
    exc_cls = load_class(data["import_path"])
    return cast("Exception", exc_cls(data["msg"]))


def _format_json(data: Any) -> str:
    """Produce a formatted JSON string with preset options."""
    return json.dumps(
        data, ensure_ascii=False, sort_keys=True, indent=2, cls=_CustomJSONEncoder
    )


class _CustomJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, _Url):
            return str(o)
        return super().default(o)
