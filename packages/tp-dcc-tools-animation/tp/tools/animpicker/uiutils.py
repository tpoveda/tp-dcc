from __future__ import annotations

import typing
from typing import Callable
from functools import wraps

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.views.viewer import AnimPickerViewerWidget


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
