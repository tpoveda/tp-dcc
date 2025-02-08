from __future__ import annotations


import uuid
import logging

import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI
from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QMainWindow

from tp.qt import dpi, utils as qtutils

logger = logging.getLogger(__name__)


def is_dock_locked() -> bool:
    """
    Returns whether Maya dock functionality is locked.

    :return: True if dock functionality is locked; False otherwise.
    """

    cmds.optionVar(q="workspacesLockDocking")


def is_workspace_floating(workspace_name: str) -> bool:
    """
    Returns whether workspace is floating.

    :param workspace_name: name of the workspace to check floating status.
    :return: True if workspace is floating; False otherwise.
    """

    return cmds.workspaceControl(workspace_name, floating=True, q=True)


def dock_to_container(
    workspace_name: str,
    workspace_width: int,
    workspace_height: int,
    workspace_title: str | None = None,
    size: int = 35,
):
    # Import here to avoid cyclic imports
    from tp.qt.widgets import frameless

    locked = is_dock_locked()
    if locked:
        logger.warning("DCC docking is locked. Unlock it first.")
        return None, None, None

    workspace_title = workspace_title or workspace_name
    workspace_control_name = cmds.workspaceControl(
        f"{workspace_name} [{str(uuid.uuid4())[:4]}]",
        loadImmediately=True,
        label=workspace_title,
        retain=False,
        initialWidth=workspace_width,
        initialHeight=workspace_height,
        vis=True,
    )
    ptr = OpenMayaUI.MQtUtil.getCurrentParent()
    workspace_control = qtutils.wrapinstance(ptr, QMainWindow)
    w = workspace_control.window()
    w.setFixedSize(dpi.size_by_dpi(QSize(size, size)))
    w.layout().setContentsMargins(0, 0, 0, 0)
    w.setWindowOpacity(0)
    window_flags = w.windowFlags() | Qt.FramelessWindowHint
    w.setWindowFlags(window_flags)
    cmds.workspaceControl(
        workspace_control_name, resizeWidth=size, resizeHeight=size, e=1
    )
    w.show()
    w.setWindowOpacity(1)
    docking_container = frameless.DockingContainer(
        workspace_control, workspace_control_name
    )
    # Attach it to the workspaceControl.
    widget_ptr = OpenMayaUI.MQtUtil.findControl(docking_container.objectName())
    OpenMayaUI.MQtUtil.addWidgetToMayaLayout(int(widget_ptr), int(ptr))
    docking_container.move_to_mouse()

    return workspace_control_name, workspace_control, docking_container
