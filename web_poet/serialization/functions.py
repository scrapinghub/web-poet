from __future__ import annotations

import json
from typing import Any, cast

from .. import (
    HttpClient,
    HttpRequest,
    HttpRequestBody,
    HttpResponse,
    HttpResponseBody,
    PageParams,
    Stats,
)
from ..annotated import AnnotatedInstance
from ..exceptions import HttpError
from ..page_inputs.client import _SavedResponseData
from ..page_inputs.url import _Url
from .api import (
    SerializedLeafData,
    _get_name_for_class,
    deserialize_leaf,
    load_class,
    register_serialization,
    serialize_leaf,
)
from .utils import _exception_from_dict, _exception_to_dict, _format_json


def _serialize_HttpRequest(o: HttpRequest) -> SerializedLeafData:
    info = {
        "url": str(o.url),
        "method": o.method,
        "headers": list(o.headers.items()),
    }
    result: SerializedLeafData = {
        "info.json": _format_json(info).encode(),
    }
    if o.body:
        result["body.txt"] = bytes(o.body)
    return result


def _deserialize_HttpRequest(
    cls: type[HttpRequest], data: SerializedLeafData
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
        "info.json": _format_json(info).encode(),
    }


def _deserialize_HttpResponse(
    cls: type[HttpResponse], data: SerializedLeafData
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
    cls: type[HttpResponseBody], data: SerializedLeafData
) -> HttpResponseBody:
    return cls(data["html"])


register_serialization(_serialize_HttpResponseBody, _deserialize_HttpResponseBody)


def _serialize__Url(o: _Url) -> SerializedLeafData:
    return {"txt": str(o).encode()}


def _deserialize__Url(cls: type[_Url], data: SerializedLeafData) -> _Url:
    return cls(data["txt"].decode())


register_serialization(_serialize__Url, _deserialize__Url)


def _serialize_HttpClient(o: HttpClient) -> SerializedLeafData:
    serialized_data: SerializedLeafData = {
        "exists": b"",
    }
    for i, data in enumerate(o.get_saved_responses()):
        serialized_request = serialize_leaf(data.request)
        for k, v in serialized_request.items():
            serialized_data[f"{i}-HttpRequest.{k}"] = v
        if data.response:
            serialized_response = serialize_leaf(data.response)
            for k, v in serialized_response.items():
                serialized_data[f"{i}-HttpResponse.{k}"] = v
        if data.exception:
            # the request attribute is currently not saved
            exc_data = _exception_to_dict(data.exception)
            serialized_data[f"{i}-exception.json"] = _format_json(exc_data).encode()
    return serialized_data


def _deserialize_HttpClient(
    cls: type[HttpClient], data: SerializedLeafData
) -> HttpClient:
    responses: list[_SavedResponseData] = []

    serialized_requests: dict[str, SerializedLeafData] = {}
    serialized_responses: dict[str, SerializedLeafData] = {}
    serialized_exceptions: dict[str, SerializedLeafData] = {}
    for k, v in data.items():
        if k == "exists":
            continue
        # k is number-("HttpRequest"|"HttpResponse").("body"|"info").ext
        # or number-"exception.json"
        key, type_suffix = k.split("-", 1)
        type_name, suffix = type_suffix.split(".", 1)
        if type_name == "HttpRequest":
            serialized_requests.setdefault(key, {})[suffix] = v
        elif type_name == "HttpResponse":
            serialized_responses.setdefault(key, {})[suffix] = v
        elif type_name == "exception":
            serialized_exceptions.setdefault(key, {})[suffix] = v

    for key, serialized_request in serialized_requests.items():
        serialized_response = serialized_responses.get(key)
        serialized_exception = serialized_exceptions.get(key)
        if not serialized_response and not serialized_exception:
            continue
        request = deserialize_leaf(HttpRequest, serialized_request)
        if serialized_response:
            response = deserialize_leaf(HttpResponse, serialized_response)
        else:
            response = None
        exception: HttpError | None
        if serialized_exception:
            exc_data = json.loads(serialized_exception["json"])
            exception = cast("HttpError", _exception_from_dict(exc_data))
        else:
            exception = None
        responses.append(_SavedResponseData(request, response, exception))

    return cls(return_only_saved_responses=True, responses=responses)


register_serialization(_serialize_HttpClient, _deserialize_HttpClient)


def _serialize_PageParams(o: PageParams) -> SerializedLeafData:
    return {"json": _format_json(o).encode()}


def _deserialize_PageParams(
    cls: type[PageParams], data: SerializedLeafData
) -> PageParams:
    return cls(json.loads(data["json"]))


register_serialization(_serialize_PageParams, _deserialize_PageParams)


def _serialize_Stats(o: Stats) -> SerializedLeafData:
    return {}


def _deserialize_Stats(cls: type[Stats], data: SerializedLeafData) -> Stats:
    return cls()


register_serialization(_serialize_Stats, _deserialize_Stats)


def _serialize_AnnotatedInstance(o: AnnotatedInstance) -> SerializedLeafData:
    serialized_data: SerializedLeafData = {
        "metadata.json": _format_json(o.metadata).encode(),
        "result_type.txt": _get_name_for_class(type(o.result)).encode(),
    }
    serialized_result = serialize_leaf(o.result)
    for k, v in serialized_result.items():
        serialized_data["result-" + k] = v
    return serialized_data


def _deserialize_AnnotatedInstance(
    cls: type[AnnotatedInstance], data: SerializedLeafData
) -> AnnotatedInstance:
    metadata = json.loads(data["metadata.json"])
    result_type = load_class(data["result_type.txt"].decode())
    serialized_result = {}
    for k, v in data.items():
        if not k.startswith("result-"):
            continue
        serialized_result[k.split("-", 1)[1]] = v
    result: Any = deserialize_leaf(result_type, serialized_result)

    return cls(result=result, metadata=metadata)


register_serialization(_serialize_AnnotatedInstance, _deserialize_AnnotatedInstance)
