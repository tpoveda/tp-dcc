from __future__ import annotations

from typing import Any, Callable

from Qt.QtCore import QObject

from ..python import helpers


class Model(QObject):
    """
    Class that exposes functions to store data and handles data updates automatically when UI is changed.
    """

    def __init__(self):
        super().__init__()

        self.state = helpers.ObjectDict()
        self._listeners = {}

    def update(self, key: str, value: Any, force: bool = False):
        """
        Updates the data and calls all the corresponding listeners.

        :param str key: key to update.
        :param Any value: new value for given key.
        :param bool force: whether to force the update event if the value is the same.
        """

        if self.state.get(key) == value and not force:
            return
        self.state[key] = value
        for listener in self._listeners.get(key, []):
            listener(value)

    def update_all(self):
        """
        Updates all listeners.
        """

        for key, value in self.state.items():
            for listener in self._listeners.get(key, []):
                listener(value)

    def updater(self, key: str) -> Callable:
        """
        Returns a callback which, when called, changes the data.

        :param str key: key to bind.
        :return: update callback for given key.
        :rtype: Callable
        """

        return lambda value: self.update(key, value)

    def listen(self, key: str, listener: Callable, value: Any = None):
        """
        Registers a listener for the given key.

        :param str key: listener key.
        :param Callable listener: widget function that will be called when controller data is updated.
        :param Any value: optinal value to initialize state with
        """

        self._listeners[key] = self._listeners.get(key, []) + [listener]
        if key not in self.state:
            self.state[key] = value
