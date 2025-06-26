from __future__ import annotations

import typing
from abc import abstractmethod

from .base import AFnBase

if typing.TYPE_CHECKING:
    from Qt.QtWidgets import QMainWindow


class AFnUi(AFnBase):
    """
    Overloads `AFNBase` exposing functions to handle UI related behaviours.
    """

    @abstractmethod
    def main_window(self) -> QMainWindow:
        """
        Returns main window.

        :return: main window instance.
        """

        pass

    @abstractmethod
    def delete_ui(self, ui_name: str):
        """
        Deletes UI element with given name.

        :param ui_name: name of the UI element to delete.
        """

        pass
