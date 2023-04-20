from typing import Any, Dict

from web_poet.serialization.api import _get_name_for_class, load_class


def _exception_to_dict(ex: Exception) -> Dict[str, Any]:
    """Serialize an exception.

    Only the exception type and the first argument are saved.
    """
    return {
        "type_name": _get_name_for_class(type(ex)),
        "msg": ex.args[0] if ex.args else None,
    }


def _exception_from_dict(data: Dict[str, Any]) -> Exception:
    """Deserialize an exception.

    Only the exception type and the first argument are restored.
    """
    exc_cls = load_class(data["type_name"])
    return exc_cls(data["msg"])
