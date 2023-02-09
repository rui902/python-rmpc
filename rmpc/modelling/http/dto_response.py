from __future__ import annotations

from typing import Type, TypeVar

import requests

from ripcord.modelling.typing.base_dto import BaseDto


T = TypeVar("T", bound=BaseDto)


class DtoResponse(requests.Response):
    __dto_cls__: Type[T]
    _dto: T

    @property
    def dto(self) -> T:
        if not getattr(self, "_dto", None):
            self._dto = self.__dto_cls__.from_http_response(self)

        return self._dto

    @classmethod
    def from_http_response(cls, response: requests.Response, dto: Type[T] = None) -> DtoResponse:
        obj: DtoResponse = DtoResponse()

        for k, v in response.__dict__.items():
            setattr(obj, k, v)

        if dto:
            obj.__dto_cls__ = dto

        return obj

    def __repr__(self):
        return f"<{self.__class__.__qualname__} [{self.status_code}], DTO Class: {self.__dto_cls__.__qualname__}>"
