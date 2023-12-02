from __future__ import annotations

import os
import uuid
import json
import timeit
import typing
from typing import Iterator, Any

from tp.core import log
from tp.common.qt import api as qt
from tp.common.python import jsonio
from tp.common.nodegraph import registers
from tp.common.nodegraph.core import (
    utils, consts, errors, factory, history, clipboard, node, edge, vars, executor, serializer
)
from tp.common.nodegraph.models import graph as graph_model
from tp.common.nodegraph.graphics import scene, view
from tp.common.nodegraph.widgets import palette, graph as graph_widget

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import BaseNode
    from tp.common.nodegraph.nodes.node_getset import GetNode, SetNode


logger = log.rigLogger


class NodeGraph(qt.QObject):

    fileNameChanged = qt.Signal(str)
    modified = qt.Signal()
    itemSelected = qt.Signal()
    itemsDeselected = qt.Signal()
    itemDragEntered = qt.Signal(qt.QDragEnterEvent)
    itemDropped = qt.Signal(qt.QDropEvent)
    fileLoadFinished = qt.Signal()

    # Signal triggered when a node is created in the node graph.
    nodeCreated = qt.Signal(node.BaseNode)

    # Signal triggered when nodes haven been deleted from the node graph.
    nodesDeleted = qt.Signal(list)

    # Signal triggered when a node property has changed on a node.
    propertyChanged = qt.Signal(node.BaseNode, str, object)

    def __init__(
            self, model: graph_model.NodeGraphModel | None = None, viewer: view.GraphicsView | None = None,
            undo_stack: qt.QUndoStack | None = None, parent: qt.QObject | None = None):
        super().__init__(parent=parent)

        self.setObjectName('NodeGraph')

        self._model = model or graph_model.NodeGraphModel()

        self._uuid = str(uuid.uuid4())
        self._file_name: str = ''
        self._scene_width = self._scene_height = 64000
        self._has_been_modified = False
        self._items_are_being_deleted = False
        self._is_executing = False
        self._edges: list[edge.Edge] = []
        self._vars = vars.SceneVars(self)
        self._executor = executor.GraphExecutor(self)
        self._edge_type = edge.Edge.Type.BEZIER
        self._last_selected_items: list[qt.QGraphicsItem] = []

        self._graphics_scene = scene.GraphicsScene(self)
        self._graphics_scene.set_scene_size(self._scene_width, self._scene_height)
        self._viewer = viewer or view.GraphicsView(self._graphics_scene)
        self._widget: graph_widget.NodeGraphWidget | None = None

        self._history = history.SceneHistory(self)
        self._clipboard = clipboard.SceneClipboard(self)
        self._undo_stack = undo_stack or qt.QUndoStack(self)
        self._undo_view: qt.QUndoView | None = None

        self._setup_signals()

        self._update_title()

    def __repr__(self) -> str:
        return '<{}("root") object at {}>'.format(self.__class__.__name__, hex(id(self)))

    @classmethod
    def class_from_node_data(cls, node_data: dict) -> type:
        """
        Returns class based on node serialized data.

        :param dict node_data: node serialized data.
        :return: node class.
        :rtype: type
        """

        node_id = node_data.get('node_id')
        return registers.node_class_from_id(node_id) if node_id else node.Node

    @property
    def model(self) -> graph_model.NodeGraphModel:
        return self._model

    @property
    def graphics_scene(self) -> scene.GraphicsScene:
        return self._graphics_scene

    @property
    def history(self) -> history.SceneHistory:
        return self._history

    @property
    def undo_stack(self) -> qt.QUndoStack:
        """
        Getter method that returns the undo stack used in the node graph.

        :return: node graph undo stack.
        :rtype: qt.QUndoStack
        """

        return self._undo_stack

    @property
    def undo_view(self) -> qt.QUndoView:
        """
        Getter method that returns the node graph undo view widget.

        :return: undo graph view.
        :rtype: qt.QUndoView
        """

        if not self._undo_view:
            self._undo_view = qt.QUndoView(self._undo_stack)
            self._undo_view.setWindowTitle('Undo History')

        return self._undo_view

    @property
    def file_name(self) -> str:
        return self._file_name

    @file_name.setter
    def file_name(self, value: str):
        self._file_name = value
        self.fileNameChanged.emit(self._file_name)

    @property
    def file_base_name(self) -> str:
        name = self.file_base_name
        return name or 'Untitled'

    @property
    def user_friendly_title(self) -> str:
        file_name = self.file_base_name
        if self.has_been_modified:
            file_name += '*'

        return file_name

    @property
    def uuid(self) -> str:
        return self._uuid

    @uuid.setter
    def uuid(self, value: str):
        self._uuid = value

    @property
    def view(self) -> view.GraphicsView:
        return self._graphics_scene.views()[0]

    @property
    def vars(self) -> vars.SceneVars:
        return self._vars

    @property
    def executor(self) -> executor.GraphExecutor:
        return self._executor

    @property
    def file_base_name(self) -> str:
        return os.path.basename(self.file_name) if self.file_name else ''

    @property
    def has_been_modified(self) -> bool:
        return self._has_been_modified

    @has_been_modified.setter
    def has_been_modified(self, flag: bool):
        self._has_been_modified = flag
        self.modified.emit()

    @property
    def nodes(self) -> list[node.BaseNode]:
        return list(self.iterate_nodes())

    @property
    def edges(self) -> list[edge.Edge]:
        return self._edges

    @property
    def selected_items(self) -> list[qt.QGraphicsItem]:
        return self._graphics_scene.selectedItems()

    @property
    def selected_nodes(self) -> list[node.BaseNode]:
        return [found_node for found_node in self.nodes if found_node.view.isSelected()]

    @property
    def selected_edges(self) -> list[edge.Edge]:
        return [found_edge for found_edge in self._edges if found_edge.graphics_edge.isSelected()]

    @property
    def edge_type(self) -> edge.Edge.Type:
        return self._edge_type

    @edge_type.setter
    def edge_type(self, value: edge.Edge.Type):
        fallback_type = edge.Edge.Type.BEZIER
        if isinstance(value, int):
            try:
                value = list(edge.Edge.Type)[value]
            except IndexError:
                value = fallback_type
        elif isinstance(value, edge.Edge.Type):
            pass
        else:
            try:
                value = edge.Edge.Type[str(value)]
            except Exception:
                logger.error(f'Scene: Invalid edge type value: {value}')
                value = fallback_type
        if self._edge_type == value:
            return
        self._edge_type = value
        self.update_edge_types()

    @property
    def is_executing(self) -> bool:
        return self._is_executing

    @is_executing.setter
    def is_executing(self, flag: bool):
        self._is_executing = flag

    # @override
    # def contextMenuEvent(self, event: qt.QContextMenuEvent) -> None:
    #
    #     def _handle_node_context_menu():
    #         context_menu = NodeContextMenu(self)
    #         context_menu.exec_(self.mapToGlobal(event.pos()))
    #
    #     def _handle_edge_context_menu():
    #         pass
    #
    #     if self._viewer.is_view_dragging:
    #         event.ignore()
    #         return
    #
    #     try:
    #         item = self.item_at(event.pos())
    #         if not item:
    #             _handle_node_context_menu()
    #         if hasattr(item, 'node') or hasattr(item, 'socket') or not item:
    #             _handle_node_context_menu()
    #         elif hasattr(item, 'edge'):
    #             _handle_edge_context_menu()
    #         super().contextMenuEvent(event)
    #     except Exception:
    #         logger.exception('contextMenuEvent exception', exc_info=True)

    def node_by_name(self, name: str) -> BaseNode | None:
        """
        Returns the node from given name.

        :param str name: name of the node to get.
        :return: node instance with given name.
        :rtype: BaseNode or None
        """

        found_node: BaseNode | None = None
        for node in self._model.nodes.values():
            if node.name() == name:
                found_node = node
                break

        return found_node

    def add_node(self, node_to_add: BaseNode, pos: tuple[float, float] | None = None, emit_signal: bool = True):
        """
        Adds a node into graph.
        Handles the update of the graph model and ads node item into the scene view.

        :param BaseNode node_to_add: node we want to add into the graph.
        :param tuple[float, float] pos: optional position where node will be placed within viewer.
        :param bool emit_signal: whether to notify other graph listeners that a new node has been added.
        """

        self.model.nodes[node_to_add.uuid] = node_to_add
        self.view.add_node(node_to_add.view, pos)

        # node with and height is calculated when is added to the scene, so we have to update
        # the node model here
        node_to_add.model.width = node_to_add.view.width
        node_to_add.model.height = node_to_add.view.height

        if emit_signal:
            self.nodeCreated.emit(node_to_add)

    def remove_node(self, node_to_remove: BaseNode, emit_signal: bool = True):
        """
        Removes given node from graph.
        Handles the removal of the node from graph model and makes sure node view is removed from viewer.

        :param BaseNode node_to_remove: node we want to remove from graph.
        :param bool emit_signal: whether to notify other graph listeners that a new node has been removed.
        """

        node_id = node_to_remove.uuid
        self.model.nodes.pop(node_to_remove.uuid)
        node_to_remove.view.delete()
        if emit_signal:
            self.nodesDeleted.emit([node_id])

    def remove_nodes(self, nodes_to_remove: list[BaseNode], emit_signal: bool = True):
        """
        Removes given nodes from graph.
        Handles the removal of the node from graph model and makes sure node view is removed from viewer.

        :param BaseNode nodes_to_remove: nodes we want to remove from graph.
        :param bool emit_signal: whether to notify other graph listeners that a new nodes have been removed.
        """

        node_ids: list[str] = []
        for node_to_remove in nodes_to_remove:
            node_ids.append(node_to_remove.uuid)
            self.model.nodes.pop(node_to_remove.uuid)
            node_to_remove.view.delete()

        if emit_signal:
            self.nodesDeleted.emit(node_ids)

    def create_node(
            self, node_type: int | str, name: str | None = None, selected: bool = True,
            color: tuple[int, int, int] | str | None = None, text_color: tuple[int, int, int] | str | None = None,
            header_color: tuple[int, int, int] | str | None = None, pos: list[int, int] | None = None,
            push_undo: bool = True) -> BaseNode:
        """
        Creates a new node in the node graph.

        :param int or str node_type: node instance type.
        :param str name: name of the node.
        :param bool selected: whether created node should be set as selected.
        :param tuple[int, int, int] or str or None color: optional node color.
        :param tuple[int, int, int] or str or None text_color: optional node text color.
        :param tuple[int, int, int] or str or None header_color: optional node header color.
        :param list[int, int] pos: optional node position within scene.
        :param bool push_undo: whether command should be registered within undo stack.
        :return: newly created node instance.
        :rtype: BaseNode
        :raises errors.NodeCreationError: if was not possible to create new node because node with given type is not
            registered.
        """

        node = factory.create_node(node_type)
        if not node:
            raise errors.NodeCreationError(f'Cannot find node: {node_type}')

        widget_types = node.model.__dict__.pop('_temp_property_widget_types')
        property_attributes = node.model.__dict__.pop('_temp_property_attributes')

        if self.model.node_common_properties(node.type) is None:
            node_attributes = {node.type: {n: {'widget_type': wt} for n, wt in widget_types.items()}}
            for name, attrs in property_attributes.items():
                node_attributes[node.type][name].update(attrs)
            self.model.set_node_common_properties(node_attributes)

        node.NODE_NAME = self.unique_node_name(name or node.NODE_NAME)
        node.model.selected = selected
        if pos:
            node.model.pos = [float(pos[0]), float(pos[1])]
        node.model.layout_direction = self.layout_direction()

        node.update()

        self.history.store_history(f'Created Node {node.as_str(name_only=True)}')

        return node

    def spawn_node_from_data(self, node_id: int, json_data: dict, position: qt.QPointF) -> BaseNode | None:
        """
        Spawns a new node into scene based on given ID and serialized node data.

        :param int node_id: ID of the node to create.
        :param dict json_data: serialized node data.
        :param qt.QPointF position: position of the node within the scene.
        :return: newly created node.
        :rtype: node.BaseNode or None
        """

        try:
            node = registers.node_class_from_id(node_id)(self)
            if node_id == 100:      # function
                node.title = json_data.get('title')
                node.func_signature = json_data.get('func_signature', '')
            node.set_position(position.x(), position.y())
            self.history.store_history(f'Created Node {node.as_str(name_only=True)}')
            return node
        except Exception:
            logger.exception('Failed to instance node', exc_info=True)

    def spawn_getset(self, var_name: str, position: qt.QPointF, setter: bool = False) -> GetNode | SetNode | None:
        """
        Spawns a new getter/setter into scene based on given ID and serialized node data.

        :param str var_name: name of the variable to create getter/setter node for.
        :param qt.QPointF position: position of the node within the scene.
        :param bool setter: whether to create a setter or getter node.
        :return: newly created getter/setter node.
        :rtype: GetNode or SetNode or None
        """

        node_id = 104 if setter else 103
        try:
            node: GetNode | SetNode = registers.node_class_from_id(node_id)(self)
            node.set_var_name(var_name, init_sockets=True)
            node.set_position(position.x(), position.y())
            self.history.store_history(f'Created Node {node.as_str(name_only=True)}')
            return node
        except Exception:
            logger.exception('Failed to instance node', exc_info=True)

    def layout_direction(self) -> int:
        """
        Returns the current node graph layout direction.

        :return: layout direction.
        :rtype: int
        """

        return self.model.layout_direction

    def set_layout_direction(self, direction: int):
        """
        Sets the node graph layout direction to be horizontal or vertical.

        :param int direction: layout direction.
        """

        direction_types = [e.value for e in consts.LayoutDirection]
        if direction not in direction_types:
            direction = consts.LayoutDirection.Horizontal.value
        self.model.layout_direction = direction
        for node in self.nodes:
            node.set_layout_direction(direction)
        self._viewer.set_layout_direction(direction)

    def item_at(self, position: qt.QPoint) -> qt.QGraphicsItem | None:
        """
        Returns item at given position.

        :param qt.QPoint position: position to get item at.
        :return: found position item at given position.
        :rtype: qt.QGraphicsItem or None
        """

        return self.view.itemAt(position)

    def set_history_init_point(self):
        """
        Sets history initial point.
        """

        logger.debug(f'Store initial scene history (Size: {self.history.size})')
        self._history.store_history(self._history.SCENE_INIT_DESCRIPTION)

    def unique_node_name(self, name: str) -> str:
        """
        Returns a unique node name to avoid having nodes with the same name.

        :param str name: name of the node.
        :return: unique node name.
        :rtype: str
        """

        node_names = [n.name() for n in self.nodes]
        return utils.unique_node_name(name, node_names)

    def node_by_id(self, node_id: str | None) -> node.BaseNode | None:
        """
        Returns the node from given node ID string.

        :param str node_id: ID of the node to retrieve.
        :return: node instance with given ID.
        :rtype: node.BaseNode or None
        """

        return self._model.nodes.get(node_id)

    def iterate_nodes(self) -> Iterator[node.BaseNode]:
        """
        Generator function that yields all nodes within graph.

        :return: iterated graph scene nodes.
        :rtype: Iterator[node.BaseNode]
        """
        for found_node in self.model.nodes.values():
            yield found_node

    def list_node_ids(self) -> list[str]:
        """
        Returns list of node IDs within the scene.

        :return: scene node IDs.
        """

        return [scene_node.uuid for scene_node in self.nodes]

    def remove_node(self, node_to_remove: node.BaseNode):
        """
        Removes given node from list of scene nodes.

        :param node.BaseNode node_to_remove: node instance to remove from scene.
        ..note:: this function does not remove node view from the graphics view
        """

        self.model.nodes.pop(node_to_remove.uuid)

    def add_edge(self, edge_to_add: edge.Edge):
        """
        Adds given edge to the list of scene edges.

        :param edge.Edge edge_to_add: node instance to add to the scene.
        ..note:: this function does not add edge view into the graphics view
        """

        self._edges.append(edge_to_add)

    def list_edge_ids(self) -> list[str]:
        """
        Returns list of edge IDs within the scene.

        :return: scene edge IDs.
        """

        return [scene_edge.uuid for scene_edge in self.edges]

    def remove_edge(self, edge_to_remove: edge.Edge):
        """
        Removes given edge from list of scene edges.

        :param edge.Edge edge_to_remove: node instance to remove from scene.
        ..note:: this function does not remove edge view from the graphics view
        """

        self._edges.remove(edge_to_remove)

    def update_edge_types(self):
        """
        Updates all scene edge style based on current scene edge style.
        """

        for scene_edge in self.edges:
            scene_edge.update_edge_graphics_type()

    def rename_selected_node(self):
        """
        Rename selected node.
        """

        selection = self.selected_nodes
        if not selection:
            logger.warning('Select a node to rename.')
            return

        selection[-1].edit_title()

    def copy_selected(self):
        """
        Copies selected nodes into clipboard.
        """

        if not self.selected_nodes:
            logger.warning('No nodes selected to copy')
            return

        try:
            data = self._clipboard.serialize_selected(delete=False)
            str_data = json.dumps(data, indent=4)
            qt.QApplication.clipboard().setText(str_data)
        except Exception:
            logger.exception('Copy exception', exc_info=True)

    def cut_selected(self):
        """
        Cuts selected nodes into clipboard.
        """

        if not self.selected_nodes:
            logger.warning('No nodes selected to cut')
            return

        try:
            data = self._clipboard.serialize_selected(delete=True)
            str_data = json.dumps(data, indent=4)
            qt.QApplication.clipboard().setText(str_data)
            self._last_selected_items.clear()
        except Exception:
            logger.exception('Cut exception', exc_info=True)

    def paste_from_clipboard(self):
        """
        Paste nodes from clipboard
        """

        raw_data = qt.QApplication.clipboard().text()
        try:
            data = json.loads(raw_data)
        except ValueError:
            logger.error('Invalid JSON paste data')
            return

        if 'nodes' not in data.keys():
            logger.warning('Clipboard JSON does not contains any nodes')
            return

        self._clipboard.deserialize_data(data)

    def delete_selected(self, store_history: bool = True):
        """
        Deletes selected nodes from scene.

        :param bool store_history: whether to store operation within scene history stack.
        """

        self._items_are_being_deleted = True
        try:
            for node in self.selected_nodes:
                node.remove()
            for edge in self.selected_edges:
                edge.remove()
        except Exception:
            logger.exception('Failed to delete selected items')
        self._items_are_being_deleted = False

        if store_history:
            self.history.store_history('Item deleted', set_modified=True)

        self.itemsDeselected.emit()

    def save_to_file(self, file_path: str):
        """
        Saves current scene into a file in disk.

        :param str file_path: path where scene should be stored.
        """

        try:
            data = serializer.serialize_graph(self)
            if not jsonio.validate_json(data):
                logger.error('Scene data is not valid')
                logger.info(data)
                return
            result = jsonio.write_to_file(data, file_path, sort_keys=False)
            if not result:
                logger.error('Was not possible to save build')
                return
            logger.info(f'Saved build {file_path}')
            self.file_name = file_path
            self.has_been_modified = False
            self.modified.emit()
        except Exception:
            logger.exception('Failed to save build', exc_info=True)

    def load_from_file(self, file_path: str):
        """
        Loads scene contents from file in disk.

        :param str file_path: absolute file path pointing to valid scene contents file.
        """

        try:
            self.clear()
            start_time = timeit.default_timer()
            data = jsonio.read_file(file_path)
            serializer.deserialize_graph(self, data)
            logger.info("Rig build loaded in {0:.2f}s".format(timeit.default_timer() - start_time))
            self.history.clear()
            self.executor.reset_stepped_execution()
            self.file_name = file_path
            self.has_been_modified = False
            self.set_history_init_point()
            self.fileLoadFinished.emit()
        except Exception:
            logger.exception('Failed to load scene build file', exc_info=True)

    def regenerate_uuids(self):
        """
        Regenerate UUIDs for all nodes within scene.
        """

        obj_count = 1
        self.uuid = str(uuid.uuid4())
        for scene_node in self.nodes:
            scene_node.uuid = str(uuid.uuid4())
            obj_count += 1
            for socket in scene_node.inputs + scene_node.outputs:
                socket.uuid = str(uuid.uuid4())
                obj_count += 1
        for scene_edge in self.edges:
            scene_edge.uuid = str(uuid.uuid4())
            obj_count += 1
        logger.info(f'Generated new UUIDs for {obj_count} objects')

    def clear(self):
        """
        Removes all nodes from scene.
        """

        for node_to_remove in self.model.nodes.values():
            node_to_remove.remove(silent=True)
        self.model.nodes.clear()
        self.has_been_modified = False

    def widget(self) -> graph_widget.NodeGraphWidget:
        """
        Returns graph widget for adding graph into a layout.

        :return: node graph widget.
        :rtype: graph_widget.NodeGraphWidget
        """

        if self._widget is not None:
            return self._widget

        self._widget = graph_widget.NodeGraphWidget()
        self._widget.addTab(self._viewer, 'Node Graph')
        tab_bar = self._widget.tabBar()
        for btn_flag in [tab_bar.RightSide, tab_bar.LeftSide]:
            tab_btn = tab_bar.tabButton(0, btn_flag)
            if not tab_btn:
                continue
            tab_btn.deleteLater()
            tab_bar.setTabButton(0, btn_flag, None)
        self._widget.tabCloseRequested.connect(self._on_close_sub_graph_tab)

        self._setup_actions(self._widget)

        return self._widget

    def is_modified(self) -> bool:
        """
        Returns whether editor scene has been modified by user.

        :return: True if scene has been modified; False otherwise.
        :rtype: bool
        """

        return self.has_been_modified

    def maybe_save(self) -> bool:
        """
        Shows a warning message if save is modified and not saved.

        :return: True is scene was saved or has  not been modified; False otherwise.
        :rtype: bool
        """

        if not self.is_modified():
            return True

        res = qt.QMessageBox.warning(
            self.widget(), 'Build not saved', 'Save Changes to current build?',
            qt.QMessageBox.Save | qt.QMessageBox.No | qt.QMessageBox.Cancel)
        if res == qt.QMessageBox.Save:
            return self.save_build()
        elif res == qt.QMessageBox.No:
            return True
        elif res == qt.QMessageBox.Cancel:
            return False

        return True

    def save_build_as(self) -> bool:
        """
        Saves current graph into disk in a new file.

        :return: True if save operation was successful; False otherwise.
        :rtype: bool
        """

        graph_filter = 'Graph (*.graph)'
        file_path = qt.QFileDialog.getSaveFileName(self.widget(), 'Save graph to file', '', graph_filter)[0]
        if not file_path:
            return False

        self.save_to_file(file_path)

        return True

    def open_build(self) -> bool:
        """
        Opens a graph.

        :return: True if build was opened successfully; False otherwise.
        :rtype: bool
        """

        if not self.maybe_save():
            return False

        graph_filter = 'Graph (*.graph)'
        file_path = qt.QFileDialog.getOpenFileName(self.widget(), 'Open graph', '', graph_filter)[0]
        if not file_path:
            return False

        self.load_from_file(file_path)

        return True

    def new_build(self):
        """
        Clears current scene and shows a warning message if current build has not been modified.
        """

        if not self.maybe_save():
            return

        self.clear()
        self.file_name = None

    def save_build(self):
        """
        Saves current build graph into disk.

        :return: True if save operation was successful; False otherwise.
        :rtype: bool
        """

        res = True
        if self.file_name:
            self.save_to_file(self.file_name)
        else:
            res = self.save_build_as()

        return res

    def _setup_actions(self, widget: graph_widget.NodeGraphWidget):
        """
        Internal function that setup all actions.
        """

        widget.addAction(palette.PopupNodesPalette.show_action(self, self._viewer))

    def _setup_signals(self):
        """
        Internal function that creates all signal connections.
        """

        self.itemDragEntered.connect(self._on_item_drag_enter)
        self.itemDropped.connect(self._on_item_dropped)
        self.fileNameChanged.connect(self._update_title)
        self.modified.connect(self._update_title)

        self._graphics_scene.selectionChanged.connect(self._on_selection_changed)
        self._viewer.nodeBackdropUpdated.connect(self._on_node_backdrop_updated)

    def _update_title(self):
        """
        Internal function that updates editor title.
        """

        pass

        # self.setWindowTitle(self.user_friendly_title)

    def _on_selection_changed(self):
        """
        Internal callback function that is called each time scene selection changes.
        """

        # Ignore selection update if rubberband dragging, item deletion is in progress
        if any([self.view.rubberband_dragging_rect, self._items_are_being_deleted]):
            return

        current_selection = self.graphics_scene.selectedItems()
        if current_selection == self._last_selected_items:
            return

        # No current selection and existing previous selection (To avoid resetting selection after cut operation)
        if not current_selection:
            self.history.store_history('Deselected everything', set_modified=False)
            self.itemsDeselected.emit()
        else:
            self.history.store_history('Selection changed', set_modified=False)
            self.itemSelected.emit()

        self._last_selected_items = current_selection

    def _on_item_drag_enter(self, event: qt.QDragEnterEvent):
        """
        Internal callback function that is called each time an item is dragged within editor scene view.

        :param qt.QDragEnterEvent event: Qt drag enter event.
        """

        logger.debug('On item drag enter')
        if event.mimeData().hasFormat('noddle/x-node-palette_item') or event.mimeData().hasFormat('noddle/x-vars_item'):
            event.acceptProposedAction()
        else:
            logger.warning(f'Unsupported item: {event.mimeData().formats()}')
            event.setAccepted(False)

    def _on_item_dropped(self, event: qt.QDropEvent):
        """
        Internal callback function that is called each time an item is dropped within editor scene view.

        :param qt.QDropEvent event: Qt drop event.
        """

        def _handle_nodes_palette_drop():
            event_data = event.mimeData().data('noddle/x-node-palette_item')
            data_stream = qt.QDataStream(event_data, qt.QIODevice.ReadOnly)
            pixmap = qt.QPixmap()
            data_stream >> pixmap
            node_id = data_stream.readInt32()
            json_data = json.loads(data_stream.readQString())
            mouse_pos = event.pos()
            scene_pos = self.view.mapToScene(mouse_pos)
            logger.debug(f'''Dropped Item:
                            > NODE_ID: {node_id}
                            > DATA: {json_data}
                            > MOUSE POS: {mouse_pos}
                            > SCENE POS {scene_pos}''')
            self.spawn_node_from_data(node_id, json_data, scene_pos)
            event.setDropAction(qt.Qt.MoveAction)
            event.accept()

        def _handle_variable_drop():
            event_data = event.mimeData().data('noddle/x-vars_item')
            data_stream = qt.QDataStream(event_data, qt.QIODevice.ReadOnly)
            json_data = json.loads(data_stream.readQString())
            mouse_pos = event.pos()
            scene_pos = self.view.mapToScene(mouse_pos)
            logger.debug('''Dropped Variable:
                            > DATA: {data}
                            > SCENE POS {scene_pos}'''.format(data=json_data, scene_pos=scene_pos))
            var_name = json_data['var_name']
            get_set_menu = qt.QMenu(self.widget())
            getter_action = qt.QAction('Get', get_set_menu)
            setter_action = qt.QAction('Set', get_set_menu)
            get_set_menu.addAction(getter_action)
            get_set_menu.addAction(setter_action)
            result_action = get_set_menu.exec_(self.widget().mapToGlobal(event.pos()))
            if result_action is None:
                return
            self.spawn_getset(var_name, scene_pos, setter=result_action == setter_action)
            event.setDropAction(qt.Qt.MoveAction)
            event.accept()

        logger.debug('On item drop')
        if event.mimeData().hasFormat('noddle/x-node-palette_item'):
            _handle_nodes_palette_drop()
        elif event.mimeData().hasFormat('noddle/x-vars_item'):
            _handle_variable_drop()
        else:
            logger.warning('Unsupported item format: {0}'.format(event.mimeData()))
            event.ignore()
            return

    def _on_node_backdrop_updated(self, node_id: str, update_property: str, value: Any):
        """
        Internal callback function that is called each time a backdrop node is updated.

        :param str node_id: backdrop node ID.
        :param str update_property: updated property.
        :param Any value: updated property value.
        """

        backdrop_node = self.node_by_id(node_id)
        # if backdrop_node and isinstance(backdrop_node, node_backdrop.BackdropNode):
        #     backdrop_node.update_property(update_property, value)

    def _on_close_sub_graph_tab(self, index: int):
        """
        Internal callback function that is called each time the close button is clicked on expanded sub graph tab.

        :param int index: tab index.
        """

        pass


class NodeContextMenu(qt.QMenu):
    def __init__(self, graph: NodeGraph):
        super().__init__('Node')

        self._graph = graph

        self._setup_actions()
        self._populate()
        self._setup_signals()

    def _setup_actions(self):
        """
        Internal function that setup menu actions.
        """

        self._copy_action = qt.QAction('&Copy', self)
        self._cut_action = qt.QAction('&Cut', self)
        self._paste_action = qt.QAction('&Paste', self)
        self._delete_action = qt.QAction('&Delete', self)

    def _populate(self):
        """
        Internal function that populates menu.
        """

        self.addAction(self._copy_action)
        self.addAction(self._cut_action)
        self.addAction(self._paste_action)
        self.addSeparator()
        self.addAction(self._delete_action)

    def _setup_signals(self):
        """
        Internal function that setup menu connections.
        """

        self._copy_action.triggered.connect(self._on_copy_action_triggered)
        self._cut_action.triggered.connect(self._on_cut_action_triggered)
        self._paste_action.triggered.connect(self._on_paste_action_triggered)
        self._delete_action.triggered.connect(self._on_delete_action_triggered)

    def _on_copy_action_triggered(self):
        """
        Internal callback funtion that is called each time Copy action is triggered by the user.
        """

        if not self._graph:
            return

        self._graph.copy_selected()

    def _on_cut_action_triggered(self):
        """
        Internal callback funtion that is called each time Cut action is triggered by the user.
        """

        if not self._graph:
            return

        self._graph.cut_selected()

    def _on_paste_action_triggered(self):
        """
        Internal callback funtion that is called each time Paste action is triggered by the user.
        """

        if not self._graph:
            return

        self._graph.paste_from_clipboard()

    def _on_delete_action_triggered(self):
        """
        Internal callback funtion that is called each time Delete action is triggered by the user.
        """

        if not self._graph:
            return

        self._graph.delete_selected()
