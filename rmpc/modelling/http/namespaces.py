from __future__ import annotations

import logging
from typing import (
    Any,
    AnyStr,
    ClassVar,
    Dict,
    List,
    Optional,
    Sequence,
    Union,
)

import furl
import requests
from requests import JSONDecodeError

from rmpc.modelling.typing.namespaces import BaseNamespace

logger = logging.getLogger(__name__)


class HttpNamespace(BaseNamespace):
    @classmethod
    def from_response_object(
        cls, http_resp: requests.Response, **kwargs
    ) -> BaseNamespace:
        # If response content isn't JSON, convert content to None
        hide_non_json_response = kwargs.setdefault("hide_non_json_response", True)

        # If above option is False, and it isn't JSON, if len(content) higher than this value, trim content to value
        hide_response_body_if_longer_than = kwargs.setdefault(
            "hide_response_body_if_longer_than", 500
        )

        is_json = False
        try:
            content = http_resp.json()
            is_json = True

        except JSONDecodeError:
            _cnt = http_resp.content

            if (
                not hide_response_body_if_longer_than
                and _cnt
                and len(_cnt) > hide_response_body_if_longer_than
            ):
                _cnt_len = len(_cnt)
                _cnt_trim = _cnt[: max(0, hide_response_body_if_longer_than - 50)]
                _cnt = f"{_cnt_trim} <... +{len(_cnt_trim) - len(http_resp.content)} chars>"

            content = {"content": _cnt if not hide_non_json_response else None}

        return BaseNamespace(
            **content,
            __namespace_meta__=BaseNamespace(
                is_json=is_json,
                request=RequestNamespace.from_request_object(http_resp.request),
                response=ResponseNamespace.from_response_object(http_resp).to_dict(),
            ),
        )


class RequestNamespace(BaseNamespace):
    method: str
    url: furl.furl
    body: Optional[Any]
    headers: Dict[str, AnyStr]

    _default_allowed_fields: ClassVar = {"headers", "method", "body", "url"}

    @classmethod
    def from_request_object(
        cls, http_req: requests.PreparedRequest, **kwargs
    ) -> RequestNamespace:
        allowed_fields: Sequence[str] = kwargs.setdefault(
            "request_allowed_fields", list(cls._default_allowed_fields)
        )
        ignore_fields: Sequence[str] = kwargs.setdefault("request_ignored_fields", [])

        default_kwargs = {"headers", "method", "body"}.union(allowed_fields)

        # url is a special case that will be manually handled below
        default_kwargs.difference_update(["url", "headers"])

        req_ns_kwargs = {k: getattr(http_req, k, None) for k in list(default_kwargs)}

        # Update with all customized keys/objects
        req_ns_kwargs.update(
            {
                "url": furl.furl(http_req.url),
                "headers": dict(http_req.headers),
            }
        )

        ns_keys = list(req_ns_kwargs.keys())[:]
        for k in ns_keys:
            if k not in allowed_fields or k in ignore_fields:
                del req_ns_kwargs[k]

        return RequestNamespace(**req_ns_kwargs)


class ResponseNamespace(BaseNamespace):
    ok: bool
    reason: AnyStr
    status_code: int
    url: furl.furl
    history: List[Union[furl.furl, ResponseNamespace]]

    _default_allowed_fields: ClassVar = {
        "ok",
        "reason",
        "status_code",
        "url",
        "history",
    }

    @classmethod
    def from_response_object(
        cls, http_resp: requests.Response, **kwargs
    ) -> ResponseNamespace:
        allowed_fields: Sequence[str] = kwargs.setdefault(
            "response_allowed_fields", list(cls._default_allowed_fields)
        )
        ignore_fields: Sequence[str] = kwargs.setdefault("response_ignored_fields", [])

        default_kwargs = {"ok", "reason", "status_code"}.union(allowed_fields)

        # url and history are special cases that will be manually handled below
        default_kwargs.difference_update(["url", "history"])

        resp_ns_kwargs = {k: getattr(http_resp, k) for k in list(default_kwargs)}

        # Update with all customized keys/objects
        resp_ns_kwargs.update(
            {
                "url": furl.furl(http_resp.url),
                "history": list(
                    map(ResponseNamespace.from_response_object, http_resp.history or [])
                ),
            }
        )

        ns_keys = list(resp_ns_kwargs.keys())[:]
        for k in ns_keys:
            if k not in allowed_fields or k in ignore_fields:
                del resp_ns_kwargs[k]

        return ResponseNamespace(**resp_ns_kwargs)
