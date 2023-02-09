import json
import logging
from datetime import datetime
from typing import Mapping, List, Dict

import requests
from pythonjsonlogger import jsonlogger
from requests import JSONDecodeError

from rmpc.logging.encoders.custom.json import CustomJsonEncoder

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def __init__(self, *args, **kwargs):
        self.disable_extra_fields = kwargs.pop("disable_extra_fields", False)
        custom_json_default = kwargs.pop("custom_json_default", None)
        if custom_json_default:
            kwargs.setdefault("json_default", custom_json_default)

        custom_json_encoder: CustomJsonEncoder | None = kwargs.pop(
            "custom_json_encoder", CustomJsonEncoder
        )
        if custom_json_encoder:
            kwargs.setdefault("json_encoder", custom_json_encoder)

        kwargs.setdefault("json_serializer", self.custom_serializer)
        kwargs.setdefault("json_ensure_ascii", True)

        super().__init__(*args, **kwargs)

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Recreate Level
        log_record["level"] = (
            getattr(log_record, "level", getattr(record, "levelname", None)) or "INFO"
        ).upper()

        # Recreate Timestamp
        log_record["timestamp"] = log_record.get("timestamp", datetime.now())
        if isinstance(log_record["timestamp"], datetime):
            log_record["timestamp"] = log_record["timestamp"].isoformat()

        message_dict = self.filter_message_dict_entries(message_dict)
        log_record.update(**message_dict)

    def filter_message_dict_entries(self, message_dict: dict):
        if not message_dict:
            return message_dict

        for k, v in dict(message_dict).items():
            if isinstance(v, (requests.Request, requests.PreparedRequest)):
                message_dict[k] = type(self).filter_request_object(v)

            elif isinstance(v, requests.Response):
                message_dict[k] = type(self).filter_response_object(v)

        return message_dict

    @classmethod
    def filter_request_object(cls, obj: requests.Request | requests.PreparedRequest):
        if not obj:
            return obj

        return {
            "body": getattr(obj, "body", None),
            "headers": cls.filter_headers_object(getattr(obj, "headers", None)),
            "method": getattr(obj, "method", None),
            "url": getattr(obj, "url", None),
        }

    @classmethod
    def filter_headers_object(cls, obj: dict | Mapping | Dict):
        if not obj:
            return obj

        return {
            k: (
                cls.filter_headers_object(v)
                if hasattr(v, "__dict__") or isinstance(v, (Dict, Mapping))
                else v
            )
            for k, v in obj.items()
            if k not in ["_store"]
        }

    @classmethod
    def filter_response_object(cls, obj: requests.Response):
        if not obj:
            return obj

        content = getattr(obj, "content", None)
        try:
            content = obj.json()
        except JSONDecodeError:
            pass

        if isinstance(content, bytes):
            content = content.decode("utf-8")

        return {
            "content": content,
            "status_code": getattr(obj, "status_code", None),
            "headers": cls.filter_headers_object(getattr(obj, "headers", None)),
            "url": getattr(obj, "url", None),
            "encoding": getattr(obj, "encoding", None),
            "reason": getattr(obj, "reason", None),
            "elapsed": obj.elapsed.total_seconds(),
            "request": cls.filter_request_object(getattr(obj, "request", None)),
        }

    def process_message_dict(self, log_record: dict):
        if not isinstance(log_record, dict):
            log_record = getattr(log_record, "__dict__", dict(log_record))

        message_dict = {}
        for k in [k for k in ["extra", "args", "msg", "message"] if k in log_record]:
            v = type(self).customize_kv_pairs(k, log_record.pop(k, None))
            if v and isinstance(v, dict):
                message_dict.update(v)

        return message_dict

    def format(self, record):
        log_record = dict(getattr(record, "__dict__", {}))
        message_dict = self.process_message_dict(log_record)
        self.add_fields(log_record, record, message_dict)
        log_record = self.process_log_record(log_record)
        return self.serialize_log_record(log_record)

    @staticmethod
    def custom_serializer(obj, *args, **kwargs):
        kwargs.setdefault("sort_keys", True)
        return json.dumps(obj, *args, **kwargs)

    def process_log_record(self, log_record):
        log_record = dict(super().process_log_record(dict(log_record)) or {})

        log_record = {k: v for k, v in log_record.items() if k and v}

        if self.disable_extra_fields:
            log_record = {
                k: v
                for k, v in log_record.items()
                if k and k not in [
                    "filename",
                    "funcName",
                    "levelname",
                    "lineno",
                    "module",
                    "name",
                    "pathname",
                ]
            }

        return (
            type(self.json_encoder).encode_object(log_record)
            if isinstance(self.json_encoder, CustomJsonEncoder)
            else log_record
        )

    @classmethod
    def customize_kv_pairs(cls, key, obj):
        if not obj:
            return {}

        if isinstance(obj, (requests.Request, requests.PreparedRequest)):
            return {
                "request": obj,
            }

        if isinstance(obj, requests.Response):
            return {
                "response": obj,
            }

        if isinstance(obj, (dict, Mapping)):
            return {k: v for k, v in obj.items()}

        if not isinstance(obj, (int, float, str, bytes, bool)):
            if isinstance(obj, (list, tuple, List)):
                obj = [e for e in obj if e]

        # Default just repeat the original key
        return {key: obj}
