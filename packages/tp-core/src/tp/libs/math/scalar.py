from __future__ import annotations

from typing import Iterator


def is_equal(x: float, y: float, tolerance: float = 0.000001) -> bool:
    """
    Checks if 2 float values are equal withing a given tolerance.

    :param x: first value to compare.
    :param y: second value to compare.
    :param tolerance: comparison tolerance.
    :return: True if both values are equal.
    """

    return abs(x - y) < tolerance


def is_close(
    x: float,
    y: float,
    relative_tolerance: float = 1e-03,
    absolute_tolerance: float = 1e-03,
) -> bool:
    """
    Returns whether two given numbers are relatively close.

    :param x: first value to compare.
    :param y: second value to compare.
    :param relative_tolerance: relative tolerance.
    :param absolute_tolerance: absolute tolerance.
    :return: True if both numbers are relatively close; False otherwise.
    """

    return abs(x - y) <= max(
        relative_tolerance * max(abs(x), abs(y)), absolute_tolerance
    )


def lerp_value(start: int | float, end: int | float, alpha: float) -> float:
    """
    Linearly interpolates between two values based on a given fraction.

    This function computes a value between `start` and `end` using the formula:

        result = start + alpha * (end - start)

    The parameter `alpha` should be in the range [0,1]:
      - `alpha = 0.0` returns `start`
      - `alpha = 1.0` returns `end`
      - Intermediate values smoothly interpolate between the two.

    :param start: The starting value.
    :param end: The target value.
    :param alpha: The interpolation factor (0.0 to 1.0).
    :return: The interpolated value.

    Example:
    >>> lerp_value(10, 20, 0.0)  # No interpolation, returns start
    10.0
    >>> lerp_value(10, 20, 0.5)  # Halfway between 10 and 20
    15.0
    >>> lerp_value(10, 20, 1.0)  # Full interpolation, returns end
    20.0
    """

    return start + alpha * (end - start)


def lerp_smooth(current: float, goal: float, weight: float = 0.1) -> float:
    """
    Gradually moves a value toward a goal by a weighted percentage.

    This function updates `current` so that it moves `weight` fraction closer to `goal`
    each time it is called. It is commonly used for **smooth animations**, **damped movement**,
    and **gradual transitions**.

    The function follows the formula:

        result = (goal * weight) + (current * (1.0 - weight))

    If `weight = 0.0`, the result is unchanged (`current`).
    If `weight = 1.0`, the result jumps directly to `goal`.

    :param current: The current value.
    :param goal: The target value.
    :param weight: The fraction to move toward the goal (0.0 to 1.0). Default is 0.1 (10% movement).
    :return: The new updated value.

    Example:
    >>> lerp_smooth(10, 20, 0.0)  # No movement
    10.0
    >>> lerp_smooth(10, 20, 0.5)  # Moves halfway toward the goal
    15.0
    >>> lerp_smooth(10, 20, 1.0)  # Jumps directly to the goal
    20.0

    Example (Iterative Movement Simulation):
    >>> for _ in range(5):
    ...     print(lerp_smooth(0, 100, 0.2))
    20.0
    36.0
    48.8
    59.04
    67.232
    """

    return (goal * weight) + ((1.0 - weight) * current)


def generate_linear_steps(start: float, end: float, count: int) -> Iterator[float]:
    """
    Generates `count` evenly spaced values between `start` and `end`.

    This function produces a sequence of `count` linearly spaced numbers between
    `start` and `end`, **including both endpoints**.

    The generated values follow this pattern:

        step = (end - start) / (count - 1)

    Example Usage:

    >>> list(generate_linear_steps(-10, 10, 5))
    [-10.0, -5.0, 0.0, 5.0, 10.0]

    >>> for value in generate_linear_steps(0.0, 1.0, 5):
    ...     print(value)
    0.0
    0.25
    0.5
    0.75
    1.0

    :param start: The starting value.
    :type start: float
    :param end: The ending value.
    :type end: float
    :param count: The number of steps to generate (must be ≥ 2).
    :type count: int
    :return: A generator yielding `count` evenly spaced values from `start` to `end`.
    :rtype:
    :raises ValueError: If `count` is less than 2.
    """
    if count < 2:
        raise ValueError("count must be at least 2 to generate meaningful steps.")

    step = (end - start) / (count - 1)

    for i in range(count):
        yield start + i * step


def range_percentage(
    min_value: int | float, max_value: int | float, value: int | float
) -> float:
    """
    Returns the percentage of the given value in the given range.

    :param min_value: minimum value of the range.
    :param max_value: maximum value of the range.
    :param value: value to get the percentage of.
    :return: percentage of the value in the range.
    """

    try:
        return (value - min_value) / (max_value - min_value)
    except ZeroDivisionError:
        return 0.0


def clamp(
    number: int | float, min_value: int | float = 0.0, max_value: int | float = 1.0
) -> int | float:
    """
    Clamps a number between two values.

    :param number: value to clamp
    :param min_value: maximum value of the number
    :param max_value: minimum value of the number
    :return: clamped value.
    """

    return max(min(number, max_value), min_value)
