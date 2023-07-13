from __future__ import annotations

import typing

from tp.common.qt import api as qt
from tp.preferences.interfaces import core

if typing.TYPE_CHECKING:
	from tp.tools.toolbox.manager import ToolUisManager
	from tp.tools.toolbox.widgets.toolboxframe import ToolboxFrame


class ToolboxMenuButton(qt.IconMenuButton):
	"""
	Custom toolbox menu button that includes three menus:
		- Left Click: opens the tool groups menu (e.g: Animation, Rigging, Modeling, ...).
		- Middle Click: opens a popup window that displays row of icons of all available tool UIs.
		- Right Click: opens a menu with all the available tool UIs.
	"""

	MENU_ICON = 'menu_dots'

	def __init__(self, size: int = 20, tool_uis_manager: ToolUisManager = None, parent: ToolboxFrame | None = None):
		super().__init__(parent=parent)

		self._tool_uis_manager = tool_uis_manager
		self._theme_prefs = core.theme_preference_interface()

		self.setIconSize(qt.QSize(size, size))
		self.setFixedWidth(25)
		self.set_icon(self.MENU_ICON, self._theme_prefs.MAIN_FOREGROUND_COLOR)

		self._toolbox_popup = None
		self._setup_menus()

	@property
	def toolbox_popup(self):
		return self._toolbox_popup

	def _setup_menus(self):
		"""
		Internal function that setups toolbox menus.
		"""

		pass
