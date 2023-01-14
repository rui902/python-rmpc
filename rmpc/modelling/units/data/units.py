from __future__ import annotations

import math
from enum import Enum


def get_unit_bytes_value(num: int | float | Unit | Units):
    if isinstance(num, Unit):
        return num.bytes

    if isinstance(num, Units):
        return num.value

    return num


class Units(Enum):
    B = (1, "Byte")
    KB = (1 << 10, "Kilobyte")
    MB = (1 << 20, "Megabyte")
    GB = (1 << 30, "Gigabyte")
    TB = (1 << 40, "Terabyte")
    PB = (1 << 50, "Petabyte")
    YB = (1 << 60, "Exabyte")
    ZB = (1 << 70, "Zettabyte")
    EB = (1 << 80, "Yottabyte")

    @property
    def full_name(self) -> str:
        return self._full_name_

    @property
    def value(self) -> int:
        return self._value_

    def __new__(cls, value: int | float, full_name: str = None):
        obj = object.__new__(cls)
        obj._value_ = int(value)
        obj._full_name_ = full_name

        return obj

    def __init__(self, value: int, full_name: str = None):
        self._value_ = int(value)
        self._full_name_ = full_name

    def __repr__(self):
        return f"Units(Name={self.name}, FullName={self.full_name}, Bytes={self.value})"

    def __str__(self):
        return self.name

    def __lt__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.value < other_value

    def __le__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.value <= other_value

    def __eq__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.value == other_value

    def __ne__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.value != other_value

    def __gt__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.value > other_value

    def __ge__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.value >= other_value


class Unit:
    value: float
    base_unit: Units

    def __init__(self, num: int | float, target_unit: Units = Units.B, auto_update_unit=False):
        self.value = float(num)
        self.base_unit = target_unit

        if auto_update_unit:
            self.convert_to_highest_unit()

    @property
    def bytes(self):
        return int(self.value * self.base_unit.value)

    def get_unit_value(self, target_unit: Units):
        return float(self.bytes) / target_unit.value

    def convert_to(self, target_unit: Units):
        self.value = self.get_unit_value(target_unit)
        self.base_unit = target_unit
        return self

    def convert_to_highest_unit(self):
        highest_unit = self.highest_unit()
        self.value = highest_unit.value
        self.base_unit = highest_unit.base_unit
        return self

    def pretty_print(self):
        highest_unit = self.highest_unit()

        unit_name = highest_unit.base_unit.name
        value = highest_unit.value

        if value == 0 or value % math.floor(value) == 0:
            # Convert to int when number ends in ".0"
            value = int(value)

        return "%s%s" % (value, unit_name)

    def highest_unit(self) -> Unit:
        num_bytes = self.bytes

        if num_bytes == 0:
            return Unit(0, Units.B)

        units_list = [u for u in Units]
        i = int(math.floor(math.log(abs(num_bytes), 1024)))
        p = math.pow(1024, i)
        s = round(num_bytes / p, 2)

        return Unit(s, units_list[i])

    @classmethod
    def __parse_aritmethic_objs__(cls, unit_1: int | float | Unit | Units, unit_2: int | float | Unit | Units):
        # 1. Get Bytes for each of the Units being compared
        bytes_u1 = get_unit_bytes_value(unit_1)
        bytes_u2 = get_unit_bytes_value(unit_2)

        # 2. Convert to a <Unit> Instance, and convert both to the highest base unit of each
        new_u1 = Unit(bytes_u1, Units.B).convert_to_highest_unit()
        new_u2 = Unit(bytes_u2, Units.B).convert_to_highest_unit()

        # 3. Find the Highest Base Unit among them
        highest_base_unit = new_u1.base_unit if new_u1.base_unit > new_u2.base_unit else new_u2.base_unit

        # 4. Convert both to the Highest Base Unit and compare the values when both have the same unit
        return new_u1.convert_to(highest_base_unit).value, new_u2.convert_to(highest_base_unit).value, highest_base_unit

    def __str__(self):
        return self.pretty_print()

    def __repr__(self):
        bytes_str = f", Bytes={self.bytes}" if self.base_unit.name != Units.B.name else ""
        return f"Unit(" \
               f"Value={self.value}, " \
               f"Unit={self.base_unit}, " \
               f"Pretty={self.pretty_print()}" \
               f"{bytes_str}" \
               f")"

    def __lt__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.bytes < other_value

    def __le__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.bytes <= other_value

    def __eq__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.bytes == other_value

    def __ne__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.bytes != other_value

    def __gt__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.bytes > other_value

    def __ge__(self, other: int | float | Unit | Units):
        other_value = get_unit_bytes_value(other)
        return self.bytes >= other_value

    def __add__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__add__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __sub__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__sub__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __mul__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__mul__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __truediv__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__truediv__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __floordiv__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__floordiv__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __mod__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__mod__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __radd__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__radd__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __rsub__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__rsub__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __rmul__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__rmul__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __rtruediv__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__rtruediv__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __rfloordiv__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__rfloordiv__(base_value, other_value), common_unit).convert_to_highest_unit()

    def __rmod__(self, other: int | float | Unit | Units):
        base_value, other_value, common_unit = Unit.__parse_aritmethic_objs__(self, other)
        return Unit(type(base_value).__rmod__(base_value, other_value), common_unit).convert_to_highest_unit()


if __name__ == "__main__":
    def main():
        def print_units_comparison():
            for u1 in Units:
                for u2 in Units:
                    print(f"Comparing: {u1} with: {u2}")
                    print(f"--------------------------")
                    print(f"{u1} == {u2}: {u1 == u2}")
                    print(f"{u1} != {u2}: {u1 != u2}")
                    print(f"{u1} >= {u2}: {u1 >= u2}")
                    print(f"{u1} <= {u2}: {u1 <= u2}")
                    print(f"{u1} > {u2}: {u1 > u2}")
                    print(f"{u1} < {u2}: {u1 < u2}")
                    print("")

                print("")

        def print_units_with_examples():
            units = [u for u in Units]
            values = [0, 1, 1000, 1024, 5000]

            for u in units[:-3]:
                print("")
                print("Testing Unit: %r" % u)
                print("----------------")

                for v in values:
                    unit = Unit(v, u)
                    print("%s: %r" % (unit, unit))

        def print_unit_arithmetics():
            u1 = Unit(0.985, Units.GB)
            u2 = Unit(319.8, Units.MB)

            print(f"U1: {u1!r}")
            print(f"U2: {u2!r}")

            print("")
            print("Arithmetic with another Unit Instance:")
            print(f"{u1} > {u2}: {u1 > u2}")
            print(f"{u1} < {u2}: {u1 < u2}")
            print(f"{u1} == {u2}: {u1 == u2}")
            print(f"{u1} + {u2}: {(u1 + u2)}")
            print(f"{u1} - {u2}: {(u1 - u2)}")
            print(f"{u1} * {u2}: {(u1 * u2)}")
            print(f"{u1} / {u2}: {(u1 / u2)}")
            print(f"{u1} // {u2}: {(u1 // u2)}")

            print("")
            print("Arithmetic with Base Units:")
            print(f"{u1} > 1{Units.GB}: {u1 > Units.GB}")
            print(f"{u1} < 1{Units.GB}: {u1 < Units.GB}")
            print(f"{u1} == 1{Units.GB}: {u1 == Units.GB}")
            print(f"{u1} + 1{Units.GB}: {(u1 + Units.GB)}")
            print(f"{u1} - 1{Units.GB}: {(u1 - Units.GB)}")
            print(f"{u1} * 1{Units.GB}: {(u1 * Units.GB)}")
            print(f"{u1} / 1{Units.GB}: {(u1 / Units.GB)}")
            print(f"{u1} // 1{Units.GB}: {(u1 // Units.GB)}")

        # print_units_with_examples()
        # print("\n")
        # print_units_comparison()
        # print("\n")
        print_unit_arithmetics()

    main()
