import json
from typing import Dict, List, Type

from .. import HttpClient, HttpRequest, HttpRequestBody, HttpResponse, HttpResponseBody
from ..page_inputs.client import SavedResponseData
from ..page_inputs.url import _Url
from .api import (
    SerializedLeafData,
    deserialize_leaf,
    register_serialization,
    serialize_leaf,
)


def _serialize_HttpRequest(o: HttpRequest) -> SerializedLeafData:
    info = {
        "url": str(o.url),
        "method": o.method,
        "headers": list(o.headers.items()),
    }
    result: SerializedLeafData = {
        "info.json": json.dumps(
            info, ensure_ascii=False, sort_keys=True, indent=2
        ).encode(),
    }
    if o.body:
        result["body.txt"] = bytes(o.body)
    return result


def _deserialize_HttpRequest(
    cls: Type[HttpRequest], data: SerializedLeafData
) -> HttpRequest:
    body = HttpRequestBody(data.get("body.txt", b""))
    info = json.loads(data["info.json"])
    return cls(
        body=body,
        url=info["url"],
        method=info["method"],
        headers=info["headers"],
    )


register_serialization(_serialize_HttpRequest, _deserialize_HttpRequest)


def _serialize_HttpResponse(o: HttpResponse) -> SerializedLeafData:
    info = {
        "url": str(o.url),
        "status": o.status,
        "headers": list(o.headers.items()),
        "_encoding": o._encoding,
    }
    return {
        "body.html": bytes(o.body),
        "info.json": json.dumps(
            info, ensure_ascii=False, sort_keys=True, indent=2
        ).encode(),
    }


def _deserialize_HttpResponse(
    cls: Type[HttpResponse], data: SerializedLeafData
) -> HttpResponse:
    body = HttpResponseBody(data["body.html"])
    info = json.loads(data["info.json"])
    return cls(
        body=body,
        url=info["url"],
        status=info["status"],
        headers=info["headers"],
        encoding=info["_encoding"],
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
    for i, data in enumerate(o.get_saved_responses()):
        serialized_request = serialize_leaf(data.request)
        for k, v in serialized_request.items():
            serialized_data[f"{i}-HttpRequest.{k}"] = v
        serialized_response = serialize_leaf(data.response)
        for k, v in serialized_response.items():
            serialized_data[f"{i}-HttpResponse.{k}"] = v
    return serialized_data


def _deserialize_HttpClient(
    cls: Type[HttpClient], data: SerializedLeafData
) -> HttpClient:
    responses: List[SavedResponseData] = []

    serialized_requests: Dict[str, SerializedLeafData] = {}
    serialized_responses: Dict[str, SerializedLeafData] = {}
    for k, v in data.items():
        # k is number-("HttpRequest"|"HttpResponse").("body"|"info").ext
        key, type_suffix = k.split("-", 1)
        type_name, suffix = type_suffix.split(".", 1)
        if type_name == "HttpRequest":
            serialized_requests.setdefault(key, {})[suffix] = v
        elif type_name == "HttpResponse":
            serialized_responses.setdefault(key, {})[suffix] = v

    for key, serialized_request in serialized_requests.items():
        serialized_response = serialized_responses.get(key)
        if not serialized_response:
            continue
        request = deserialize_leaf(HttpRequest, serialized_request)
        response = deserialize_leaf(HttpResponse, serialized_response)
        responses.append(SavedResponseData(request, response))

    return cls(return_only_saved_responses=True, responses=responses)


register_serialization(_serialize_HttpClient, _deserialize_HttpClient)
