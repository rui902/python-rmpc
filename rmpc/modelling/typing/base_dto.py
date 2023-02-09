import abc

import requests

from rmpc.modelling.http.namespaces import HttpNamespace
from rmpc.modelling.typing.namespaces import BaseNamespace


class BaseDto(BaseNamespace):
    @classmethod
    def from_http_response(cls, http_resp: requests.Response):
        return cls.from_namespace(HttpNamespace.from_response_object(http_resp))

    @classmethod
    def from_namespace(cls, ns: BaseNamespace):
        return cls.from_dict(ns.to_dict())

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, d: dict, **kwargs):
        raise NotImplementedError()
