from __future__ import annotations

from typing import Type

from Qt.QtWidgets import QWidget, QHBoxLayout

from .valuelineedit import NumericLineEditPropertyWidget
from .abstract import AbstractPropertyWidget


class VectorAbstractProperty(AbstractPropertyWidget):
    """
    Abstract property widget that represents a vector property.
    """

    def __init__(self, fields: int = 0, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._can_emit: bool = True
        self._value: list[int | float] = []
        self._items: list[NumericLineEditPropertyWidget] = []

        self._main_layout = QHBoxLayout()
        self._main_layout.setSpacing(2)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_layout)

        for i in range(fields):
            self._add_item(i)

    def get_value(self):
        """
        Returns the value of the property widget.

        :return: value of the property widget.
        """

        return self._value

    def set_value(self, value: list[int | float] | tuple[int | float]):
        """
        Sets the value of the property widget.

        :param value: value to set.
        """

        if value == self.get_value():
            return

        self._value = value
        self._can_emit = False
        try:
            self._update_items()
        finally:
            self._can_emit = True
        self._on_line_edit_value_changed()

    def set_data_type(self, data_type: Type):
        """
        Sets the data type of the property widget.

        :param data_type: data type to set.
        """

        for item in self._items:
            item.set_data_type(data_type)

    def set_steps(self, steps: list[int | float]):
        """
        Sets the steps of the property widget.

        :param steps: steps to set.
        """

        for item in self._items:
            item.set_steps(steps)

    def set_min(self, value: int | float):
        """
        Sets the minimum value of the property widget.

        :param value: minimum value to set.
        """

        for item in self._items:
            item.set_min(value)

    def set_max(self, value: int | float):
        """
        Sets the maximum value of the property widget.

        :param value: maximum value to set.
        """

        for item in self._items:
            item.set_max(value)

    def _add_item(self, index: int):
        """
        Internal function that adds a new item to the property widget.

        :param index: index of the item to add.
        """

        line_edit = NumericLineEditPropertyWidget(parent=self)
        line_edit.setProperty("index", index)
        line_edit.valueChanged.connect(
            lambda: self._on_line_edit_value_changed(
                line_edit.get_value(), line_edit.property("index")
            )
        )

        self.layout().addWidget(line_edit)
        self._value.append(0.0)
        self._items.append(line_edit)

    def _update_items(self):
        """
        Internal function that updates the items of the property widget.
        """

        if not isinstance(self._value, (list, tuple)):
            raise TypeError(f'Value "{self._value}" must be a list or tuple')
        for i, value in enumerate(self._value):
            if i + 1 > len(self._items):
                continue
            if self._items[i].get_value() != value:
                self._items[i].set_value(value)

    def _on_line_edit_value_changed(
        self, value: int | float | None = None, index: int | None = None
    ):
        """
        Internal function that is called when a line edit value changes.

        :param value: line edit value.
        :param index: line edit index.
        """

        if not self._can_emit:
            return

        if index is not None:
            self._value = list(self._value)
            self._value[index] = value
        self.valueChanged.emit(self.name, self._value)


class Vector2PropertyWidget(VectorAbstractProperty):
    """
    Vector property widget that represents a 2D vector property.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(fields=2, parent=parent)


class Vector3PropertyWidget(VectorAbstractProperty):
    """
    Vector property widget that represents a 3D vector property.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(fields=3, parent=parent)


class Vector4PropertyWidget(VectorAbstractProperty):
    """
    Vector property widget that represents a 4D vector property.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(fields=4, parent=parent)
