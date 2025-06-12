from __future__ import annotations

import re
from typing import Type

from Qt.QtCore import Qt, Signal, QRegularExpression
from Qt.QtWidgets import QLineEdit, QMenu, QAction
from Qt.QtGui import QCursor, QMouseEvent, QRegularExpressionValidator

_NUMBER_REGEX = re.compile(r"^((?:\-)*\d+)*([\.,])*(\d+(?:[eE](?:[\-\+])*\d+)*)*")


class NumericLineEditPropertyWidget(QLineEdit):
    """
    Abstract property widget that represents a numeric line edit property.
    """

    valueChanged = Signal(object)

    def __init__(self, data_type: Type = float, parent=None):
        super().__init__(parent=parent)

        self._previous_x: int | None = None
        self._previous_value: int | float | None = None
        self._step: int = 1
        self._speed: float = 0.05
        self._data_type: Type = float
        self._min: int | float | None = None
        self._max: int | float | None = None
        self._middle_mouse_button_state: bool = False

        self._menu = NumericLineEditMenu(parent=self)
        self._menu.mouseMoved.connect(self.mouseMoveEvent)
        self._menu.mouseReleased.connect(self.mouseReleaseEvent)
        self._menu.stepChanged.connect(self._on_menu_step_changed)

        self.editingFinished.connect(self._on_editing_finished)

        self.set_data_type(data_type)

        self.setText("0")
        self.setToolTip('"Middle Mouse Button + Drag Left/Right" to change value')

    def __repr__(self) -> str:
        """
        Returns a string representation of the numeric line edit property widget.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self.text()}") object at {hex(id(self))}>'

    def mousePressEvent(self, event: QMouseEvent):
        """
        Function that is called when the mouse is pressed.

        :param event: mouse event.
        """

        if event.button() == Qt.MiddleButton:
            self._middle_mouse_button_state = True
            self._previous_x = None
            self._menu.exec_(QCursor.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Function that is called when the mouse is moved.

        :param event: mouse event.
        """

        if self._middle_mouse_button_state:
            if self._previous_x is None:
                self._previous_x = event.x()
                self._previous_value = self.get_value()
            else:
                self._step = self._menu.step
                delta = event.x() - self._previous_x
                value = self._previous_value
                value = value + int(delta * self._speed) * self._step
                self.set_value(value)
                self.valueChanged.emit(self.get_value())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Function that is called when the mouse is released.

        :param event: mouse event.
        """

        self._menu.close()
        self._middle_mouse_button_state = False
        super().mouseReleaseEvent(event)

    def get_value(self) -> int | float:
        """
        Returns the value of the widget.

        :return: value of the widget.
        """

        return self._convert_text(self.text())

    def set_value(self, value: int | float):
        """
        Sets the value of the widget.

        :param value: value to set.
        """

        text = str(value)
        converted = self._convert_text(text)
        current = self.get_value()
        if converted == current:
            return
        point = None
        if isinstance(converted, float):
            point = _NUMBER_REGEX.match(str(value)).groups(2)
        if self._min is not None and converted < self._min:
            text = str(self._min)
            if point and point not in text:
                text = str(self._min).replace(".", point)
        if self._max is not None and converted > self._max:
            text = str(self._max)
            if point and point not in text:
                text = text.replace(".", point)

        self.setText(text)

    def set_data_type(self, data_type: Type):
        """
        Sets the data type of the widget.

        :param data_type: data type.
        """

        self._data_type = data_type
        steps: list[int | float] | None = None
        validator: QRegularExpressionValidator | None = None
        if data_type is int:
            regexp = QRegularExpression(r"\d+")
            validator = QRegularExpressionValidator(regexp, self)
            steps = [1, 10, 100, 1000]
            self._min = None if self._min is None else int(self._min)
            self._max = None if self._max is None else int(self._max)
        elif data_type is float:
            regexp = QRegularExpression(r"\d+[\.,]\d+(?:[eE](?:[\-\+]|)\d+)*")
            validator = QRegularExpressionValidator(regexp, self)
            steps = [0.001, 0.01, 0.1, 1]
            self._min = None if self._min is None else float(self._min)
            self._max = None if self._max is None else float(self._max)
        if validator is not None:
            self.setValidator(validator)
        if steps:
            if not self._menu.steps:
                self._menu.set_steps(steps)
        self._menu.set_data_type(data_type)

    def set_steps(self, steps: list[int | float] | None = None):
        """
        Sets the steps of the widget.

        :param steps: list of steps.
        """

        step_types = {int: [1, 10, 100, 1000], float: [0.001, 0.01, 0.1, 1]}
        # noinspection PyTypeChecker
        steps = steps or step_types.get(self._data_type)
        self._menu.set_steps(steps)

    def set_min(self, value: int | float | None = None):
        """
        Sets the minimum value of the widget.

        :param value: minimum value.
        """

        if self._data_type is int:
            self._min = int(value)
        elif self._data_type is float:
            self._min = float(value)
        else:
            self._min = value

    def set_max(self, value: int | float | None = None):
        """
        Sets the maximum value of the widget.

        :param value: maximum value.
        """

        if self._data_type is int:
            self._max = int(value)
        elif self._data_type is float:
            self._max = float(value)
        else:
            self._max = value

    def _convert_text(self, text: str) -> int | float:
        """
        Internal function that converts the text to the appropriate value.

        :param text: text to convert.
        :return: converted value.
        """

        match = _NUMBER_REGEX.match(text)
        if match:
            val1, _, val2 = match.groups()
            val1 = val1 or "0"
            val2 = val2 or "0"
            value = float(val1 + "." + val2)
        else:
            value = 0.0
        if self._data_type is int:
            value = int(value)

        return value

    def _on_menu_step_changed(self):
        """
        Internal callback function that is called when the step of the menu is changed.
        """

        self._previous_x = None

    def _on_editing_finished(self):
        """
        Internal callback function that is called when the editing is finished.
        """

        if self._data_type is float:
            match = _NUMBER_REGEX.match(self.text())
            if match:
                val1, point, val2 = match.groups()
                if point:
                    val1 = val1 or "0"
                    val2 = val2 or "0"
                    self.setText(val1 + point + val2)
        self.valueChanged.emit(self.get_value())


class NumericLineEditMenu(QMenu):
    """
    Menu that is used by the numeric line edit property widget.
    """

    mouseMoved = Signal(object)
    mouseReleased = Signal(object)
    stepChanged = Signal()

    def __init__(self, parent: NumericLineEditPropertyWidget | None = None):
        super().__init__(parent=parent)

        self._step: int = 1
        self._steps: list[int] = []
        self._last_action: QAction | None = None

    @property
    def step(self) -> int:
        """
        Returns the step of the menu.

        :return: step value.
        """

        return self._step

    @property
    def steps(self) -> list[int]:
        """
        Returns the steps of the menu.

        :return: list of steps.
        """

        return self._steps

    def __repr__(self) -> str:
        """
        Returns a string representation of the numeric line edit menu.

        :return: string representation.
        """

        return f"<{self.__class__.__name__} object at {hex(id(self))}>"

    def mousePressEvent(self, event: QMouseEvent):
        """
        Function that is called when the mouse is pressed.

        :param event: mouse event.
        """

        return

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Function that is called when the mouse is moved.

        :param event: mouse event.
        """

        self.mouseMoved.emit(event)
        super().mouseMoveEvent(event)
        action = self.actionAt(event.pos())
        if action:
            if action is not self._last_action:
                self.stepChanged.emit()
            self._last_action = action
            self._step = action.property("step")
        elif self._last_action:
            self.setActiveAction(self._last_action)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Function that is called when the mouse is released.

        :param event: mouse event.
        """

        self.mouseReleased.emit(event)
        super().mouseReleaseEvent(event)

    def set_steps(self, steps: list[int]):
        """
        Function that sets the steps of the menu.

        :param steps: list of steps.
        """

        self.clear()
        self._steps = steps
        for step in steps:
            self._add_step_action(step)

    def set_data_type(self, data_type: Type):
        """
        Function that sets the data type of the menu.

        :param data_type: data type.
        """

        if data_type is int:
            new_steps: list[int] = []
            for step in self._steps:
                if "." not in str(step):
                    new_steps.append(step)
        elif data_type is float:
            self.set_steps(self._steps)

    def _add_step_action(self, step: int):
        """
        Internal function that adds a step action to the menu.

        :param step: step value.
        """

        action = QAction(str(step), self)
        action.setProperty("step", step)
        self.addAction(action)


class IntLineEditPropertyWidget(NumericLineEditPropertyWidget):
    """
    Property widget that represents an integer line edit property.
    """

    def __init__(self, parent=None):
        super().__init__(data_type=int, parent=parent)


class FloatLineEditPropertyWidget(NumericLineEditPropertyWidget):
    """
    Property widget that represents a float line edit property.
    """

    def __init__(self, parent=None):
        super().__init__(data_type=float, parent=parent)
