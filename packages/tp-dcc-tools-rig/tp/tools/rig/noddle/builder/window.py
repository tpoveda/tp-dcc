from __future__ import annotations

import typing

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.common.resources import api as resources
# from tp.common.nodegraph.core import graph
# from tp.common.nodegraph.nodes import basic, widgets
# from tp.common.nodegraph.editors import propertieseditor

from tp.tools.rig.noddle.builder.widgets import workspace, palette, history
from tp.tools.rig.noddle.builder.menus import file_menu
from tp.tools.rig.noddle.builder.graph import editor

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.clients.maya.client import NoddleBuilderClient

logger = log.rigLogger


class NoddleBuilderWindow(qt.FramelessWindow):

    def __init__(self, client: NoddleBuilderClient, parent: qt.QWidget | None = None):

        self._client = client
        self._window_title = 'Noddle Builder v0.0.1'

        super().__init__(title=self._window_title, parent=parent)

        self.setMinimumSize(1200, 800)

    @property
    def client(self) -> NoddleBuilderClient:
        return self._client

    @property
    def mdi_area(self) -> qt.QMdiArea:
        return self._mdi_area

    @property
    def workspace_widget(self) -> workspace.WorkspaceWidget:
        return self._workspace_widget

    @property
    def current_window(self) -> qt.QMdiSubWindow:
        return self._mdi_area.currentSubWindow()

    @property
    def current_editor(self) -> editor.NodeEditor | None:
        return self.current_window.widget() if self.current_window else None

    @override
    def _setup_ui(self):
        super()._setup_ui()

        main_layout = self.main_layout()
        self._main_window = qt.QMainWindow(parent=self)
        self._main_window.setTabPosition(qt.Qt.RightDockWidgetArea, qt.QTabWidget.East)
        self._main_window.setTabPosition(qt.Qt.LeftDockWidgetArea, qt.QTabWidget.North)
        self._window_main_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self._window_main_widget = qt.widget(self._window_main_layout, parent=self)
        self._main_window.setCentralWidget(self._window_main_widget)
        main_layout.addWidget(self._main_window)

        self._workspace_widget = workspace.WorkspaceWidget(client=self._client, parent=self)
        self._workspace_dock = qt.QDockWidget(self._workspace_widget.LABEL)
        self._workspace_dock.setWidget(self._workspace_widget)
        self._workspace_dock.setAllowedAreas(qt.Qt.RightDockWidgetArea)

        self._attributes_editor = qt.QWidget(parent=self)
        self._attributes_editor_dock = qt.QDockWidget('Attributes')
        self._attributes_editor_dock.setWidget(self._attributes_editor)
        self._attributes_editor_dock.setAllowedAreas(qt.Qt.RightDockWidgetArea)

        self._history_widget = history.SceneHistoryWidget(self)
        self._history_dock = qt.QDockWidget('History')
        self._history_dock.setWidget(self._history_widget)
        self._history_dock.setAllowedAreas(qt.Qt.LeftDockWidgetArea | qt.Qt.RightDockWidgetArea)

        self._nodes_palette = palette.NodesPalette(client=self._client, parent=self)
        self._nodes_palette_dock = qt.QDockWidget('Nodes Palette')
        self._nodes_palette_dock.setWidget(self._nodes_palette)
        self._nodes_palette_dock.setAllowedAreas(qt.Qt.LeftDockWidgetArea)

        self._vars_widget = qt.QWidget(parent=self)
        self._vars_dock = qt.QDockWidget('Variables')
        self._vars_dock.setWidget(self._vars_widget)
        self._vars_dock.setAllowedAreas(qt.Qt.LeftDockWidgetArea)

        self._mdi_area = qt.QMdiArea(parent=self)
        self._mdi_area.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        self._mdi_area.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        self._mdi_area.setViewMode(qt.QMdiArea.TabbedView)
        self._mdi_area.setDocumentMode(True)
        self._mdi_area.setTabsClosable(True)
        self._mdi_area.setTabsMovable(True)

        # self._graph = graph.NodeGraph()
        # self._graph.register_nodes(
        #     [
        #         basic.BasicNodeA,
        #         basic.BasicNodeB,
        #         basic.CustomGroupNode,
        #         basic.CustomSocketsNode,
        #         widgets.DropdownMenuNode,
        #         widgets.TextInputNode,
        #         widgets.CheckboxNode
        #     ]
        # )
        # self._graph_widget = self._graph.widget
        # self._graph_widget.resize(1100, 800)
        # self._graph_widget.show()
        # node_basic_a = self._graph.create_node('nodes.basic.BasicNodeA', text_color='#feab20')
        # node_basic_a.set_disabled(False)
        # # create node and set a custom icon.
        # node_basic_b = self._graph.create_node('nodes.basic.BasicNodeB', name='custom icon')
        # icon_path = r"D:\tools\dev\tp-dcc-dev\packages\tp-dcc-common\tp\common\resources\icons\color\face.png"
        # node_basic_b.set_icon(icon_path)
        # # create node with the custom port shapes.
        # n_custom_sockets = self._graph.create_node('nodes.custom.sockets.CustomSocketsNode', name='custom ports')
        # n_text_input = self._graph.create_node('nodes.widget.TextInputNode', name='text node', color='#0a1e20')
        # n_checkbox = self._graph.create_node('nodes.widget.CheckboxNode', name='checkbox node')
        # n_combo_menu = self._graph.create_node('nodes.widget.DropdownMenuNode', name='combobox node')
        # n_group = self._graph.create_node('nodes.group.CustomGroupNode')
        # n_text_input.set_output(0, n_custom_sockets.input(0))
        # n_text_input.set_output(0, n_checkbox.input(0))
        # n_text_input.set_output(0, n_combo_menu.input(0))
        # self._graph.auto_layout_nodes()
        # n_backdrop = self._graph.create_node('Backdrop')
        # n_backdrop.wrap_nodes([n_custom_sockets, n_combo_menu])
        # self._graph.clear_selection()
        # self._graph.fit_to_selection()
        # properties_editor = propertieseditor.PropertiesEditorWidget(graph=self._graph)
        # properties_editor.setWindowFlags(qt.Qt.Tool)
        # def display_properties_bin(_):
        #     if not properties_editor.isVisible():
        #         properties_editor.show()
        # self._graph.nodeDoubleClicked.connect(display_properties_bin)

        self._main_window.addDockWidget(qt.Qt.RightDockWidgetArea, self._workspace_dock)
        self._main_window.addDockWidget(qt.Qt.RightDockWidgetArea, self._attributes_editor_dock)
        self._main_window.tabifyDockWidget(self._workspace_dock, self._attributes_editor_dock)
        self._workspace_dock.raise_()
        self._main_window.addDockWidget(qt.Qt.RightDockWidgetArea, self._history_dock)
        self._main_window.addDockWidget(qt.Qt.LeftDockWidgetArea, self._nodes_palette_dock)
        self._main_window.addDockWidget(qt.Qt.LeftDockWidgetArea, self._vars_dock)

        # self._window_main_layout.addWidget(self._graph_widget)
        self._window_main_layout.addWidget(self._mdi_area)

        self._setup_menubar()

    @override
    def _setup_signals(self):
        super()._setup_signals()

        self._update_button.clicked.connect(self._on_update_button_clicked)
        self._mdi_area.subWindowActivated.connect(self._on_mdi_area_sub_window_activated)

    def new_build(self):
        """
        Creates a new build graph.
        """

        try:
            sub_window = self._create_mdi_child()
            sub_window.show()
        except Exception:
            logger.exception('Failed to create new build', exc_info=True)

    def open_build(self):
        """
        Opens build file.
        """

        sub_window = self.current_window or self._create_mdi_child()
        sub_window.widget().open_build()

    def open_build_tabbed(self):
        """
        Opens build file in a new tab.
        """

        sub_window = self._create_mdi_child()
        res = sub_window.window().open_build()
        if not res:
            self.mdi_area.removeSubWindow(sub_window)

    def save_build(self):
        """
        Saves current build into disk.
        """

        if not self.current_editor:
            return

        self.current_editor.save_build()

    def save_build_as(self):
        """
        Saves current build into disk in a new file.
        """

        if not self.current_editor:
            return

        self.current_editor.save_build_as()

    def _setup_menubar(self):
        """
        Internal function that setup menubar.
        """

        self._menubar = qt.QMenuBar(parent=self._main_window)
        self._main_window.setMenuBar(self._menubar)

        self._update_button = qt.base_button(icon=resources.icon('refresh'))
        self._menubar.setCornerWidget(self._update_button, qt.Qt.TopRightCorner)

        self._file_menu = file_menu.FileMenu(self)

        self._menubar.addMenu(self._file_menu)

    def _create_mdi_child(self):
        """
        Internal function that creates a new node editor.
        """

        new_editor = editor.NodeEditor(client=self._client, parent=self)
        sub_window = self._mdi_area.addSubWindow(new_editor)
        new_editor.scene.signals.fileNameChanged.connect(self._update_title)
        new_editor.scene.signals.modified.connect(self._update_title)

        return sub_window

    def _update_title(self):
        """
        Internal function that updates window title.
        """

        if not self.current_editor:
            self.setWindowTitle(self._window_title)
            return

        self.setWindowTitle(f'{self._window_title} - {self.current_editor.user_friendly_title}')

    def _on_update_button_clicked(self):
        """
        Internal callback function that is called each time Update button is clicked by the user.
        """

        self._workspace_widget.update_data()
        self._nodes_palette.update_nodes_tree()

    def _on_mdi_area_sub_window_activated(self):
        """
        Internal callback function that is called each time MDI area sub window is activated.
        """

        self._update_title()
        self._history_widget.update_history_connection()


