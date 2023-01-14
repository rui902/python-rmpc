import logging
from abc import ABC, abstractmethod


class Validator(ABC):
    private_name: str = ""

    def __set_name__(self, owner, name):
        self.private_name = "_" + name

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        self.validate(value)
        setattr(obj, self.private_name, value)

    @abstractmethod
    def validate(self, value):
        pass


if __name__ == "__main__":
    logging.warning("Running %r", __name__)
