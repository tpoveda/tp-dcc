#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya docking functionality
"""

import uuid

import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI

from tp.core import output
from tp.common.python import helpers
from tp.common.qt import api as qt
from tp.common.qt import dpi, qtutils

if helpers.is_python3():
	long = int


def is_dock_locked():
	"""
	Returns whether Maya dock functionality is locked.

	:return: True if dock functionality is locked; False otherwise.
	:rtype: bool
	"""

	cmds.optionVar(q='workspacesLockDocking')


def is_workspace_floating(workspace_name):
	"""
	Returns whether workspace is floating.

	:param str workspace_name: name of the workspace to check floating status.
	:return: True if workspace is floating; False otherwise.
	:rtype: bool
	"""

	return cmds.workspaceControl(workspace_name, floating=True, q=True)


def dock_to_container(workspace_name, workspace_width, workspace_height, workspace_title=None, size=35):

	# Import here to avoid cyclic imports
	from tp.common.qt.widgets import frameless

	locked = is_dock_locked()
	if locked:
		output.display_warning('DCC docking is locked. Unlock it first.')
		return None, None, None

	workspace_title = workspace_title or workspace_name
	workspace_control_name = cmds.workspaceControl(
		f'{workspace_name} [{str(uuid.uuid4())[:4]}]', loadImmediately=True, label=workspace_title,
		retain=False, initialWidth=workspace_width, initialHeight=workspace_height, vis=True)
	ptr = OpenMayaUI.MQtUtil.getCurrentParent()
	workspace_control = qtutils.wrapinstance(ptr, qt.QMainWindow)
	w = workspace_control.window()
	w.setFixedSize(dpi.size_by_dpi(qt.QSize(size, size)))
	w.layout().setContentsMargins(0, 0, 0, 0)
	w.setWindowOpacity(0)
	window_flags = w.windowFlags() | qt.Qt.FramelessWindowHint
	w.setWindowFlags(window_flags)
	cmds.workspaceControl(workspace_control_name, resizeWidth=size, resizeHeight=size, e=1)
	w.show()
	w.setWindowOpacity(1)
	docking_container = frameless.DockingContainer(workspace_control, workspace_control_name)
	# Attach it to the workspaceControl
	widget_ptr = OpenMayaUI.MQtUtil.findControl(docking_container.objectName())
	OpenMayaUI.MQtUtil.addWidgetToMayaLayout(long(widget_ptr), long(ptr))
	docking_container.move_to_mouse()

	return workspace_control_name, workspace_control, docking_container
