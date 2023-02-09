from __future__ import annotations

import json
import logging
from typing import (
    Dict,
)

from munch import DefaultMunch

logger = logging.getLogger(__name__)


class BaseNamespace(DefaultMunch):
    @classmethod
    def from_dict(cls, d: Dict, **kwargs):
        return cls.fromDict(d, **kwargs)

    def to_dict(self):
        return self.toDict()

    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, default=str, **kwargs)

    @property
    def __dict__(self):
        return dict(self.to_dict())

    def __hash__(self):
        return hash(self.__dict__)

    def __repr__(self):
        dict_repr = ", ".join([f"{k}={getattr(self, k)!r}" for k in self])
        return (
            f"{self.__class__.__qualname__}("
            f"{dict_repr}"
            f")"
        )

    def __str__(self):
        return self.to_json()
