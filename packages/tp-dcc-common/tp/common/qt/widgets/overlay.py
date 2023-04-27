#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that includes classes to create overlay widgets
"""

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QApplication, QDialog, QHBoxLayout

from tp.common.qt import qtutils


class OverlayWidget(QDialog):

	widgetMousePress = Signal(object)
	widgetMouseMove = Signal(object)
	widgetMouseRelease = Signal(object)

	PRESSED = False
	OVERLAY_ACTIVE_KEY = Qt.AltModifier

	def __init__(self, parent, layout_class=QHBoxLayout):
		super().__init__(parent=parent)

		self._layout = layout_class(self)
		self._debug = False
		self.setup_ui(layout_class)

	def setup_ui(self, layout_class):
		if qtutils.is_pyside2() or qtutils.is_pyqt5():
			self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
		else:
			self.setWindowFlags(Qt.FramelessWindowHint)
		self.setMouseTracking(True)
		self.update()
		self.setStyleSheet('background-color: transparent;')

		self.main_layout = layout_class()
		self.setLayout(self.main_layout)

	def update(self):
		self.setGeometry(0, 0, self.parent().geometry().width(), self.parent().geometry().height())
		super(OverlayWidget, self).update()

	def enterEvent(self, event):
		"""
		Overrides base QDialog enterEvent function.
		On mouse enter, check if it is pressed

		:param Qt.Event event: Qt enter event.
		"""

		if not self.PRESSED:
			self.hide()

		event.ignore()

	def mousePressEvent(self, event):
		"""
		Overrides base QDialog mousePressEvent function.
		Send events back down to parent.

		:param QEvent event: Qt mouse press event.
		"""

		if not QApplication.keyboardModifiers() == self.OVERLAY_ACTIVE_KEY:
			event.ignore()
			return

		self.widgetMousePress.emit(event)
		self.PRESSED = True
		self.update()

	def mouseMoveEvent(self, event):
		"""
		Overrides base QDialog mouseMoveEvent function.

		:param QEvent event: Qt mouse move evente.
		"""

		pass

	def mouseReleaseEvent(self, event):
		"""
		Overrides base QDialog mouseReleaseEvent function.
		Send events back down to parent

		:param QEvent event: Qt mouse release event.
		:return:
		"""
		self.widgetMouseRelease.emit(event)
		self.PRESSED = False
		self.update()

	def keyReleaseEvent(self, event):
		"""
		Overrides base QDialog keyReleaseEvent function.

		:param QEvent event: Qt key release event.
		:return:
		"""

		self.hide()

	def show(self, *args, **kwargs):
		"""
		Overrides base QDialog show function.
		:return:
		"""

		self.PRESSED = True
		super().show(*args, **kwargs)
		self.update()

	def set_debug_mode(self, debug):
		"""
		Debug mode to show where the dialog window is. Turns the window a transparent red

		:param bool debug:: whether loading debug mode is enabled.
		"""
		self._debug = debug
		if debug:
			self.setStyleSheet("background-color: #88ff0000;")
		else:
			self.setStyleSheet("background-color: transparent;")
