import json
from typing import Dict, Type

from .. import (
    HttpClient,
    HttpResponse,
    HttpResponseBody,
    HttpResponseHeaders,
    ResponseUrl,
)
from ..page_inputs.url import _Url
from .api import (
    SerializedLeafData,
    deserialize_leaf,
    register_serialization,
    serialize_leaf,
)


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


def _serialize_HttpClient(o: HttpClient) -> SerializedLeafData:
    serialized_data: SerializedLeafData = {}
    for response_key, response in o.saved_responses.items():
        serialized_response = serialize_leaf(response)
        key_prefix = response_key + "-"
        for k, v in serialized_response.items():
            serialized_data[key_prefix + k] = v
    return serialized_data


def _deserialize_HttpClient(
    cls: Type[HttpClient], data: SerializedLeafData
) -> HttpClient:
    serialized_responses: Dict[str, SerializedLeafData] = {}
    for k, v in data.items():
        response_key, subkey = k.rsplit("-", 1)
        serialized_responses.setdefault(response_key, {})[subkey] = v

    result = cls(return_only_saved_responses=True)
    for response_key, serialized_response in serialized_responses.items():
        result.saved_responses[response_key] = deserialize_leaf(
            HttpResponse, serialized_response
        )
    return result


register_serialization(_serialize_HttpClient, _deserialize_HttpClient)
