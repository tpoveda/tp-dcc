from __future__ import annotations

import json
import typing

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.libs.rig.noddle.core import asset
from tp.tools.rig.noddle.builder.graph.core import scene
from tp.tools.rig.noddle.builder.graph.graphics import view
from tp.tools.rig.noddle.builder.graph.widgets import palette

logger = log.rigLogger

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.controller import NoddleController


class NodeEditor(qt.QWidget):

    aboutToClose = qt.Signal(qt.QWidget, qt.QCloseEvent)

    def __init__(self, controller: NoddleController, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._controller = controller

        self._setup_ui()
        self.scene.set_history_init_point()

    @property
    def controller(self) -> NoddleController:
        return self._controller

    @property
    def scene(self) -> scene.Scene:
        return self._scene

    @property
    def file_name(self) -> str:
        return self.scene.file_name

    @property
    def file_base_name(self) -> str:
        name = self.scene.file_base_name
        return name or 'Untitled'

    @property
    def user_friendly_title(self) -> str:
        file_name = self.file_base_name
        if self.scene.has_been_modified:
            file_name += '*'

        return file_name

    @override
    def closeEvent(self, event: qt.QCloseEvent) -> None:
        self.aboutToClose.emit(self, event)

    @override
    def contextMenuEvent(self, event: qt.QContextMenuEvent) -> None:

        def _handle_node_context_menu():
            context_menu = NodeContextMenu(self)
            context_menu.exec_(self.mapToGlobal(event.pos()))

        def _handle_edge_context_menu():
            pass

        if self._view.is_view_dragging:
            event.ignore()
            return

        try:
            item = self.scene.item_at(event.pos())
            if not item:
                _handle_node_context_menu()
            if hasattr(item, 'node') or hasattr(item, 'socket') or not item:
                _handle_node_context_menu()
            elif hasattr(item, 'edge'):
                _handle_edge_context_menu()
            super().contextMenuEvent(event)
        except Exception:
            logger.exception('contextMenuEvent exception', exc_info=True)

    def is_modified(self) -> bool:
        """
        Returns whether editor scene has been modified by user.

        :return: True if scene has been modified; False otherwise.
        :rtype: bool
        """

        return self.scene.has_been_modified

    def maybe_save(self) -> bool:
        """
        Shows a warning message if save is modified and not saved.

        :return: True is scene was saved or has  not been modified; False otherwise.
        :rtype: bool
        """

        if not self.is_modified():
            return True

        res = qt.QMessageBox.warning(
            self, 'Build not saved', 'Save Changes to current build?',
            qt.QMessageBox.Save | qt.QMessageBox.No | qt.QMessageBox.Cancel)
        if res == qt.QMessageBox.Save:
            return self.save_build()
        elif res == qt.QMessageBox.No:
            return True
        elif res == qt.QMessageBox.Cancel:
            return False

        return True

    def new_build(self):
        """
        Clears current scene and shows a warning message if current build has not been modified.
        """

        if not self.maybe_save():
            return

        self.scene.clear()
        self.scene.file_name = None

    def save_build(self):
        """
        Saves current build graph into disk.

        :return: True if save operation was successful; False otherwise.
        :rtype: bool
        """

        if not asset.Asset.get():
            logger.warning('Asset is not set')
            return False

        res = True
        if self.scene.file_name:
            self.scene.save_to_file(self.scene.file_name)
        else:
            res = self.save_build_as()

        return res

    def save_build_as(self) -> bool:
        """
        Saves current build graph into disk in a new file.

        :return: True if save operation was successful; False otherwise.
        :rtype: bool
        """

        if not asset.Asset.get():
            logger.warning('Asset is not set')
            return False

        rig_filter = 'Rig Build (*.rig)'
        file_path = qt.QFileDialog.getSaveFileName(
            self, 'Save build graph to file', asset.Asset.get().new_build_path, rig_filter)[0]
        if not file_path:
            return False
        self.scene.save_to_file(file_path)
        return True

    def open_build(self) -> bool:
        """
        Opens a build for the active asset.

        :return: True if build was opened successfully; False otherwise.
        :rtype: bool
        """

        if not asset.Asset.get():
            logger.warning('Asset is not set!')
            return False
        if not self.maybe_save():
            return False

        rig_filter = 'Rig Build (*.rig)'
        file_path = qt.QFileDialog.getOpenFileName(self, 'Open rig build scene', asset.Asset.get().build, rig_filter)[0]
        if not file_path:
            return False

        self.scene.load_from_file(file_path)

        return True

    def _setup_ui(self):
        """
        Internal function that setups node editor widgets.
        """

        self.setAttribute(qt.Qt.WA_DeleteOnClose)
        self.setMinimumSize(200, 500)
        self._setup_widgets()
        self._setup_actions()
        self._setup_layouts()
        self._setup_signals()
        self._update_title()

    def _setup_widgets(self):
        """
        Internal function that creates all UI widgets.
        """

        self._scene = scene.Scene()
        self._view = view.GraphicsView(self._scene.graphics_scene)

    def _setup_actions(self):
        """
        Internal function that setup all actions.
        """

        self.addAction(palette.PopupNodesPalette.show_action(self, self._view))

    def _setup_layouts(self):
        """
        Internal function that creates all UI layouts and add all widgets to them.
        """

        self._main_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(self._main_layout)

        self._main_layout.addWidget(self._view)

    def _setup_signals(self):
        """
        Internal function that creates all signal connections.
        """

        self.scene.signals.itemDragEntered.connect(self._on_item_drag_enter)
        self.scene.signals.itemDropped.connect(self._on_item_dropped)
        self.scene.signals.fileNameChanged.connect(self._update_title)
        self.scene.signals.modified.connect(self._update_title)

    def _update_title(self):
        """
        Internal function that updates editor title.
        """

        self.setWindowTitle(self.user_friendly_title)

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
            scene_pos = self._scene.view.mapToScene(mouse_pos)
            logger.debug(f'''Dropped Item:
                            > NODE_ID: {node_id}
                            > DATA: {json_data}
                            > MOUSE POS: {mouse_pos}
                            > SCENE POS {scene_pos}''')
            self._scene.spawn_node_from_data(node_id, json_data, scene_pos)
            event.setDropAction(qt.Qt.MoveAction)
            event.accept()

        def _handle_variable_drop():
            event_data = event.mimeData().data('noddle/x-vars_item')
            data_stream = qt.QDataStream(event_data, qt.QIODevice.ReadOnly)
            json_data = json.loads(data_stream.readQString())
            mouse_pos = event.pos()
            scene_pos = self.scene.view.mapToScene(mouse_pos)
            logger.debug('''Dropped Varible:
                            > DATA: {data}
                            > SCENE POS {scene_pos}'''.format(data=json_data, scene_pos=scene_pos))
            var_name = json_data['var_name']
            get_set_menu = qt.QMenu(self)
            getter_action = qt.QAction('Get', get_set_menu)
            setter_action = qt.QAction('Set', get_set_menu)
            get_set_menu.addAction(getter_action)
            get_set_menu.addAction(setter_action)
            result_action = get_set_menu.exec_(self.mapToGlobal(event.pos()))
            if result_action is None:
                return
            self.scene.spawn_getset(var_name, scene_pos, setter=result_action==setter_action)
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


class NodeContextMenu(qt.QMenu):
    def __init__(self, editor: NodeEditor):
        super().__init__('Node', editor)

        self._scene = editor.scene

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

        if not self._scene:
            return

        self._scene.copy_selected()

    def _on_cut_action_triggered(self):
        """
        Internal callback funtion that is called each time Cut action is triggered by the user.
        """

        if not self._scene:
            return

        self._scene.cut_selected()

    def _on_paste_action_triggered(self):
        """
        Internal callback funtion that is called each time Paste action is triggered by the user.
        """

        if not self._scene:
            return

        self._scene.paste_from_clipboard()

    def _on_delete_action_triggered(self):
        """
        Internal callback funtion that is called each time Delete action is triggered by the user.
        """

        if not self._scene:
            return

        self._scene.delete_selected()
