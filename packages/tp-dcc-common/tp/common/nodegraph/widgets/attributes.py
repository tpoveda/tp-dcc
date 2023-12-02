from __future__ import annotations

import typing

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.common.nodegraph import registers
from tp.common.nodegraph.core import socket

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import Node

logger = log.tpLogger


class AttributesWidget(qt.QGroupBox):

    IGNORED_DATA_TYPES = [registers.DataType.EXEC, registers.DataType.LIST]
    IGNORED_CLASSES = [dt['class'] for dt in IGNORED_DATA_TYPES]

    def __init__(self, node: Node, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._node = node
        self._fields_map: dict[str, tuple[socket.Socket, qt.QWidget]] = {}

        self.main_layout = qt.form_layout()
        self.setLayout(self.main_layout)

        self.setTitle(self._node.DEFAULT_TITLE)

        self._setup_fields()
        self.update_fields()
        self._setup_signals()

    @override
    def showEvent(self, event: qt.QShowEvent) -> None:
        super().showEvent(event)
        self.update_fields()

    def update_fields(self):
        """
        Updates all attribute fields with the latest values from node.
        """

        with qt.block_signals(self):
            for label, socket_widget_pair in self._fields_map.items():
                found_socket, widget = socket_widget_pair
                self._update_widget_value(found_socket, widget)
                if isinstance(found_socket, socket.InputSocket):
                    widget.setEnabled(not found_socket.has_edge())

    def _setup_fields(self):
        """
        Internal function that creates the fields for the node attributes to edit.
        """

        self._fields_map.clear()
        socket_list = self._node.list_non_exec_inputs()
        socket_list = socket_list or self._node.list_non_exec_outputs()

        for found_socket in socket_list:
            try:
                if any([issubclass(found_socket.data_class, dt_class) for dt_class in self.__class__.IGNORED_CLASSES]):
                    continue
                widget = None
                if issubclass(found_socket.data_class, registers.DataType.STRING.get('class')):
                    widget = qt.QLineEdit()
                elif issubclass(found_socket.data_class, registers.DataType.BOOLEAN.get('class')):
                    widget = qt.QCheckBox()
                elif issubclass(found_socket.data_class, registers.DataType.NUMERIC.get('class')):
                    widget = qt.QDoubleSpinBox()
                    widget.setRange(-9999, 9999)
                # elif issubclass(socket.data_class, editor_conf.DataType.LIST.get('class')):
                #     widget = QtWidgets.QListWidget()
                elif issubclass(found_socket.data_class, registers.DataType.CONTROL.get('class')):
                    widget = qt.QLineEdit()
                elif issubclass(found_socket.data_class, registers.DataType.COMPONENT.get('class')):
                    widget = qt.QLineEdit()
                else:
                    logger.error(f'Failed to create attribute field: {found_socket}::{found_socket.data_class}')
                if widget:
                    # Store in the map and add to layout
                    self._store_in_fields_map(found_socket, widget)
                    self.main_layout.addRow(found_socket.label, widget)
                # Signals
            except Exception:
                logger.exception('Attribute field add exception', exc_info=True)

    def _setup_signals(self):
        """
        Internal function that creates all signal connections.
        """

        for label, socket_widget_pair in self._fields_map.items():
            socket_found, widget = socket_widget_pair
            if isinstance(socket_found, socket.InputSocket):
                socket_found.signals.connectionChanged.connect(self.update_fields)
            if socket_found.is_runtime_data():
                continue
            if isinstance(widget, qt.QLineEdit):
                widget.textChanged.connect(socket_found.set_value)
            elif isinstance(widget, qt.QAbstractSpinBox):
                widget.valueChanged.connect(socket_found.set_value)
            elif isinstance(widget, qt.QCheckBox):
                widget.toggled.connect(socket_found.set_value)

    def _store_in_fields_map(
            self, socket_to_store: socket.Socket, widget: qt.QLineEdit | qt.QCheckBox | qt.QDoubleSpinBox):
        """
        Internal function that maps given socket label with the socket instance and its attribute editor.

        :param socket.Socket socket_to_store: socket to store.
        :param qt.QWidget widget: attribute editor widget.
        """

        self._fields_map[socket_to_store.label] = (socket_to_store, widget)

    def _update_widget_value(
            self, socket_to_update: socket.Socket, widget: qt.QLineEdit | qt.QCheckBox | qt.QDoubleSpinBox):
        """
        Internal function that handles the update of the node field attribute editor.

        :param socket.Socket socket_to_update: socket to update value of.
        :param qt.QWidget widget: attribute editor widget.
        """

        try:
            if issubclass(socket_to_update.data_class, registers.DataType.STRING.get('class')):
                widget.setText(str(socket_to_update.value()))
            elif issubclass(socket_to_update.data_class, registers.DataType.BOOLEAN.get('class')):
                widget.setChecked(socket_to_update.value())
            elif issubclass(socket_to_update.data_class, registers.DataType.NUMERIC.get('class')):
                if socket_to_update.value():
                    widget.setValue(socket_to_update.value())
            elif issubclass(socket_to_update.data_class, registers.DataType.CONTROL.get('class')):
                if socket_to_update.value():
                    widget.setText(str(socket_to_update.value().fullPathName()))
                else:
                    widget.clear()
            elif issubclass(socket_to_update.data_class, registers.DataType.COMPONENT.get('class')):
                if socket_to_update.value():
                    if hasattr(socket_to_update.value(), 'pynode'):
                        widget.setText(str(socket_to_update.value().pynode.name()))
                    else:
                        widget.setText(str(socket_to_update.value()))
            else:
                logger.error(f'Failed to create attribute field: {socket_to_update}::{socket_to_update.data_class}')
        except Exception:
            logger.exception(f'Failed to update widget value for {socket_to_update}', exc_info=True)
