from __future__ import annotations

import json
import typing
import logging

from Qt.QtCore import Qt, Signal, QSize, QByteArray, QDataStream, QIODevice, QMimeData
from Qt.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractItemView,
)
from Qt.QtGui import QIcon, QDrag

from ..core import consts
from ...python import paths

if typing.TYPE_CHECKING:
    from ..core.graph import NodeGraph

logger = logging.getLogger(__name__)


class NodeGraphVariablesWidget(QWidget):
    """
    Widget that will be used to display the variables of the graph.
    """

    addedVariable = Signal(str)
    removedVariable = Signal(str)
    renamedVariable = Signal(str, str)
    variableSelected = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def refresh(self, graph: NodeGraph | None):
        """
        Function that refreshes the widget with the given graph.

        :param graph: node graph to get variables of.
        """

        self._variables_list.populate(graph)

    def _setup_widgets(self):
        """
        Internal function that creates the widgets that will be part of the variables widget
        """

        self._variables_list = NodeGraphVariablesList(self)
        self._add_variable_button = QPushButton(parent=self)
        self._add_variable_button.setFlat(True)
        self._add_variable_button.setIcon(
            QIcon(paths.canonical_path("../resources/icons/plus.svg"))
        )
        self._delete_variable_button = QPushButton(parent=self)
        self._delete_variable_button.setFlat(True)
        self._delete_variable_button.setIcon(
            QIcon(paths.canonical_path("../resources/icons/minus.svg"))
        )

    def _setup_layouts(self):
        """
        Internal function that sets up the layouts of the widget
        """

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(2)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self._add_variable_button)
        buttons_layout.addWidget(self._delete_variable_button)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._variables_list)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def _setup_signals(self):
        """
        Internal function that sets up the signals of the widget
        """

        self._variables_list.renamedVariable.connect(self.renamedVariable.emit)
        self._variables_list.itemClicked.connect(
            lambda item: self.variableSelected.emit(item.text())
        )
        self._add_variable_button.clicked.connect(self._on_add_variable)
        self._delete_variable_button.clicked.connect(self._on_remove_variable)

    def _on_add_variable(self):
        """
        Internal callback function that is called when the add variable button is clicked
        """

        self.addedVariable.emit("variable")

    def _on_remove_variable(self):
        """
        Internal callback function that is called when the remove variable button is clicked
        """

        selection = self._variables_list.selectedItems()
        if not selection:
            return

        variable_name = (
            selection[-1]
            .data(NodeGraphVariablesList.JSON_DATA_ROLE)
            .get("variable_name")
        )
        self.removedVariable.emit(variable_name)


class NodeGraphVariablesList(QListWidget):
    """
    List widget that will be used to display the variables of the graph.
    """

    PIXMAP_ROLE = Qt.UserRole
    JSON_DATA_ROLE = Qt.UserRole + 1

    renamedVariable = Signal(str, str)

    def __init__(self, parent: NodeGraphVariablesWidget | None = None):
        super().__init__(parent=parent)

        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        self._setup_signals()

    def startDrag(self, supported_actions: Qt.DropActions):
        """
        Function that starts the drag event.

        :param supported_actions: Qt.DropActions
        """

        # noinspection PyBroadException
        try:
            item = self.currentItem()
            json_data = item.data(NodeGraphVariablesList.JSON_DATA_ROLE)
            item_data = QByteArray()
            data_stream = QDataStream(item_data, QIODevice.WriteOnly)
            data_stream.writeQString(json.dumps(json_data))
            mime_data = QMimeData()
            mime_data.setData(consts.VARS_ITEM_MIME_DATA_FORMAT, item_data)
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec_(Qt.MoveAction)
        except Exception:
            logger.exception("Variables drag exception.")

    def populate(self, graph: NodeGraph | None):
        """
        Function that populates the list with the variables of the given graph.

        :param graph: node graph to get variables of.
        """

        self.clear()

        if not graph or not graph.variables():
            return

        for variable in graph.variables():
            new_item = QListWidgetItem()
            new_item.setFlags(
                Qt.ItemIsEnabled
                | Qt.ItemIsSelectable
                | Qt.ItemIsDragEnabled
                | Qt.ItemIsEditable
            )
            new_item.setText(variable.name)
            new_item.setSizeHint(QSize(16, 16))
            new_item.setData(
                NodeGraphVariablesList.JSON_DATA_ROLE, {"variable_name": variable.name}
            )
            self.addItem(new_item)

    def _setup_signals(self):
        """
        Internal function that sets up the signals of the widget
        """

        self.itemDoubleClicked.connect(self.editItem)
        self.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item: QListWidgetItem):
        """
        Internal callback function that is called when an item is changed

        :param item: QListWidgetItem that was changed.
        """

        json_data = item.data(NodeGraphVariablesList.JSON_DATA_ROLE)
        if not json_data:
            return

        old_variable_name = json_data["variable_name"]

        if not item.text().strip():
            item.setText(old_variable_name)
        if item.text() == old_variable_name:
            return

        old_row = self.row(item)
        self.renamedVariable.emit(old_variable_name, item.text())
