from __future__ import annotations


def linear_interpolation(start: int | float, end: int | float, alpha: float) -> float:
    """
    Returns the linear interpolation between two values.

    :param start: float, start value
    :param end: float, end value
    :param alpha: float, interpolation value
    :return: float, linear interpolation between start and end values
    """

    return start + alpha * (end - start)


def range_percentage(
    min_value: int | float, max_value: int | float, value: int | float
) -> float:
    """
    Returns the percentage of the given value in the given range.

    :param min_value: float, minimum value of the range
    :param max_value: float, maximum value of the range
    :param value: float, value to get the percentage of
    :return: float, percentage of the value in the range
    """

    try:
        return (value - min_value) / (max_value - min_value)
    except ZeroDivisionError:
        return 0.0
