#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that extends default Qt labels (QLabel) functionality
"""

from Qt.QtCore import Qt, Property, Signal
from Qt.QtWidgets import QLabel, QSizePolicy, QStyleOption
from Qt.QtGui import QPainter

from tp.common.qt import dpi


def label(text='', tooltip='', upper=False, bold=False, elide_mode=Qt.ElideNone, parent=None):
	"""
	Creates a new label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether label text is forced to be uppercase.
	:param bool bold: whether label font is bold.
	:param Qt.Elide elide_mode: whether label text should elide.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	return BaseLabel(text=text, tooltip=tooltip, bold=bold, upper=upper, elide_mode=elide_mode, parent=parent)


def h1_label(text='', tooltip='', upper=False, bold=False, parent=False):
	"""
	Creates a new H1label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether or not label text is forced to be uppercase.
	:param bool bold: whether or not label font is bold.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h1()

	return new_label


def h2_label(text='', tooltip='', upper=False, bold=False, parent=False):
	"""
	Creates a new H2 label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether or not label text is forced to be uppercase.
	:param bool bold: whether or not label font is bold.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h2()

	return new_label


def h3_label(text='', tooltip='', upper=False, bold=False, parent=False):
	"""
	Creates a new H3 label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether or not label text is forced to be uppercase.
	:param bool bold: whether or not label font is bold.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h3()

	return new_label


def h4_label(text='', tooltip='', upper=False, bold=False, parent=False):
	"""
	Creates a new H4 label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether or not label text is forced to be uppercase.
	:param bool bold: whether or not label font is bold.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h4()

	return new_label


def h5_label(text='', tooltip='', upper=False, bold=False, parent=False):
	"""
	Creates a new H5 label widget.

	:param str text: label text.
	:param str tooltip: label tooltip.
	:param bool upper: whether or not label text is forced to be uppercase.
	:param bool bold: whether or not label font is bold.
	:param QWidget parent: parent widget.
	:return: new label widget instance.
	:rtype: BaseLabel
	"""

	new_label = label(text=text, tooltip=tooltip, upper=upper, bold=bold, parent=parent).h5()

	return new_label


def clipped_label(text='', width=0, ellipsis=True, always_show_all=False, parent=None):
	"""
	Custom QLabel that clips itself if the widget width is smaller than the text.

	:param str text: label text.
	:param int width: minimum width.
	:param bool ellipsis: whether to elide label.
	:param bool ellipsis: whether label will have ellipsis.
	:param bool always_show_all: force the label to show the complete text or hide the complete text.
	:param QWidget parent: parent widget.
	"""

	return ClippedLabel(text=text, width=width, ellipsis=ellipsis, always_show_all=always_show_all, parent=parent)


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
			self, text='', tooltip='', upper=False, bold=False, enable_menu=True, parent=None, elide_mode=Qt.ElideNone):
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

		self.setToolTip(tooltip)
		self.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.LinksAccessibleByMouse)
		self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
		self.strong(bold)

	def _get_type(self):
		"""
		Internal Qt property function that returns label type.

		:return: label type.
		:rtype: BaseLabel.Types
		"""

		return self._type

	def _set_type(self, value):
		"""
		Internal Qt property function that sets label type.

		:param BaseLabel.Types value: label type.
		"""

		self._type = value
		self.style().polish(self)

	def _get_level(self):
		"""
		Internal Qt property function that returns label level.

		:return: label level.
		:rtype: str
		"""

		return self._level

	def _set_level(self, value):
		"""
		Internal Qt property function that sets label level.

		:param str value: label level.
		"""

		self._level = value
		self.style().polish(self)

	def _get_underline(self):
		"""
		Internal Qt property function that returns whether or not label is using an underline style.

		:return: True if labael has underline style; False otherwise.
		:rtype: bool
		"""

		return self._underline

	def _set_underline(self, flag):
		"""
		Internal Qt property function that sets label to use an underline style.

		:param bool flag: underline flag.
		"""

		self._underline = flag
		self.style().polish(self)

	def _get_delete(self):
		"""
		Internal Qt property function that returns whether or not label is using a delete style.

		:return: True if the label has a delete style; False otherwise.
		:rtype: bool
		"""

		return self._delete

	def _set_delete(self, flag):
		"""
		 Internal Qt property function that sets label to use a delete style.

		 :param bool flag: delete flag
		 """

		self._delete = flag
		self.style().polish(self)

	def _get_strong(self):
		"""
		Internal Qt property function that returns whether or not label is using a strong style.

		:return: True if the label has a strong style; False otherwise.
		:type: bool
		"""

		return self._strong

	def _set_strong(self, flag):
		"""
		 Internal Qt property function that sets label to use a strong style.

		 :param bool flag: strong flag.
		 """

		self._strong = flag
		self.style().polish(self)

	def _get_mark(self):
		"""
		Internal Qt property function that returns whether or not label is using a mark style.

		:return: True if the label has a mark style; False otherwise.
		:rtype: bool
		"""

		return self._mark

	def _set_mark(self, flag):
		"""
		 Internal Qt property function that sets label to use a mark style.

		 :param bool flag: mark flag.
		 """

		self._mark = flag
		self.style().polish(self)

	def _get_code(self):
		"""
		Internal Qt property function that returns whether or not label is using a code style.

		:return: True if the label has a code style; False otherwise.
		:rtype: bool
		"""

		return self._code

	def _set_code(self, flag):
		"""
		Internal Qt property function that sets label to use a code style.

		:param bool flag: code flag.
		"""

		self._code = flag
		self.style().polish(self)

	def _get_elide_mode(self):
		"""
		Internal Qt property function that returns which elide mode label is using.

		:return: label elide mode.
		:rtype: Qt.ElideLeft or Qt.ElideMiddle or Qt.ElideRight or Qt.ElideNone
		"""

		return self._elide_mode

	def _set_elide_mode(self, value):
		"""
		Internal Qt property function that sets elide mode used by the label.


		:param Qt.ElideLeft or Qt.ElideMiddle or Qt.ElideRight or Qt.ElideNone value: elide mode.
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

	def mousePressEvent(self, event):
		"""
		Overrides mousePressEvent function to emit clicked signal each time user clicks on the label.

		:param QEvent event: Qt mouse event.
		"""

		self.clicked.emit()
		super(BaseLabel, self).mousePressEvent(event)

	def resizeEvent(self, event):
		"""
		Overrides base QObject resizeEvent function
		"""

		self._update_elided_text()

	def text(self):
		"""
		Overrides base QLabel text function
		:return: str
		"""

		return self._actual_text

	def setText(self, text):
		"""
		Overrides base QLabel setText function
		:return: str
		"""

		self._actual_text = text
		self._update_elided_text()
		self.setToolTip(text)

	def h1(self):
		"""
		Sets label with h1 type.
		"""

		self.theme_level = self.Levels.H1

		return self

	def h2(self):
		"""
		Sets label with h2 type.
		"""

		self.theme_level = self.Levels.H2

		return self

	def h3(self):
		"""
		Sets label with h3 type.
		"""

		self.theme_level = self.Levels.H3

		return self

	def h4(self):
		"""
		Sets label with h4 type.
		"""

		self.theme_level = self.Levels.H4

		return self

	def h5(self):
		"""
		Sets label with h4 type.
		"""

		self.theme_level = self.Levels.H5

		return self

	def secondary(self):
		"""
		Sets label with secondary type.
		"""

		self.theme_type = self.Types.SECONDARY

		return self

	def warning(self):
		"""
		Sets label with warning type.
		"""

		self.theme_type = self.Types.WARNING

		return self

	def danger(self):
		"""
		Sets label with danger type.
		"""

		self.theme_type = self.Types.DANGER

		return self

	def strong(self, flag=True):
		"""
		Sets label with strong type.

		:param bool flag: whether enable strong mode.
		"""

		self.theme_strong = flag

		return self

	def mark(self, flag=True):
		"""
		Sets label with mark type.

		:param bool flag: whether or not enable mar mode.
		"""

		self.theme_mark = flag

		return self

	def code(self, flag=True):
		"""
		Sets label with code type.

		:param bool flag: whether or not enable code mode.
		"""

		self.theme_code = flag

		return self

	def delete(self, flag=True):
		"""
		Sets label with delete type.

		:param bool flag: whether or not enable delete mode.
		"""

		self.theme_delete = flag

		return self

	def underline(self, flag=True):
		"""
		Sets label with underline type.

		:param bool flag: whether or not enable underline mode.
		"""

		self.theme_underline = flag

		return self

	def _update_elided_text(self):
		"""
		Internal function that updates the elided text on the label
		"""

		font_metrics = self.fontMetrics()
		elided_text = font_metrics.elidedText(self._actual_text, self._elide_mode, self.width() - 2 * 2)
		super(BaseLabel, self).setText(elided_text)


class ClippedLabel(BaseLabel):
	"""
	Custom QLabel that clips itself if the widget width is smaller than the text.

	:param str text: label text.
	:param int width: minimum width.
	:param bool ellipsis: whether label will have ellipsis.
	:param bool always_show_all: force the label to show the complete text or hide the complete text.
	:param QWidget parent: parent widget.
	"""

	_width = _text = _elided = None

	def __init__(self, text='', width=0, ellipsis=True, always_show_all=False, parent=None):
		super(ClippedLabel, self).__init__(text, parent=parent)

		self._always_show_all = always_show_all
		self._ellipsis = ellipsis

		self.setMinimumWidth(width if width > 0 else 1)

	def paintEvent(self, event):
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
			if self._ellipsis:
				self.style().drawItemText(
					painter, rect, self.alignment(), option.palette, self.isEnabled(),
					self._elided, self.foregroundRole())
			else:
				self.style().drawItemText(
					painter, rect, self.alignment(), option.palette, self.isEnabled(),
					self.text(), self.foregroundRole())
