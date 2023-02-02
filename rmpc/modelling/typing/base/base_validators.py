import logging
from abc import ABC, abstractmethod
from typing import Optional


class Validator(ABC):
    owner: object = None
    fqdn: str = ""
    real_name: str = ""
    private_name: str = ""
    required: bool = False

    def __init__(self, required: bool = False, *args, **kwargs):
        self.required = required
        super().__init__(*args, **kwargs)

    def __set_name__(self, owner, name):
        self.owner = owner
        self.real_name = f"{name}"
        self.fqdn = f"{owner.__qualname__}.{name}"
        self.private_name = "_" + name

    def __get__(self, obj, obj_type=None):
        if not hasattr(obj, self.private_name):
            return self.raise_validation_exception(AttributeError(self.private_name)) or None

        value = getattr(obj, self.private_name)
        return value

    def __set__(self, obj, value):
        if self.validate(value) is not False:
            setattr(obj, self.private_name, value)

    @abstractmethod
    def validate(self, value) -> Optional[bool]:
        raise NotImplementedError

    def raise_validation_exception(self, exc: Exception) -> bool:
        if self.required is True:
            raise exc

        else:
            return False


if __name__ == "__main__":
    logging.warning("Running %r", __name__)
