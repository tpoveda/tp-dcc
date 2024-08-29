from __future__ import annotations

import re
import json
import typing
import logging

from Qt.QtCore import (
    Qt,
    QPoint,
    QSize,
    QByteArray,
    QDataStream,
    QIODevice,
    QMimeData,
)
from Qt.QtWidgets import (
    QWidget,
    QAbstractItemView,
    QTreeWidget,
    QTreeWidgetItem,
)
from Qt.QtGui import QPixmap, QDrag

from ...qt import factory
from ...qt.widgets import search
from ..core import consts

if typing.TYPE_CHECKING:
    from ..core.graph import NodeGraph

logger = logging.getLogger(__name__)


class NodesPalette(QWidget):
    """
    Class that defines the nodes palette widget.
    """

    def __init__(self, icon_size: int = 32, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._icon_size = QSize(icon_size, icon_size)
        self._search_line: search.SearchLineEdit | None = None
        self._nodes_tree: NodesTreeWidget | None = None

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

        self.setMinimumWidth(190)

    @property
    def icon_size(self) -> QSize:
        """
        Getter method that returns the icon size of the palette icons.

        :return: palette icons size.
        """

        return self._icon_size

    @property
    def nodes_tree(self) -> NodesTreeWidget:
        """
        Getter method that returns the nodes tree widget.

        :return: nodes tree widget.
        """

        return self._nodes_tree

    def refresh(self, graph: NodeGraph):
        """
        Refreshes the palette with the nodes registered within given graph factory.

        :param graph: node graph to get nodes from factory of.
        """

        self._nodes_tree.populate(graph)

    def _setup_widgets(self):
        """
        Internal function that creates and setup widgets.
        """

        self._search_line = search.SearchLineEdit(parent=self)
        self._search_line.setPlaceholderText("Search Nodes...")
        self._nodes_tree = NodesTreeWidget(nodes_palette=self)

    def _setup_layouts(self):
        """
        Internal function that creates and setup layouts.
        """

        main_layout = factory.vertical_layout(margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        main_layout.addWidget(self._search_line)
        main_layout.addWidget(self._nodes_tree)

    def _setup_signals(self):
        """
        Internal function that connects signals and slots.
        """

        pass


class NodesTreeWidget(QTreeWidget):
    """
    Widget that displays the nodes tree.
    """

    PIXMAP_ROLE = Qt.UserRole
    NODE_ID_ROLE = Qt.UserRole + 1
    JSON_DATA_ROLE = Qt.UserRole + 2

    def __init__(self, nodes_palette: NodesPalette):
        super().__init__(parent=nodes_palette)

        self._nodes_palette: NodesPalette = nodes_palette

        self.setIconSize(self._nodes_palette.icon_size)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setColumnCount(1)
        self.setHeaderHidden(True)

    def startDrag(self, supported_actions: Qt.DropActions | Qt.DropAction):
        """
        Starts a drag event.

        :param supported_actions: supported drag actions.
        """

        # noinspection PyBroadException
        try:
            item = self.currentItem()
            node_id = item.data(0, NodesTreeWidget.NODE_ID_ROLE)
            pixmap = item.data(0, NodesTreeWidget.PIXMAP_ROLE)
            json_data = item.data(0, NodesTreeWidget.JSON_DATA_ROLE)
            item_data = QByteArray()
            data_stream = QDataStream(item_data, QIODevice.WriteOnly)
            data_stream << pixmap
            data_stream.writeQString(node_id)
            data_stream.writeQString(json.dumps(json_data))
            mime_data = QMimeData()
            mime_data.setData(consts.NODES_PALETTE_ITEM_MIME_DATA_FORMAT, item_data)
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.setHotSpot(QPoint(int(pixmap.width() / 2), int(pixmap.height() / 2)))
            drag.setPixmap(pixmap)
            drag.exec_(Qt.MoveAction)
        except Exception:
            logger.exception("Error while starting drag event", exc_info=True)

    def populate(self, graph: NodeGraph):
        """
        Populates the tree with nodes from given graph.

        :param graph: node graph to get nodes from.
        """

        self.clear()

        if not graph:
            return

        self._add_registered_nodes(graph)

    def add_category(
        self, name: str, expanded: bool = True, parent: QTreeWidgetItem | None = None
    ) -> QTreeWidgetItem:
        """
        Adds a new category item to the tree.

        :param name: name of the category.
        :param expanded: whether the category should be expanded.
        :param parent: category parent item.
        :return: newly created category item.
        """

        parent = parent or self
        category_item = QTreeWidgetItem(parent)
        category_item.setFlags(Qt.ItemIsEnabled)
        category_item.setText(0, name)
        category_item.setExpanded(expanded)

        return category_item

    def get_or_create_category_item(
        self, name: str, expanded: bool = True, parent: QTreeWidgetItem | None = None
    ) -> QTreeWidgetItem:
        """
        Returns the category item with the given name. If the category item does not exist, it is created.

        :param name: name of the category item to find.
        :param expanded: if the category does not exist, whether the category item is expanded.
        :param parent: parent item to add the category item to.
        :return: category item.
        """

        found_items = self.findItems(name, Qt.MatchExactly | Qt.MatchRecursive, 0)
        if parent is not self:
            found_items = [item for item in found_items if item.parent() is parent]
        return (
            found_items[0]
            if found_items
            else self.add_category(name, expanded=expanded, parent=parent)
        )

    def _add_registered_nodes(self, graph: NodeGraph, search_filter: str = ""):
        """
        Internal function that adds registered nodes to the tree.

        :param graph: node graph to get nodes from.
        """

        keys = list(graph.factory.node_classes)
        keys.sort()
        for node_id in keys:
            node_class = graph.factory.node_class_by_id(node_id)
            if node_class.CATEGORY == consts.INTERNAL_CATEGORY:
                continue
            palette_label = node_class.PALETTE_LABEL or node_class.NODE_NAME
            filter_matched = search_filter and (
                re.search(search_filter, palette_label, re.IGNORECASE) is not None
                or re.search(search_filter, node_class.CATEGORY, re.IGNORECASE)
                is not None
            )
            if search_filter and not filter_matched:
                continue
            self._add_node_item(
                node_id,
                palette_label,
                category=node_class.CATEGORY,
                icon_name=node_class.ICON_NAME,
            )

    def _add_node_item(
        self,
        node_id: str,
        label_text: str,
        func_signature: str = "",
        category: str = "",
        icon_name: str | None = None,
        expanded: bool = True,
    ) -> QTreeWidgetItem:
        """
        Internal function that adds a new node item to the tree.

        :param node_id: ID of the node to add.
        :param label_text: node item text.
        :param func_signature: optional function signature for the node item.
        :param category: optional node category.
        :param icon_name: optional node icon name.
        :param expanded: whether node item is expanded.
        :return: added node item.
        """

        category = category or "Undefined"
        category_path = category.split("/")
        parent_item = self
        for category_name in category_path:
            parent_item = self.get_or_create_category_item(
                category_name, expanded=expanded, parent=parent_item
            )

        item = QTreeWidgetItem()
        parent_item.addChild(item)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
        item.setText(0, label_text)
        item.setSizeHint(0, self._nodes_palette.icon_size)
        item.setData(0, NodesTreeWidget.PIXMAP_ROLE, QPixmap())
        item.setData(0, NodesTreeWidget.NODE_ID_ROLE, node_id)
        json_data = {"title": item.text(0), "func_signature": func_signature}
        item.setData(0, NodesTreeWidget.JSON_DATA_ROLE, json_data)

        return item
