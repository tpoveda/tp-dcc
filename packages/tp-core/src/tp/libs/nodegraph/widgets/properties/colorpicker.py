from __future__ import annotations

from typing import Type

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget, QPushButton, QHBoxLayout, QColorDialog
from Qt.QtGui import QColor

from .abstract import AbstractPropertyWidget
from .vectors import Vector3PropertyWidget, Vector4PropertyWidget


class ColorPickRGBPropertyWidget(AbstractPropertyWidget):
    """
    Color picker widget that allows to pick a color using RGB values.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._color: tuple[int, int, int] = (0, 0, 0)

        self._button = QPushButton(parent=self)
        self._vector = Vector3PropertyWidget(parent=self)
        self._vector.set_steps([1, 10, 100])
        self._vector.set_data_type(int)
        self._vector.set_value([0, 0, 0])
        self._vector.set_min(0)
        self._vector.set_max(255)
        self._update_color()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        main_layout.addWidget(self._button, 0, Qt.AlignLeft)
        main_layout.addWidget(self._vector, 1, Qt.AlignLeft)

        self._button.clicked.connect(self._on_button_clicked)
        self._vector.valueChanged.connect(self._on_vector_value_changed)

    def get_value(self) -> tuple[int]:
        """
        Returns the value of the property widget.

        :return: value of the property widget.
        """

        return self._color[:3]

    def set_value(self, value: tuple[int]):
        """
        Sets the value of the property widget.

        :param value: value to set.
        """

        if value == self.get_value():
            return

        self._color = value
        self._update_color()
        self._vector.set_value(self._color)
        self.valueChanged.emit(self.name, value)

    def set_data_type(self, data_type: Type):
        """
        Sets the data type of the property widget.

        :param data_type: data type to set.
        """

        self._vector.set_data_type(data_type)

    def _update_color(self):
        """
        Internal function that updates the color of the button.
        """

        c = [int(max(min(i, 255), 0)) for i in self._color]
        hex_color = "#{0:02x}{1:02x}{2:02x}".format(*c)
        self._button.setStyleSheet(
            """
            QPushButton {{background-color: rgba({0}, {1}, {2}, 255);}}
            QPushButton::hover {{background-color: rgba({0}, {1}, {2}, 200);}}
            """.format(*c)
        )
        self._button.setToolTip("rgb: {}\nhex: {}".format(self._color[:3], hex_color))

    def _on_button_clicked(self):
        """
        Internal callback function that is called when the button is clicked.
        """

        current_color = QColor(*self.get_value())
        color = QColorDialog.getColor(current_color, self)
        if color.isValid():
            # noinspection PyTypeChecker
            self.set_value(color.getRgb())

    def _on_vector_value_changed(self, _, value: list[int, int, int]):
        """
        Internal callback function that is called when the vector value changes.

        :param value: vector value.
        """

        self._color = tuple(value)
        self._update_color()
        self.valueChanged.emit(self.name, value)


class ColorPickRGBAPropertyWidget(ColorPickRGBPropertyWidget):
    """
    Color picker widget that allows to pick a color using RGBA values.
    """

    def __init__(self, parent: QWidget | None = None):
        AbstractPropertyWidget.__init__(self, parent=parent)

        self._color: tuple[int, int, int, int] = (0, 0, 0, 255)
        self._button = QPushButton(parent=self)
        self._vector = Vector4PropertyWidget(parent=self)
        self._vector.set_steps([1, 10, 100])
        self._vector.set_data_type(int)
        self._vector.set_value([0, 0, 0, 255])
        self._vector.set_min(0)
        self._vector.set_max(255)
        self._update_color()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        main_layout.addWidget(self._button, 0, Qt.AlignLeft)
        main_layout.addWidget(self._vector, 1, Qt.AlignLeft)

        self._button.clicked.connect(self._on_button_clicked)
        self._vector.valueChanged.connect(self._on_vector_value_changed)

    def _update_color(self):
        """
        Internal function that updates the color of the button.
        """

        c = [int(max(min(i, 255), 0)) for i in self._color]
        hex_color = "#{0:02x}{1:02x}{2:02x}{3:03x}".format(*c)
        self._button.setStyleSheet(
            """
            QPushButton {{background-color: rgba({0}, {1}, {2}, {3});}}
            QPushButton::hover {{background-color: rgba({0}, {1}, {2}, {3});}}
            """.format(*c)
        )
        self._button.setToolTip("rgba: {}\nhex: {}".format(self._color, hex_color))

    def get_value(self) -> tuple[int]:
        """
        Returns the value of the property widget.

        :return: value of the property widget.
        """

        return self._color[:4]
