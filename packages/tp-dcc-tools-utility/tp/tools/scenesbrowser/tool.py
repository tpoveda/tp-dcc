from __future__ import annotations

import typing
from typing import List

from overrides import override

from tp.core import dcc, tool
from tp.common.qt import api as qt
from tp.tools.toolbox.widgets import toolui

from tp.tools.scenesbrowser import view, controller


class ScenesBrowserTool(tool.Tool):

	id = 'tp.utility.scenebrowser'
	creator = 'Tomi Poveda'
	tags = ['scenes', 'browser']

	@override
	def execute(self, *args, **kwargs):

		win = None
		if dcc.is_maya():
			win = qt.FramelessWindow(title='Scenes Browser')
			tool_ui = ScenesBrowserToolUi()
			tool_ui.pre_content_setup()
			win.main_layout().addWidget(tool_ui.contents()[0])
			tool_ui.post_content_setup()
			win.show()

		return win


class ScenesBrowserToolUi(toolui.ToolUiWidget):

	id = TOOL_ID = 'tp.utility.scenebrowser'

	def __init__(self):
		super().__init__()

		self._controller = None				# type: ScenesBrowserController
		self._tool_ui_widget = None			# type: ScenesBrowserToolUi

	@override
	def pre_content_setup(self):
		self._tool_ui_widget = self
		if dcc.is_maya():
			from tp.tools.scenesbrowser.maya import controller as maya_controller
			self._controller = maya_controller.MayaScenesBrowserController(tool_ui_widget=self._tool_ui_widget)
		else:
			self._controller = controller.ScenesBrowserController(tool_ui_widget=self._tool_ui_widget)

	@override
	def contents(self) -> List[qt.QWidget]:
		return [view.ScenesBrowserView(
			tool_ui_widget=self._tool_ui_widget, controller=self._controller, parent=self)]
