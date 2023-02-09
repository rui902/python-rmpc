from __future__ import annotations

import logging
import re
from typing import (
    AnyStr,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Type,
    Union,
)

import furl
import requests

from rmpc.modelling.http.dto_response import DtoResponse
from rmpc.modelling.http.client import BaseClient
from rmpc.modelling.http.utils import HttpMethods

logger = logging.getLogger(__name__)


class BaseHttpEndpoint:
    parent_api: Optional[BaseHttpApi] = None
    methods: Set = set({})
    _url: Optional[Union[furl.furl, furl.Path]] = None
    _client: Optional[BaseClient] = None
    _session: Optional[Union[requests.Session]] = None

    _all_methods: ClassVar = {"GET", "PUT", "POST", "DELETE"}

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = self.parent_api.session

        return self._session

    @session.setter
    def session(self, session: Union[requests.Session]):
        self._session = session

    @property
    def client(self) -> BaseClient:
        if self._client is None:
            self._client = self.parent_api.client

        return self._client

    @client.setter
    def client(self, client: BaseClient):
        self._client = client

    @property
    def url(self) -> furl.furl:
        return furl.furl(self._url).copy()

    @url.setter
    def url(self, url: Union[AnyStr, furl.Path, furl.furl]):
        self._url = furl.furl(url).copy()

    def __init__(self, parent_api: BaseHttpApi):
        if not self.url:
            raise AttributeError("URL is Required")

        if not parent_api:
            raise AttributeError("Parent API is required")

        self.parent_api = parent_api

        if not isinstance(self.url, furl.furl):
            self.url = furl.furl(self.url)

        self.url = furl.furl(parent_api.url).add(path=furl.furl(self.url).url)

    def get(self, url: Union[furl.furl, str], *args, **kwargs) -> DtoResponse:
        return self.request(HttpMethods.GET, url=url, *args, **kwargs)

    def put(self, url: Union[furl.furl, str], *args, **kwargs) -> DtoResponse:
        return self.request(HttpMethods.PUT, url=url, *args, **kwargs)

    def post(self, url: Union[furl.furl, str], *args, **kwargs) -> DtoResponse:
        return self.request(HttpMethods.POST, url=url, *args, **kwargs)

    def delete(self, url: Union[furl.furl, str], *args, **kwargs) -> DtoResponse:
        return self.request(HttpMethods.DELETE, url=url, *args, **kwargs)

    def request(
        self, method: HttpMethods, url: Union[furl.furl, str], *args, **kwargs
    ) -> DtoResponse:
        if method not in BaseHttpEndpoint._all_methods:
            raise AttributeError(f"Invalid method {method!r}")

        dto = kwargs.pop("dto", None)
        url = furl.furl(url, query_params=kwargs.pop("query_params", {})).tostr()

        return DtoResponse.from_http_response(self.client.request(method, url, *args, **kwargs), dto=dto)


class ApiEndpointList:
    bases: Optional[Dict[AnyStr, Type[BaseHttpEndpoint]]] = None
    _endpoints: Optional[Dict[BaseHttpEndpoint]] = None

    @property
    def items(self):
        if self._endpoints is None:
            self._endpoints = {}

        return self._endpoints

    def __init__(self, *args, **kwargs):
        if self._endpoints is None:
            self._endpoints = {}

        if self.bases is None:
            self.bases = {}

        if list(args):
            if not all(
                isinstance(v, type) and v.__class__ is BaseHttpEndpoint.__class__
                for v in args
            ):
                raise TypeError(
                    f"All endpoints must be subclass of {BaseHttpEndpoint!r}"
                )

            self.update_bases_from_list(list(args))

        if kwargs and not all(
            isinstance(k, str)
            and isinstance(v, type)
            and v.__class__ is BaseHttpEndpoint.__class__
            for k, v in kwargs.items()
        ):
            self.update_bases_from_dict(kwargs)

    def init(self, parent_api: BaseHttpApi):
        for base_ep_name, base_ep_cls in self.bases.items():
            base_ep_name = base_ep_name.lower()
            endpoint = base_ep_cls(parent_api)
            self.add_endpoint(endpoint, base_ep_name)

    def add_endpoint(self, endpoint: BaseHttpEndpoint, endpoint_name: AnyStr = None):
        if not endpoint_name:
            endpoint_name = BaseHttpApi.normalize_endpoint_name(
                type(endpoint).__name__
            ).lower()

        if type(endpoint) not in self.bases.values():
            self.update_bases_from_dict({type(endpoint).__name__: type(endpoint)})

        self._endpoints[endpoint_name] = endpoint

        setattr(self, endpoint_name, endpoint)

        return endpoint_name

    def update_bases_from_dict(self, bases: Dict[AnyStr, Type[BaseHttpEndpoint]]):
        bases_copy = dict(bases)
        for original_key, v in bases_copy.items():
            k = BaseHttpApi.normalize_endpoint_name(original_key)

            if not k.isidentifier():
                raise AttributeError(f"Endpoint {k!r} isn't a valid name")

            if not isinstance(v, type) or v.__class__ is not BaseHttpEndpoint.__class__:
                raise TypeError(f"{v!r} isn't of type {type(BaseHttpEndpoint)}")

            del bases[original_key]
            bases[k] = v

        self.bases.update(**bases)

    def update_bases_from_list(self, bases: List[Type[BaseHttpEndpoint]]):
        new_bases = {}

        for v in bases:
            k = BaseHttpApi.normalize_endpoint_name(v.__name__)

            if not k.isidentifier():
                raise AttributeError(f"Endpoint {k!r} isn't a valid name")

            if not isinstance(v, type) or v.__class__ is not BaseHttpEndpoint.__class__:
                raise TypeError(f"{v!r} isn't of type {type(BaseHttpEndpoint)}")

            new_bases[k] = v

        self.bases.update(**new_bases)

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __getattr__(self, item):
        if (
            item not in self.__dict__
            and item not in self.items
            and (item in list(map(str.lower, self.bases)) or item in self.bases)
        ):
            raise NotImplementedError(
                f"Must initialize {self.__qualname__!r} before accessing the endpoints"
            )

        return getattr(super(), item)


class BaseHttpApi:
    client: Optional[BaseClient] = None
    url: Optional[furl.furl] = None
    endpoints: Optional[ApiEndpointList] = ApiEndpointList()
    auto_init_endpoints: bool = True
    _session: Optional[Union[requests.Session]] = None

    valid_ep_regex: ClassVar = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]+$", flags=re.I)
    invalid_ep_regex: ClassVar = re.compile(r"\W+", flags=re.I)

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()

        return self._session

    @session.setter
    def session(self, session: Union[requests.Session]):
        self._session = session

    def __init__(self, **kwargs):
        self.client = kwargs.pop("client", None)

        session = kwargs.pop("session", getattr(self.client, "session", None))
        if session:
            self.session = session

        url = kwargs.pop("url", None)
        if url is not None:
            self.url = furl.furl(url, path=furl.furl(self.url).url)

        if not self.url:
            raise NotImplementedError(
                f"Must Set default value for: {self.url.__qualname__!r}"
            )

        if len(self.endpoints) > 0 and self.auto_init_endpoints is True:
            self.endpoints.init(self)

    @classmethod
    def normalize_endpoint_name(cls, ep_name):
        if BaseHttpApi.valid_ep_regex.match(ep_name) and ep_name.isidentifier():
            return ep_name

        new_ep_name = BaseHttpApi.invalid_ep_regex.sub("_", ep_name)
        if BaseHttpApi.valid_ep_regex.match(new_ep_name) and new_ep_name.isidentifier():
            return new_ep_name

        raise AttributeError(f"Invalid Endpoint Name: {ep_name!r}")

    def __get_or_init_endpoint__(self, cls: Type[BaseHttpEndpoint]):
        private_prop_name = (
            f"_ep_"
            f"{getattr(self, '__qualname__', self.__class__.__qualname__)}_"
            f"{getattr(cls, '__qualname__', cls.__class__.__qualname__)}"
        ).replace(".", "_")

        ep = getattr(self, private_prop_name, None)
        if ep:
            return ep

        ep = cls(self)
        self.endpoints.add_endpoint(ep)
        setattr(self, private_prop_name, ep)
        return ep


if __name__ == "__main__":
    logger.debug("Test")
