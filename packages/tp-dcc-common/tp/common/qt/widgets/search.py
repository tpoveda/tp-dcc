#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets related with search functionality
"""

from __future__ import annotations

from typing import Tuple

from overrides import override
from Qt.QtCore import Qt, Signal, QObject, QSize, QEvent
from Qt.QtWidgets import QWidget, QLabel, QLineEdit, QToolButton, QStyle
from Qt.QtGui import QIcon, QPixmap, QResizeEvent, QKeyEvent, QFocusEvent

from tp.core import dcc
from tp.common.resources import api as resources
from tp.common.qt import consts, dpi
from tp.common.qt.widgets import layouts, buttons, comboboxes
from tp.preferences.interfaces import core


def search_widget(
		placeholder_text: str = '', search_line: QLineEdit | None = None, parent: QWidget | None = None) -> SearchFindWidget:
	"""
	Returns widget that allows to do searches within widgets.

	:param str placeholder_text: search placeholder text.
	:param QLineEdit search_line: custom line edit widget to use.
	:param QWidget parent: parent widget.
	:return: search find widget instance.
	:rtype: SearchFindWidget
	"""

	new_widget = SearchFindWidget(search_line=search_line, parent=parent)
	new_widget.set_placeholder_text(str(placeholder_text))

	return new_widget


class SearchFindWidget(QWidget, dpi.DPIScaling):

	textChanged = Signal(str)
	editingFinished = Signal(str)
	returnPressed = Signal()

	def __init__(self, search_line: QLineEdit | None = None, parent: QWidget | None = None):
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
		if dcc.is_mobu() and dcc.version_name() == '2022':
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

	@override
	def changeEvent(self, event: QEvent) -> None:
		"""
		Function that overrides base changeEvent function to make sure line edit is properly updated.

		:param QEvent event: Qt event.
		"""

		try:
			if event.type() == QEvent.EnabledChange:
				enabled = self.isEnabled()
				self._search_button.setEnabled(enabled)
				self._search_line.setEnabled(enabled)
				self._clear_button.setEnabled(enabled)
		except AttributeError:
			pass
	# 	super().changeEvent(event)

	@override
	def resizeEvent(self, event: QResizeEvent) -> None:
		"""
		Function that overrides base resizeEvent function to make sure that search icons are properly placed.

		:param QEvent event: Qt resize event.
		"""

		if not self._clear_button and self._search_line:
			return

		super().resizeEvent(event)

		x = self.width() - self._clear_button_padded_width() * 0.85
		y = (self.height() - self._clear_button.height()) * 0.5
		self._clear_button.move(int(x - 6), int(y))
		self._search_button.move(
			self._search_line_frame_width() * 3, int((self.height() - self._search_button.height()) * 0.5))

	@override
	def keyPressEvent(self, event: QKeyEvent) -> None:
		"""
		Function that overrides base keyPressEvent function to make sure that line is clared too.

		:param QEvent event: Qt key event.
		"""

		if event.key() == Qt.Key_Escape:
			self.clear()
			self._search_line.clearFocus()
		super().keyPressEvent(event)

	@override
	def eventFilter(self, watched: QObject, event: QEvent) -> bool:
		"""
		Overrides base eventFilter function
		:param QObject watched: watched object.
		:param QEvent event: event.
		:return:
		"""

		try:
			if watched is self._search_line:
				if event.type() == QEvent.FocusIn:
					self.focusInEvent(event)
				elif event.type() == QEvent.FocusOut:
					self.focusOutEvent(event)
		except AttributeError:
			pass
		return super().eventFilter(watched, event)

	def get_text(self) -> str:
		"""
		Returns current search text.

		:return: search text.
		:rtype: str
		"""

		if not self._search_line:
			return ''
		return self._search_line.text()

	def set_text(self, text: str):
		"""
		Sets current search text.
		:param str text: search text.
		"""

		if not (self._clear_button and self._search_line):
			return

		self._clear_button.setVisible(not (len(text) == 0))
		if text != self.get_text():
			self._search_line.setText(text)

	def get_placeholder_text(self) -> str:
		"""
		Returns current search line edit placeholder text.

		:return: placeholder text.
		:rtype: str
		"""

		if not self._search_line:
			return ''

		return self._search_line.text()

	def set_placeholder_text(self, text: str):
		"""
		Sets search line edit placeholder text.

		:param str text: placeholder text.
		"""

		if not self._search_line:
			return
		self._search_line.setPlaceholderText(text)

	def set_focus(self, reason: Qt.FocusReason = Qt.OtherFocusReason):
		"""
		Sets the focus reason for the search line edit.

		:param Qt.FocusReason reason: focus reason flag.
		"""

		if self._search_line:
			self._search_line.setFocus(reason)
		else:
			self.setFocus(Qt.OtherFocusReason)

	def clear(self, focus: bool = True):
		"""
		Clear search line edit text.

		:param bool focus: whether to focus line edit widget after clearing it.
		"""

		if not self._search_line:
			return
		self._search_line.clear()
		if focus:
			self.set_focus()

	def select_all(self):
		"""
		Selects all search line edit text.
		"""

		if not self._search_line:
			return
		self._search_line.selectAll()

	def update_minimum_size(self):
		"""
		Updates the minimum size of the search line edit widget.
		"""

		self._search_line.setMinimumSize(
			max(
				self._search_line.minimumSizeHint().width(),
				self._clear_button_padded_width() + self._search_button_padded_width()),
			max(
				self._search_line.minimumSizeHint().height(),
				max(self._clear_button_padded_width(), self._search_button_padded_width()))
		)

	def _search_line_frame_width(self) -> int:
		"""
		Internal function that returns the search line widget frame width.

		:return: search line edit frame width.
		:rtype: int
		"""

		# NOTE: For some weird reason, in MoBu 2022 style related calls do not work
		# Internal C++ object (PySide2.QtWidgets.QProxyStyle) already deleted.
		if dcc.is_mobu() and dcc.version_name() == '2022':
			return 2
		else:
			return self._search_line.style().pixelMetric(QStyle.PM_DefaultFrameWidth)

	def _clear_button_padded_width(self) -> int:
		"""
		Internal function that returns clear button padded width.

		:return: clear button padded width.
		:rtype: int
		"""

		return self._clear_button.width() + self._search_line_frame_width() * 2

	def _clear_button_padded_height(self) -> int:
		"""
		Internal function that returns clear button padded height.

		:return: clear button padded height.
		:rtype: int
		"""

		return self._clear_button.height() + self._search_line_frame_width() * 2

	def _search_button_padded_width(self) -> int:
		"""
		Internal function that returns search button padded width.

		:return: search button padded width.
		:rtype: int
		"""

		return self._search_button.width() + 2 + self._search_line_frame_width() * 3

	def _search_button_padded_height(self) -> int:
		"""
		Internal function that returns search button padded width.

		:return: search button padded width.
		:rtype: int
		"""

		return self._search_button.height() + self._search_line_frame_width() * 2


class ClearToolButton(QToolButton):
	"""
	For CSS purposes only
	"""

	pass


class SearchToolButton(QToolButton):
	"""
	For CSS purposes only
	"""

	pass


class SearchLineEdit(QLineEdit, dpi.DPIScaling):
	"""
	Custom line edit widget with two icons to search and clear.
	"""

	textCleared = Signal()

	def __init__(
			self, search_pixmap: QPixmap | None = None, clear_pixmap: QPixmap | None = None,
			icons_enabled: bool = True, parent: QWidget | None = None):
		super().__init__(parent)

		self._icons_enabled = icons_enabled
		self._theme_pref = core.theme_preference_interface()
		self._background_color = None

		clear_pixmap = clear_pixmap or resources.pixmap('close', size=dpi.dpi_scale(16), color=(128, 128, 128))
		search_pixmap = search_pixmap or resources.pixmap('search', size=dpi.dpi_scale(16), color=(128, 128, 128))
		self._clear_button = ClearToolButton(parent=self)
		self._clear_button.setIcon(QIcon(clear_pixmap))
		self._search_button = SearchToolButton(parent=self)
		self._search_button.setIcon(search_pixmap)

		self._setup_ui()

		self._theme_pref.updated.connect(self._on_theme_updated)

	@override
	def resizeEvent(self, event: QResizeEvent) -> None:
		if not self._icons_enabled:
			super().resizeEvent(event)
			return

		size = self._clear_button.sizeHint()
		frame_width = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
		rect = self.rect()
		y_pos = int(abs(rect.bottom() - size.height()) * 0.5 + dpi.dpi_scale(1))
		self._clear_button.move(self.rect().right() - frame_width - size.width(), y_pos - 2)
		self._search_button.move(self.rect().left() + dpi.dpi_scale(1), y_pos)
		self._update_stylesheet()

	@override
	def focusInEvent(self, arg__1: QFocusEvent) -> None:
		super().focusInEvent(arg__1)

		# We do not want search widgets to be the first focus on window activate.
		if arg__1.reason() == Qt.FocusReason.ActiveWindowFocusReason:
			self.clearFocus()

	def set_background_color(self, color: Tuple[int, int, int]):
		"""
		Sets the background color.

		:param Tuple[int, int, int] color: background color.
		"""

		self._background_color = color
		self.set_icons_enabled(self._icons_enabled)

	def set_icons_enabled(self, flag: bool):
		"""
		Sets whether icons are enabled.

		:param bool flag: True to enable icons; False to hide them.
		"""

		if self._icons_enabled:
			frame_width = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
			self._update_stylesheet()
			min_size = self.minimumSizeHint()
			self.setMinimumSize(
				max(min_size.width(), self._search_button.sizeHint().width() + self._clear_button.sizeHint().width() + frame_width * 2 + 2),
				max(min_size.height(), self._clear_button.sizeHint().height() + frame_width * 2 + 2)
			)
		else:
			self._search_button.hide()
			self._clear_button.hide()
			self.setStyleSheet('')

		self._icons_enabled = flag

	def _setup_ui(self):
		"""
		Setup widgets.
		"""

		self._clear_button.setCursor(Qt.ArrowCursor)
		self._clear_button.setStyleSheet('QToolButton {border: none; padding: 1px;}')
		self._clear_button.hide()
		self._clear_button.clicked.connect(self.clear)
		self.textChanged.connect(self._on_text_changed)
		self._search_button.setStyleSheet('QToolButton {border: none; padding: 1px;}')
		self.set_icons_enabled(self._icons_enabled)
		self.setProperty('clearFocus', True)

	def _update_stylesheet(self):
		"""
		Internal function that updates widget stylesheet.
		"""

		if self._background_color is None:
			self._background_color = self._theme_pref.TEXT_BOX_BG_COLOR
		background_color = str(self._background_color) if self._background_color is not None else ''

		background_style = f'background-color: rgba{background_color}'
		frame_width = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
		top_pad = 0 if self.height() < dpi.dpi_scale(25) else -2 if dpi.dpi_multiplier() == 1.0 else 0
		self.setStyleSheet(
			'QLineEdit {{ padding-left: {}px; padding-right: {}px; {}; padding-top: {}px; }}'.format(
				self._search_button.sizeHint().width() + frame_width + dpi.dpi_scale(1),
				self._clear_button.sizeHint().width() + frame_width + dpi.dpi_scale(1),
				background_style, top_pad))

	def _on_theme_updated(self, event: 'ThemeUpdateEvent'):
		"""
		Internal callback function that is called each time theme is updated.

		:param ThemeUpdateEvent event: theme update event.
		"""

		self._background_color = event.theme_dict.TEXT_BOX_BG_COLOR
		self._update_stylesheet()

	def _on_text_changed(self, text: str):
		"""
		Internal callback function that is called each time search text changes.

		:param str text: search text.
		"""

		self._clear_button.setVisible(True if text and self._icons_enabled else False)


class ViewSearchWidget(QWidget):
	"""
	Custom search widget intended to be used by column-row views such as table views.
	"""

	columnVisibilityIndexChanged = Signal(int, int)
	columnFilterIndexChanged = Signal(str)
	searchTextChanged = Signal(str)
	searchTextCleared = Signal()

	def __init__(self, show_column_visibility_box: bool = True, parent: QWidget | None = None):
		super().__init__(parent=parent)

		self._search_box_label = QLabel('Search By:', parent=self)
		self._search_header_box = comboboxes.combobox(parent=self)
		self._search_widget = SearchLineEdit(parent=self)
		self._search_widget.setMaximumHeight(self._search_header_box.size().height())

		self._column_visibility_box = None
		if show_column_visibility_box:
			self._column_visibility_box = comboboxes.combobox(parent=self)
			self._column_visibility_box.setMinimumWidth(100)
			self._column_visibility_box.checkStateChanged.connect(self._on_column_visibility_changed)

		self._search_layout = layouts.vertical_layout(spacing=consts.SMALL_SPACING, margins=(0, 0, 0, 0), parent=self)
		if self._column_visibility_box is not None:
			self._search_layout.addWidget(self._column_visibility_box)
		self._search_layout.addWidget(self._search_box_label)
		self._search_layout.addWidget(self._search_header_box)
		self._search_layout.addWidget(self._search_widget)

		self._search_header_box.itemSelected.connect(self.columnFilterIndexChanged.emit)
		self._search_widget.textCleared.connect(self.searchTextCleared.emit)
		self._search_widget.textChanged.connect(self.searchTextChanged.emit)

	def set_header_visibility(self, flag: bool):
		"""
		Sets header widgets visibility.

		:param bool flag: True to show header widgets; False to hide them.
		"""

		self._search_header_box.hide() if not flag else self._search_header_box.show()
		self._search_box_label.hide() if not flag else self._search_box_label.show()

	def set_header_items(self, items: list[str]):
		"""
		Sets the items for the hader.

		:param list[str] items: list of header item names.
		"""

		self._search_header_box.clear()
		for i in items:
			self._search_header_box.addItem(i, is_checkable=False)

	def set_visibility_items(self, items: list[str]):
		"""
		Sets the items to show within the column visibility combo box.

		:param list[str] items: list of visibility items to set.
		"""

		if not self._column_visibility_box:
			return
		self._column_visibility_box.clear()
		for item in items:
			self._column_visibility_box.addItem(item, is_checkable=True)

	def _on_column_visibility_changed(self, index: int, state: Qt.CheckState):
		"""
		Internal callback function that is called each time column visibility combobox item check state changes.

		:param int index: index of the combo box item which its visibility has changed.
		:param Qt.CheckState state: new check state.
		"""

		self.columnVisibilityIndexChanged.emit(index, state)
