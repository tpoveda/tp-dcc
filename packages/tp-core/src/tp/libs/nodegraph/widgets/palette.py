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
from Qt.QtGui import QIcon, QPixmap, QDrag

from ...qt import factory
from ...qt.widgets import search
from ..core import consts, datatypes

if typing.TYPE_CHECKING:
    from ..core.graph import NodeGraph

logger = logging.getLogger(__name__)


class NodesPalette(QWidget):
    """
    Class that defines the nodes palette widget.
    """

    def __init__(
        self,
        icon_size: int = 32,
        data_type_filter: datatypes.DataType | None = None,
        functions_first: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._icon_size = QSize(icon_size, icon_size)
        self._data_type_filter = data_type_filter
        self._functions_first = functions_first
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
    def data_type_filter(self) -> datatypes.DataType | None:
        """
        Getter method that returns the data type filter.

        :return: data type filter.
        """

        return self._data_type_filter

    @property
    def functions_first(self) -> bool:
        """
        Getter method that returns whether functions should be displayed first.

        :return: whether functions should be displayed first.
        """

        return self._functions_first

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
        self._add_registered_functions(graph)

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
        :param search_filter: search filter.
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
                icon_path=node_class.ICON_PATH,
            )

    def _add_registered_functions(self, graph: NodeGraph, search_filter: str = ""):
        """
        Internal function that adds registered functions to the tree.

        :param graph: node graph to get nodes from.
        :param search_filter: search filter.
        """

        keys = list(graph.factory.function_data_types)
        keys.sort()

        for data_type_name in keys:
            # If data type filter is set, skip if data type does not match filter type class.
            if data_type_name != "UNBOUND" and self._nodes_palette.data_type_filter:
                if not issubclass(
                    self._nodes_palette.data_type_filter.type_class,
                    graph.factory.data_type_by_name(data_type_name).type_class,
                ):
                    continue

            function_signatures = graph.factory.function_signatures_by_type_name(
                data_type_name
            )
            for function_signature in function_signatures:
                expanded = self._nodes_palette.functions_first or bool(search_filter)
                function = graph.factory.function_by_type_name_and_signature(
                    data_type_name, function_signature
                )
                if not function:
                    continue
                icon_path = function.icon
                nice_name = function.nice_name
                sub_category_name = function.category or "General"
                palette_name = nice_name or function_signature

                # If search filter is set, skip if search filter does not match palette name or sub category name.
                filter_matched = bool(search_filter) and (
                    re.search(search_filter, palette_name, re.IGNORECASE) is not None
                    or re.search(
                        search_filter, sub_category_name, re.IGNORECASE is not None
                    )
                )
                if search_filter and not filter_matched:
                    continue

                self._add_node_item(
                    "tp.nodegraph.nodes.FunctionNode",
                    palette_name,
                    func_signature=function_signature,
                    category=f"Functions/{sub_category_name}",
                    icon_path=icon_path,
                    expanded=expanded,
                )

    def _add_node_item(
        self,
        node_id: str,
        label_text: str,
        func_signature: str = "",
        category: str = "",
        icon_path: str | None = None,
        expanded: bool = True,
    ) -> QTreeWidgetItem:
        """
        Internal function that adds a new node item to the tree.

        :param node_id: ID of the node to add.
        :param label_text: node item text.
        :param func_signature: optional function signature for the node item.
        :param category: optional node category.
        :param icon_path: optional node icon path.
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
        pixmap = QPixmap(icon_path) if icon_path else QPixmap()
        item = QTreeWidgetItem()
        parent_item.addChild(item)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
        item.setText(0, label_text)
        item.setIcon(0, QIcon(pixmap))
        item.setSizeHint(0, self._nodes_palette.icon_size)
        item.setData(0, NodesTreeWidget.PIXMAP_ROLE, pixmap)
        item.setData(0, NodesTreeWidget.NODE_ID_ROLE, node_id)
        json_data = {"title": item.text(0), "func_signature": func_signature}
        item.setData(0, NodesTreeWidget.JSON_DATA_ROLE, json_data)

        return item
