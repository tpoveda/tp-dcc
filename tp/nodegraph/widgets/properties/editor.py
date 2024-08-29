from __future__ import annotations

import typing
import logging
from typing import Any
from collections import defaultdict

from Qt.QtCore import Qt, Signal, QModelIndex, QRect
from Qt.QtWidgets import (
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QPushButton,
    QLabel,
    QCheckBox,
    QTabWidget,
    QGroupBox,
    QComboBox,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QAbstractItemView,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)
from Qt.QtGui import QIcon, QPen, QBrush, QPainter, QWheelEvent

from .base import LineEditPropertyWidget
from .factory import NodePropertyWidgetFactory
from ...core.node import BaseNode, Node

if typing.TYPE_CHECKING:
    from .abstract import AbstractPropertyWidget
    from ...core.port import NodePort
    from ...core.graph import NodeGraph

logger = logging.getLogger(__name__)


class PropertyEditor(QWidget):
    """
    Base class for displaying ane editing nodes properties.
    """

    propertyChanged = Signal(str, str, object)

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

    def _create_node_property_editor_widget(
        self, node: BaseNode
    ) -> NodePropertyEditorWidget:
        """
        Internal function that creates a new node property editor widget.

        :param node: node to create the property editor widget for.
        :return: node property editor widget instance.
        """

        return NodePropertyEditorWidget(node=node, parent=self)

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


class NodePropertyEditorWidget(QWidget):
    """
    Widget that represents a node property editor.
    """

    propertyChanged = Signal(str, str, object)
    propertyClosed = Signal(str)

    def __init__(self, node: BaseNode, parent: PropertyEditor | None = None):
        super().__init__(parent=parent)

        self._node_id = node.id
        self._tab_containers: dict[str, NodePropertiesContainer] = {}

        self._tab = QTabWidget(parent=self)

        self._close_button = QPushButton(parent=self)
        self._close_button.setToolTip("Close Property.")
        self._close_button.setIcon(
            QIcon(self.style().standardPixmap(QStyle.SP_DialogCloseButton))
        )
        self._close_button.setMaximumWidth(40)
        self._name_property_widget = LineEditPropertyWidget(parent=self)
        self._name_property_widget.name = "name"
        self._name_property_widget.setToolTip("name\nSet the node name.")
        self._name_property_widget.set_value(node.name)
        self._type_widget = QLabel(parent=self)
        self._type_widget.setAlignment(Qt.AlignRight)
        self._type_widget.setToolTip(
            "type\nNode type identifier followed by the class name."
        )
        font = self._type_widget.font()
        font.setPointSize(10)
        self._type_widget.setFont(font)
        self._port_connections = self._read_node(node)

        name_layout = QHBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.addWidget(QLabel("name", parent=self))
        name_layout.addWidget(self._name_property_widget)
        name_layout.addWidget(self._close_button)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
        main_layout.addLayout(name_layout)
        main_layout.addWidget(self._tab)
        main_layout.addWidget(self._type_widget)
        self.setLayout(main_layout)

        self._close_button.clicked.connect(self._on_close_button_clicked)
        self._name_property_widget.valueChanged.connect(
            self._on_property_widget_value_changed
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return (
            f'<{self.__class__.__name__}("{self._node_id}") object at {hex(id(self))}>'
        )

    @property
    def node_id(self) -> str:
        """
        Returns the node id of the property editor.

        :return: str
        """

        return self._node_id

    @property
    def connection_widget(self) -> NodePortConnectionsContainer:
        """
        Returns the connection widget of the property editor.

        :return: NodePortConnectionsContainer
        """

        return self._port_connections

    def add_tab(self, tab_name: str) -> NodePropertiesContainer:
        """
        Adds a new tab to the property editor.

        :param tab_name: name of the tab to add.
        :return: properties container widget.
        """

        if tab_name in self._tab_containers:
            raise AssertionError(f"Tab with name '{tab_name}' already exists.")

        self._tab_containers[tab_name] = NodePropertiesContainer(parent=self)
        self._tab.addTab(self._tab_containers[tab_name], tab_name)

        return self._tab_containers[tab_name]

    def tab_widget(self) -> QTabWidget:
        """
        Returns the tab widget of the property editor.

        :return: QTabWidget
        """

        return self._tab

    def add_property_widget(
        self, name: str, widget: AbstractPropertyWidget, tab_name: str = "Properties"
    ):
        """
        Adds a new property widget to the property editor.

        :param name: name of the property to add.
        :param widget: property widget to add.
        :param tab_name: name of the tab to add the property widget to.
        """

        if tab_name not in self._tab_containers:
            tab_name = "Properties"

        self._tab_containers[tab_name].add_property_widget(name, widget)
        widget.valueChanged.connect(self._on_property_widget_value_changed)

    def property_widget(self, name: str) -> QWidget | None:
        """
        Returns the property widget for the given name.

        :param name: name of the widget to return.
        :return: QWidget | None
        """

        if name == "name":
            return self._name_property_widget

        found_widget: QWidget | None = None
        for container in self._tab_containers.values():
            found_widget = container.property_widget(name)
            if not found_widget:
                continue

        return found_widget

    def property_widgets(self) -> list[QWidget]:
        """
        Returns all property widgets in the property editor.

        :return: dict[str, QWidget]
        """

        widgets = [self._name_property_widget]
        for container in self._tab_containers.values():
            widgets.extend(container.property_widgets().values())

        return widgets

    def set_port_lock_widgets_disabled(self, flag: bool = True):
        """
        Sets the port lock widgets to disable.

        :param flag: bool
        """

        if not self._port_connections:
            return

        self._port_connections.set_lock_controls_disable(flag)

    def _read_node(self, node: BaseNode | Node) -> NodePortConnectionsContainer:
        """
        Internal function that populates widget from a node.

        :param node: node to read from.
        :return: ports container widget.
        """

        model = node.model
        graph_model = node.graph.model
        # noinspection PyTypeChecker
        common_properties = graph_model.node_common_properties(node.type)

        tab_mapping: dict[str, list[tuple[str, Any]]] = defaultdict(list)
        for property_name, property_value in model.custom_properties.items():
            tab_name = model.tab_name(property_name)
            tab_mapping[tab_name].append((property_name, property_value))

        reserved_tabs = ["Node", "Ports"]
        for tab in sorted(tab_mapping.keys()):
            if tab in reserved_tabs:
                logger.warning(f"Tab name '{tab}' is reserved and cannot be used.")
                continue
            self.add_tab(tab)

        widget_factory = NodePropertyWidgetFactory()

        for tab in sorted(tab_mapping.keys()):
            properties_container = self._tab_containers[tab]
            for property_name, property_value in tab_mapping[tab]:
                property_widget_type = model.widget_type(property_name)
                if property_widget_type == 0:
                    continue
                property_widget = widget_factory.widget(property_widget_type)
                if not property_widget:
                    logger.warning(f"Property widget for '{property_name}' not found.")
                    continue
                property_widget.name = property_name
                tooltip: str | None = None
                if property_name in common_properties:
                    if "items" in common_properties[property_name].keys():
                        property_widget.set_items(
                            common_properties[property_name]["items"]
                        )
                    if "range" in common_properties[property_name].keys():
                        prop_range = common_properties[property_name]["range"]
                        property_widget.set_min(prop_range[0])
                        property_widget.set_max(prop_range[1])
                properties_container.add_property_widget(
                    name=property_name,
                    widget=property_widget,
                    value=property_value,
                    label=property_name.replace("_", " "),
                    tooltip=tooltip,
                )
                property_widget.valueChanged.connect(
                    self._on_property_widget_value_changed
                )

        self.add_tab("Node")
        default_node_properties: dict[str, str] = {
            "color": "Node base color.",
            "text_color": "Node text color.",
            "border_color": "Node border color.",
            "disabled": "Disable/Enable node state.",
            "id": "Unique identifier of the node.",
        }
        node_properties_container = self._tab_containers["Node"]
        for property_name, tooltip in default_node_properties.items():
            widget_type = model.widget_type(property_name)
            property_widget = widget_factory.widget(widget_type)
            if not property_widget:
                logger.warning(f"Property widget for '{property_name}' not found.")
                continue
            property_widget.name = property_name
            node_properties_container.add_property_widget(
                name=property_name,
                widget=property_widget,
                value=model.property(property_name),
                label=property_name.replace("_", " "),
                tooltip=tooltip,
            )
            property_widget.valueChanged.connect(self._on_property_widget_value_changed)

        self._type_widget.setText(model.property("type") or "")

        ports_container: NodePortConnectionsContainer | None = None
        if node.inputs or node.outputs:
            ports_container = NodePortConnectionsContainer(node=node, parent=self)
            self._tab.addTab(ports_container, "Ports")

        tab_index = {self._tab.tabText(x): x for x in range(self._tab.count())}
        current_index: int | None = None
        for tab_name, properties_container in self._tab_containers.items():
            property_widgets = properties_container.property_widgets()
            if not property_widgets:
                self._tab.setTabVisible(tab_index[tab_name], False)
                continue
            if current_index is None:
                current_index = tab_index[tab_name]

        self._tab.setCurrentIndex(current_index)

        return ports_container

    def _on_close_button_clicked(self):
        """
        Internal callback function that is called when the close button is clicked.
        """

        self.propertyClosed.emit(self._node_id)

    def _on_property_widget_value_changed(
        self, property_name: str, property_value: Any
    ):
        """
        Internal callback function that is called when a property widget value changes.

        :param property_name: name of the property that changed.
        :param property_value: new value of the property.
        """

        self.propertyChanged.emit(self._node_id, property_name, property_value)


class NodePropertiesContainer(QWidget):
    """
    Widget that displays the node properties.
    """

    def __init__(self, parent: NodePropertyEditorWidget | None = None):
        super().__init__(parent=parent)

        self._property_widgets: dict[str, QWidget] = {}

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(main_layout)

        self._layout = QGridLayout()
        self._layout.setSpacing(6)
        self._layout.setColumnStretch(1, 1)

        main_layout.addLayout(self._layout)

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f"<{self.__class__.__name__} object at {hex(id(self))}>"

    def add_property_widget(
        self,
        name: str,
        widget: AbstractPropertyWidget,
        value: Any = None,
        label: str | None = None,
        tooltip: str | None = None,
    ):
        """
        Adds a new property widget to the container.

        :param name: property name to be displayed.
        :param widget: property widget to add.
        :param value: value of the property.
        :param label: label to display.
        :param tooltip: tooltip to display.
        """

        label = label or name
        label_widget = QLabel(label, parent=self)
        if tooltip:
            widget.setToolTip(f"{name}\n{tooltip}")
            label_widget.setToolTip(f"{name}\n{tooltip}")
        else:
            widget.setToolTip(name)
            label_widget.setToolTip(name)
        if value is not None:
            widget.set_value(value)
        row = self._layout.rowCount()
        if row > 0:
            row += 1
        label_flags = Qt.AlignCenter | Qt.AlignRight
        if widget.__class__.__name__ == "TextEditPropertyWidget":
            label_flags = label_flags | Qt.AlignTop
        self._layout.addWidget(label_widget, row, 0, label_flags)
        self._layout.addWidget(widget, row, 1)
        self._property_widgets[name] = widget

    def property_widget(self, name: str) -> QWidget:
        """
        Returns the property widget for the given name.

        :param name: name of the property widget to return.
        :return: QWidget | None
        """

        return self._property_widgets.get(name)

    def property_widgets(self) -> dict[str, QWidget]:
        """
        Returns all property widgets in the container.

        :return: dict[str, QWidget]
        """

        return self._property_widgets


class NodePortConnectionsContainer(QWidget):
    """
    Widget that displays the node ports and connections.
    """

    def __init__(self, node: BaseNode | Node, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._node = node
        self._ports: dict[str, NodePort] = {}

        self._input_group, self._input_tree = self._setup_tree_group("Input Ports")
        self._input_group.setToolTip("Display input port connections.")
        for port in node.inputs:
            self._setup_row(self._input_tree, port)
        for i in range(self._input_tree.columnCount()):
            self._input_tree.resizeColumnToContents(i)

        self._output_group, self._output_tree = self._setup_tree_group("Output Ports")
        self._output_group.setToolTip("Display output port connections.")
        for port in node.outputs:
            self._setup_row(self._output_tree, port)
        for i in range(self._output_tree.columnCount()):
            self._output_tree.resizeColumnToContents(i)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.addWidget(self._input_group)
        main_layout.addWidget(self._output_group)
        main_layout.addStretch()
        self.setLayout(main_layout)

        self._input_group.setChecked(False)
        self._input_tree.setVisible(False)
        self._output_group.setChecked(False)
        self._output_tree.setVisible(False)

    def __repr__(self) -> str:
        """
        Returns a string representation of the widget.

        :return: string representation.
        """

        return f"<{self.__class__.__name__} object at {hex(id(self))}>"

    @property
    def input_group(self) -> QGroupBox:
        """
        Returns the input group box.

        :return: input group box.
        """

        return self._input_group

    @property
    def input_tree(self) -> QTreeWidget:
        """
        Returns the input tree widget.

        :return: input tree widget.
        """

        return self._input_tree

    @property
    def output_group(self) -> QGroupBox:
        """
        Returns the output group box.

        :return: output group box.
        """

        return self._output_group

    @property
    def output_tree(self) -> QTreeWidget:
        """
        Returns the output tree widget.

        :return: output tree widget.
        """

        return self._output_tree

    def _setup_tree_group(self, title: str) -> tuple[QGroupBox, QTreeWidget]:
        """
        Internal function that sets up a tree group.

        :param title: title of the group.
        :return: tuple containing the group box and tree widget contained within it.
        """

        group_box_layout = QVBoxLayout()
        group_box_layout.setContentsMargins(2, 2, 2, 2)
        group_box = QGroupBox(parent=self)
        group_box.setMaximumHeight(200)
        group_box.setCheckable(True)
        group_box.setChecked(True)
        group_box.setTitle(title)
        group_box.setLayout(group_box_layout)

        headers = ["Locked", "Name", "Connections", ""]
        tree_widget = QTreeWidget(parent=self)
        tree_widget.setColumnCount(len(headers))
        tree_widget.setHeaderLabels(headers)
        tree_widget.setHeaderHidden(False)
        tree_widget.header().setStretchLastSection(False)
        QHeaderView.setSectionResizeMode(tree_widget.header(), 2, QHeaderView.Stretch)
        group_box.setLayout(QVBoxLayout())

        group_box_layout.addWidget(tree_widget)

        return group_box, tree_widget

    def _setup_row(self, tree: QTreeWidget, port: NodePort):
        """
        Internal function that sets up a row in the tree widget.

        :param tree: tree widget to set up row of.
        :param port: port to set up.
        """

        item = QTreeWidgetItem(tree)
        item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
        item.setText(1, port.name)
        item.setToolTip(0, "Lock Port")
        item.setToolTip(1, "Port Name")
        item.setToolTip(2, "Select connected port.")
        item.setToolTip(3, "Center on connected port node.")

        lock_checkbox = QCheckBox(parent=self)
        lock_checkbox.setChecked(port.locked)

        combo = QComboBox(parent=self)
        for port in port.connected_ports():
            item_name = f'{port.name} : "{port.node.name}"'
            self._ports[item_name] = port
            combo.addItem(item_name)

        focus_button = QPushButton(parent=self)
        focus_button.setIcon(
            QIcon(tree.style().standardPixmap(QStyle.SP_DialogYesButton))
        )

        tree.setItemWidget(item, 0, lock_checkbox)
        tree.setItemWidget(item, 2, combo)
        tree.setItemWidget(item, 3, focus_button)

        lock_checkbox.clicked.connect(lambda x: port.set_locked(x))
        focus_button.clicked.connect(
            lambda: self._on_focus_to_node(self._ports.get(combo.currentText()))
        )

    def set_lock_controls_disable(self, flag: bool = False):
        """
        Enables/Disables port lock column widgets.

        :param flag: True to disable checkbox; False to enable it.
        """

        for i in range(self._input_tree.topLevelItemCount()):
            item = self._input_tree.topLevelItem(i)
            checkbox_widget = self._input_tree.itemWidget(item, 0)
            checkbox_widget.setDisabled(flag)
        for i in range(self._output_tree.topLevelItemCount()):
            item = self._output_tree.topLevelItem(i)
            checkbox_widget = self._output_tree.itemWidget(item, 0)
            checkbox_widget.setDisabled(flag)

    @staticmethod
    def _on_focus_to_node(port: NodePort):
        """
        Internal callback function that focuses on a node.

        :param port: port to focus on.
        """

        if not port:
            return

        node = port.node
        node.graph.center_on([node])
        node.graph.clear_selected_nodes()
        node.selected = True
