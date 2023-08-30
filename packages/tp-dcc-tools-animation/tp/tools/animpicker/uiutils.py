from __future__ import annotations

import time
import queue
import typing
import hashlib
import urllib.parse
from typing import Callable
from functools import wraps

from overrides import override

from tp.core import log
from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.views.viewer import AnimPickerViewerWidget

logger = log.animLogger


def set_button_color(button: qt.QPushButton, r: float, g: float, b: float):
	"""
	Sets the color of the given button.

	:param qt.QPushButton button: button instance to set color of.
	:param float r: red color channel.
	:param float g: green color channel.
	:param float b: blue color channel.
	"""

	palette = button.palette()
	palette.setColor(qt.QPalette.Button, qt.QColor.fromRgbF(r, g, b))
	palette.setColor(qt.QPalette.Window, qt.QColor.fromRgbF(r, g, b))
	palette.setColor(qt.QPalette.ButtonText, qt.QColor(qt.Qt.black))
	button.setPalette(palette)


def scene_exists(fn: Callable) -> Callable:
	"""
	Decorator function that checks whether the scene where picker items should be placed exists. If that's the case
	the function is executed.

	:param Callable fn: function to call
	:return: wrapped function.
	:rtype: Callable
	"""

	@wraps(fn)
	def wrapper(*args):
		widget = args[0]			# type: AnimPickerViewerWidget
		scene = widget.tab_widget.current_scene()
		return fn(*(args + (scene,))) if scene else None

	return wrapper


def generate_hash_code(item: qt.QGraphicsItem) -> str:
	"""
	Generates a new hash code for given graphics item.

	:param qt.QGraphicsItem item: item we want to generate hash code for.
	:return: generated hash code.
	:rtype: str
	"""

	pos = item.pos()
	digest = hashlib.sha224(f'{time.time()}{pos.x()}{pos.y()}'.encode('utf-8')).hexdigest()[:10]
	return urllib.parse.quote_plus(digest)


def warning(msg: str, parent: qt.QWidget | None = None) -> bool:
	"""
	Shows a warning message.

	:param str msg: warning message.
	:param qt.QWidget or None parent: message box parent.
	:return: non-valid operation status.
	:rtype: bool
	"""

	logger.warning(msg)
	qt.QMessageBox.warning(parent, 'Warning', msg)
	return False


class ThreadDispatcher(qt.QThread):

	class _Event(qt.QEvent):
		EVENT_TYPE = qt.QEvent.Type(qt.QEvent.registerEventType())
		def __init__(self, callback):
			super().__init__(ThreadDispatcher._Event.EVENT_TYPE)
			self.callback = callback

	def __init__(self, parent: qt.QWidget):
		super().__init__()

		self.idle_loop = queue.Queue()
		self.parent = parent

	@override
	def run(self) -> None:
		while True:
			callback = self.idle_loop.get()
			if callback is None:
				break
			qt.QApplication.postEvent(self.parent, ThreadDispatcher._Event(callback))

	def stop(self):
		self.idle_loop.put(None)
		self.wait()

	def idle_add(self, func, *args, **kwargs):

		def idle():
			func(*args, **kwargs)
			return False

		self.idle_loop.put(idle)
		if not self.isRunning():
			self.start()
