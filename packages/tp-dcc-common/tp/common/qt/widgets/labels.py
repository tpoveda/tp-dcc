#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that extends default Qt labels (QLabel) functionality
"""

from __future__ import annotations

from typing import Any

from overrides import override

from Qt.QtCore import Qt, Property, Signal
from Qt.QtWidgets import QWidget, QLabel, QSizePolicy, QStyleOption
from Qt.QtGui import QIcon, QPainter, QMouseEvent, QResizeEvent, QPaintEvent

from tp.common.qt import dpi
from tp.common.qt.widgets import layouts


def label(
		text: str = '', tooltip: str = '', status_tip: str | None = None, upper: bool = False, bold: bool = False,
		alignment: Qt.AlignmentFlag | None = None, elide_mode: Qt.TextElideMode = Qt.ElideNone,
		min_width: int | None = None, max_width: int | None = None, properties: list[tuple[str, Any]] | None = None,
		parent: QWidget | None = None) -> BaseLabel:
	"""
	Creates a new label widget.

	:param str text: label text.
	:param str tooltip: optional label tooltip.
	:param str tooltip: optional label status tip.
	:param bool upper: whether label text is forced to be uppercase.
	:param bool bold: whether label font is bold.
	:param Qt.AlignFlag or None alignment: optional aligment flag for the label.
	:param Qt.TextElideMode elide_mode: whether label text should elide.
	:param int or None min_width: optional minimum width for the label.
	:param int or None max_width: optional maximum width for the label.
	:param list[tuple[str, Any]] or None properties: optional dynamic properties to add to the label.
	:param str or None tooltip: optional label tooltip.
	:param str or None status_tip: optional status tip.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	new_label = BaseLabel(
		text=text, tooltip=tooltip, status_tip=status_tip, bold=bold, upper=upper, elide_mode=elide_mode, parent=parent)
	if min_width is not None:
		new_label.setMinimumWidth(min_width)
	if max_width is not None:
		new_label.setMaximumWidth(max_width)

	if alignment:
		new_label.setAlignment(alignment)

	if properties:
		for name, value in properties:
			new_label.setProperty(name, value)

	return new_label


def h1_label(
		text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
		elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
		parent: QWidget | None = False) -> BaseLabel:
	"""
	Creates a new H1 label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether label text is forced to be uppercase.
	:param bool bold: whether label font is bold.
	:param Qt.TextElideMode elide_mode: whether label text should elide.
	:param int or None min_width: optional minimum width for the label.
	:param int or None max_width: optional maximum width for the label.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	return label(
		text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
		max_width=max_width, parent=parent).h1()


def h2_label(
		text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
		elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
		parent: QWidget | None = False) -> BaseLabel:
	"""
	Creates a new H2 label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether label text is forced to be uppercase.
	:param bool bold: whether label font is bold.
	:param Qt.TextElideMode elide_mode: whether label text should elide.
	:param int or None min_width: optional minimum width for the label.
	:param int or None max_width: optional maximum width for the label.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	return label(
		text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
		max_width=max_width, parent=parent).h2()


def h3_label(
		text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
		elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
		parent: QWidget | None = False) -> BaseLabel:
	"""
	Creates a new H3 label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether label text is forced to be uppercase.
	:param bool bold: whether label font is bold.
	:param Qt.TextElideMode elide_mode: whether label text should elide.
	:param int or None min_width: optional minimum width for the label.
	:param int or None max_width: optional maximum width for the label.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	return label(
		text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
		max_width=max_width, parent=parent).h3()


def h4_label(
		text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
		elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
		parent: QWidget | None = False) -> BaseLabel:
	"""
	Creates a new H4 label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether label text is forced to be uppercase.
	:param bool bold: whether label font is bold.
	:param Qt.TextElideMode elide_mode: whether label text should elide.
	:param int or None min_width: optional minimum width for the label.
	:param int or None max_width: optional maximum width for the label.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	return label(
		text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
		max_width=max_width, parent=parent).h4()


def h5_label(
		text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
		elide_mode: Qt.TextElideMode = Qt.ElideNone, min_width: int | None = None, max_width: int | None = None,
		parent: QWidget | None = False) -> BaseLabel:
	"""
	Creates a new H5 label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether label text is forced to be uppercase.
	:param bool bold: whether label font is bold.
	:param Qt.TextElideMode elide_mode: whether label text should elide.
	:param int or None min_width: optional minimum width for the label.
	:param int or None max_width: optional maximum width for the label.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	return label(
		text=text, tooltip=tooltip, upper=upper, bold=bold, elide_mode=elide_mode, min_width=min_width,
		max_width=max_width, parent=parent).h5()


def clipped_label(
		text: str = '', width: int = 0, elide: bool = True, always_show_all: bool = False,
		parent: QWidget | None = None) -> ClippedLabel:
	"""
	Custom QLabel that clips itself if the widget width is smaller than the text.

	:param str text: label text.
	:param int width: minimum width.
	:param bool elide: whether to elide label.
	:param bool always_show_all: force the label to show the complete text or hide the complete text.
	:param QWidget parent: parent widget.
	:return: new clipped label widget instance.
	:rtype: ClippedLabel
	"""

	return ClippedLabel(text=text, width=width, elide=elide, always_show_all=always_show_all, parent=parent)


def icon_label(
		icon: QIcon, text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
		enable_menu: bool = True, parent: QWidget | None = None) -> IconLabel:
	"""
	Creates a new widget with a horizontal layout with an icon and a label.

	:param QIcon icon: label icon.
	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether label text is forced to be uppercase.
	:param bool bold: whether label font is bold.
	:param bool enable_menu: whether enable label menu.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: IconLabel
	"""

	return IconLabel(icon, text=text, tooltip=tooltip, upper=upper, bold=bold, enable_menu=enable_menu, parent=parent)


class BaseLabel(QLabel, dpi.DPIScaling):
	"""
	Custom QLabel implementation that extends standard Qt QLabel class
	"""

	clicked = Signal()

	class Levels(object):
		"""
		Class that defines different label header levels
		"""

		H1 = 1  # header 1
		H2 = 2  # header 2
		H3 = 3  # header 3
		H4 = 4  # header 4
		H5 = 5  # header 5

	class Types(object):
		"""
		Class that defines different label types
		"""

		SECONDARY = 'secondary'
		WARNING = 'warning'
		DANGER = 'danger'

	def __init__(
			self, text: str = '', tooltip: str = '', status_tip: str = '', upper: bool = False, bold: bool = False,
			enable_menu: bool = True,
			parent: QWidget | None = None, elide_mode: Qt.TextElideMode = Qt.ElideNone):
		text = text.upper() if upper else text
		self._enable_menu = enable_menu
		self._actual_text = text

		super().__init__(text, parent)

		self._type = ''
		self._level = 0
		self._underline = False
		self._mark = False
		self._delete = False
		self._strong = False
		self._code = False
		self._elide_mode = elide_mode

		if tooltip:
			self.setToolTip(tooltip)
		if status_tip:
			self.setStatusTip(status_tip)
		self.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.LinksAccessibleByMouse)
		self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
		self.strong(bold)

	def _get_type(self) -> str:
		"""
		Internal Qt property function that returns label type.

		:return: label type.
		:rtype: str
		"""

		return self._type

	def _set_type(self, value: BaseLabel.Types):
		"""
		Internal Qt property function that sets label type.

		:param str value: label type.
		"""

		self._type = value
		self.style().polish(self)

	def _get_level(self) -> int:
		"""
		Internal Qt property function that returns label level.

		:return: label level.
		:rtype: int
		"""

		return self._level

	def _set_level(self, value: int):
		"""
		Internal Qt property function that sets label level.

		:param int value: label level.
		"""

		self._level = value
		self.style().polish(self)

	def _get_underline(self) -> bool:
		"""
		Internal Qt property function that returns whether label is using an underline style.

		:return: True if labael has underline style; False otherwise.
		:rtype: bool
		"""

		return self._underline

	def _set_underline(self, flag: bool):
		"""
		Internal Qt property function that sets label to use an underline style.

		:param bool flag: underline flag.
		"""

		self._underline = flag
		self.style().polish(self)

	def _get_delete(self) -> bool:
		"""
		Internal Qt property function that returns whether label is using delete style.

		:return: True if the label is using delete style; False otherwise.
		:rtype: bool
		"""

		return self._delete

	def _set_delete(self, flag: bool):
		"""
		Internal Qt property function that sets label to use a delete style.

		:param bool flag: delete flag
		"""

		self._delete = flag
		self.style().polish(self)

	def _get_strong(self) -> bool:
		"""
		Internal Qt property function that returns whether label is using a strong style.

		:return: True if the label has a strong style; False otherwise.
		:type: bool
		"""

		return self._strong

	def _set_strong(self, flag: bool):
		"""
		Internal Qt property function that sets label to use a strong style.

		:param bool flag: strong flag.
		"""

		self._strong = flag
		self.style().polish(self)

	def _get_mark(self) -> bool:
		"""
		Internal Qt property function that returns whether label is using a mark style.

		:return: True if the label has a mark style; False otherwise.
		:rtype: bool
		"""

		return self._mark

	def _set_mark(self, flag: bool):
		"""
		Internal Qt property function that sets label to use a mark style.

		:param bool flag: mark flag.
		"""

		self._mark = flag
		self.style().polish(self)

	def _get_code(self) -> bool:
		"""
		Internal Qt property function that returns whether label is using a code style.

		:return: True if the label has a code style; False otherwise.
		:rtype: bool
		"""

		return self._code

	def _set_code(self, flag: bool):
		"""
		Internal Qt property function that sets label to use a code style.

		:param bool flag: code flag.
		"""

		self._code = flag
		self.style().polish(self)

	def _get_elide_mode(self) -> Qt.TextElideMode:
		"""
		Internal Qt property function that returns which elide mode label is using.

		:return: label elide mode.
		:rtype: Qt.TextElideMode
		"""

		return self._elide_mode

	def _set_elide_mode(self, value: Qt.TextElideMode):
		"""
		Internal Qt property function that sets elide mode used by the label.

		:param Qt.TextElideMode value: elide mode.
		"""

		self._elide_mode = value
		self._update_elided_text()

	theme_type = Property(str, _get_type, _set_type)
	theme_level = Property(int, _get_level, _set_level)
	theme_underline = Property(bool, _get_underline, _set_underline)
	theme_delete = Property(bool, _get_delete, _set_delete)
	theme_mark = Property(bool, _get_mark, _set_mark)
	theme_strong = Property(bool, _get_strong, _set_strong)
	theme_code = Property(bool, _get_code, _set_code)
	theme_elide_mode = Property(bool, _get_elide_mode, _set_elide_mode)

	@override
	def mousePressEvent(self, ev: QMouseEvent) -> None:
		"""
		Overrides mousePressEvent function to emit clicked signal each time user clicks on the label.

		:param QEvent ev: Qt mouse event.
		"""

		self.clicked.emit()
		super().mousePressEvent(ev)

	@override
	def resizeEvent(self, event: QResizeEvent) -> None:
		"""
		Overrides base QObject resizeEvent function.
		"""

		self._update_elided_text()

	@override
	def text(self) -> str:
		"""
		Overrides base QLabel text function.

		:return: str
		"""

		return self._actual_text

	@override
	def setText(self, arg__1: str) -> None:
		"""
		Overrides base QLabel setText function.

		:param str arg__1: label text tos set.
		"""

		self._actual_text = arg__1
		self._update_elided_text()
		self.setToolTip(arg__1)

	def h1(self) -> BaseLabel:
		"""
		Sets label with h1 type.

		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_level = self.Levels.H1

		return self

	def h2(self) -> BaseLabel:
		"""
		Sets label with h2 type.

		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_level = self.Levels.H2

		return self

	def h3(self) -> BaseLabel:
		"""
		Sets label with h3 type.

		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_level = self.Levels.H3

		return self

	def h4(self) -> BaseLabel:
		"""
		Sets label with h4 type.

		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_level = self.Levels.H4

		return self

	def h5(self) -> BaseLabel:
		"""
		Sets label with h4 type.

		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_level = self.Levels.H5

		return self

	def secondary(self) -> BaseLabel:
		"""
		Sets label with secondary type.

		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_type = self.Types.SECONDARY

		return self

	def warning(self) -> BaseLabel:
		"""
		Sets label with warning type.

		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_type = self.Types.WARNING

		return self

	def danger(self) -> BaseLabel:
		"""
		Sets label with danger type.

		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_type = self.Types.DANGER

		return self

	def strong(self, flag: bool = True) -> BaseLabel:
		"""
		Sets label with strong type.

		:param bool flag: whether enable strong mode.
		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_strong = flag

		return self

	def mark(self, flag: bool = True) -> BaseLabel:
		"""
		Sets label with mark type.

		:param bool flag: whether or not enable mar mode.
		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_mark = flag

		return self

	def code(self, flag: bool = True) -> BaseLabel:
		"""
		Sets label with code type.

		:param bool flag: whether or not enable code mode.
		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_code = flag

		return self

	def delete(self, flag: bool = True) -> BaseLabel:
		"""
		Sets label with delete type.

		:param bool flag: whether or not enable delete mode.
		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_delete = flag

		return self

	def underline(self, flag: bool = True) -> BaseLabel:
		"""
		Sets label with underline type.

		:param bool flag: whether or not enable underline mode.
		:return: current label instance.
		:rtype: BaseLabel
		"""

		self.theme_underline = flag

		return self

	def _update_elided_text(self):
		"""
		Internal function that updates the elided text on the label
		"""

		font_metrics = self.fontMetrics()
		elided_text = font_metrics.elidedText(self._actual_text, self._elide_mode, self.width() - 2 * 2)
		super().setText(elided_text)


class ClippedLabel(BaseLabel):
	"""
	Custom QLabel that clips itself if the widget width is smaller than the text.

	:param str text: label text.
	:param int width: minimum width.
	:param bool elipsis: whether label will have ellipsis.
	:param bool always_show_all: force the label to show the complete text or hide the complete text.
	:param QWidget parent: parent widget.
	"""

	_width = _text = _elided = None

	def __init__(self, text='', width=0, elide=True, always_show_all=False, parent=None):
		super(ClippedLabel, self).__init__(text, parent=parent)

		self._always_show_all = always_show_all
		self._elide = elide

		self.setMinimumWidth(width if width > 0 else 1)

	@override
	def paintEvent(self, arg__1: QPaintEvent) -> None:
		painter = QPainter(self)
		self.drawFrame(painter)
		margin = self.margin()
		rect = self.contentsRect()
		rect.adjust(margin, margin, -margin, -margin)
		text = self.text()
		width = rect.width()
		if text != self._text or width != self._width:
			self._text = text
			self._width = width
			self._elided = self.fontMetrics().elidedText(text, Qt.ElideRight, width)

		option = QStyleOption()
		option.initFrom(self)

		if self._always_show_all:
			# show all text or show nothing
			if self._width >= self.sizeHint().width():
				self.style().drawItemText(
					painter, rect, self.alignment(), option.palette,
					self.isEnabled(), self.text(), self.foregroundRole())

		else:  # if alwaysShowAll is false though, draw the ellipsis as normal
			if self._elide:
				self.style().drawItemText(
					painter, rect, self.alignment(), option.palette, self.isEnabled(),
					self._elided, self.foregroundRole())
			else:
				self.style().drawItemText(
					painter, rect, self.alignment(), option.palette, self.isEnabled(),
					self.text(), self.foregroundRole())


class IconLabel(QWidget):
	"""
	Custom widget that contains a horizontal layout with an icon and a label.
	"""

	def __init__(
			self, icon: QIcon, text: str = '', tooltip: str = '', upper: bool = False, bold: bool = False,
			enable_menu: bool = True, parent: QWidget | None = None):
		super().__init__(parent)

		main_layout = layouts.horizontal_layout(
			margins=(0, 0, 0, 0), spacing=dpi.dpi_scale(4), alignment=Qt.AlignLeft, parent=self)
		self.setLayout(main_layout)

		self._label = BaseLabel(
			text=text, tooltip=tooltip, upper=upper, bold=bold, enable_menu=enable_menu, parent=parent)
		icon_size = self._label.sizeHint().height()
		self._icon_pixmap = icon.pixmap(icon_size, icon_size)
		self._icon_label = QLabel(parent=self)
		self._icon_label.setPixmap(self._icon_pixmap)

		main_layout.addWidget(self._icon_label)
		main_layout.addWidget(self._label)
		main_layout.addStretch()

	@property
	def label(self) -> BaseLabel:
		return self._label
