from __future__ import annotations

from Qt.QtWidgets import QMainWindow

from ..abstract.ui import AFnUi


class FnUi(AFnUi):
    """
    Overloads `AFNBase` exposing functions to handle UI related behaviours for Standalone application.
    """

    # noinspection PyMethodMayBeStatic
    def main_window(self) -> QMainWindow | None:
        """
        Returns main window.

        :return: main window instance.
        """

        return None

    def delete_ui(self, ui_name: str):
        """
        Deletes UI element with given name.

        :param ui_name: name of the UI element to delete.
        """

        pass
