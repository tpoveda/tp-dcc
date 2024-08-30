from __future__ import annotations

import typing
import logging

from Qt.QtCore import Signal
from Qt.QtWidgets import (
    QWidget,
    QComboBox,
    QLineEdit,
    QAbstractSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QFormLayout,
)

from ...core import datatypes

if typing.TYPE_CHECKING:
    from .editor import PropertyEditor
    from ...core.consts import Variable

logger = logging.getLogger(__name__)


class VariablePropertyEditor(QWidget):
    """
    Widget that will be used to edit the properties of a variable node.
    """

    variableTypeChanged = Signal(str, str)

    def __init__(self, variable: Variable, parent: PropertyEditor | None = None):
        super().__init__(parent=parent)

        self._variable = variable

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    @property
    def variable(self) -> Variable:
        """
        Getter method that returns the variable of the property editor.

        :return: variable of the property editor.
        """

        return self._variable

    def _setup_widgets(self):
        """
        Internal function that creates the widgets that will be part of the variable property editor.
        """

        variable_data_type_name = self._variable.graph.variable_data_type(
            self._variable.name, as_data_type=False
        )
        variable_data_type = self._variable.graph.variable_data_type(
            self._variable.name, as_data_type=True
        )
        variable_value = self._variable.graph.variable_value(self._variable.name)

        self._data_type_combo_box = QComboBox(parent=self)
        data_types = list(self._variable.graph.factory.data_types.keys())
        data_types.sort()
        data_types.remove("EXEC")
        self._data_type_combo_box.addItems(data_types)
        self._data_type_combo_box.setCurrentText(variable_data_type_name.upper())

        self._value_widget: QLineEdit | QDoubleSpinBox | QCheckBox | None = None
        if (
            variable_data_type.type_class
            in self._variable.graph.factory.runtime_data_types(classes=True)
        ):
            self._value_widget = QLineEdit(parent=self)
            self._value_widget.setText(str(variable_value))
            self._value_widget.setEnabled(False)
        elif variable_data_type == datatypes.Numeric:
            self._value_widget = QDoubleSpinBox(parent=self)
            self._value_widget.setRange(-9999, 9999)
            self._value_widget.setValue(variable_value)
        elif variable_data_type == datatypes.String:
            self._value_widget = QLineEdit(parent=self)
            self._value_widget.setText(str(variable_value))
        elif variable_data_type == datatypes.Boolean:
            self._value_widget = QCheckBox(parent=self)
            self._value_widget.setChecked(variable_value)
        else:
            logger.warning(
                f"Missing widget creation for data: {variable_data_type.type_class}"
            )

    def _setup_layouts(self):
        """
        Internal function that sets up the layouts of the widget.
        """

        main_layout = QFormLayout()
        self.setLayout(main_layout)

        main_layout.addRow("Type:", self._data_type_combo_box)
        if self._value_widget:
            main_layout.addRow("Value:", self._value_widget)

    def _setup_signals(self):
        """
        Internal function that sets up the signals of the widget.
        """

        self._data_type_combo_box.currentTextChanged.connect(
            self._on_data_type_combo_box_current_text_changed
        )

        if self._value_widget:
            if isinstance(self._value_widget, QLineEdit):
                self._value_widget.textChanged.connect(
                    lambda text: self._variable.graph.set_variable_value(
                        self._variable.name, text
                    )
                )
            elif isinstance(self._value_widget, QAbstractSpinBox):
                # noinspection PyUnresolvedReferences
                self._value_widget.valueChanged.connect(
                    lambda value: self._variable.graph.set_variable_value(
                        self._variable.name, value
                    )
                )
            elif isinstance(self._value_widget, QCheckBox):
                self._value_widget.toggled.connect(
                    lambda flag: self._variable.graph.set_variable_value(
                        self._variable.name, flag
                    )
                )

    def _on_data_type_combo_box_current_text_changed(self, text: str):
        """
        Internal callback function that is called when the data type combo box text is changed.

        :param text: new text of the combo box.
        """

        self.variableTypeChanged.emit(self._variable.name, text)
