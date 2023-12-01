from __future__ import annotations

import re
import json
import typing
from typing import Union
from functools import partial

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.common.nodegraph import registers
from tp.common.nodegraph.core import edge

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.graph import NodeGraph
    from tp.common.nodegraph.graphics.view import GraphicsView

logger = log.rigLogger


class NodesPalette(qt.QWidget):
    def __init__(
            self, icon_size: int = 32, data_type_filter: dict | None = None,
            functions_first: bool = False, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._icon_size = qt.QSize(icon_size, icon_size)
        self._data_filter_type = data_type_filter
        self._functions_first = functions_first

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

        self.setMinimumWidth(190)

        self.update_nodes_tree()

    @property
    def data_type_filter(self) -> dict:
        return self._data_filter_type

    @property
    def icon_size(self) -> qt.QSize:
        return self._icon_size

    @property
    def functions_first(self) -> bool:
        return self._functions_first

    @functions_first.setter
    def functions_first(self, flag: bool):
        self._functions_first = flag
        self.update_nodes_tree()

    @property
    def nodes_tree(self) -> NodesTreeWidget:
        return self._nodes_tree

    def update_nodes_tree(self):
        """
        Populates nodes tree.
        """

        self._nodes_tree.populate()

    def _setup_widgets(self):
        """
        Internal function that creates all UI widgets.
        """

        self._search_line = qt.SearchLineEdit(parent=self)
        self._search_line.setPlaceholderText('Search')
        self._nodes_tree = NodesTreeWidget(self)

    def _setup_layouts(self):
        """
        Internal function that creates all UI layouts and add all widgets to them.
        """

        self._main_layout = qt.vertical_layout(margins=(0, 0, 0, 0))
        self.setLayout(self._main_layout)

        self._main_layout.addWidget(self._search_line)
        self._main_layout.addWidget(self._nodes_tree)

    def _setup_signals(self):
        """
        Internal function that creates all signal connections.
        """

        self._search_line.textChanged.connect(partial(self._nodes_tree.populate))


class NodesTreeWidget(qt.QTreeWidget):

    PIXMAP_ROLE = qt.Qt.UserRole
    NODE_ID_ROLE = qt.Qt.UserRole + 1
    JSON_DATA_ROLE = qt.Qt.UserRole + 2

    def __init__(self, nodes_palette: NodesPalette, parent: qt.QWidget | None = None):
        super().__init__(parent or nodes_palette)

        self._nodes_palette = nodes_palette

        self.setIconSize(self._nodes_palette.icon_size)
        self.setSelectionMode(qt.QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setColumnCount(1)
        self.setHeaderHidden(True)

    def startDrag(self, supportedActions: Union[qt.Qt.DropActions, qt.Qt.DropAction]) -> None:
        try:
            item = self.currentItem()
            node_id = int(item.data(0, NodesTreeWidget.NODE_ID_ROLE))
            pixmap = qt.QPixmap(item.data(0, NodesTreeWidget.PIXMAP_ROLE))
            json_data = item.data(0, NodesTreeWidget.JSON_DATA_ROLE)
            item_data = qt.QByteArray()
            data_stream = qt.QDataStream(item_data, qt.QIODevice.WriteOnly)
            data_stream << pixmap
            data_stream.writeInt32(node_id)
            data_stream.writeQString(json.dumps(json_data))
            mime_data = qt.QMimeData()
            mime_data.setData('noddle/x-node-palette_item', item_data)
            drag = qt.QDrag(self)
            drag.setMimeData(mime_data)
            drag.setHotSpot(qt.QPoint(int(pixmap.width() / 2), int(pixmap.height() / 2)))
            drag.setPixmap(pixmap)
            drag.exec_(qt.Qt.MoveAction)
        except Exception:
            logger.exception('Palette drag exception', exc_info=True)

    def add_category(
            self, name: str, expanded: bool = True, parent: qt.QTreeWidgetItem | None = None) -> qt.QTreeWidgetItem:
        parent = parent or self
        category_item = qt.QTreeWidgetItem(parent)
        category_item.setFlags(qt.Qt.ItemIsEnabled)
        category_item.setText(0, name)
        category_item.setExpanded(expanded)

        return category_item

    def category(
            self, name: str, expanded: bool = True, parent: qt.QTreeWidgetItem | None = None) -> qt.QTreeWidgetItem:
        found_items = self.findItems(name, qt.Qt.MatchExactly | qt.Qt.MatchRecursive, 0)
        if parent is not self:
            found_items = [item for item in found_items if item.parent() is parent]
        item = found_items[0] if found_items else self.add_category(name, expanded=expanded, parent=parent)
        return item

    def populate(self, search_filter: str = ''):
        """
        Populates tree widget contents based on search filter.

        :param str search_filter: search filter to apply.
        """

        self.clear()

        if self._nodes_palette.functions_first:
            self._add_registered_functions(search_filter=search_filter)
            self._add_registered_nodes(search_filter=search_filter)
        else:
            self._add_registered_nodes(search_filter=search_filter)
            self._add_registered_functions(search_filter=search_filter)

    def _add_registered_nodes(self, search_filter: str = ''):
        keys = list(registers.NODES_REGISTER.keys())
        keys.sort()
        for node_id in keys:
            node_class = registers.NODES_REGISTER[node_id]
            if node_class.CATEGORY == 'INTERNAL':
                continue
            palette_label = node_class.PALETTE_LABEL if hasattr(
                node_class, 'PALETTE_LABEL') else node_class.DEFAULT_TITLE
            filter_matched = bool(search_filter) and (
                    re.search(search_filter, palette_label, re.IGNORECASE) is not None or
                    re.search(search_filter, node_class.CATEGORY, re.IGNORECASE) is not None)
            if search_filter and not filter_matched:
                continue
            self._add_node_item(node_id, palette_label, category=node_class.CATEGORY, icon_name=node_class.ICON)

    def _add_registered_functions(self, search_filter: str = ''):
        keys = list(registers.FUNCTIONS_REGISTER.keys())
        keys.sort()
        for data_type_name in keys:
            if data_type_name != 'UNBOUND' and self._nodes_palette.data_type_filter:
                if not issubclass(
                        self._nodes_palette.data_type_filter.get('class'),
                        registers.DataType.type_from_name(data_type_name).get('class')):
                    continue
            func_map = registers.FUNCTIONS_REGISTER[data_type_name]
            func_signatures_list = func_map.keys()
            func_signatures_list = list(func_signatures_list) if not isinstance(
                func_signatures_list, list) else func_signatures_list
            for func_sign in func_signatures_list:
                expanded = self._nodes_palette.functions_first or bool(search_filter)
                func_dict = func_map[func_sign]
                icon_name = func_dict['icon']
                nice_name = func_dict.get('nice_name')
                sub_category_name = func_dict.get('category', 'General')
                palette_name = nice_name if nice_name else func_sign
                filter_matched = bool(search_filter) and (
                        re.search(search_filter, palette_name, re.IGNORECASE) is not None or
                        re.search(search_filter, sub_category_name, re.IGNORECASE is not None))
                if search_filter and not filter_matched:
                    continue

                self._add_node_item(
                    100, palette_name, func_signature=func_sign, category=F'Functions/{sub_category_name}',
                    icon_name=icon_name, expanded=expanded)
                    
    def _add_node_item(
            self, node_id: int, label_text: str, func_signature: str = '', category: str = 'Undefined',
            icon_name: str | None = None, expanded: bool = True) -> qt.QTreeWidgetItem:
        """
        Internal function that adds a new tree item into the nodes palette tree widget.

        :param int node_id:
        :param str label_text:
        :param str func_signature:
        :param str category:
        :param str icon_name:
        :param bool expanded:
        :return: newly added tree widget item.
        :rtype: qt.QTreeWidgetItem
        """

        icon_name = icon_name or 'tpdcc'
        icon = resources.icon(icon_name)
        icon = icon if not icon.isNull() else resources.icon('tpdcc')
        pixmap = icon.pixmap(icon.availableSizes()[-1]) if icon.availableSizes() else qt.QPixmap()

        category_path = category.split('/')
        parent_item = self
        for category_name in category_path:
            parent_item = self.category(category_name, parent=parent_item, expanded=expanded)

        item = qt.QTreeWidgetItem()
        parent_item.addChild(item)
        item.setFlags(qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable | qt.Qt.ItemIsDragEnabled)
        item.setText(0, label_text)
        item.setIcon(0, icon)
        item.setSizeHint(0, self._nodes_palette.icon_size)
        item.setData(0, NodesTreeWidget.PIXMAP_ROLE, pixmap)
        item.setData(0, NodesTreeWidget.NODE_ID_ROLE, int(node_id))
        json_data = {
            'title': item.text(0),
            'func_signature': func_signature
        }
        item.setData(0, NodesTreeWidget.JSON_DATA_ROLE, json_data)

        return item


class PopupNodesPalette(qt.QDialog):

    @classmethod
    def show_action(
            cls, node_editor: NodeEditor, graphics_view: GraphicsView,
            shortcut: qt.QKeySequence = qt.QKeySequence(qt.Qt.Key_Tab)) -> qt.QAction:

        action = qt.QAction(node_editor)
        action.setShortcut(shortcut)
        action.triggered.connect(lambda: cls.create(graphics_view))

        return action

    @classmethod
    def create(cls, graphics_view: GraphicsView):
        popup_dialog = cls(graphics_view)
        popup_dialog.move(qt.QCursor.pos())
        popup_dialog.exec_()

    def __init__(self, view: GraphicsView, parent: qt.QWidget | None = None):
        super().__init__(parent=parent or view)

        self._view = view
        self._graph: NodeGraph = self._view.graphics_scene.graph
        self._nodes_palette: NodesPalette | None = None

        self.setWindowFlags(qt.Qt.FramelessWindowHint | qt.Qt.Dialog)

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    @override
    def eventFilter(self, arg__1: qt.QObject, arg__2: qt.QEvent) -> bool:
        if arg__2.type() == qt.QEvent.KeyPress and arg__2.matches(qt.QKeySequence.InsertParagraphSeparator):
            item = self._nodes_palette.nodes_tree.currentItem()
            if item:
                self._spawn_clicked_node(item)
                return True

        return False

    def is_dragging_from_output(self) -> bool:
        """
        Returns whether popup was shown while a drag operation from output socket was being executed.

        :return: True if drag from output socket operation was being executed; False otherwise.
        :rtype :bool
        """

        return bool(self._view.dragging.drag_edge and self._view.dragging.drag_edge.start_socket)

    def is_dragging_from_input(self) -> bool:
        """
        Returns whether popup was shown while a drag operation from input socket was being executed.

        :return: True if drag from input socket operation was being executed; False otherwise.
        :rtype :bool
        """

        return bool(self._view.dragging.drag_edge and self._view.dragging.drag_edge.end_socket)

    def _setup_widgets(self):
        """
        Internal function that creates all UI widgets.
        """

        data_type_filter = self._view.dragging.source_socket_datatype()
        self._nodes_palette = NodesPalette(icon_size=16, data_type_filter=data_type_filter, functions_first=True)
        self._nodes_palette.nodes_tree.setDragEnabled(False)
        self._nodes_palette.nodes_tree.installEventFilter(self)

    def _setup_layouts(self):
        """
        Internal function that creates all UI layouts and add all widgets to them.
        """

        self._main_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(self._main_layout)

        self._main_layout.addWidget(self._nodes_palette)

    def _setup_signals(self):
        """
        Internal function that creates all signal connections.
        """

        self._nodes_palette.nodes_tree.itemClicked.connect(self._on_nodes_palette_tree_item_clicked)

    def _spawn_clicked_node(self, item: qt.QTreeWidgetItem):
        """
        Internal function that spawns node based on selected nodes tree widget item.

        :param qt.QTreeWidgetItem item: tree widget item.
        """

        if not item.flags() & qt.Qt.ItemIsSelectable:
            return

        node_id = item.data(0, NodesTreeWidget.NODE_ID_ROLE)
        json_data = item.data(0, NodesTreeWidget.JSON_DATA_ROLE)
        new_node = self._graph.spawn_node_from_data(node_id, json_data, self._view.last_scene_mouse_pos)
        if not new_node:
            logger.warning('Was not possible to create node!')
            self.close()
            return

        # Connect dragging edge
        # Output -> Input
        if self.is_dragging_from_output():
            start_socket = self._view.dragging.drag_edge.start_socket
            start_node = self._view.dragging.drag_edge.start_socket.node
            socket_to_connect = new_node.find_first_input_with_label(start_socket.label)
            if not socket_to_connect:
                socket_to_connect = new_node.find_first_input_of_datatype(start_socket.data_type)
            if start_node._exec_out_socket and not start_node._exec_out_socket.has_edge() and new_node._exec_in_socket:
                edge.Edge(self._graph, start_socket=start_node._exec_out_socket, end_socket=new_node._exec_in_socket)
            self._view.dragging.end_edge_drag(socket_to_connect)
        # Input -> Output
        elif self.is_dragging_from_input():
            end_socket = self._view.dragging.drag_edge.end_socket
            end_node = self._view.dragging.drag_edge.end_socket.node
            socket_to_connect = new_node.find_first_output_with_label(end_socket.label)
            if not socket_to_connect:
                socket_to_connect = new_node.find_first_output_of_datatype(end_socket.data_type)
            if end_node._exec_in_socket and not end_node._exec_in_socket.has_edge() and new_node._exec_out_socket:
                edge.Edge(self._graph, start_socket=new_node._exec_out_socket, end_socket=end_node._exec_in_socket)
            self._view.dragging.end_edge_drag(socket_to_connect)
        self.close()

    def _on_nodes_palette_tree_item_clicked(self, item: qt.QTreeWidgetItem):
        """
        Internal callback function that is called each time an item within nodes tree widget is clicked by the user.

        :param qt.QTreeWidgetItem item: clicked tree widget item.
        """

        self._spawn_clicked_node(item)
