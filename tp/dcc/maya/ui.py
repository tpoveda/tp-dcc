from __future__ import annotations

import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI1

from ..abstract.ui import AFnUi
from ...externals.Qt import QtCompat
from ...externals.Qt.QtWidgets import QMainWindow


class FnUi(AFnUi):
    """
    Overloads `AFNBase` exposing functions to handle UI related behaviours for Maya application.
    """

    # noinspection PyMethodMayBeStatic
    def main_window(self) -> QMainWindow:
        """
        Returns main window.

        :return: main window instance.
        """

        # noinspection PyUnresolvedReferences
        return QtCompat.wrapInstance(int(OpenMayaUI1.MQtUtil.mainWindow()), QMainWindow)

    def delete_ui(self, ui_name: str):
        """
        Deletes UI element with given name.

        :param ui_name: name of the UI element to delete.
        """

        cmds.deleteUI(self._workspace_control_name)
