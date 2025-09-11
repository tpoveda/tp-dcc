from __future__ import annotations

from Qt.QtCore import QSize
from Qt.QtWidgets import QWidget

from tp.libs import qt
from tp.libs.qt.widgets import IconMenuButton


class ToolPanelsMenuButton(IconMenuButton):
    def __init__(self, size: int = 20, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self.set_icon(qt.icon("menu_dots"))
        self.setIconSize(QSize(size, size))
        self.setFixedHeight(25)
