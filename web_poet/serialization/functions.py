import json
from typing import Any, Dict, Generic, Type, Union

import attrs

from .. import (
    HttpResponse,
    HttpResponseBody,
    HttpResponseHeaders,
    Injectable,
    ResponseUrl,
)
from ..page_inputs.url import _Url
from .api import SerializedData, deserialize, register_serialization, serialize


def _serialize_dict(o: dict) -> SerializedData:
    return {"json": json.dumps(o).encode()}


def _deserialize_dict(t: Type[dict], data: SerializedData) -> dict:
    return t(json.loads(data["json"]))


register_serialization(_serialize_dict, _deserialize_dict)


def _serialize_Injectable(o: Injectable) -> SerializedData:
    # None is Injectable
    if o is None:
        return {}

    assert attrs.has(o)  # FIXME
    deps = attrs.asdict(o, recurse=False)
    return {dep_name: serialize(dep) for dep_name, dep in deps.items()}


def _deserialize_Injectable(t: Type[Injectable], data: SerializedData) -> Injectable:
    def _strip_Optional(t: Type) -> Type:
        # Python >= 3.8
        try:
            from typing import get_args, get_origin
        # Compatibility
        except ImportError:
            get_args = (
                lambda t: getattr(t, "__args__", ()) if t is not Generic else Generic
            )
            get_origin = lambda t: getattr(t, "__origin__", None)  # noqa: E731
        args = get_args(t)
        if (
            get_origin(t) is Union
            and len(args) == 2
            and args[1] == type(None)  # noqa: E721
        ):
            return args[0]
        return t

    # None is Injectable
    if t is Type[None]:
        return None

    assert attrs.has(t)  # FIXME
    attributes = attrs.fields_dict(t)
    attributes_data: Dict[str, Any] = {}
    for attr_name in attributes:
        if not data.get(attr_name):
            attributes_data[attr_name] = None
        else:
            attr_type = attributes[attr_name].type
            attr_type = _strip_Optional(attr_type)
            attr_data = deserialize(attr_type, data[attr_name])
            attributes_data[attr_name] = attr_data
    return t(**attributes_data)


register_serialization(_serialize_Injectable, _deserialize_Injectable)


def _serialize_HttpResponse(o: HttpResponse) -> SerializedData:
    other_data = {
        "url": str(o.url),
        "status": o.status,
        "headers": list(o.headers.items()),
        "_encoding": o._encoding,
    }
    return {
        "body": serialize(o.body),
        "other": serialize(other_data),
    }


def _deserialize_HttpResponse(
    t: Type[HttpResponse], data: SerializedData
) -> HttpResponse:
    body = deserialize(HttpResponseBody, data["body"])
    other_data = deserialize(dict, data["other"])
    return t(
        body=body,
        url=ResponseUrl(other_data["url"]),
        status=other_data["status"],
        headers=HttpResponseHeaders(other_data["headers"]),
        encoding=other_data["_encoding"],
    )


register_serialization(_serialize_HttpResponse, _deserialize_HttpResponse)


def _serialize_HttpResponseBody(o: HttpResponseBody) -> SerializedData:
    return {"html": bytes(o)}


def _deserialize_HttpResponseBody(
    t: Type[HttpResponseBody], data: SerializedData
) -> HttpResponseBody:
    return t(data["html"])


register_serialization(_serialize_HttpResponseBody, _deserialize_HttpResponseBody)


def _serialize_bytes(o: bytes) -> SerializedData:
    return {"bin": bytes(o)}


def _deserialize_bytes(t: Type[bytes], data: SerializedData) -> bytes:
    return t(data["bin"])


register_serialization(_serialize_bytes, _deserialize_bytes)


def _serialize_str(o: str) -> SerializedData:
    return {"txt": o.encode()}


def _deserialize_str(t: Type[str], data: SerializedData) -> str:
    return t(data["txt"].decode())


register_serialization(_serialize_str, _deserialize_str)


def _serialize__Url(o: _Url) -> SerializedData:
    return {"txt": str(o).encode()}


def _deserialize__Url(t: Type[_Url], data: SerializedData) -> _Url:
    return t(data["txt"].decode())


register_serialization(_serialize__Url, _deserialize__Url)
