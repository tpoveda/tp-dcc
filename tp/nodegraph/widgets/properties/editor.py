from __future__ import annotations

import typing
import logging
from typing import Any

from Qt.QtCore import Qt, Signal, QModelIndex, QRect
from Qt.QtWidgets import (
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QPushButton,
    QTreeWidget,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QAbstractItemView,
    QVBoxLayout,
    QHBoxLayout,
)
from Qt.QtGui import QPen, QBrush, QPainter, QWheelEvent

from .node import NodePropertyEditorWidget
from .variable import VariablePropertyEditor
from ...core.node import BaseNode
from ...core.consts import Variable
from ...nodes.node_getset import VariableNode

if typing.TYPE_CHECKING:
    from ...core.graph import NodeGraph

logger = logging.getLogger(__name__)


class PropertyEditor(QWidget):
    """
    Base class for displaying ane editing nodes properties.
    """

    propertyChanged = Signal(str, str, object)
    variableTypeChanged = Signal(str, str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._lock: bool = False
        self._block_signal: bool = False
        self._graph: NodeGraph | None = None

        self._properties_list = PropertiesListWidget(parent=self)
        self._limit_spinbox = QSpinBox(parent=self)
        self._limit_spinbox.setToolTip("Set Display Nodes Limit.")
        self._limit_spinbox.setMinimum(0)
        self._limit_spinbox.setMaximum(10)
        self._limit_spinbox.setValue(2)
        self._button_lock = QPushButton("Lock", parent=self)
        self._button_lock.setToolTip(
            "Lock the properties editor preventing nodes from being loaded."
        )
        self._clear_button = QPushButton("Clear", parent=self)
        self._clear_button.setToolTip("Clear all properties.")

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(2)
        top_layout.addWidget(self._limit_spinbox)
        top_layout.addStretch(1)
        top_layout.addWidget(self._button_lock)
        top_layout.addWidget(self._clear_button)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self._properties_list, 1)

        self._limit_spinbox.valueChanged.connect(self._on_limit_spinbox_value_changed)
        self._button_lock.clicked.connect(self._on_lock_button_clicked)
        self._clear_button.clicked.connect(self._on_clear_button_clicked)

        self.setWindowTitle("Properties Editor")
        self.resize(450, 400)

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f"<{self.__class__.__name__} object at {hex(id(self))}>"

    @property
    def limit(self) -> int:
        """
        Returns the limit of nodes to display.

        :return: int
        """

        return self._limit_spinbox.value()

    @limit.setter
    def limit(self, value: int):
        """
        Sets the limit of nodes to display.

        :param value: int
        """

        self._limit_spinbox.setValue(value)

    def property_editor_widget(
        self, node: str | BaseNode
    ) -> NodePropertyEditorWidget | QWidget | None:
        """
        Returns the property editor widget for the given node.

        :param node: node to return the property editor widget for.
        :return: NodePropertyEditorWidget
        """

        node_id = node.id if isinstance(node, BaseNode) else node
        found_items = self._properties_list.findItems(node_id, Qt.MatchExactly)
        if not found_items:
            return None

        return self._properties_list.cellWidget(found_items[0].row(), 0)

    def update_property_editor_widget(
        self, node: BaseNode, property_name: str, property_value: Any
    ):
        """
        Updates the property editor widget for the given node.

        :param node: node to update the property editor widget for.
        :param property_name: name of the property to update.
        :param property_value: value of the property to update.
        """

        properties_widget = self.property_editor_widget(node.id)
        if not properties_widget:
            return

        property_widget = properties_widget.property_widget(property_name)
        if not properties_widget:
            return

        # noinspection PyUnresolvedReferences
        if property_widget and property_value != property_widget.get_value():
            self._block_signal = True
            try:
                # noinspection PyUnresolvedReferences
                property_widget.set_value(property_value)
            finally:
                self._block_signal = False

    def add_node(self, node: BaseNode):
        """
        Adds a new node to properties editor.

        :param node: node to add.
        """

        if self.limit == 0 or self._lock:
            return

        # Do not add variable nodes to the properties editor.
        if isinstance(node, VariableNode):
            return

        rows = self._properties_list.rowCount() - 1
        if rows >= self.limit:
            self._properties_list.removeRow(rows - 1)

        found_item = self._properties_list.findItems(node.id, Qt.MatchExactly)
        if found_item:
            self._properties_list.removeRow(found_item[0].row())

        self._properties_list.insertRow(0)

        node_property_widget = self._create_node_property_editor_widget(node)
        node_property_widget.propertyClosed.connect(
            self._on_node_property_widget_property_closed
        )
        node_property_widget.propertyChanged.connect(
            self._on_node_property_widget_property_changed
        )
        port_connection_widget = node_property_widget.connection_widget
        if port_connection_widget:
            port_connection_widget.input_group.clicked.connect(
                lambda v: self._on_port_tree_visible_changed(
                    node_property_widget.node_id, v, port_connection_widget.input_tree
                )
            )
            port_connection_widget.output_group.clicked.connect(
                lambda v: self._on_port_tree_visible_changed(
                    node_property_widget.node_id, v, port_connection_widget.output_tree
                )
            )

        self._properties_list.setCellWidget(0, 0, node_property_widget)

        item = QTableWidgetItem(node.id)
        self._properties_list.setItem(0, 0, item)
        self._properties_list.selectRow(0)

    def remove_node(self, node: str | BaseNode):
        """
        Removes a node from properties editor.

        :param node: node to remove.
        """

        node_id = node.id if isinstance(node, BaseNode) else node
        self._on_node_property_widget_property_closed(node_id)

    def add_variable(self, variable: Variable):
        """
        Adds a new variable to properties editor.

        :param variable: variable to add.
        """

        if self.limit == 0 or self._lock:
            return

        rows = self._properties_list.rowCount() - 1
        if rows >= self.limit:
            self._properties_list.removeRow(rows - 1)

        found_item = self._properties_list.findItems(variable.name, Qt.MatchExactly)
        if found_item:
            self._properties_list.removeRow(found_item[0].row())

        self._properties_list.insertRow(0)

        variable_property_widget = self._create_variable_property_editor_widget(
            variable
        )
        variable_property_widget.variableTypeChanged.connect(
            self._on_variable_property_type_changed
        )

        self._properties_list.setCellWidget(0, 0, variable_property_widget)

        item = QTableWidgetItem(variable.name)
        self._properties_list.setItem(0, 0, item)
        self._properties_list.selectRow(0)

    def remove_variable(self, variable: str | Variable):
        """
        Removes a variable from properties editor.

        :param variable: variable to remove.
        """

        variable_name = variable.name if isinstance(variable, Variable) else variable
        self._on_variable_property_widget_variable_closed(variable_name)

    def clear(self):
        """
        Clears all properties in the properties editor.
        """

        self._on_clear_button_clicked()

    def _on_node_property_widget_property_closed(self, node_id: str):
        """
        Internal callback function that is called when a node property widget is closed.

        :param node_id: id of the node that closed.
        """

        found_items = self._properties_list.findItems(node_id, Qt.MatchExactly)
        [self._properties_list.removeRow(i.row()) for i in found_items]

    def _on_node_property_widget_property_changed(
        self, node_id: str, property_name: str, property_value: Any
    ):
        """
        Internal callback function that is called when a node property widget changes.

        :param node_id: id of the node that changed.
        :param property_name: name of the property that changed.
        :param property_value: new value of the property.
        """

        if self._block_signal:
            return

        self.propertyChanged.emit(node_id, property_name, property_value)

    def _on_variable_property_type_changed(
        self, variable_name: str, data_type_name: str
    ):
        """
        Internal callback function that is called when a variable property type changes.

        :param variable_name: name of the variable that changed.
        :param data_type_name: name of the data type that changed.
        """

        if self._block_signal:
            return

        # noinspection PyUnresolvedReferences
        variable = self.sender().variable
        self.variableTypeChanged.emit(variable_name, data_type_name)
        self.remove_variable(variable_name)
        self.add_variable(variable)

    def _on_variable_property_widget_variable_closed(self, variable_name: str):
        """
        Internal callback function that is called when a variable property widget is closed.

        :param variable_name: name of the variable that closed.
        """

        found_items = self._properties_list.findItems(variable_name, Qt.MatchExactly)
        [self._properties_list.removeRow(i.row()) for i in found_items]

    def _create_node_property_editor_widget(
        self, node: BaseNode
    ) -> NodePropertyEditorWidget:
        """
        Internal function that creates a new node property editor widget.

        :param node: node to create the property editor widget for.
        :return: node property editor widget instance.
        """

        return NodePropertyEditorWidget(node=node, parent=self)

    def _create_variable_property_editor_widget(self, variable: Variable):
        """
        Internal function that creates a new variable property editor widget.

        :param variable: variable to create the property editor widget for.
        :return: variable property editor widget instance.
        """

        return VariablePropertyEditor(variable=variable, parent=self)

    def _on_limit_spinbox_value_changed(self, value: int):
        """
        Internal callback function that is called when the limit spinbox value changes.

        :param value: int
        """

        rows = self._properties_list.rowCount()
        if rows > value:
            self._properties_list.setRowCount(rows - 1)

    def _on_lock_button_clicked(self):
        """
        Internal callback function that is called when the lock button is clicked.
        """

        self._lock = not self._lock
        self._button_lock.setText("Unlock" if self._lock else "Lock")

    def _on_clear_button_clicked(self):
        """
        Internal callback function that is called when the clear button is clicked.
        """

        self._properties_list.clear()
        self._properties_list.setRowCount(0)

    def _on_port_tree_visible_changed(
        self, node_id: str, visible: bool, tree_widget: QTreeWidget
    ):
        """
        Internal callback function that is called when the port tree visibility changes.

        :param node_id: id of the node.
        :param visible: True if visible; False otherwise.
        :param tree_widget: tree widget to change visibility of.
        """

        found_items = self._properties_list.findItems(node_id, Qt.MatchExactly)
        if not found_items:
            return

        tree_widget.setVisible(visible)
        widget = self._properties_list.cellWidget(found_items[0].row(), 0)
        widget.adjustSize()
        QHeaderView.setSectionResizeMode(
            self._properties_list.verticalHeader(), QHeaderView.ResizeToContents
        )


class PropertiesListWidget(QTableWidget):
    """
    Widget that displays a list of properties for a given node.
    """

    def __init__(self, parent: PropertyEditor | None = None):
        super().__init__(parent=parent)

        self.setColumnCount(1)
        self.setShowGrid(False)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        QHeaderView.setSectionResizeMode(
            self.verticalHeader(), QHeaderView.ResizeToContents
        )
        QHeaderView.setSectionResizeMode(
            self.horizontalHeader(), 0, QHeaderView.Stretch
        )
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setItemDelegate(PropertiesListDelegate())

    def wheelEvent(self, event: QWheelEvent):
        """
        Overrides the base QTableWidget wheelEvent to handle wheel event.

        :param event: QWheelEvent
        """

        delta = event.angleDelta().y() * 0.2
        self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta))


class PropertiesListDelegate(QStyledItemDelegate):
    """
    Delegate class for the properties list widget.
    """

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """
        Overrides the base QStyledItemDelegate paint method to paint the item.

        :param painter: painter object to paint item with.
        :param option: style option to paint item with.
        :param index: index of the item to paint.
        """

        painter.save()
        try:
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.setPen(Qt.NoPen)
            background_color = option.palette.base().color()
            painter.setBrush(QBrush(background_color))
            painter.drawRect(option.rect)
            border_width = 1
            if option.state & QStyle.State_Selected:
                bdr_clr = option.palette.highlight().color()
                painter.setPen(QPen(bdr_clr, 1.5))
            else:
                bdr_clr = option.palette.alternateBase().color()
                painter.setPen(QPen(bdr_clr, 1))

            painter.setBrush(Qt.NoBrush)
            painter.drawRect(
                QRect(
                    option.rect.x() + border_width,
                    option.rect.y() + border_width,
                    option.rect.width() - (border_width * 2),
                    option.rect.height() - (border_width * 2),
                )
            )
        finally:
            painter.restore()
