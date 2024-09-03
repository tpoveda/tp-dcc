from __future__ import annotations

import typing
import logging
from typing import Type, Any
from functools import partial

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QTabWidget,
    QStyle,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)
from Qt.QtGui import QIcon, QShowEvent

from tp.qt import contexts
from tp.nodegraph.core import consts

from .base import LineEditPropertyWidget
from .factory import NodePropertyWidgetFactory
from ...core import datatypes

if typing.TYPE_CHECKING:
    from .abstract import AbstractPropertyWidget
    from ...core.port import NodePort
    from ...core.node import BaseNode, Node

logger = logging.getLogger(__name__)


class NodePropertyEditorWidget(QWidget):
    """
    Widget that represents a node property editor.
    """

    IGNORED_DATA_CLASSES: list[datatypes.DataType] = [datatypes.Exec, datatypes.List]
    IGNORED_CLASSES: list[Type] = [
        data_type.type_class for data_type in IGNORED_DATA_CLASSES
    ]

    propertyChanged = Signal(str, str, object)
    propertyClosed = Signal(str)

    def __init__(self, node: BaseNode, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._node_id = node.id
        self._tab_containers: dict[str, NodePropertiesContainer] = {}
        self._port_properties_map: dict[
            str, tuple[NodePort, AbstractPropertyWidget]
        ] = {}

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
        font.setBold(True)
        self._type_widget.setFont(font)

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

        self._widget_factory = NodePropertyWidgetFactory()

        self._setup_node(node)

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

    def showEvent(self, event: QShowEvent):
        """
        Overrides QWidget showEvent function.
        """

        super().showEvent(event)
        self.update_port_properties()

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

    def update_port_properties(self):
        """
        Updates the properties of the ports.
        """

        with contexts.block_signals(self):
            for port, widget in self._port_properties_map.values():
                self._update_port_widget_value(port, widget)
                if port.type == consts.PortType.Input.value:
                    widget.setEnabled(not port.connected_ports())

    def _update_port_widget_value(self, port: NodePort, widget: AbstractPropertyWidget):
        pass

    def _setup_node(self, node: BaseNode | Node):
        """
        Internal function that sets up the node.

        :param node: node to get data from.
        """

        self._setup_fields(node)
        self._setup_node_properties(node)
        self.update_port_properties()
        self._setup_signals()

    def _setup_fields(self, node: BaseNode | Node):
        """
        Internal function that sets up the fields of the widget.

        :param node: node to get data from.
        """

        self.add_tab("Node")
        node_properties_container = self._tab_containers["Node"]
        ports = node.non_exec_inputs
        ports = ports or node.non_exec_outputs
        for port in ports:
            type_class = port.data_type.type_class
            if any(
                [
                    issubclass(type_class, data_type)
                    for data_type in self.__class__.IGNORED_CLASSES
                ]
            ):
                continue

            widget_type = (
                port.data_type.property_type.value
                if port.data_type.property_type
                else None
            )

            property_widget = (
                self._widget_factory.widget(widget_type)
                if widget_type is not None
                else None
            )
            if not property_widget:
                logger.warning(
                    f'Was not possible to create property widget for "{port}::{port.data_type.type_class}"'
                )
                continue
            property_widget.name = port.name
            node_properties_container.add_property_widget(
                name=port.name,
                widget=property_widget,
                value=port.value(),
                label=port.name.replace("_", " "),
            )
            self._port_properties_map[port.name] = (port, property_widget)

    def _setup_node_properties(self, node: BaseNode | Node):
        """
        Internal function that sets up the node properties.

        :param node: node to get data from.
        """

        model = node.model

        self.add_tab("Properties")
        default_node_properties: dict[str, str] = {
            "color": "Node base color.",
            "text_color": "Node text color.",
            "border_color": "Node border color.",
            "disabled": "Disable/Enable node state.",
            "id": "Unique identifier of the node.",
        }
        node_properties_container = self._tab_containers["Properties"]
        for property_name, tooltip in default_node_properties.items():
            widget_type = model.widget_type(property_name)
            property_widget = self._widget_factory.widget(widget_type)
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

    def _setup_signals(self):
        """
        Internal function that sets up signals.
        """

        for port, widget in self._port_properties_map.values():
            if port.type == consts.PortType.Input.value:
                port.signals.connectionChanged.connect(self.update_port_properties)
            if not port.model.is_runtime_data():
                widget.valueChanged.connect(
                    partial(self._on_port_property_widget_value_changed, port)
                )

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

    def _on_port_property_widget_value_changed(
        self, port: NodePort, port_name: str, port_value: Any
    ):
        """
        Internal callback function that is called when a socket property widget value changes.

        :param port_name: name of the socket that changed.
        :param port_value: new value of the socket.
        """

        port.set_value(port_value)


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
