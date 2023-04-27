#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets related with search functionality
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import Qt, Signal, QSize, QEvent
from Qt.QtWidgets import QWidget, QLineEdit, QStyle

from tp.core import dcc
from tp.common.resources import api as resources
from tp.common.qt import dpi
from tp.common.qt.widgets import layouts, buttons


def search_widget(placeholder_text='', search_line=None, parent=None):
	"""
	Returns widget that allows to do searches within widgets.

	:param str placeholder_text: search placeholder text.
	:param QLineEdit search_line: custom line edit widget to use.
	:param QWidget parent: parent widget.
	:return: search find widget instance.
	:rtype: SearchFindWidget
	"""

	search_widget = SearchFindWidget(search_line=search_line, parent=parent)
	search_widget.set_placeholder_text(str(placeholder_text))

	return search_widget


class SearchFindWidget(QWidget, dpi.DPIScaling):

	textChanged = Signal(str)
	editingFinished = Signal(str)
	returnPressed = Signal()

	def __init__(self, search_line=None, parent=None):
		super().__init__(parent=parent)

		self._search_line = search_line

		self.setLayout(layouts.horizontal_layout(spacing=2, margins=(2, 2, 2, 2)))

		self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

		self._search_line = self._search_line or QLineEdit(parent=self)
		self._search_line.setParent(self)
		self._search_line.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
		self._search_line.installEventFilter(self)

		# NOTE: For some weird reason, in MoBu 2022 style related calls do not work
		# Internal C++ object (PySide2.QtWidgets.QProxyStyle) already deleted.
		if dcc.is_mobu() and dcc.get_version_name() == '2022':
			icon_size = dpi.dpi_scale(14)
		else:
			icon_size = self.style().pixelMetric(QStyle.PM_SmallIconSize)

		self._clear_button = buttons.IconMenuButton(parent=self)
		self._clear_button.setIcon(resources.icon('close'))
		self._clear_button.setIconSize(QSize(icon_size - 6, icon_size - 6))
		self._clear_button.setFixedSize(QSize(icon_size, icon_size))
		self._clear_button.setFocusPolicy(Qt.NoFocus)
		self._clear_button.hide()
		self._search_button = buttons.IconMenuButton(parent=self)
		self._search_button.setAttribute(Qt.WA_TransparentForMouseEvents, True)
		self._search_button.setIcon(resources.icon('search'))
		self._search_button.setIconSize(QSize(icon_size, icon_size))
		self._search_button.setFixedSize(QSize(icon_size, icon_size))
		self._search_button.setEnabled(True)
		self._search_button.setFocusPolicy(Qt.NoFocus)

		self._search_line.setStyleSheet(
			"""
			QLineEdit { padding-left: %spx; padding-right: %spx; border-radius:10px; }
			""" % (self._search_button_padded_width(), self._clear_button_padded_width())
		)

		self.update_minimum_size()

		self.layout().addWidget(self._search_line)

	def setup_signals(self):
		"""
		Function that connects signals for all widget UI widgets.
		"""

		self._search_line.textChanged.connect(self.textChanged.emit)
		self._search_line.textChanged.connect(self.set_text)
		self._clear_button.clicked.connect(self.clear)

	@property
	def search_line(self):
		return self._search_line

	def changeEvent(self, event):
		"""
		Function that overrides base changeEvent function to make sure line edit is properly updated.

		:param QEvent event: Qt event.
		"""

		if event.type() == QEvent.EnabledChange:
			enabled = self.isEnabled()
			self._search_button.setEnabled(enabled)
			self._search_line.setEnabled(enabled)
			self._clear_button.setEnabled(enabled)
		super(SearchFindWidget, self).changeEvent(event)

	def resizeEvent(self, event):
		"""
		Function that overrides base resizeEvent function to make sure that search icons are properly placed.

		:param QEvent event: Qt resize event.
		"""

		if not self._clear_button and self._search_line:
			return
		super(SearchFindWidget, self).resizeEvent(event)
		x = self.width() - self._clear_button_padded_width() * 0.85
		y = (self.height() - self._clear_button.height()) * 0.5
		self._clear_button.move(x - 6, y)
		self._search_button.move(self._search_line_frame_width() * 3, (self.height() - self._search_button.height()) * 0.5)

	def keyPressEvent(self, event):
		"""
		Function that overrides base keyPressEvent function to make sure that line is clared too.

		:param QEvent event: Qt key event.
		"""

		if event.key() == Qt.Key_Escape:
			self.clear()
			self._search_line.clearFocus()
		super(SearchFindWidget, self).keyPressEvent(event)

	def eventFilter(self, widget, event):
		"""
		Overrides base eventFilter function
		:param widget:
		:param event:
		:return:
		"""

		try:
			if widget is self._search_line:
				if event.type() == QEvent.FocusIn:
					self.focusInEvent(event)
				elif event.type() == QEvent.FocusOut:
					self.focusOutEvent(event)
		except AttributeError:
			pass
		return super(SearchFindWidget, self).eventFilter(widget, event)

	def get_text(self):
		if not self._search_line:
			return ''
		return self._search_line.text()

	def set_text(self, text):
		if not (self._clear_button and self._search_line):
			return

		self._clear_button.setVisible(not (len(text) == 0))
		if text != self.get_text():
			self._search_line.setText(text)

	def get_placeholder_text(self):
		if not self._search_line:
			return ''

		return self._search_line.text()

	def set_placeholder_text(self, text):
		if not self._search_line:
			return
		self._search_line.setPlaceholderText(text)

	def set_focus(self, reason=Qt.OtherFocusReason):
		if self._search_line:
			self._search_line.setFocus(reason)
		else:
			self.setFocus(Qt.OtherFocusReason)

	def clear(self):
		if not self._search_line:
			return
		self._search_line.clear()
		self.set_focus()

	def select_all(self):
		if not self._search_line:
			return
		self._search_line.selectAll()

	def update_minimum_size(self):
		self._search_line.setMinimumSize(
			max(
				self._search_line.minimumSizeHint().width(),
				self._clear_button_padded_width() + self._search_button_padded_width()),
			max(
				self._search_line.minimumSizeHint().height(),
				max(self._clear_button_padded_width(), self._search_button_padded_width()))
		)

	def _search_line_frame_width(self):
		# NOTE: For some weird reason, in MoBu 2022 style related calls do not work
		# Internal C++ object (PySide2.QtWidgets.QProxyStyle) already deleted.
		if dcc.is_mobu() and dcc.get_version_name() == '2022':
			return 2
		else:
			return self._search_line.style().pixelMetric(QStyle.PM_DefaultFrameWidth)

	def _clear_button_padded_width(self):
		return self._clear_button.width() + self._search_line_frame_width() * 2

	def _clear_button_padded_height(self):
		return self._clear_button.height() + self._search_line_frame_width() * 2

	def _search_button_padded_width(self):
		return self._search_button.width() + 2 + self._search_line_frame_width() * 3

	def _search_button_padded_height(self):
		return self._search_button.height() + self._search_line_frame_width() * 2
