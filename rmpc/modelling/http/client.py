import logging
from typing import Optional

import furl
import requests
from requests import Response

from rmpc.modelling.http.utils import HttpMethods
from rmpc.modelling.typing.namespaces import BaseNamespace

logger = logging.getLogger(__name__)


__all__ = [
    "BaseClient",
]


class BaseClient:
    config: Optional[BaseNamespace] = None
    session: Optional[requests.Session] = None
    _host: Optional[str] = None
    _tenant: Optional[str] = None
    _fqdn: Optional[str] = None
    _auth_tenant: Optional[str] = None
    _base_url: Optional[furl.furl] = None
    _base_path: Optional[furl.Path] = None
    _url: Optional[furl.furl] = None

    @property
    def host(self) -> str:
        return self._host

    @host.setter
    def host(self, host: str):
        self._host = host
        self._update_host_or_tenant_hook()

    @property
    def tenant(self) -> str:
        return self._tenant

    @tenant.setter
    def tenant(self, tenant: str):
        self._tenant = tenant

        if not self.auth_tenant:
            self.auth_tenant = self.tenant

        self._update_host_or_tenant_hook()

    @property
    def fqdn(self) -> str:
        return self._fqdn

    @fqdn.setter
    def fqdn(self, fqdn: str | furl.furl):
        self._fqdn = furl.furl(
            host=furl.furl(fqdn).url.split("://", maxsplit=1)[-1]
        ).host

    @property
    def auth_tenant(self) -> str:
        return self._auth_tenant or self._tenant

    @auth_tenant.setter
    def auth_tenant(self, auth_tenant: str):
        self._auth_tenant = auth_tenant

    @property
    def base_url(self) -> furl.furl:
        return self._base_url.copy()

    @base_url.setter
    def base_url(self, url: str | furl.furl):
        self._base_url = furl.furl(url=url)

    @property
    def base_path(self) -> furl.Path:
        return self._base_path

    @base_path.setter
    def base_path(self, path: str | furl.Path):
        self._base_path = furl.Path(path)
        self._update_host_or_tenant_hook()

    @property
    def url(self) -> furl.furl:
        return furl.furl(self._url).copy()

    @url.setter
    def url(self, url: str | furl.furl):
        self._url = furl.furl(url)

    def __init__(self, **kwargs):
        self.host = kwargs.pop("host")
        self.tenant = kwargs.pop("tenant")
        self.base_path = kwargs.pop("base_path", None)
        self.auth_tenant = kwargs.pop("auth_tenant", self.tenant)
        self._update_host_or_tenant_hook()

        self.session = kwargs.get("session", None) or None

        if not self.session:
            self.session = requests.Session()

    @classmethod
    def from_rc_config(cls, cfg: BaseNamespace):
        kwargs = {}

        if not cfg.host:
            raise AttributeError("Host cannot be Empty")

        if not cfg.tenant:
            raise AttributeError("Tenant cannot be empty")

        client = cls(**cfg.to_dict())
        client.config = cfg

        return client

    def _update_host_or_tenant_hook(self):
        if self.host and self.tenant:
            self.base_url = furl.furl(f"https://{self.tenant}.{self.host}")
            self.fqdn = self.base_url.host
            self.url = furl.furl(url=self.base_url, path=furl.furl(self.base_path).url)

    def get(self, url: furl.furl | str, **kwargs) -> Response:
        return self.request(HttpMethods.GET, f"{url}", **kwargs)

    def post(self, url: furl.furl | str, **kwargs) -> Response:
        return self.request(HttpMethods.POST, f"{url}", **kwargs)

    def delete(self, url: furl.furl | str, **kwargs) -> Response:
        return self.request(HttpMethods.DELETE, f"{url}", **kwargs)

    def put(self, url: furl.furl | str, **kwargs) -> Response:
        return self.request(HttpMethods.PUT, f"{url}", **kwargs)

    def patch(self, url: furl.furl | str, **kwargs) -> Response:
        return self.request(HttpMethods.PATCH, f"{url}", **kwargs)

    def request(self, method: HttpMethods, url: furl.furl | str, *args, **kwargs):
        """
        Handles a base usage of url validation and management using furl, and then attempts to forward the request using
        the given Session methods for the current HttpMethod (e.g. if Method is GET, attempt to call Session.get),
        in order to handle the **kwargs as well as perform the default validations
        (e.g. Post should contain a data/json param, etc.)

        :param method: HTTP Method (i.e. One of ["GET", "PUT", "POST", "PATCH", "DELETE"])
        :param url: A String or Furl instance (if this isn't a full url, it will be added to self.url)
        :param args: List of *args as expected to be used by Session.request (or the particular Session Method)
        :param kwargs: Dict of **kwargs as expected to be used by Session.request (or the particular Session Method)
        :return: {requests.Response} - The Session.Response
        """

        if self.tenant and "tenant" not in kwargs:
            kwargs["tenant"] = self.tenant

        _url = f"{url}"

        url = furl.furl(f"{'https://' if '://' not in _url else ''}{_url}")

        if not url.host or not url.scheme:
            url = self.url.join(_url)

        assert url.scheme and url.host, "Invalid Furl Instance"

        # Fetch the session's method for the current method (e.g. session.get / session.post / etc.)
        session_req = getattr(self.session, method.name.lower(), None)

        if session_req and callable(session_req):
            return session_req(url.tostr(), *args, **kwargs)

        return self.session.request(method.name.upper(), url.tostr(), *args, **kwargs)
