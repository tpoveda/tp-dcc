#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains generic Qt windows implementation
"""

from Qt.QtCore import Qt, Signal, QObject, QSettings, QPoint, QSize
from Qt.QtWidgets import QLayout, QWidget, QFrame

from tp.core import dcc
from tp.preferences.interfaces import core as core_interfaces
from tp.common.qt import dpi, qtutils
from tp.common.qt.widgets import layouts, titlebar, frameless


class WindowContents(QFrame):
	"""
	Frame that contains the contents of a window.
	For CSS purposes.
	"""

	pass


class BaseWindow(QWidget):

	WINDOW_SETTINGS_PATH = ''				# Window settings registry path (e.g: tp/dcc/window)
	HELP_URL = ''							# Web URL to use when displaying the help documentation for this window
	MINIMIZED_WIDTH = 390

	closed = Signal()

	class KeyboardModifierFilter(QObject):

		modifierPressed = Signal()
		windowEvent = Signal(object)

		_CURRENT_EVENT = None

		def eventFilter(self, obj, event):
			self._CURRENT_EVENT = event
			self.windowEvent.emit(event)

			return super().eventFilter(obj, event)

	def __init__(
			self, name='', title='', width=None, height=None, resizable=True, modal=False, init_pos=None,
			title_bar_class=None, overlay=True, always_show_all_title=False, on_top=False, save_window_pref=False,
			minimize_enabled=True, minimize_button=False, maximize_button=False, parent=None):
		super().__init__(parent=None)

		self.setObjectName(name or title)
		width, height = dpi.dpi_scale(width or 0), dpi.dpi_scale(height or 0)

		self._name = name
		self._title = title
		self._on_top = on_top
		self._minimized = False
		self._settings = QSettings()
		self._save_window_pref = save_window_pref
		self._parent_container = None
		self._window_resizer = None
		self._minimize_enabled = minimize_enabled
		self._modal = modal
		self._parent = parent
		self._init_width = width
		self._init_height = height
		self._always_show_all_title = always_show_all_title
		self._saved_size = QSize()
		self._filter = BaseWindow.KeyboardModifierFilter()

		if self.WINDOW_SETTINGS_PATH:
			position = QPoint(*(init_pos or ()))
			init_pos = position or self._settings.value('/'.join((self.WINDOW_SETTINGS_PATH, 'pos')))
		self._init_pos = init_pos

		title_bar_class = title_bar_class or titlebar.TitleBar
		self._title_bar = title_bar_class(always_show_all=always_show_all_title, parent=self)

		self._setup_ui()
		self.set_title(title)
		self._setup_signals()
		self.set_resizable(resizable)
		self._overlay = None
		self._prev_style = self.title_style()

		if overlay:
			self._overlay = frameless.FramelessOverlay(
				parent=self, title_bar=self._title_bar, top_left=self._window_resizer.top_left_resizer,
				top_right=self._window_resizer.top_right_resizer, bottom_left=self._window_resizer.bottom_right_resizer,
				bottom_right=self._window_resizer.bottom_right_resizer, resizable=resizable)
			self._overlay.widgetMousePress.connect(self.mousePressEvent)
			self._overlay.widgetMouseMove.connect(self.mouseMoveEvent)
			self._overlay.widgetMouseRelease.connect(self.mouseReleaseEvent)

		if not minimize_button:
			self.set_minimize_button_visible(False)

		if not maximize_button:
			self.set_maximize_button_visible(False)

		self.setup_ui()
		self.setup_signals()

	@property
	def docked(self):
		return self._title_bar.logo_button.docked

	@property
	def undocked(self):
		return self._title_bar.logo_button.undocked

	@property
	def title_bar(self):
		return self._title_bar

	@property
	def name(self):
		return self._name

	@property
	def title(self):
		return self._title

	@property
	def parent_container(self):
		return self._parent_container

	def setup_ui(self):
		"""
		Function that can be overriden to add custom widgets and layouts.
		"""

		pass

	def setup_signals(self):
		"""
		Function that can be overriden to setup widget signals.
		"""

		pass

	def show(self, move=None):
		"""
		Overrides base show function to show parent container.

		:param bool move: whether to move window to specific location.
		"""

		self._parent_container.show()
		result = super().show()
		if move is not None:
			self.move(move)
		else:
			self._move_to_init_pos()

		return result

	def hide(self):
		"""
		Overrides base hide function to hide parent container.
		"""

		self._parent_container.hide()
		return super().hide()

	def keyPressEvent(self, event):
		"""
		Overrides key press event function.
		"""

		if self._overlay and event.modifiers() == Qt.AltModifier:
			self._overlay.show()

		return super().keyPressEvent(event)

	def main_layout(self) -> QLayout:
		"""
		Returns window main content layouts instance.

		:return: contents layout.
		:rtype: QLayout
		..note:: if not layout exists, a new one will be created.
		"""

		if self._main_contents.layout() is None:
			self._main_contents.setLayout(layouts.vertical_layout())

		return self._main_contents.layout()

	def set_main_layout(self, layout: QLayout):
		"""
		Sets main window layout.

		:param QLayout layout: main window contents layout.
		"""

		self._main_contents.setLayout(layout)

	def set_title(self, title):
		"""
		Sets title text.

		:param str title: title.
		"""

		self._title_bar.set_title_text(title)
		self._title = title
		super().setWindowTitle(title)

	def set_resizable(self, flag):
		"""
		Sets whether window is resizable.

		:param bool flag: True to make window resizable; False otherwise.
		"""

		self._window_resizer.set_enabled(flag)

	def set_default_stylesheet(self):
		"""
		Tries to set the default stylesheet for this window.
		"""

		try:
			core_interface = core_interfaces.theme_preference_interface()
			result = core_interface.stylesheet()
			self.setStyleSheet(result.data)
		except ImportError as exc:
			print('Error while setting default stylesheet ...')
			print(exc)

	def center_to_parent(self):
		"""
		Centers container to parent.
		"""

		qtutils.update_widget_sizes(self._parent_container)
		size = self.rect().size()
		if self._parent:
			widget_center = qtutils.get_widget_center(self._parent)
			pos = self._parent.pos()
		else:
			widget_center = qtutils.get_current_screen_geometry()
			pos = QPoint(0, 0)

		self._parent_container.move(widget_center + pos - QPoint(size.width() / 2, size.height() / 3))

	def is_minimized(self):
		"""
		Returns whether window is minimized.

		:return: True if window is minimized; False otherwise.
		:rtype: bool
		"""

		return self._minimized

	def set_minimize_enabled(self, flag):
		"""
		Sets whether window can be minimized.

		:param bool flag: Turn to enable minimize functionality; False otherwise.
		"""

		self._minimize_enabled = flag

	def is_movable(self):
		"""
		Returns whether window is movable.

		:return: True if window is movable; False otherwise.
		:rtype: bool
		"""

		return self._title_bar.move_enabled

	def set_movable(self, flag):
		"""
		Sets whether window is movable.

		:param bool flag: True to make window movable; False otherwise.
		"""

		self._title_bar.move_enabled = flag

	def is_docked(self):
		"""
		Returns whether window is docked.

		:return: True if window is docked; False otherwise.
		:rtype: bool
		"""

		return self._parent_container.is_docking_container()

	def minimize(self):
		"""
		Minimizes UI.
		"""

		if not self._minimize_enabled:
			return

		self._saved_size = self.window().size()
		self._set_ui_minimized(True)
		qtutils.process_ui_events()
		qtutils.single_shot_timer(lambda: self.window().resize(dpi.dpi_scale(BaseWindow.MINIMIZED_WIDTH), 0))

	def maximize(self):
		"""
		Maximizes UI.
		"""

		self._set_ui_minimized(False)
		self.window().resize(self._saved_size)

	def title_style(self):
		"""
		Returns current title style.

		:return: title style.
		:rtype: int
		"""

		return self._title_bar.title_style()

	def set_title_style(self, title_style):
		"""
		Sets title style.

		:param int title_style: title style.
		"""

		self._title_bar.set_title_style(title_style)

	def set_minimize_button_visible(self, flag):
		"""
		Sets whether minimize button is visible.

		:param bool flag: True to make minimize button visible; False otherwise.
		"""

		self._title_bar.set_minimize_button_visible(flag)

	def set_maximize_button_visible(self, flag):
		"""
		Sets whether minimize button is visible.

		:param bool flag: True to make maximize button visible; False otherwise.
		"""

		self._title_bar.set_maximize_button_visible(flag)

	def attach_to_frameless_window(self, save_window_pref=True):
		"""
		Attaches this widget to a frameless window.

		:param bool save_window_pref: whether to save window settings.
		:return: frameless window instance.
		:rtype: frameless.FramelessWindow
		"""

		self._parent = self._parent or dcc.get_main_window()
		self._parent_container = frameless.FramelessWindow(
			width=self._init_width, height=self._init_height, save_window_pref=save_window_pref, on_top=self._on_top,
			parent=self._parent)
		self._parent_container.set_widget(self)
		if self._modal:
			self._parent_container.setWindowModality(Qt.ApplicationModal)
		self._move_to_init_pos() if self._init_pos else self.center_to_parent()

		return self._parent_container

	def _setup_ui(self):
		"""
		Internal function that initializes UI.
		"""

		self.attach_to_frameless_window(save_window_pref=self._save_window_pref)
		self._minimized = False
		self._frameless_layout = layouts.grid_layout()
		self._setup_frameless_layout()
		self._window_resizer = frameless.WindowResizer(install_to_layout=self._frameless_layout, parent=self)

		self.set_default_stylesheet()

	def _setup_signals(self):
		"""
		Internal function that initializes window signals.
		"""

		self.docked.connect(self._on_docked)
		self.undocked.connect(self._on_undocked)
		self._title_bar.doubleClicked.connect(self._on_title_bar_double_clicked)

		try:
			theme_interface = core_interfaces.theme_preference_interface()
			theme_interface.updated.connect(self._on_update_theme)
		except Exception:
			pass

	def _setup_frameless_layout(self):
		"""
		Internal function that initializes frameless layout
		"""

		self.setLayout(self._frameless_layout)
		self._main_contents = WindowContents(self)
		self._frameless_layout.setHorizontalSpacing(0)
		self._frameless_layout.setVerticalSpacing(0)
		self._frameless_layout.setContentsMargins(0, 0, 0, 0)
		self._frameless_layout.addWidget(self._title_bar, 1, 1, 1, 1)
		self._frameless_layout.addWidget(self._main_contents, 2, 1, 1, 1)
		self._frameless_layout.setColumnStretch(1, 1)							# title column
		self._frameless_layout.setColumnStretch(2, 1)							# main contents row

	def _move_to_init_pos(self):
		"""
		Internal function that moves widget to the internal initial position.
		"""

		qtutils.update_widget_sizes(self._parent_container)
		self._init_pos = qtutils.contain_widget_in_screen(self, self._init_pos)
		self._parent_container.move(self._init_pos)

	def _set_ui_minimized(self, flag):
		"""
		Internal function that minimizes/maximizes UI.

		:param bool flag: True to minimize UI; False to maximize UI.
		"""

		self._minimized = flag

		if flag:
			if not self._minimize_enabled:
				return
			self._prev_style = self.title_style()
			self.set_title_style(titlebar.TitleBar.TitleStyle.THIN)
			self._main_contents.hide()
			self._title_bar.left_contents.hide()
			self._title_bar.right_contents.hide()
		else:
			self._main_contents.show()
			self.set_title_style(self._prev_style)
			self._title_bar.left_contents.show()
			self._title_bar.right_contents.show()

	def _show_resizers(self):
		"""
		Internal function that show resizers.
		"""

		self._window_resizer.show()

	def _hide_resizers(self):
		"""
		Internal function that hides resizers.
		"""

		self._window_resizer.hide()

	def _on_docked(self, container):
		"""
		Internal callabck function that is called when window is docked.

		:param DockContainer container: dock container instance.
		"""

		if self.is_minimized():
			self._set_ui_minimized(False)

		self.set_movable(False)
		self._hide_resizers()
		self._parent_container = container

	def _on_undocked(self):
		"""
		Internal callback function that is called when window is undocked.
		"""

		self._show_resizers()
		self.set_movable(True)

	def _on_title_bar_double_clicked(self):
		"""
		Internal callback function that is called when title bar is duoble clicked by the user.
		"""

		self.minimize() if not self.is_minimized() else self.maximize()

	def _on_update_theme(self, event):
		"""
		Internal callack function that is called when theme is updated.

		:param ThemeUpdateEvent event: theme event.
		"""

		self.setStyleSheet(event.stylesheet)
