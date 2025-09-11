from __future__ import annotations

from typing import Tuple

from Qt.QtCore import Qt
from Qt.QtWidgets import QApplication, QWidget, QDialog
from Qt.QtGui import QIcon, QGuiApplication

from .. import utils


class BaseDialog(QDialog):
    """Extends base `QDialog` class."""

    def __init__(
        self,
        title: str = "",
        width: int = 600,
        height: int = 800,
        icon: QIcon | None = None,
        show_on_initialize: bool = True,
        transparent: bool = False,
        parent: QWidget | None = None,
    ):
        """Initialize a new instance of the class.

        :param title: The title of the dialog. Default is an empty string.
        :param width: The width of the dialog. Default is 600.
        :param height: The height of the dialog. Default is 800.
        :param icon: The path to the icon of the dialog. Default is an empty string.
        :param show_on_initialize: Whether to show the dialog upon initialization. Default is True.
        :param transparent: Whether the dialog should be transparent. Default is False.
        :param parent: The parent widget, if any. Default is None, indicating no parent.
        """

        super().__init__(parent=parent)

        if transparent:
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setWindowFlags(Qt.FramelessWindowHint)

        self._title = title
        # self._theme_pref = core.theme_preference_interface()
        # self._theme_pref.updated.connect(self._on_theme_updated)

        self.setObjectName(title)
        self.setWindowTitle(title)
        self.setContentsMargins(2, 2, 2, 2)
        self.resize(width, height)

        if icon is not None:
            self.setWindowIcon(icon)

        if show_on_initialize:
            self.center()
            self.show()

        self.resize(width, height)

    def center(self, to_cursor: bool = True):
        """Move the dialog to the center of the current window.

        :param bool to_cursor: whether to center dialog to screen or cursor.
        """

        frame_geo = self.frameGeometry()
        center_point = utils.current_screen().geometry().center()
        frame_geo.moveCenter(center_point)
        self.move(frame_geo.topLeft())

    def fill_to_parent(self, margins: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        """Fills size to parent.

        :param Tuple[int, int, int, int] margins: optional left-top-right-bottom margins.
        """

        self.setGeometry(
            margins[0],
            margins[1],
            self.window().geometry().width() - margins[0] - margins[2],
            self.window().geometry().height() - margins[1] - margins[3],
        )

    def toggle_maximized(self):
        """Toggles maximized window state."""

        self.showNormal() if self.windowState() and Qt.WindowMaximized else self.showMaximized()

    # def _on_theme_updated(self, event: 'ThemeUpdateEvent'):
    #     """
    #     Internal callback function that is called each time theme is updated.
    #
    #     param ThemeUpdateEvent event: theme update event.
    #     """
    #
    #     self.setStyleSheet(event.stylesheet)
