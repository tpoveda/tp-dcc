from __future__ import annotations

from typing import Tuple

from Qt.QtCore import QObject
from Qt.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QStackedLayout

import maya.cmds as cmds

from tp.maya.cmds import gui



def primary_node_editor() -> str:
	"""
	Returns the name of the primary node editor.

	:return: node editor name.
	:rtype: str
	"""

	all_node_editors = cmds.getPanel(scriptType='nodeEditorPanel')
	for node_editor in all_node_editors:
		node_editor_name = f'{node_editor}NodeEditorEd'
		if cmds.nodeEditor(node_editor_name, query=True, primary=True):
			return node_editor

	return ''


def node_editor_as_qt_widgets(node_editor_name: str) -> Tuple[QWidget, QGraphicsView, QGraphicsScene]:
	"""
	Returns the node editor widget, graphics view and graphics scene as Qt widgets.

	:param str node_editor_name: node editor Maya name.
	:return: node editor widget, graphics view and graphics scene.
	:rtype: Tuple[QWidget, QGraphicsView, QGraphicsScene]
	"""

	node_editor_panel = gui.to_qt_object(node_editor_name)			# type: QWidget
	stack = node_editor_panel.findChild(QStackedLayout)
	view = stack.currentWidget().findChild(QGraphicsView)

	return node_editor_panel, view, view.scene()


class NodeEditorWrapper(QObject):
	"""
	Wrapper class for Autodesk Maya node editor and provides Qt related function to interact with it.
	"""

	def __init__(self, node_editor_name: str | None = None):
		super().__init__()

		if not node_editor_name:
			self._maya_name = primary_node_editor()
			self.setObjectName(self._maya_name)
			if not self._maya_name:
				self._editor, self._view, self._scene = None, None, None
			else:
				self._editor, self._view, self._scene = node_editor_as_qt_widgets(self._maya_name)
		else:
			self.setObjectName(node_editor_name)
			self._maya_name = node_editor_name
			self._editor, self._view, self._scene = node_editor_as_qt_widgets(self._maya_name)

	def add_nodes_on_create(self) -> bool:
		"""
		Returns whether new nodes are added to the wrapped node editor when they are created.

		:return: True if new nodes are added to the node editor when they are created; False otherwise.
		:rtype: bool
		"""

		return cmds.nodeEditor(self.objectName(), addNewNodes=True, query=True)

	def set_add_nodes_on_create(self, state: bool):
		"""
		Sets whether new nodes are added to the wrapped node editor when they are created.

		:param bool state: True if new nodes should be added to the node editor when they are created; False otherwise.
		"""

		cmds.nodeEditor(self.objectName(), addNewNodes=state, edit=True)
