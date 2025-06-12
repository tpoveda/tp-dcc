from __future__ import annotations

from typing import Any
from abc import abstractmethod

from Qt.QtCore import Signal
from Qt.QtWidgets import QWidget


class AbstractPropertyWidget(QWidget):
    """
    Abstract class that defines a property widget.
    """

    valueChanged = Signal(str, object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._name: str | None = None

    def __repr__(self) -> str:
        """
        Returns the string representation of the property widget.

        :return: string representation.
        """

        return f"<{self.__class__.__name__}( at {hex(id(self))})"

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of the property widget.

        :return: name of the property widget.
        """

        return self._name

    @name.setter
    def name(self, value: str):
        """
        Setter method that sets the name of the property widget.

        :param value: name to set.
        """

        self._name = value

    @abstractmethod
    def get_value(self):
        """
        Returns the value of the property widget.

        :return: value of the property widget.
        """

        raise NotImplementedError

    @abstractmethod
    def set_value(self, value: Any):
        """
        Sets the value of the property widget.

        :param value: value to set.
        """

        raise NotImplementedError
