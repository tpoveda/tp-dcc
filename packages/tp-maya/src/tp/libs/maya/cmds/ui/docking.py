from __future__ import annotations

import uuid
import typing
from typing import cast

import maya.cmds as cmds
from loguru import logger
import maya.OpenMayaUI as OpenMayaUI
from Qt.QtCore import Qt, QSize, QObject
from Qt.QtWidgets import QMainWindow

from tp.libs.qt import dpi, utils as qtutils

if typing.TYPE_CHECKING:
    from tp.libs.qt.widgets.frameless import DockingContainer


def is_dock_locked() -> bool:
    """Return whether Maya dock functionality is locked.

    Returns:
        True if dock functionality is locked; False otherwise.
    """

    return bool(cmds.optionVar(query="workspacesLockDocking"))


def is_workspace_floating(workspace_name: str) -> bool:
    """Return whether the workspace is floating.

    Args:
        workspace_name: name of the workspace to check floating status.

    Returns:
        True if the workspace is floating; False otherwise.
    """

    return cmds.workspaceControl(workspace_name, floating=True, query=True)


def dock_to_container(
    workspace_name: str,
    workspace_width: int,
    workspace_height: int,
    workspace_title: str | None = None,
    size: int = 35,
) -> tuple[str | None, QObject | None, DockingContainer | None]:
    """Dock a workspace control to a frameless container.

    Args:
        workspace_name: Name of the workspace control to create.
        workspace_width: Width of the workspace control.
        workspace_height: Height of the workspace control.
        workspace_title: Title of the workspace control.
        size: Size of the docking container in pixels.

    Returns:
        tuple: A tuple containing the workspace control name,
            the workspace control instance, and the docking container instance.
    """

    # Import here to avoid cyclic imports
    from tp.libs.qt.widgets import frameless

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
        visible=True,
    )
    ptr = OpenMayaUI.MQtUtil.getCurrentParent()
    workspace_control = cast(QMainWindow, qtutils.wrapinstance(ptr, QMainWindow))
    w = workspace_control.window()
    w.setFixedSize(dpi.size_by_dpi(QSize(size, size)))
    w.layout().setContentsMargins(0, 0, 0, 0)
    w.setWindowOpacity(0)
    window_flags = w.windowFlags() | Qt.FramelessWindowHint
    w.setWindowFlags(window_flags)
    cmds.workspaceControl(
        workspace_control_name, resizeWidth=size, resizeHeight=size, edit=True
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
