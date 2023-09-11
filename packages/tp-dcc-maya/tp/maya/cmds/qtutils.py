#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utils functions to work with Qt in Maya
"""

from __future__ import annotations

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget

import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI1

from tp.core import log
from tp.common.qt import qtutils as qt

logger = log.tpLogger


def add_widget_to_maya_layout(widget: QWidget):
    """
    Adds given QWidget to maya layout.

    :param QWidget widget: widget to add into Maya layout.
    """

    parent = OpenMayaUI1.MQtUtil.getCurrentParent()
    mixin_ptr = OpenMayaUI1.MQtUtil.findControl(widget.objectName())
    OpenMayaUI1.MQtUtil.addWidgetToMayaLayout(int(mixin_ptr), int(parent))


def dock_widget(
        widget: QWidget, label: str, retain: bool = False, show: bool = True,
        initial_width: int | None = None) -> QWidget:
    """
    Creates an instance of the class and dock into Maya UI,

    :param QWidget widget: widget we want to dock into Maya UI.
    :param str label: dock label.
    :param bool retain: whether to retain size.
    :param bool show: whether to show dock widget.
    :param int or None initial_width: optional initial width.
    :return: docked widget.
    :rtype: QWidget
    """

    initial_width = initial_width or cmds.optionVar(query='workspacesWidePanelInitialWidth') * 0.75

    workspace_control = widget.objectName() + '_workspace_control'
    try:
        cmds.deleteUI(workspace_control)
        cmds.workspaceControlState(workspace_control, remove=True)
        logger.debug('Removed workspace {0}'.format(workspace_control))
    except Exception:
        pass

    main_control = cmds.workspaceControl(
        workspace_control, ttc=['AttributeEditor', -1], iw=initial_width, mw=True,
        wp='preferred', label=label, retain=retain)
    control_widget = OpenMayaUI1.MQtUtil.findControl(workspace_control)
    control_wrap = qt.wrapinstance(int(control_widget), QWidget)
    control_wrap.setAttribute(Qt.WA_DeleteOnClose)
    widget.setParent(control_wrap)
    control_wrap.layout().addWidget(widget)
    if show:
        cmds.evalDeferred(lambda *args: cmds.workspaceControl(main_control, e=True, rs=True, fl=False))

    return control_wrap
