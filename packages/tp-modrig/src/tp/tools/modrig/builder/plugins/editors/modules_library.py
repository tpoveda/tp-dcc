from __future__ import annotations

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget

from tp.libs.qt import dpi
from tp.libs.qt.widgets import TreeViewWidget

from .abstract_editor import EditorPlugin


class ModulesLibraryEditor(EditorPlugin):
    id = "modules_library"
    name = "Modules"
    description = "Modules Library Editor"
    version = "0.1.0"

    def get_allowed_areas(self) -> Qt.DockWidgetArea | Qt.DockWidgetAreas:
        """Get the allowed dock areas for this plugin."""

        return Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea

    def get_default_area(self) -> Qt.DockWidgetArea:
        """Get the default dock area for this plugin."""

        return Qt.LeftDockWidgetArea


class ModulesLibraryWidget(TreeViewWidget):
    def __init__(
        self,
        title="Modules",
        expand: bool = True,
        sorting: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(title=title, expand=expand, sorting=sorting, parent=parent)

        # self.tree_view.setHeaderHidden(True)
        # self.tree_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.tree_view.setIndentation(dpi.dpi_scale(10))
