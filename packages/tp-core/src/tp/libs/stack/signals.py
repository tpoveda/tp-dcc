from __future__ import annotations

from typing import Callable


class Signal:
    """
    Signal class that allows to handle events within functions to trigger mid-call
    callbacks.
    """

    def __init__(self):
        super().__init__()

        self._callables: list[Callable] = []

    def connect(self, func: Callable):
        """
        Connects a function to this signal.

        :param func: Callable
        """

        self._callables.append(func)

    def disconnect(self, func: Callable | None = None) -> bool:
        """
        Disconnects a function from this signal.

        :param func: callable to disconnect. If None, all functions will be
            disconnected.
        :return: True if the function was disconnected; False otherwise.
        """

        if func is None:
            self._callables.clear()
            return True

        if callable not in self._callables:
            return False

        self._callables.remove(func)

        return True

    def emit(self, *args, **kwargs):
        """
        Emits the signal, calling all connected functions.

        :param args: arguments to pass to the connected functions.
        :param kwargs: keyword arguments to pass to the connected functions.
        """

        for func in self._callables:
            func(*args, **kwargs)
