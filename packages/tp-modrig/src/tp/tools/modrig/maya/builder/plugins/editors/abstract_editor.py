from __future__ import annotations

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget


class EditorPlugin(QWidget):
    """Base class for editor plugins."""

    id = ""
    name = "Editor Plugin"
    description = "Base class for editor plugins"
    version = "0.1.0"

    # noinspection PyMethodMayBeStatic
    def get_allowed_areas(self) -> Qt.DockWidgetArea | Qt.DockWidgetAreas:
        """Get the allowed dock areas for this plugin.

        Returns:
            The allowed dock areas
        """

        return Qt.AllDockWidgetAreas

    # noinspection PyMethodMayBeStatic
    def get_default_area(self) -> Qt.DockWidgetArea:
        """Get the default dock area for this plugin.

        Returns:
            The default dock area
        """

        return Qt.RightDockWidgetArea
