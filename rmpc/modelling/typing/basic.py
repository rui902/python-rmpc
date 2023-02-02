from typing import List, Callable, Iterable

from rmpc.modelling.typing.base.base_validators import Validator


class OneOf(Validator):
    def __init__(self, enum: Iterable = None, *options, **kwargs):
        super().__init__(*options, **kwargs)
        self.options = set()

        if enum is not None and isinstance(enum, Iterable):
            self.options.update(set({o.name for o in enum}))

        else:
            self.options.update(set(options))

        for opt in self.options:
            setattr(self, opt, opt)

    def validate(self, value):
        if value not in self.options:
            # If value is an enum option, try to get the name of the option, instead of checking the instance itself
            opt_name = getattr(value, "name", None)
            if opt_name is None or opt_name not in self.options:
                return self.raise_validation_exception(
                    ValueError(
                        f"Expected {self.real_name}(value={value!r}) to be one of {self.options!r}"
                    )
                )

        return True


class Number(Validator):
    def __init__(self, minvalue=None, maxvalue=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    def validate(self, value):
        if not isinstance(value, (int, float)):
            return self.raise_validation_exception(
                TypeError(
                    f"Expected {self.real_name}(value={value!r}) to be an int or float"
                )
            )

        if self.minvalue is not None and value < self.minvalue:
            return self.raise_validation_exception(
                ValueError(
                    f"Expected {self.real_name}(value={value!r}) to be at least {self.minvalue!r}"
                )
            )

        if self.maxvalue is not None and value > self.maxvalue:
            return self.raise_validation_exception(
                ValueError(
                    f"Expected {self.real_name}(value={value!r}) to be no more than {self.maxvalue!r}"
                )
            )

        return True


class String(Validator):
    def __init__(
        self,
        minsize=None,
        maxsize=None,
        extra_validations: List[Callable] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.minsize = minsize
        self.maxsize = maxsize
        self.extra_validations = extra_validations

    def validate(self, value):
        if not isinstance(value, str):
            return self.raise_validation_exception(
                TypeError(f"Expected {self.real_name}(value={value!r}) to be an str")
            )

        if self.minsize is not None and len(value) < self.minsize:
            return self.raise_validation_exception(
                ValueError(
                    f"Expected {self.real_name}(value={value!r}) to be no smaller than {self.minsize!r}"
                )
            )

        if self.maxsize is not None and len(value) > self.maxsize:
            return self.raise_validation_exception(
                ValueError(
                    f"Expected {self.real_name}(value={value!r}) to be no bigger than {self.maxsize!r}"
                )
            )

        if self.extra_validations:
            for validate in self.extra_validations:
                if not validate(value):
                    return self.raise_validation_exception(
                        ValueError(f"Expected {validate} to be true for {value!r}")
                    )

        return True


if __name__ == "__main__":
    from enum import Enum, auto

    class Kinds(Enum):
        wood = auto()
        metal = auto()
        plastic = auto()

    class Component:
        name = String(
            minsize=3, maxsize=10, extra_validations=[str.isupper], required=True
        )
        kind = OneOf(Kinds, required=False)
        quantity = Number(minvalue=0)

        def __init__(self, name=None, kind=None, quantity=None):
            self.name = name
            self.kind = kind
            self.quantity = quantity

    c1 = Component("TEST")
    print("Testing Valid Component: %r" % c1)
    print("c1.name: %r" % c1.name)
    print("c1.kind: %r" % c1.kind)
    print("c1.quantity: %r" % c1.quantity)

    c2 = Component()
    print("Testing Invalid Component: %r" % c2)
    print("c2.name: %r" % c2.name)
    print("c2.kind: %r" % c2.kind)
    print("c2.quantity: %r" % c2.quantity)
