from __future__ import annotations


class LinearColor(list):
    """
    Represents RGBA color, using a value from 0..1.
    """

    def __init__(self, r: float = 0.0, g: float = 0.0, b: float = 0.0, a: float = 1.0):
        super().__init__([r, g, b, a])

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.r}, {self.g}, {self.b}, {self.a})'

    @classmethod
    def from_seq(cls, seq: tuple[int | float, ...] | list[int | float, ...]) -> LinearColor:
        """
        Returns a linear color from the given sequence of 0.0 to 1.0 values.

        :param tuple[int or float, ...] or list[int or float, ...] seq: sequence of values.
        :return: linear color.
        """

        return cls(*seq[:4])

    @classmethod
    def from_8bit(cls, seq: tuple[int | float, ...] | list[int | float, ...]) -> LinearColor:
        """
        Returns a linear color from the given sequence of 0 to 255 values.

        :param tuple[int or float, ...] or list[int or float, ...] seq: sequence of values.
        :return: linear color.
        """

        return LinearColor.from_seq([channel / 255.0 for channel in seq])

    @property
    def r(self) -> float:
        return self[0]

    @r.setter
    def r(self, value: float):
        self[0] = value

    @property
    def g(self) -> float:
        return self[1]

    @g.setter
    def g(self, value: float):
        self[1] = value

    @property
    def b(self) -> float:
        return self[2]

    @b.setter
    def b(self, value: float):
        self[2] = value

    @property
    def a(self) -> float:
        return self[3]

    @a.setter
    def a(self, value: float):
        self[3] = value

    def as_8bit(self) -> tuple[int, ...]:
        """
        Returns this linear color (0.0..1.0) as an 8-bit color (0..255)

        :return: 8-bit color color tuple.
        :rtype: tuple[int, int, int, int]
        """

        return tuple([int(channel * 255) for channel in self])
