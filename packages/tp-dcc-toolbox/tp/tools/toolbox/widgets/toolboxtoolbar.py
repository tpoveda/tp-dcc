from __future__ import annotations

import typing
from typing import Type, Callable

from tp.common.python import color
from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.tools.toolbox.manager import ToolUisManager
	from tp.tools.toolbox.widgets.toolboxframe import ToolboxFrame


class ToolboxToolBar(qt.FlowToolBar):
	"""
	Custom toolbar that is added within toolbox frame.
	"""

	def __init__(
			self, toolbox_frame: ToolboxFrame, tool_uis_manager: ToolUisManager, icon_size: int = 20,
			icon_padding: int = 2, start_hidden: bool = True, parent: ToolboxFrame | None = None):
		super().__init__(icon_size=icon_size, icon_padding=icon_padding, parent=parent)

		if start_hidden:
			self.hide()

		self._toolbox_frame = toolbox_frame
		self._tool_uis_manager = tool_uis_manager
		self.overflow_menu_active(True)

	def add_tool_ui(self, tool_ui_class: Type, toggle_connect: Callable | None = None) -> qt.IconMenuButton:
		"""
		Adds a new button that links to given tool Ui class.

		:param Type tool_ui_class: tool Ui class.
		:param Callable or None toggle_connect: optional toggleable function to call.
		:return: newly created tool button.
		:rtype: qt.IconMenuButton
		"""

		tool_ui_color = self._tool_uis_manager.tool_ui_color(tool_ui_class.id)
		desaturated_color = color.desaturate(tool_ui_color, 0.75)
		ui_data = tool_ui_class.ui_data

		tool_button = self.add_tool_button(
			ui_data['icon'], ui_data['label'], desaturated_color, double_click_enabled=True)
		tool_button.setToolTip(ui_data['label'])
		tool_button.setProperty('toolUiId', tool_ui_class.id)
		tool_button.setProperty('colorDisabled', desaturated_color)
		tool_button.setProperty('color', tool_ui_color)
		tool_button.setProperty('iconName', ui_data['icon'])
		tool_button.leftClicked.connect(lambda btn=tool_button: toggle_connect(tool_ui_class.id, activate=True))
		tool_button.middleClicked.connect(lambda btn=tool_button: toggle_connect(tool_ui_class.id, activate=False))
		if ui_data.get('defaultActionDoubleClick', False):
			tool_button.leftDoubleClicked.connect(
				lambda: self._on_tool_ui_button_double_clicked(tool_ui_class, toggle_connect=toggle_connect))
		else:
			tool_button.double_click_enabled = False

		return tool_button

	def _on_tool_ui_button_double_clicked(self, tool_ui_class: Type, toggle_connect: Callable):
		"""
		Internal callback function that is called each time a tool ui button double-clicked by the user.

		:param Type tool_ui_class: tool Ui class.
		:param Callable or None toggle_connect: optional toggleable function to call.
		:return: newly created tool button.
		"""

		tool_ui_instance = self._toolbox_frame.tool_ui(tool_ui_class.id)
		if tool_ui_instance is None:
			tool_ui_instance = toggle_connect(tool_ui_class.id, hidden=True)

		tool_ui_instance.default_action()
