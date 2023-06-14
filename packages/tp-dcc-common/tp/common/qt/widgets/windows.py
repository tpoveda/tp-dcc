from __future__ import annotations

import sys
from multiprocessing import Process

from overrides import override
from Qt.QtCore import QEvent
from Qt.QtWidgets import QApplication, QWidget

from tp.core.abstract import window
from tp.common.python import decorators, win32
from tp.common.qt import qtutils


class StandaloneWindow(window.AbstractWindow):
	"""
	Window intended to be used in standalone Python applications.
	"""

	class MultiAppLaunch(Process):
		"""
		Launch multiple QApplications in separated processes
		"""

		def __init__(self, cls, *args, **kwargs):
			self.cls = cls
			self.args = args
			self.kwargs = kwargs
			super().__init__()

		@override
		def run(self) -> None:
			"""
			Launches the app once the process has started.
			"""

			try:
				app = QApplication(sys.argv)
			except RuntimeError:
				app = QApplication.instance()
			new_window = super(StandaloneWindow, self.cls).show(*self.args, **self.kwargs)
			if isinstance(app, QApplication):
				app.setActiveWindow(new_window)
			sys.exit(app.exec_())

	def __init__(self, parent: QWidget | None = None):
		super().__init__(parent)

		self._standalone = True

	@classmethod
	@override
	def clear_window_instance(cls, window_id: str) -> dict:
		previous_instance = super(StandaloneWindow, cls).clear_window_instance(window_id)
		if previous_instance is None:
			return

		if not previous_instance['window'].is_closed():
			try:
				previous_instance['window'].close()
			except (RuntimeError, ReferenceError):
				pass

		return previous_instance

	@decorators.HybridMethod
	@override(check_signature=False)
	def show(cls, self, *args, **kwargs) -> StandaloneWindow:

		if self is not cls:
			return super(StandaloneWindow, self).show()

		# Open a new window
		instance = kwargs.pop('instance', False)
		exec_ = kwargs.pop('exec_', True)

		new_window = None
		try:
			app = QApplication(sys.argv)
			new_window = super(StandaloneWindow, cls).show(*args, **kwargs)
			if isinstance(app, QApplication):
				app.setActiveWindow(new_window)
		except RuntimeError:
			if instance:
				app = QApplication.instance()
				new_window = super(StandaloneWindow, cls).show(*args, **kwargs)
				if isinstance(app, QApplication):
					app.setActiveWindow(new_window)
				if exec_:
					app.exec_()
			else:
				StandaloneWindow.MultiAppLaunch(cls, *args, **kwargs).start()
		else:
			if exec_:
				sys.exit(app.exec_())

		return new_window

	@override
	def closeEvent(self, event: QEvent):
		"""
		Overrides closeEvent function to save the window location on window close.

		:param QEvent event: Qt event.
		"""

		self.save_window_position()
		self.clear_window_instance(self.ID)
		return super(StandaloneWindow, self).closeEvent(event)

	@override
	def save_window_position(self, settings_path: str | None = None):
		if 'standalone' not in self._window_settings:
			self._window_settings['standalone'] = dict()
		settings = self._window_settings['standalone']

		key = self._get_settings_key()
		if key not in settings:
			settings[key] = dict()

		settings[key]['width'] = self.width()
		settings[key]['height'] = self.height()
		settings[key]['x'] = self.x()
		settings[key]['y'] = self.y()

		return super(StandaloneWindow, self).save_window_position()

	@override
	def load_window_position(self):
		key = self._get_settings_key()
		try:
			x = self._window_settings['standalone'][key]['x']
			y = self._window_settings['standalone'][key]['y']
			width = self._window_settings['standalone'][key]['width']
			height = self._window_settings['standalone'][key]['height']
		except KeyError:
			super(StandaloneWindow, self).load_window_position()
		else:
			x, y = win32.set_coordinates_to_screen(x, y, width, height, padding=5)
			self.resize(width, height)
			self.move(x, y)

	@override
	def window_palette(self) -> str | None:
		current_palette = super(StandaloneWindow, self).window_palette()
		if current_palette is None:
			if qtutils.is_pyside() or qtutils.is_pyqt4():
				return 'Qt.4'
			elif qtutils.is_pyside2() or qtutils.is_pyqt5():
				return 'Qt.5'

		return current_palette

	@override(check_signature=False)
	def set_window_palette(self, name: str, version: int | None, style: bool = True, force: bool = False):
		"""
		Sets the palette of the window. If the window is parented to another StandaloneWindow, then skip to avoid
		overriding its color scheme.

		:param str name: name of the paelette to set.
		:param int or None version: optional palette version to set.
		:param bool style: whether to apply style.
		"""

		if not force:
			for widget in QApplication.topLevelWidgets():
				if widget != self and isinstance(widget, window.AbstractWindow) and not widget.is_instance():
					return

		super(StandaloneWindow, self).set_window_palette(name, version=version, style=style)
