import json
from typing import Type

from .. import HttpResponse, HttpResponseBody, HttpResponseHeaders, ResponseUrl
from ..page_inputs.url import _Url
from .api import SerializedLeafData, register_serialization


def _serialize_HttpResponse(o: HttpResponse) -> SerializedLeafData:
    other_data = {
        "url": str(o.url),
        "status": o.status,
        "headers": list(o.headers.items()),
        "_encoding": o._encoding,
    }
    return {
        "body.html": bytes(o.body),
        "other.json": json.dumps(
            other_data, ensure_ascii=False, sort_keys=True, indent=2
        ).encode(),
    }


def _deserialize_HttpResponse(
    cls: Type[HttpResponse], data: SerializedLeafData
) -> HttpResponse:
    body = HttpResponseBody(data["body.html"])
    other_data = json.loads(data["other.json"])
    return cls(
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
    cls: Type[HttpResponseBody], data: SerializedLeafData
) -> HttpResponseBody:
    return cls(data["html"])


register_serialization(_serialize_HttpResponseBody, _deserialize_HttpResponseBody)


def _serialize__Url(o: _Url) -> SerializedLeafData:
    return {"txt": str(o).encode()}


def _deserialize__Url(cls: Type[_Url], data: SerializedLeafData) -> _Url:
    return cls(data["txt"].decode())


register_serialization(_serialize__Url, _deserialize__Url)
