from __future__ import annotations

from typing import Callable

from .composition import Ignore
from .helpers import composition_methods as _methods
from .helpers import composition_results as _results


def take_min(func: Callable) -> Callable:
    """Decorator that assumes a numeric return from each method and will
    return the smallest value.
    """

    def inner(*args, **kwargs) -> int | float:
        """Takes the smallest value from the results of the methods.

        Args:
            *args: Arguments to be passed to the function.
            **kwargs: Keyword arguments to be passed to the function.

        Returns:
            The smallest value from the results of the methods.
        """

        return min(_results(args[0], func.__name__, *args, **kwargs))

    return inner


def take_max(func: Callable) -> Callable:
    """Decorator that assumes a numeric return from each method and will
    return the largest value.
    """

    def inner(*args, **kwargs) -> int | float:
        """Takes the largest value from the results of the methods.

        Args:
            *args: Arguments to be passed to the function.
            **kwargs: Keyword arguments to be passed to the function.

        Returns:
            The largest value from the results of the methods.
        """

        return max(_results(args[0], func.__name__, *args, **kwargs))

    return inner


def take_sum(func: Callable) -> Callable:
    """Decorator that assumes a numeric return from each method and will
    return the sum of all values.
    """

    def inner(*args, **kwargs) -> int | float:
        """Takes the sum of all values from the results of the methods.

        Args:
            *args: Arguments to be passed to the function.
            **kwargs: Keyword arguments to be passed to the function.

        Returns:
            The sum of all values from the results of the methods.
        """

        return sum(_results(args[0], func.__name__, *args, **kwargs))

    return inner


def take_average(func: Callable) -> Callable:
    """Decorator that assumes a numeric return from each method and will
    return the average of all values.
    """

    def inner(*args, **kwargs) -> int | float:
        """Takes the average of all values from the results of the methods.

        Args:
            *args: Arguments to be passed to the function.
            **kwargs: Keyword arguments to be passed to the function.

        Returns:
            The average of all values from the results of the methods.
        """

        results = _results(args[0], func.__name__, *args, **kwargs)
        sum_of_results = sum(results)
        if sum_of_results == 0:
            return sum_of_results

        return sum_of_results / len(results)

    return inner


def take_first(func: Callable) -> Callable:
    """Decorator that takes the first value from the results of the methods."""

    def inner(*args, **kwargs) -> int | float | None:
        """Takes the first value from the results of the methods.

        Args:
            *args: Arguments to be passed to the function.
            **kwargs: Keyword arguments to be passed to the function.

        Returns:
            The first value from the results of the methods.
        """

        for method in _methods(args[0], func.__name__):
            result = method(*args[1:], **kwargs)
            if isinstance(result, Ignore):
                continue
            return result

        return None

    return inner
