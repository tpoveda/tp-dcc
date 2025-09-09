from __future__ import annotations

from Qt.QtWidgets import QWidget, QMainWindow, QDockWidget, QPushButton

from tp.libs.qt import factory as qt
from tp.tools.modrig.builder.plugins.editors.modules_library import ModulesLibraryWidget


class ModuleCreatorView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self):
        """Set up the widgets for the view."""

        self._main_window = QMainWindow()
        self._main_window.setCentralWidget(QPushButton("Hello World"))

        self._modules_library = ModulesLibraryWidget(parent=self)
        modules_library_dock = QDockWidget(parent=self)
        modules_library_dock.setWidget(self._modules_library)
        modules_library_dock.setAllowedAreas(
            qt.Qt.LeftDockWidgetArea | qt.Qt.RightDockWidgetArea
        )
        self._main_window.addDockWidget(qt.Qt.LeftDockWidgetArea, modules_library_dock)

    def _setup_layouts(self):
        """Set up the layouts for the view."""

        main_layout = qt.vertical_layout()
        self.setLayout(main_layout)

        main_layout.addWidget(self._main_window)
