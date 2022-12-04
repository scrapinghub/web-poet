import json
from typing import Type

from .. import HttpResponse, HttpResponseBody, HttpResponseHeaders, ResponseUrl
from ..page_inputs.url import _Url
from .api import (
    SerializedLeafData,
    deserialize_leaf,
    register_serialization,
    serialize_leaf,
)


def _serialize_dict(o: dict) -> SerializedLeafData:
    return {"json": json.dumps(o).encode()}


def _deserialize_dict(t: Type[dict], data: SerializedLeafData) -> dict:
    return t(json.loads(data["json"]))


register_serialization(_serialize_dict, _deserialize_dict)


def _serialize_HttpResponse(o: HttpResponse) -> SerializedLeafData:
    other_data = {
        "url": str(o.url),
        "status": o.status,
        "headers": list(o.headers.items()),
        "_encoding": o._encoding,
    }
    body_serialized = serialize_leaf(o.body)
    other_serialized = serialize_leaf(other_data)
    result = {}
    result.update({f"body.{k}": v for k, v in body_serialized.items()})
    result.update({f"other.{k}": v for k, v in other_serialized.items()})
    return result


def _deserialize_HttpResponse(
    t: Type[HttpResponse], data: SerializedLeafData
) -> HttpResponse:
    body_serialized = {}
    other_serialized = {}
    for k, v in data.items():
        if k.startswith("body."):
            body_serialized[k[len("body.") :]] = v
        elif k.startswith("other."):
            other_serialized[k[len("other.") :]] = v

    body = deserialize_leaf(HttpResponseBody, body_serialized)
    other_data = deserialize_leaf(dict, other_serialized)
    return t(
        body=body,
        url=ResponseUrl(other_data["url"]),
        status=other_data["status"],
        headers=HttpResponseHeaders(other_data["headers"]),
        encoding=other_data["_encoding"],
    )


register_serialization(_serialize_HttpResponse, _deserialize_HttpResponse)


def _serialize_HttpResponseBody(o: HttpResponseBody) -> SerializedLeafData:
    return {"html": bytes(o)}


def _deserialize_HttpResponseBody(
    t: Type[HttpResponseBody], data: SerializedLeafData
) -> HttpResponseBody:
    return t(data["html"])


register_serialization(_serialize_HttpResponseBody, _deserialize_HttpResponseBody)


def _serialize_bytes(o: bytes) -> SerializedLeafData:
    return {"bin": bytes(o)}


def _deserialize_bytes(t: Type[bytes], data: SerializedLeafData) -> bytes:
    return t(data["bin"])


register_serialization(_serialize_bytes, _deserialize_bytes)


def _serialize_str(o: str) -> SerializedLeafData:
    return {"txt": o.encode()}


def _deserialize_str(t: Type[str], data: SerializedLeafData) -> str:
    return t(data["txt"].decode())


register_serialization(_serialize_str, _deserialize_str)


def _serialize__Url(o: _Url) -> SerializedLeafData:
    return {"txt": str(o).encode()}


def _deserialize__Url(t: Type[_Url], data: SerializedLeafData) -> _Url:
    return t(data["txt"].decode())


register_serialization(_serialize__Url, _deserialize__Url)
