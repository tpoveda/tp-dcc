from __future__ import annotations

from Qt.QtCore import Qt, QObject, Signal
from Qt.QtWidgets import (
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
)
from Qt.QtGui import QFocusEvent


class LabelPropertyWidget(QLabel):
    """
    Widget that represents a node property as a "QLabel" widget.
    """

    valueChanged = Signal(str, object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._name: str | None = None

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self._name}") object at {hex(id(self))}>'

    @property
    def name(self) -> str:
        """
        Returns the name of the widget.

        :return: str
        """

        return self._name

    @name.setter
    def name(self, name: str):
        """
        Sets the name of the widget.

        :param name: str
        """

        self._name = name

    def get_value(self) -> str:
        """
        Returns the value of the widget.

        :return: str
        """

        return self.text()

    def set_value(self, value: str):
        """
        Sets the value of the widget.

        :param value: str
        """

        if value == self.get_value():
            return

        self.setText(value)
        self.valueChanged.emit(self.name, value)


class LineEditPropertyWidget(QLineEdit):
    """
    Widget that represents a node property as a "QLineEdit" widget.
    """

    valueChanged = Signal(str, object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._name: str | None = None
        self.editingFinished.connect(self._on_editing_finished)

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self._name}") object at {hex(id(self))}>'

    @property
    def name(self) -> str:
        """
        Returns the name of the widget.

        :return: str
        """

        return self._name

    @name.setter
    def name(self, name: str):
        """
        Sets the name of the widget.

        :param name: str
        """

        self._name = name

    def get_value(self) -> str:
        """
        Returns the value of the widget.

        :return: str
        """

        return self.text()

    def set_value(self, value: str):
        """
        Sets the value of the widget.

        :param value: str
        """

        value = str(value)
        if value == self.get_value():
            return

        self.setText(value)
        self.valueChanged.emit(self.name, value)

    def _on_editing_finished(self):
        """
        Internal callback function that is called when the editing is finished.
        """

        self.valueChanged.emit(self.name, self.text())


class TextEditPropertyWidget(QTextEdit):
    """
    Widget that represents a node property as a "QTextEdit" widget.
    """

    valueChanged = Signal(str, object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._name: str | None = None
        self._prev_text: str = ""

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self._name}") object at {hex(id(self))}>'

    @property
    def name(self) -> str:
        """
        Returns the name of the widget.

        :return: str
        """

        return self._name

    @name.setter
    def name(self, name: str):
        """
        Sets the name of the widget.

        :param name: str
        """

        self._name = name

    def get_value(self) -> str:
        """
        Returns the value of the widget.

        :return: str
        """

        return self.toPlainText()

    def set_value(self, value: str):
        """
        Sets the value of the widget.

        :param value: str
        """

        value = str(value)
        if value == self.get_value():
            return

        self.setPlainText(value)
        self.valueChanged.emit(self.name, value)

    def focusInEvent(self, event: QFocusEvent):
        """
        Function that is called when the widget receives focus.

        :param event: focus event.
        """

        super().focusInEvent(event)
        self._prev_text = self.toPlainText()

    def focusOutEvent(self, event: QFocusEvent):
        """
        Function that is called when the widget loses focus.

        :param event: focus event.
        """

        super().focusOutEvent(event)
        if self._prev_text != self.toPlainText():
            self.valueChanged.emit(self.name, self.toPlainText())
        self._prev_text = ""


class ComboBoxPropertyWidget(QComboBox):
    """
    Widget that represents a node property as a "QComboBox" widget.
    """

    valueChanged = Signal(str, object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._name: str | None = None
        self.currentIndexChanged.connect(self._on_current_index_changed)

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self._name}") object at {hex(id(self))}>'

    @property
    def name(self) -> str:
        """
        Returns the name of the widget.

        :return: str
        """

        return self._name

    @name.setter
    def name(self, name: str):
        """
        Sets the name of the widget.

        :param name: str
        """

        self._name = name

    def get_value(self) -> str:
        """
        Returns the value of the widget.

        :return: str
        """

        return self.currentText()

    def set_value(self, value: str):
        """
        Sets the value of the widget.

        :param value: str
        """

        if value == self.get_value():
            return

        index = self.findText(value, Qt.MatchExactly)
        self.setCurrentIndex(index)
        if index >= 0:
            self.valueChanged.emit(self.name, value)

    def items(self) -> list[str]:
        """
        Returns the items of the combo box.

        :return: list[str]
        """

        return [self.itemText(i) for i in range(self.count())]

    def set_items(self, items: list[str]):
        """
        Sets the items of the combo box.

        :param items: list[str]
        """

        self.clear()
        self.addItems(items)

    def _on_current_index_changed(self, index: int):
        """
        Internal callback function that is called when the index is changed.

        :param index: int
        """

        self.valueChanged.emit(self.name, self.get_value())


class CheckBoxPropertyWidget(QCheckBox):
    """
    Widget that represents a node property as a "QCheckBox" widget.
    """

    valueChanged = Signal(str, object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._name: str | None = None
        self.clicked.connect(self._on_clicked)

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self._name}") object at {hex(id(self))}>'

    @property
    def name(self) -> str:
        """
        Returns the name of the widget.

        :return: str
        """

        return self._name

    @name.setter
    def name(self, name: str):
        """
        Sets the name of the widget.

        :param name: str
        """

        self._name = name

    def get_value(self) -> bool:
        """
        Returns the value of the widget.

        :return: bool
        """

        return self.isChecked()

    def set_value(self, value: bool):
        """
        Sets the value of the widget.

        :param value: bool
        """

        value = bool(value)
        if value == self.get_value():
            return

        self.setChecked(value)
        self.valueChanged.emit(self.name, value)

    def _on_clicked(self):
        """
        Internal callback function that is called when the checkbox is clicked.
        """

        self.valueChanged.emit(self.name, self.get_value())


class SpinBoxPropertyWidget(QSpinBox):
    """
    Widget that represents a node property as a "QSpinBox" widget.
    """

    valueChanged = Signal(str, object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._name: str | None = None
        self.setButtonSymbols(QSpinBox.NoButtons)
        self.valueChanged.connect(self._on_value_changed)

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self._name}") object at {hex(id(self))}>'

    @property
    def name(self) -> str:
        """
        Returns the name of the widget.

        :return: str
        """

        return self._name

    @name.setter
    def name(self, name: str):
        """
        Sets the name of the widget.

        :param name: str
        """

        self._name = name

    def get_value(self) -> int:
        """
        Returns the value of the widget.

        :return: int
        """

        return self.value()

    def set_value(self, value: int):
        """
        Sets the value of the widget.

        :param value: int
        """

        value = int(value)
        if value == self.get_value():
            return

        self.setValue(value)

    def _on_value_changed(self, value: int):
        """
        Internal callback function that is called when the value is changed.

        :param value: int
        """

        self.valueChanged.emit(self.name, value)


class DoubleSpinBoxPropertyWidget(QDoubleSpinBox):
    """
    Widget that represents a node property as a "QDoubleSpinBox" widget.
    """

    valueChanged = Signal(str, object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._name: str | None = None
        self.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.valueChanged.connect(self._on_value_changed)

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self._name}") object at {hex(id(self))}>'

    @property
    def name(self) -> str:
        """
        Returns the name of the widget.

        :return: str
        """

        return self._name

    @name.setter
    def name(self, name: str):
        """
        Sets the name of the widget.

        :param name: str
        """

        self._name = name

    def get_value(self) -> float:
        """
        Returns the value of the widget.

        :return: float
        """

        return self.value()

    def set_value(self, value: float):
        """
        Sets the value of the widget.

        :param value: float
        """

        value = float(value)
        if value == self.get_value():
            return

        self.setValue(value)

    def _on_value_changed(self, value: float):
        """
        Internal callback function that is called when the value is changed.

        :param value: float
        """

        self.valueChanged.emit(self.name, value)
