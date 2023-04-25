#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom styled Qt buttons
"""

from Qt.QtCore import Qt, QRect, QSize, QTimer
from Qt.QtWidgets import QSizePolicy, QPushButton, QStyle, QStyleOption, QStyleOptionButton, QStylePainter
from Qt.QtGui import QFont, QFontMetrics, QColor, QPen, QBrush, QPainter, QPainterPath, QLinearGradient

from tp.core import dcc

NORMAL, DOWN, DISABLED = 1, 2, 3
INNER, OUTER = 1, 2


class BaseStyleButtonAnimationObject(object):
	_glow_pens = {}
	for index in range(1, 11):
		_glow_pens[index] = [QPen(QColor(0, 255, 0, 12 * index), 1, Qt.SolidLine),
							 QPen(QColor(0, 255, 0, 5 * index), 3, Qt.SolidLine),
							 QPen(QColor(0, 255, 0, 2 * index), 5, Qt.SolidLine),
							 QPen(QColor(0, 255, 0, 25.5 * index), 1, Qt.SolidLine)]

	_pens_text = QPen(QColor(202, 207, 210), 1, Qt.SolidLine)
	_pens_shadow = QPen(QColor(9, 10, 12), 1, Qt.SolidLine)
	_pens_border = QPen(QColor(9, 10, 12), 2, Qt.SolidLine)
	_pens_clear = QPen(QColor(0, 0, 0, 0), 1, Qt.SolidLine)

	_pens_text_disabled = QPen(QColor(102, 107, 110), 1, Qt.SolidLine)
	_pens_shadow_disabled = QPen(QColor(0, 0, 0), 1, Qt.SolidLine)

	_brush_clear = QBrush(QColor(0, 0, 0, 0))
	_brush_border = QBrush(QColor(9, 10, 12))

	def __init__(self):
		font = QFont()
		font.setPointSize(8)
		font.setFamily("Calibri")
		self.setFont(font)

		self._hover = False
		self._glow_index = 0
		self._anim_timer = QTimer()
		self._anim_timer.timeout.connect(self._animate_glow)

	def enterEvent(self, event):
		super(self.__class__, self).enterEvent(event)

		if not self.isEnabled():
			return

		self._hover = True
		self._start_anim()

	def leaveEvent(self, event):
		super(self.__class__, self).leaveEvent(event)

		if not self.isEnabled():
			return

		self._hover = False
		self._start_anim()

	def _animate_glow(self):
		if self._hover:
			if self._glow_index >= 10:
				self._glow_index = 10
				self._anim_timer.stop()
			else:
				self._glow_index += 1

		else:
			if self._glow_index <= 0:
				self._glow_index = 0
				self._anim_timer.stop()
			else:
				self._glow_index -= 1

		dcc.execute_deferred(self.update)

	def _start_anim(self):
		if self._anim_timer.isActive():
			return

		self._anim_timer.start(20)


class StyleBaseButton(QPushButton, BaseStyleButtonAnimationObject):
	def __init__(self, *args, **kwargs):

		self._style = kwargs.pop('button_style', None)
		self._pad = kwargs.pop('icon_padding', 0)
		self._min_size = kwargs.pop('min_size', 8)
		self._radius = kwargs.pop('radius', 5)
		self._icon = kwargs.pop('icon', None)

		QPushButton.__init__(self, *args, **kwargs)
		BaseStyleButtonAnimationObject.__init__(self)

		self._font_metrics = QFontMetrics(self.font())
		self._border_width = kwargs.get('border_width')

		if self._icon:
			self.setIcon(self._icon)

	def paintEvent(self, event):
		if not self._style:
			super(StyleBaseButton, self).paintEvent(event)
		else:
			self._style.paintEvent(self, event)


class IconButton(StyleBaseButton, object):
	def __init__(self, icon=None, icon_padding=0, icon_min_size=8, button_style=None, parent=None):
		super(IconButton, self).__init__(button_style=button_style, parent=parent)

		self._pad = icon_padding
		self._minSize = icon_min_size

		if icon:
			self.setIcon(icon)
		self.setStyleSheet('QPushButton { background-color: rgba(255, 255, 255, 0); border:0px; }')
		self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

	def paintEvent(self, event):

		# If we call super paintEvent function without an style, the icon will be draw twice
		if self._style:
			super(IconButton, self).paintEvent(event)

		painter = QPainter()
		painter.begin(self)
		opt = QStyleOptionButton()
		self.initStyleOption(opt)
		rect = opt.rect
		icon_size = max(min(rect.height(), rect.width()) - 2 * self._pad, self._minSize)
		opt.iconSize = QSize(icon_size, icon_size)
		self.style().drawControl(QStyle.CE_PushButton, opt, painter, self)
		painter.end()


class CloseButton(StyleBaseButton, object):
	def __init__(self, *args, **kwargs):
		super(CloseButton, self).__init__(*args, **kwargs)

		self._radius = 10
		self._style = CloseButtonStyle()
		self.setFixedHeight(20)
		self.setFixedWidth(20)


class BaseButtonStyle(object):
	_gradient = {NORMAL: {}, DOWN: {}, DISABLED: {}}
	inner_gradient = QLinearGradient(0, 3, 0, 24)
	inner_gradient.setColorAt(0, QColor(53, 57, 60))
	inner_gradient.setColorAt(1, QColor(33, 34, 36))
	_gradient[NORMAL][INNER] = QBrush(inner_gradient)
	outer_gradient = QLinearGradient(0, 2, 0, 25)
	outer_gradient.setColorAt(0, QColor(69, 73, 76))
	outer_gradient.setColorAt(1, QColor(17, 18, 20))
	_gradient[NORMAL][OUTER] = QBrush(outer_gradient)
	inner_gradient_down = QLinearGradient(0, 3, 0, 24)
	inner_gradient_down.setColorAt(0, QColor(20, 21, 23))
	inner_gradient_down.setColorAt(1, QColor(48, 49, 51))
	_gradient[DOWN][INNER] = QBrush(inner_gradient_down)
	outer_gradient_down = QLinearGradient(0, 2, 0, 25)
	outer_gradient_down.setColorAt(0, QColor(36, 37, 39))
	outer_gradient_down.setColorAt(1, QColor(32, 33, 35))
	_gradient[DOWN][OUTER] = QBrush(outer_gradient_down)
	inner_gradient_disabled = QLinearGradient(0, 3, 0, 24)
	inner_gradient_disabled.setColorAt(0, QColor(33, 37, 40))
	inner_gradient_disabled.setColorAt(1, QColor(13, 14, 16))
	_gradient[DISABLED][INNER] = QBrush(inner_gradient_disabled)
	outer_gradient_disabled = QLinearGradient(0, 2, 0, 25)
	outer_gradient_disabled.setColorAt(0, QColor(49, 53, 56))
	outer_gradient_disabled.setColorAt(1, QColor(9, 10, 12))
	_gradient[DISABLED][OUTER] = QBrush(outer_gradient_disabled)

	@staticmethod
	def paintEvent(base_button, event):
		painter = QStylePainter(base_button)
		painter.setRenderHint(QPainter.Antialiasing)

		option = QStyleOption()
		option.initFrom(base_button)
		x = option.rect.x()
		y = option.rect.y()
		height = option.rect.height() - 1
		width = option.rect.width() - 1

		radius = base_button._radius
		gradient = BaseButtonStyle._gradient[NORMAL]
		offset = 0
		if base_button.isDown():
			gradient = BaseButtonStyle._gradient[DOWN]
			offset = 1
		elif not base_button.isEnabled():
			gradient = BaseButtonStyle._gradient[DISABLED]

		painter.setBrush(base_button._brush_border)
		painter.setPen(base_button._pens_border)
		painter.drawRoundedRect(QRect(x + 1, y + 1, width - 1, height - 1), radius, radius)

		painter.setPen(base_button._pens_clear)
		painter.setBrush(gradient[OUTER])
		painter.drawRoundedRect(QRect(x + 2, y + 2, width - 3, height - 3), radius, radius)

		painter.setBrush(gradient[INNER])
		painter.drawRoundedRect(QRect(x + 3, y + 3, width - 5, height - 5), radius - 1, radius - 1)
		painter.setBrush(base_button._brush_clear)

		text = base_button.text()
		font = base_button.font()
		text_width = base_button._font_metrics.width(text)
		text_height = font.pointSize()
		text_path = QPainterPath()
		text_path.addText((width - text_width) / 2, height - ((height - text_height) / 2) - 1 + offset, font, text)

		glow_index = base_button._glow_index
		glow_pens = base_button._glow_pens
		alignment = (Qt.AlignHCenter | Qt.AlignVCenter)
		if base_button.isEnabled():
			painter.setPen(base_button._pens_shadow)
			painter.drawPath(text_path)
			painter.setPen(base_button._pens_text)
			painter.drawText(x, y + offset, width, height, alignment, text)
			if glow_index > 0:
				for index in range(3):
					painter.setPen(glow_pens[glow_index][index])
					painter.drawPath(text_path)

				painter.setPen(glow_pens[glow_index][3])
				painter.drawText(x, y + offset, width, height, alignment, text)
		else:
			painter.setPen(base_button._pens_shadow_disabled)
			painter.drawPath(text_path)
			painter.setPen(base_button._pens_text_disabled)
			painter.drawText(x, y + offset, width, height, alignment, text)


class FlatButtonStyle(BaseButtonStyle, object):
	@staticmethod
	def paintEvent(base_button, event):
		painter = QStylePainter(base_button)
		painter.setRenderHint(QPainter.Antialiasing)

		option = QStyleOption()
		option.initFrom(base_button)
		x = option.rect.x()
		y = option.rect.y()
		height = option.rect.height() - 1
		width = option.rect.width() - 1

		radius = base_button._radius
		gradient = BaseButtonStyle._gradient[NORMAL]
		offset = 0
		icon_offset = 3     # TODO: maybe we want set this as a property of the base button

		if base_button.isCheckable():
			if base_button.isChecked():
				gradient = BaseButtonStyle._gradient[DOWN]
				offset = 1
		else:
			if base_button.isDown():
				gradient = BaseButtonStyle._gradient[DOWN]
				offset = 1
			elif not base_button.isEnabled():
				gradient = BaseButtonStyle._gradient[DISABLED]

		painter.setBrush(base_button._brush_border)
		painter.setPen(base_button._pens_border)
		painter.drawRoundedRect(QRect(x + 1, y + 1, width - 1, height - 1), radius, radius)

		painter.setPen(base_button._pens_clear)
		painter.setBrush(gradient[OUTER])
		painter.drawRoundedRect(QRect(x + 1, y + 1, width - 1, height - 1), radius, radius)

		painter.setBrush(gradient[INNER])
		painter.drawRoundedRect(QRect(x + 2, y + 2, width - 2, height - 2), radius - 1, radius - 1)
		painter.setBrush(base_button._brush_clear)

		text = base_button.text()
		font = base_button.font()
		text_width = base_button._font_metrics.width(text)
		text_height = font.pointSize()
		text_path = QPainterPath()

		has_icon = base_button.icon()

		if has_icon:
			if base_button.text() == '' or base_button.text() is None:
				icon_size = max(min(height, width) - 2 * base_button._pad, base_button._min_size)
				painter.drawPixmap(
					(width - icon_size) / 2, (height - icon_size) / 2, base_button.icon().pixmap(icon_size))
			else:
				icon_size = max(min(height, width) - 2 * base_button._pad, base_button._min_size)
				painter.drawPixmap(
					(width - icon_size - text_width) / 2, (height - icon_size) / 2,
					base_button.icon().pixmap(icon_size))

		if has_icon:
			text_path.addText(
				(width - text_width + icon_size + icon_offset) / 2,
				height - ((height - text_height) / 2) - 1 + offset, font, text)
		else:
			text_path.addText(
				(width - text_width) / 2, height - ((height - text_height) / 2) - 1 + offset, font, text)

		glow_index = base_button._glow_index
		glow_pens = base_button._glow_pens
		alignment = (Qt.AlignHCenter | Qt.AlignVCenter)
		if base_button.isEnabled():
			painter.setPen(base_button._pens_shadow)
			painter.drawPath(text_path)
			painter.setPen(base_button._pens_text)

			if has_icon:
				painter.drawText(x + ((icon_size + icon_offset) * 0.5), y + offset, width, height, alignment, text)
			else:
				painter.drawText(x, y + offset, width, height, alignment, text)

			if glow_index > 0:
				for index in range(3):
					painter.setPen(glow_pens[glow_index][index])
					painter.drawPath(text_path)

				painter.setPen(glow_pens[glow_index][3])

				if has_icon:
					painter.drawText(x + ((icon_size + icon_offset) * 0.5), y + offset, width, height, alignment, text)
				else:
					painter.drawText(x, y + offset, width, height, alignment, text)
		else:
			painter.setPen(base_button._pens_shadow_disabled)
			painter.drawPath(text_path)
			painter.setPen(base_button._pens_text_disabled)

			if has_icon:
				painter.drawText(x + ((icon_size + icon_offset) * 0.5), y + offset, width, height, alignment, text)
			else:
				painter.drawText(x, y + offset, width, height, alignment, text)


class ButtonStyle3D(BaseButtonStyle, object):
	@staticmethod
	def paintEvent(base_button, event):
		painter = QStylePainter(base_button)
		painter.setRenderHint(QPainter.Antialiasing)

		option = QStyleOption()
		option.initFrom(base_button)
		x = option.rect.x()
		y = option.rect.y()
		height = option.rect.height() - 1
		width = option.rect.width() - 1

		radius = base_button._radius
		gradient = BaseButtonStyle._gradient[NORMAL]
		offset = 0

		if base_button.isCheckable():
			if base_button.isChecked():
				gradient = BaseButtonStyle._gradient[DOWN]
				offset = 1
		else:
			if base_button.isDown():
				gradient = BaseButtonStyle._gradient[DOWN]
				offset = 1
			elif not base_button.isEnabled():
				gradient = BaseButtonStyle._gradient[DISABLED]

		painter.setBrush(base_button._brush_border)
		painter.setPen(base_button._pens_border)
		painter.drawRoundedRect(QRect(x + 1, y + 1, width - 1, height - 1), radius, radius)

		if base_button.isCheckable():
			if base_button.isChecked():
				painter.setPen(base_button._pens_clear)
				painter.setBrush(gradient[OUTER])
				painter.drawRoundedRect(QRect(x + 1, y + 1, width - 1, height - 1), radius, radius)
			else:
				painter.setPen(base_button._pens_clear)
				painter.setBrush(gradient[OUTER])
				painter.drawRoundedRect(QRect(x + 2, y + 2, width - 2, height - 2), radius, radius)
		else:
			if base_button.isDown():
				painter.setPen(base_button._pens_clear)
				painter.setBrush(gradient[OUTER])
				painter.drawRoundedRect(QRect(x + 1, y + 1, width - 1, height - 1), radius, radius)
			else:
				painter.setPen(base_button._pens_clear)
				painter.setBrush(gradient[OUTER])
				painter.drawRoundedRect(QRect(x + 2, y + 2, width - 2, height - 2), radius, radius)

		painter.setBrush(gradient[INNER])
		painter.drawRoundedRect(QRect(x + 3, y + 3, width - 3, height - 3), radius - 1, radius - 1)
		painter.setBrush(base_button._brush_clear)

		text = base_button.text()
		font = base_button.font()
		text_width = base_button._font_metrics.width(text)
		text_height = font.pointSize()
		text_path = QPainterPath()
		text_path.addText((width - text_width) / 2, height - ((height - text_height) / 2) - 1 + offset, font, text)

		glow_index = base_button._glow_index
		glow_pens = base_button._glow_pens
		alignment = (Qt.AlignHCenter | Qt.AlignVCenter)
		if base_button.isEnabled():
			painter.setPen(base_button._pens_shadow)
			painter.drawPath(text_path)
			painter.setPen(base_button._pens_text)
			painter.drawText(x, y + offset, width, height, alignment, text)
			if glow_index > 0:
				for index in range(3):
					painter.setPen(glow_pens[glow_index][index])
					painter.drawPath(text_path)

				painter.setPen(glow_pens[glow_index][3])
				painter.drawText(x, y + offset, width, height, alignment, text)
		else:
			painter.setPen(base_button._pens_shadow_disabled)
			painter.drawPath(text_path)
			painter.setPen(base_button._pens_text_disabled)
			painter.drawText(x, y + offset, width, height, alignment, text)


class CloseButtonStyle(BaseButtonStyle, object):
	@staticmethod
	def paintEvent(base_button, event):
		painter = QStylePainter(base_button)
		painter.setRenderHint(QPainter.Antialiasing)

		option = QStyleOption()
		option.initFrom(base_button)
		x = option.rect.x()
		y = option.rect.y()
		height = option.rect.height() - 1
		width = option.rect.width() - 1

		gradient = BaseButtonStyle._gradient[NORMAL]
		offset = 0
		if base_button.isDown():
			gradient = BaseButtonStyle._gradient[DOWN]
			offset = 1
		elif not base_button.isEnabled():
			gradient = BaseButtonStyle._gradient[DISABLED]

		painter.setPen(base_button._pens_border)
		painter.drawEllipse(x + 1, y + 1, width - 1, height - 1)

		painter.setPen(base_button._pens_clear)
		painter.setBrush(gradient[OUTER])
		painter.drawEllipse(x + 2, y + 2, width - 3, height - 2)

		painter.setBrush(gradient[INNER])
		painter.drawEllipse(x + 3, y + 3, width - 5, height - 4)

		painter.setBrush(base_button._brush_clear)

		line_path = QPainterPath()
		line_path.moveTo(x + 8, y + 8)
		line_path.lineTo(x + 12, x + 12)
		line_path.moveTo(x + 12, y + 8)
		line_path.lineTo(x + 8, y + 12)

		painter.setPen(base_button._pens_border)
		painter.drawPath(line_path)

		glow_index = base_button._glow_index
		glow_pens = base_button._glow_pens

		if glow_index > 0:
			for index in range(3):
				painter.setPen(glow_pens[glow_index][index])
				painter.drawPath(line_path)

			painter.setPen(glow_pens[glow_index][3])
			painter.drawPath(line_path)


class ButtonStyles(object):
	BaseStyle = BaseButtonStyle()
	FlatStyle = FlatButtonStyle()
	Style3D = ButtonStyle3D()
	CloseStyle = CloseButtonStyle()
