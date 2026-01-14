from __future__ import annotations

import json
from base64 import b64decode, b64encode
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
    data = _prepare_for_json(data)
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        cls=_CustomJSONEncoder,
    )


_LIST_LIKE_TYPES = (tuple, set, frozenset)


def _get_name_for_class_match(obj: Any, types: tuple[type, ...]) -> str:
    for t in types:
        if isinstance(obj, t):
            return _get_name_for_class(t)
    raise ValueError("No matching type found")


def _prepare_for_json(o: Any) -> Any:
    if isinstance(o, (str, int, float, bool, type(None))):
        return o
    if isinstance(o, dict):
        return {k: _prepare_for_json(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_prepare_for_json(x) for x in o]
    if isinstance(o, _LIST_LIKE_TYPES):
        type_name = _get_name_for_class_match(o, _LIST_LIKE_TYPES)
        return {"_type": type_name, "_data": [_prepare_for_json(x) for x in o]}
    if isinstance(o, bytes):
        return {
            "_type": "bytes",
            "_data": b64encode(o).decode("ascii"),
        }
    return o


class _CustomJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, _Url):
            return str(o)
        return super().default(o)


def _json_object_hook(d: dict[str, Any]) -> Any:
    type_name = d.get("_type")
    if "_data" not in d or not type_name:
        return d
    data = d["_data"]
    if type_name == "bytes":
        return b64decode(data)
    allowed = {_get_name_for_class(t): t for t in _LIST_LIKE_TYPES}
    if type_name not in allowed:
        raise ValueError(f"Unknown _type in JSON data: {type_name!r}")
    return allowed[type_name](data)


def _load_json(data: str | bytes) -> Any:
    return json.loads(data, object_hook=_json_object_hook)
