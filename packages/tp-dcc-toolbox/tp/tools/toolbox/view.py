from __future__ import annotations

import time
import typing
from typing import Tuple, List, Dict

from overrides import override

from tp.core import log
from tp.common.python import helpers
from tp.common.qt import api as qt
from tp.preferences.interfaces import core
from tp.tools.toolbox import manager
from tp.tools.toolbox.widgets import toolboxframe

if typing.TYPE_CHECKING:
	from tp.tools.toolbox.widgets.toolboxtree import ToolboxTreeWidget

logger = log.tpLogger


_TOOLBOX_WINDOW = None								# type: ToolBoxWindow
_TOOLBOX_INSTANCES = []								# type: List[ToolBoxWindow]
_TOOLBOX_FRAME_INSTANCES = []						# type: List[toolboxframe.ToolboxFrame]


def add_toolbox_ui(toolbox: ToolBoxWindow):
	"""
	Adds given toolbox window to the global list of currently opened toolbox windows.

	:param ToolBoxWindow toolbox: toolbox window to add.
	"""

	_TOOLBOX_INSTANCES.append(toolbox)
	add_toolbox_frame(toolbox.toolbox_frame)


def add_toolbox_frame(toolbox_frame: toolboxframe.ToolboxFrame):
	"""
	Adds toolsbox frame into the cache, so we can use it later.

	:param toolboxframe.ToolboxFrame toolbox_frame: toolbox frame instance to add into the cache.
	"""

	_TOOLBOX_FRAME_INSTANCES.append(toolbox_frame) if toolbox_frame not in _TOOLBOX_FRAME_INSTANCES else None


def run_tool_ui(tool_uid_id: str, log_warning: bool = True) -> bool:
	"""
	Runs a tool UI, and loads it to the active toolbox window.

	:param str tool_uid_id: ID of the tool to load.
	:param bool log_warning: whether to log warning messages.
	:return: True if tool UI was executed successfully; False otherwise.
	:rtype: bool
	"""

	toolbox_window = last_focused_toolbox_ui(include_minimized=False)
	if toolbox_window is not None:
		toolbox_window.toggle_tool_ui(tool_uid_id)
		return True

	if log_warning:
		logger.warning('Tool Ui not found')

	return False


def toolbox_uis() -> List[ToolBoxWindow]:
	"""
	Returns a list with all the currently opened toolbox windows.

	:return: list of toolbox windows.
	:rtype: List[ToolBoxWindow]
	"""

	global _TOOLBOX_INSTANCES
	return _TOOLBOX_INSTANCES


def last_focused_toolbox_ui(include_minimized: bool = True) -> ToolBoxWindow | None:
	"""
	Returns the latest focused tool UI.

	:param bool include_minimized: whether to include minimized tool UIs.
	:return: last focused tool UI instance.
	:rtype: ToolBoxWindow or None
	"""

	found_toolbox_window = None
	max_time = 0
	toolbox_windows = toolbox_uis()
	for toolbox_window in toolbox_windows:
		if toolbox_window.last_focused_time > max_time:
			if (not include_minimized and not toolbox_window.is_minimized()) or include_minimized:
				found_toolbox_window = toolbox_window
				max_time = toolbox_window.last_focused_time

	return found_toolbox_window


class ToolBoxWindow(qt.FramelessWindow):

	WINDOW_SETTINGS_PATH = 'tp/toolui'
	WINDOW_HEIGHT_PADDING = 50
	TOOLBOX_WINDOW_WIDTH = 390
	TOOLBOX_WINDOW_HEIGHT = 20
	TOOLBOX_WINDOW_MAX_HEIGHT = 800

	class ToolboxTitleBar(qt.FramelessWindow.TitleBar):
		"""
		Custom title bar used by toolbox window.
		"""

		def __init__(self, show_title: bool = True, always_show_all: bool = False, parent: qt.FramelessWindow | None = None):
			super().__init__(show_title=show_title, always_show_all=always_show_all, parent=parent)

			self._toolbox_ui = self._frameless_window
			self._logo_inactive = core.theme_preference_interface().stylesheet_setting_color('TOOLBOX_LOGO_INACTIVE_COLOR')

			self.setAcceptDrops(True)

	def __init__(
			self, title: str = 'Tools', icon_color: Tuple[int, int, int] = (231, 133, 255), hue_shift: int = -30,
			width=TOOLBOX_WINDOW_WIDTH, height=TOOLBOX_WINDOW_HEIGHT, max_height=TOOLBOX_WINDOW_MAX_HEIGHT,
			tool_ids_to_run: List[str] | None = None, position: Tuple[int, int] | None = None,
			parent: qt.QWidget | None = None):
		super().__init__(
			title=title, width=width, height=height, title_bar_class=ToolBoxWindow.ToolboxTitleBar,
			always_show_all_title=True, save_window_pref=False, init_pos=position)

		self._hue_shift = hue_shift
		self._icon_color = icon_color
		self._max_height = qt.dpi_scale(max_height)
		self._resized_height = 0
		self._always_resize_to_tree = True
		self._last_focused_time = time.time()

		self._main_layout = qt.vertical_layout(margins=(0, 0, 0, 0))
		self._tool_uis_manager = manager.ToolUisManager.instance()
		self._toolbox_frame = toolboxframe.ToolboxFrame(
			toolbox_window=self, tool_uis_manager=self._tool_uis_manager, icon_color=icon_color, hue_shift=hue_shift,
			start_hidden=False, toolbar_hidden=False, parent=self)

		self._toolbox_frame.setUpdatesEnabled(False)
		try:
			self._init_ui()
			self._init_tool_uis(tool_ids_to_run)
		finally:
			self._toolbox_frame.setUpdatesEnabled(True)
		self.set_highlight(True, update_uis=True)

		add_toolbox_ui(self)
		self._toolbox_frame.resizeRequested.connect(self.resize_window)

		self.setWindowTitle(title)

	@classmethod
	def launch(cls, toolbox_kwargs: Dict | None = None, parent: qt.QWidget | None = None) -> ToolBoxWindow:
		"""
		Loads Toolbox Window.

		:param Dict or None toolbox_kwargs: optional toolbox window keyword arguments.
		:param qt.QWidget or None parent: optional parent widget.
		:return: toolbox window instance.
		:rtype: ToolBoxWindow
		"""

		global _TOOLBOX_WINDOW

		try:
			_TOOLBOX_WINDOW.close()
		except AttributeError:
			pass

		toolbox_kwargs = toolbox_kwargs or {}
		tool_ids_to_run = toolbox_kwargs.get('tool_ids_to_run', [])
		position = toolbox_kwargs.get('position', None)
		toolbox_window = ToolBoxWindow(
			icon_color=(231, 133, 255), hue_shift=10, tool_ids_to_run=tool_ids_to_run, position=position, parent=parent)
		toolbox_window.show()

		return toolbox_window

	@property
	def last_focused_time(self) -> float:
		return self._last_focused_time

	@property
	def toolbox_frame(self) -> toolboxframe.ToolboxFrame:
		return self._toolbox_frame

	@override
	def maximize(self):
		width = self._saved_size.width()
		calc_height = self._calculate_height()
		self._set_ui_minimized(False)
		self._minimized = False
		self.window().resize(width, self._resized_height if calc_height < self._resized_height else calc_height)

	# @override(check_signature=False)
	# def resize_window(self, disable_scrollbar: bool = True, delayed: bool = False):
	#
	# 	if delayed:
	# 		qt.QTimer.singleShot(0, lambda: self.resize_window(disable_scrollbar, delayed=False))
	# 		return
	#
	# 	if self.is_docked():
	# 		self.setMinimumSize(qt.QSize(self.width(), 300))
	# 		self.setMinimumSize(qt.QSize(0, 0))
	# 		return
	#
	# 	if disable_scrollbar:
	# 		self._toolbox_frame.tree.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
	#
	# 	self._max_height = self._max_window_height()
	#
	# 	new_height = self.window().minimumSizeHint().height() + self._toolbox_frame.calculate_size_hint().height()
	# 	new_height = self._max_height if new_height > self._max_height else new_height
	# 	width = self.window().rect().width()
	#
	# 	if new_height < self._resized_height and not self._always_resize_to_tree:
	# 		self.window().resize(width, self._resized_height)
	# 	else:
	# 		self.window().resize(width, new_height)
	# 		self._resized_height = new_height
	#
	# 	if disable_scrollbar:
	# 		self._toolbox_frame.tree.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)

	def toggle_tool_ui(
			self, tool_ui_id: str, activate: bool = True,
			keep_open: bool = False) -> ToolboxTreeWidget.ToolboxTreeWidgetItem:
		"""
		Toggles tool Ui with given id.

		:param str tool_ui_id: id of the tool Ui to toggle.
		:param bool activate: whether to activate tool ui.
		:param bool keep_open: whether to keep open tool ui.
		:return: tool ui widget instance.
		:rtype: ToolboxTreeWidget.ToolboxTreeWidgetItem
		"""

		return self._toolbox_frame.toggle_tool_ui(tool_ui_id, activate=activate, keep_open=keep_open)

	def set_highlight(self, flag: bool, update_uis: bool = False):
		"""
		Sets the logo highlight.

		:param bool flag: whether to highlight the logo.
		:param bool update_uis: whether to update ui icons.
		"""

		if self.is_minimized() and not flag:
			self._title_bar.set_logo_highlight(True)
			return

		self._last_focused_time = time.time()

		if flag and update_uis:
			for toolbox_ui in toolbox_uis():
				if not toolbox_ui.is_minimized():
					toolbox_ui.title_bar.set_logo_highlight(False)
			self._title_bar.set_logo_highlight(True)

	def _init_ui(self):
		"""
		Internal function initializes toolbox window UI.
		"""

		self.set_main_layout(self._main_layout)

		self._toolbox_frame.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Preferred)
		self._title_bar.contents_layout.addWidget(self._toolbox_frame)
		self._main_layout.addWidget(self._toolbox_frame.tree)
		self._main_layout.setStretch(1, 1)
		self._title_bar.corner_contents_layout.addWidget(self._toolbox_frame.menu_button)
		self.set_maximize_button_visible(False)

	def _init_tool_uis(self, tool_ui_ids: List[str]):
		"""
		Internal function that initializes tool Uis with given tool Ui ids.

		:param List[str] tool_ui_ids: list of tool Ui ids to initialize.
		"""

		tool_ui_ids = helpers.force_list(tool_ui_ids)
		for tool_ui_id in tool_ui_ids:
			self.toggle_tool_ui(tool_ui_id)

	def _max_window_height(self) -> int:
		"""
		Returns the maximum height for this window depending on the height of the screen.

		:return: maximum window height.
		:rtype: int
		"""

		pos = self.mapToGlobal(qt.QPoint(0, 0))
		desktop = qt.QApplication.desktop()
		screen_height = desktop.screenGeometry(desktop.screenNumber(desktop.cursor().pos())).height()
		relative_pos = pos - qt.QPoint(desktop.screenGeometry(self).left(), desktop.screenGeometry(self).top())

		return screen_height - relative_pos.y() - ToolBoxWindow.WINDOW_HEIGHT_PADDING

	def _calculate_height(self) -> int:
		"""
		Internal function that returns the expected height when maximizing the window.

		:return: window height.
		:rtype: int
		"""

		self._max_height = self._max_window_height()
		new_height = self.window().minimumSizeHint().height() + self._toolbox_frame.calculate_size_hint().height()
		new_height = self._max_height if new_height > self._max_height else new_height

		return new_height
