import inspect
from datetime import datetime, timedelta, date, time
from typing import Mapping, Iterable, List, Tuple, Dict

import requests
from pythonjsonlogger import jsonlogger

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class CustomJsonEncoder(jsonlogger.JsonEncoder):
    allowed_attrs = {
        "format_request_obj": ["auth", "data", "files", "headers", "json", "method", "params", "url"],
        "format_response_obj": ["content", "elapsed", "encoding", "headers", "reason", "request", "status_code", "url"],
    }

    ignored_attr = {
        "format_request_obj": ["cookies", "deregister_hook", "hooks", "prepare", "register_hook"],
        "format_response_obj": ["history", "text", "raw", "cookies"],
    }

    def encode(self, o):
        o = self.default(o)
        return super().encode(o)

    def default(self, obj):
        try:
            return type(self).encode_object(obj)

        except NotImplemented:
            logger.warning("No Custom Formatter Implemented for Type %r", type(obj))

        return super().default(obj)

    @classmethod
    def get_last_valid_attr_caller(cls):
        invalid_names = ["get_last_valid_attr_caller", "format_default_complex_obj", "get_valid_attrs"]
        valid_caller_prefix = "format_"
        fn_name = None

        for i in range(len(invalid_names) + 3):
            fn_name = inspect.stack()[i+1].function
            fn_name = str(fn_name) if fn_name else None
            if fn_name not in invalid_names and fn_name.startswith(valid_caller_prefix):
                return fn_name

        return fn_name

    @classmethod
    def get_valid_attrs(cls, obj):
        fn_name = cls.get_last_valid_attr_caller()

        available_attrs = []
        if hasattr(cls, "allowed_attrs") and isinstance(cls.allowed_attrs, dict):
            available_attrs = cls.allowed_attrs.get(type(obj).__name__, cls.allowed_attrs.get(fn_name, []))
            available_attrs = [a for a in available_attrs if a and hasattr(obj, a) and not callable(getattr(obj, a))]

        if not available_attrs:
            obj_dir = dir(obj)
            available_attrs = [k for k in obj_dir if not k.startswith("_") and not callable(getattr(obj, k))]

        ignored_attrs = []
        if hasattr(cls, "ignored_attr") and isinstance(cls.ignored_attr, dict):
            ignored_attrs = cls.ignored_attr.get(type(obj).__name__, cls.ignored_attr.get(fn_name, []))

        valid_attrs = available_attrs[:]
        if any(available_attrs) and any(ignored_attrs):
            valid_attrs = [e for e in available_attrs if e not in ignored_attrs]

        return valid_attrs

    @classmethod
    def encode_object(cls, obj):
        if obj is None:
            return None

        if not obj:
            # Treat False/Empty Objects as None, except for int/float (0) and bool (False)
            if not isinstance(obj, (int, float, bool)):
                return None

        if isinstance(obj, (int, float, str, bool)):
            return obj

        if isinstance(obj, bytes):
            return cls.format_bytes_obj(obj)

        if isinstance(obj, (date, time, datetime)):
            return cls.format_datetime_obj(obj)

        if isinstance(obj, timedelta):
            return cls.format_timedelta_obj(obj)

        if isinstance(obj, (requests.Request, requests.PreparedRequest)):
            return cls.format_request_obj(obj)

        if isinstance(obj, requests.Response):
            return cls.format_response_obj(obj)

        if hasattr(obj, "__dict__") or isinstance(obj, (dict, Mapping)):
            return cls.format_mapping_obj(obj)

        if hasattr(obj, "__iter__") or isinstance(obj, (list, tuple, Iterable, List)):
            return cls.format_iterable_obj(obj)

        return NotImplemented

    @classmethod
    def format_datetime_obj(cls, obj: date | time | datetime) -> str:
        return obj.isoformat()

    @classmethod
    def format_timedelta_obj(cls, obj: timedelta) -> float | int:
        return obj.total_seconds()

    @classmethod
    def format_bytes_obj(cls, obj: bytes) -> str:
        return str(obj.decode("utf-8"))

    @classmethod
    def format_default_complex_obj(cls, obj) -> Tuple[Dict, Iterable]:
        attrs = cls.get_valid_attrs(obj)

        if not attrs:
            return cls.encode_object(getattr(obj, "__dict__", None)), []

        return cls.encode_object({
            k: v
            for k, v in {
                attr: cls.encode_object(getattr(obj, attr, None) or None)
                for attr in attrs
            }.items()
            if k and v
        }), attrs

    @classmethod
    def format_request_obj(cls, obj: requests.Request | requests.PreparedRequest) -> dict:
        formatted_obj, attrs = cls.format_default_complex_obj(obj)
        return formatted_obj

    @classmethod
    def format_response_obj(cls, obj: requests.Response) -> dict:
        formatted_obj, attrs = cls.format_default_complex_obj(obj)

        if "content" in attrs:
            try:
                resp_content = obj.json()
            except requests.exceptions.JSONDecodeError:
                try:
                    resp_content = obj.text
                except RuntimeError:
                    resp_content = obj.content

            formatted_obj["content"] = cls.encode_object(resp_content)

        return formatted_obj

    @classmethod
    def format_mapping_obj(cls, obj: dict | Mapping) -> dict | None:
        return {
            k: v
            for k, v in {
                k: cls.encode_object(v)
                for k, v in dict(getattr(obj, "__dict__", obj)).items()
            }.items()
            if k and v
        }

    @classmethod
    def format_iterable_obj(cls, obj: list | tuple | Iterable) -> list:
        return [cls.encode_object(e) for e in obj if e]
