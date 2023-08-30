#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets for colors
"""

from __future__ import annotations

import math
import array
from functools import partial

from Qt.QtCore import Qt, Signal, Property, Slot, QSize, QSizeF, QPoint, QPointF, QRect, QRectF, QLineF, QMimeData
from Qt.QtCore import qFuzzyCompare
from Qt.QtWidgets import QStyle, QStyleOptionFrame, QStylePainter, QSizePolicy, QColorDialog, QDialogButtonBox
from Qt.QtWidgets import QApplication, QWidget, QFrame, QDialog, QToolButton, QLineEdit, QSlider, QMenu
from Qt.QtGui import QColor, QBrush, QPen, QPainter, QPainterPath, QGradient, QLinearGradient, QConicalGradient
from Qt.QtGui import QPixmap, QImage, QPolygonF, QDrag

# from tp.core import dialog
from tp.common.resources import api as resources
from tp.common.resources import color as core_color
from tp.common.python import helpers
# from tp.common.qt import base, utils, qtutils, contexts as qt_contexts
from tp.common.qt.widgets import layouts, buttons, labels, dividers
# from tp.common.qt.widgets import layouts, buttons, labels, spinbox, dividers, panel, sliders


# TODO: Move all defualt coors into a configuration file that can be ready by any widget
DEFAULT_COLORS = {
	'Grey': (102, 102, 102, 255),
	'Ok': (128, 178, 204, 255),
	'Cancel': (178, 128, 102, 255),
	'Warn': (178, 51, 51, 255),
	'Collapse': (38, 38, 38, 255),
	'Subtle': (122, 122, 153, 255)
}


class ColorButton(buttons.BaseButton):
	def __init__(self, *args, **kwargs):
		super(ColorButton, self).__init__(*args, **kwargs)


class ColorPicker(QFrame):

	COLOR_BUTTON_CLASS = ColorButton

	colorChanged = Signal(object)

	def __init__(self, *args, **kwargs):
		super(ColorPicker, self).__init__(*args, **kwargs)

		self._buttons = list()
		self._current_color = None
		self._browser_colors = None

		main_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
		self.setLayout(main_layout)

	def current_color(self):
		"""
		Returns the current color
		:return: QColor
		"""

		return self._current_color

	def set_current_color(self, color):
		"""
		Sets the current color
		:param color: QColor
		"""

		self._current_color = color

	def browser_colors(self):
		"""
		Returns the colors to be displayed in the browser
		:return: list(Color)
		"""

		return self._browser_colors

	def set_browser_colors(self, colors):
		"""
		Sets the colors to be displayed in the browser
		:param colors: list(Color)
		"""

		self._browser_colors = colors

	def delete_buttons(self):
		"""
		Deletes all color buttons
		"""

		layout = self.layout()
		while layout.count():
			item = layout.takeAt(0)
			item.widget().deleteLater()

	def set_colors(self, colors):
		"""
		Sets the colors for the color bar
		:param colors: list(str) or list(Color)
		"""

		self.delete_buttons()

		first = True
		last = False

		for i, color in enumerate(colors):
			if i == len(colors) - 1:
				last = True
			if not isinstance(color, str):
				color = core_color.Color(color)
				color = color.to_string()
			callback = partial(self._on_color_changed, color)
			css = 'background-color: {}'.format(color)

			btn = self.COLOR_BUTTON_CLASS(parent=self)
			btn.setObjectName('colorButton')
			btn.setStyleSheet(css)
			btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
			btn.setProperty('first', first)
			btn.setProperty('last', last)
			btn.clicked.connect(callback)
			self.layout().addWidget(btn)
			first = False

		browse_btn = buttons.BaseButton('...', parent=self)
		browse_btn.setObjectName('menuButton')
		browse_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		browse_btn.clicked.connect(self._on_browse_color)
		self.layout().addWidget(browse_btn)

	def _on_browse_color(self):
		"""
		Internal callback function that is triggered when the user clicks on browse button
		"""

		current_color = self.current_color()
		d = QColorDialog(self)
		d.setCurrentColor(current_color)
		standard_colors = self.browser_colors()
		if standard_colors:
			index = -1
			for standard_color in standard_colors:
				index += 1
				try:
					# PySide2/PyQt5
					standard_color = QColor(standard_color)
					d.setStandardColor(index, standard_color)
				except Exception:
					# PySide/PyQt4
					standard_color = QColor(standard_color).rgba()
					d.setStandardColor(index, standard_color)

		d.currentColorChanged.connect(self._on_color_changed)

		if d.exec_():
			self._on_color_changed(d.selectedColor())
		else:
			self._on_color_changed(current_color)

	def _on_color_changed(self, color):
		"""
		Internal callback function that is triggered when the user clcks or browse for a color
		:param color: QColor
		"""

		self._current_color = color
		self.colorChanged.emit(color)

	@Slot()
	def blandSlot(self):
		"""
		Blank slot to fix issue with PySide2.QColorDialog.open()
		"""

		pass


# class ColorSwatch(QToolButton):
#     def __init__(self, parent=None, **kwargs):
#         super(ColorSwatch, self).__init__(parent=parent)
#
#         self.normalized = kwargs.get('normalized', True)
#         self.color = kwargs.get('color', [1.0, 1.0, 1.0])
#         self.qcolor = QColor()
#         self.index_color = None
#         self.set_color(self.color)
#
#         self.clicked.connect(self._on_open_color_picker)
#
#     def set_color(self, color):
#         """
#         Sets an RGB color value
#         :param color: list, list of RGB values
#         """
#
#         if type(color) is QColor:
#             return color
#
#         # if type(color[0]) is float:
#         self.qcolor.setRgb(*color)
#         # self.setToolTip("%.2f, %.2f, %.2f" % (color[0], color[1], color[2]))
#         # else:
#         #     self.qcolor.setRgb(*color)
#         self.setToolTip("%d, %d, %d" % (color[0], color[1], color[2]))
#         self._update()
#
#         return self.color
#
#     def get_color(self):
#         """
#         Returns the current color RGB values
#         :return: list<int, int, int>, RGB color values
#         """
#
#         return self.color
#
#     def get_rgb(self, normalized=True):
#         """
#         Returns a tuple of RGB values
#         :param normalized:  bool, True if you want to get a normalized color, False otherwise
#         :return: tuple, RGB color values
#         """
#
#         if not normalized:
#             return self.qcolor.toRgb().red(), self.qcolor.toRgb().green(), self.qcolor.toRgb().blue()
#         else:
#             return self.qcolor.toRgb().redF(), self.qcolor.toRgb().greenF(), self.qcolor.toRgb().blueF()
#
#     def _update(self):
#         """
#         Updates the widget color
#         """
#
#         self.color = self.qcolor.getRgb()[0:3]
#         self.setStyleSheet(
#             """
#             QToolButton
#             {
#                 background-color: qlineargradient(
#                 spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgb(%d, %d, %d), stop:1 rgb(%d, %d, %d))
#             };
#             """ % (self.color[0] * .45, self.color[1] * .45,
#                    self.color[2] * .45, self.color[0], self.color[1], self.color[2])
#         )
#
#     def _get_hsvF(self):
#         return self.qcolor.getHsvF()
#
#     def _set_hsvF(self, color):
#         """
#         Set the current color (HSV - normalized)
#         :param color: tuple<int, int, int>, tuple  of HSV values
#         """
#
#         self.qcolor.setHsvF(color[0], color[1], color[2], 255)
#
#     def _get_hsv(self):
#         return self.qcolor.getHsv()
#
#     def _set_hsv(self, color):
#         """
#         Sets teh current color (HSV)
#         :param color: tuple<int, int, int, Tuple of HSV values (normalized)
#         """
#
#         self.qcolor.setHsv(color[0], color[1], color[2], 255)
#
#     def _on_open_color_picker(self):
#
#         color_picker = dialog.ColorDialog()
#         color_picker.exec_()
#         if color_picker.color is None:
#             return
#
#         if type(color_picker.color) == int:
#             clr = dialog.ColorDialog.maya_colors[color_picker.color]
#             self.index_color = color_picker.color
#             self.set_color((clr[0] * 255, clr[1] * 255, clr[2] * 255))


class ColorLineEdit(QLineEdit):
	"""
	Custom QLineEdit intended to be used to edit and display color names. If accepts several string formats:
		- #f00 (3 hexadecimal RGB digits)
		- #ff0000 (6 hexadecimal RGB digits)
		- rgb(255, 0, 0) (function-like)
		- red (color name)
	https://gitlab.com/mattia.basaglia/Qt-Color-Widgets
	"""

	colorEdited = Signal(QColor)
	colorChanged = Signal(QColor)
	showAlphaChanged = Signal(bool)
	previewColorChanged = Signal(QColor)
	colorEditingFinished = Signal(QColor)

	def __init__(self, parent=None):
		super(ColorLineEdit, self).__init__(parent=parent)

		self._color = QColor()
		self._show_alpha = True
		self._preview_color = True
		self._background = QBrush()

		self._background.setTexture(QPixmap(resources.pixmap('alpha_back')))
		self.set_color(QColor(Qt.white))

		self.textEdited.connect(self._on_text_edited)
		self.editingFinished.connect(self._on_editing_finished)

	def dragEnterEvent(self, event):
		if self.isReadOnly():
			return

		if event.mimeData().hasColor() or (event.mimeData().hasText() and core_color.color_from_string(
				event.mimeData().text(), self._show_alpha).isValid()):
			event.acceptProposedAction()

	def dropEvent(self, event):
		if self.isReadOnly():
			return

		if event.mimeData().hasColor():
			self.set_color(QColor(self.mimeData().colorData().value()))
			event.accept()
		elif event.mimeData().hasText():
			col = core_color.color_from_string(event.mimeData().text(), self._show_alpha)
			if col.isValid():
				self.set_color(col)
				event.accept()

	def paintEvent(self, event):
		if self._custom_alpha():
			painter = QPainter(self)
			panel = QStyleOptionFrame()
			self.initStyleOption(panel)
			r = self.style().subElementRect(QStyle.SE_LineEditContents, panel, None)
			painter.fillRect(r, self._background)
			painter.fillRect(r, self._color)

		super(ColorLineEdit, self).paintEvent(event)

	def setPalette(self, color, parent):
		if self._preview_color:
			bg = Qt.transparent if self._custom_alpha() else self._color
			text = Qt.black if core_color.color_luma_float(color) > 0.5 or color.alpha() < 0.2 else Qt.white
			try:
				bg_name = bg.name()
			except TypeError:
				bg_name = bg.name
			parent.setStyleSheet('background-color: {}; color: {}'.format(bg_name, text.name))

	def color(self):
		return self._color

	def set_color(self, color):
		if color != self._color:
			self._color = color
			self.setPalette(color, self)
			self.setText(core_color.string_from_color(self._color, self._show_alpha))
			self.colorChanged.emit(self._color)

	def preview_color(self):
		return self._preview_color

	def set_preview_color(self, preview_color):
		if preview_color != self._preview_color:
			self._preview_color = preview_color
			if self._preview_color:
				self.setPalette(self._color, self)
			else:
				self.setPalette(QApplication.palette(), self)
		self.previewColorChanged.emit(self._preview_color)

	def show_alpha(self):
		return self._show_alpha

	def set_show_alpha(self, show_alpha):
		if self._show_alpha != show_alpha:
			self._show_alpha = show_alpha
			self.setPalette(self._color, self)
			self.setText(core_color.string_from_color(self._color, self._show_alpha))
			self.showAlphaChanged.emit(self._show_alpha)

	def _custom_alpha(self):
		return self._preview_color and self._show_alpha and self._color.alpha() < 255

	def _on_text_edited(self, text):
		color = core_color.color_from_string(text, self._show_alpha)
		if color.isValid():
			self._color = color
			self.setPalette(color, self)
			self.colorEdited.emit(color)
			self.colorChanged.emit(color)

	def _on_editing_finished(self):
		color = core_color.color_from_string(self.text(), self._show_alpha)
		if color.isValid():
			self._color = color
			self.colorEditingFinished.emit(color)
			self.colorChanged.emit(color)
		else:
			self.setText(core_color.string_from_color(self._color, self._show_alpha))
			self.colorEditingFinished.emit(self._color)
			self.colorChanged.emit(color)

		self.setPalette(self._color, self)


# class Color2DSlider(QWidget):
#     """
#     Widget that allow to select 2 HSV color components at the same time
#     https://gitlab.com/mattia.basaglia/Qt-Color-Widgets
#     """
#
#     colorChanged = Signal(QColor)
#     componentXChanged = Signal(int)
#     componentYChanged = Signal(int)
#
#     SELECTOR_RADIUS = 6
#
#     class Component(object):
#         HUE = 0
#         SATURATION = 1
#         VALUE = 2
#
#     def __init__(self, parent=None):
#
#         self._hue = 1
#         self._sat = 1
#         self._val = 1
#         self._comp_x = self.Component.SATURATION
#         self._comp_y = self.Component.VALUE
#         self._square = QImage()
#
#         super(Color2DSlider, self).__init__(parent=parent)
#
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#
#     def sizeHint(self):
#         return QSize(128, 128)
#
#     def resizeEvent(self, event):
#         self._render_square(self.size())
#         self.update()
#
#     def paintEvent(self, event):
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.Antialiasing)
#         painter.drawImage(0, 0, self._square)
#         painter.setPen(QPen(Qt.black if self._val > 0.5 else Qt.white, 3))
#         painter.setBrush(Qt.NoBrush)
#         painter.drawEllipse(self._selector_pos(self.size()), self.SELECTOR_RADIUS, self.SELECTOR_RADIUS)
#
#     def mousePressEvent(self, event):
#         self._set_color_from_pos(event.pos(), self.size())
#         self.colorChanged.emit(self.color())
#         self.update()
#
#     def mouseMoveEvent(self, event):
#         self._set_color_from_pos(event.pos(), self.size())
#         self.colorChanged.emit(self.color())
#         self.update()
#
#     def mouseReleaseEvent(self, event):
#         self._set_color_from_pos(event.pos(), self.size())
#         self.colorChanged.emit(self.color())
#         self.update()
#
#     def hue(self):
#         return self._hue
#
#     def saturation(self):
#         return self._sat
#
#     def value(self):
#         return self._value
#
#     def color(self):
#         return QColor.fromHsvF(self._hue, self._sat, self._val)
#
#     def component_x(self):
#         return self._comp_x
#
#     def component_y(self):
#         return self._comp_y
#
#     def set_hue(self, hue):
#         self._hue = hue
#         self._render_square(self.size())
#         self.update()
#         self.colorChanged.emit(self.color())
#
#     def set_saturation(self, sat):
#         self._sat = sat
#         self._render_square(self.size())
#         self.update()
#         self.colorChanged.emit(self.color())
#
#     def set_value(self, val):
#         self._val = val
#         self._render_square(self.size())
#         self.update()
#         self.colorChanged.emit(self.color())
#
#     def set_color(self, color):
#         self._hue = color.hsvHueF()
#         self._sat = color.saturationF()
#         self._val = color.valueF()
#         self._render_square(self.size())
#         self.update()
#         self.colorChanged.emit(self.color())
#
#     def set_component_x(self, component_x):
#         if component_x != self._comp_x:
#             self._comp_x = component_x
#             self._render_square(self.size())
#             self.update()
#             self.componentXChanged.emit(self._comp_x)
#
#     def set_component_y(self, component_y):
#         if component_y != self._comp_y:
#             self._comp_y = component_y
#             self._render_square(self.size())
#             self.update()
#             self.componentYChanged.emit(self._comp_y)
#
#     def _pixel_hue(self, x, y):
#         if self._comp_x == self.Component.HUE:
#             return x
#         elif self._comp_y == self.Component.HUE:
#             return y
#
#         return self._hue
#
#     def _pixel_sat(self, x, y):
#         if self._comp_x == self.Component.SATURATION:
#             return x
#         elif self._comp_y == self.Component.SATURATION:
#             return y
#
#         return self._sat
#
#     def _pixel_val(self, x, y):
#         if self._comp_x == self.Component.VALUE:
#             return x
#         elif self._comp_y == self.Component.VALUE:
#             return y
#
#         return self._val
#
#     def _render_square(self, size):
#         self._square = QImage(size, QImage.Format_RGB32)
#         for y in range(size.height()):
#             y_float = 1 - float(y) / size.height()
#             for x in range(size.width()):
#                 x_float = float(x) / size.width()
#                 self._square.setPixel(
#                     x, y,
#                     QColor.fromHsvF(
#                         self._pixel_hue(x_float, y_float),
#                         self._pixel_sat(x_float, y_float),
#                         self._pixel_val(x_float, y_float)).rgb())
#
#     def _selector_pos(self, size):
#         pt = QPointF()
#         if self._comp_x == self.Component.HUE:
#             pt.setX(size.width() * self._hue)
#         elif self._comp_x == self.Component.SATURATION:
#             pt.setX(size.width() * self._sat)
#         elif self._comp_x == self.Component.VALUE:
#             pt.setX(size.width() * self._val)
#         if self._comp_y == self.Component.HUE:
#             pt.setY(size.height() * (1 - self._hue))
#         elif self._comp_y == self.Component.SATURATION:
#             pt.setY(size.height() * (1 - self._sat))
#         elif self._comp_y == self.Component.VALUE:
#             pt.setY(size.height() * (1 - self._val))
#
#         return pt
#
#     def _set_color_from_pos(self, pt, size):
#         pt_float = QPointF(
#             utils.clamp(float(pt.x()) / size.width(), 0.0, 1.0),
#             utils.clamp(1 - float(pt.y()) / size.height(), 0.0, 1.0)
#         )
#
#         if self._comp_x == self.Component.HUE:
#             self._hue = pt_float.x()
#         elif self._comp_x == self.Component.SATURATION:
#             self._sat = pt_float.x()
#         elif self._comp_x == self.Component.VALUE:
#             self._val = pt_float.x()
#         if self._comp_y == self.Component.HUE:
#             self._hue = pt_float.y()
#         elif self._comp_y == self.Component.SATURATION:
#             self._sat = pt_float.y()
#         elif self._comp_y == self.Component.VALUE:
#             self._val = pt_float.y()


# class ColorWheel(QWidget):
#
#     wheelWidthChanged = Signal(int)
#     colorChanged = Signal(QColor)
#     colorSelected = Signal(QColor)
#     colorSpaceChanged = Signal(int)
#     rotatingSelectorChanged = Signal(bool)
#     selectorShapeChanged = Signal(int)
#
#     SELECTOR_RADIUS = 6
#
#     class MouseStatus(object):
#         NOTHING = 0
#         DRAG_CIRCLE = 1
#         DRAW_SQUARE = 2
#
#     class WheelShape(object):
#         TRIANGLE = 0
#         SQUARE = 1
#
#     class WheelAngle(object):
#         FIXED = 0                   # Inner part does not rotate
#         ROTATING = 1                # Inner part follow the hue selector
#
#     class WheelColorSpace(object):
#         COLOR_HSV = 0               # Use the HSV color space
#         COLOR_HSL = 1               # Use the HSL color space
#         COLOR_LCH = 2               # Use Luma Chroma Hue (Y_601')
#
#     def __init__(self, parent=None):
#         super(ColorWheel, self).__init__(parent)
#
#         self._hue = 0
#         self._sat = 0
#         self._val = 0
#         self._wheel_width = 20
#         self._mouse_status = self.MouseStatus.NOTHING
#         self._rotating_selector = True
#         self._selector_shape = self.WheelShape.TRIANGLE
#         self._color_space = self.WheelColorSpace.COLOR_HSV
#         self._hue_ring = QPixmap()
#         self._inner_selector = QImage()
#         self._inner_selector_buffer = list()
#         self._background_is_dark = False
#         self._max_size = 128
#         self._color_from = QColor.fromHsvF
#         self._rainbow_from_hue = core_color.rainbow_hsv
#
#         self._setup()
#
#         self.setAcceptDrops(True)
#
#     def sizeHint(self):
#         return QSize(self._wheel_width * 5, self._wheel_width * 5)
#
#     def resizeEvent(self, event):
#         self._render_ring()
#         self._render_inner_selector()
#
#     def paintEvent(self, event):
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.Antialiasing)
#         painter.translate(self.geometry().width() / 2, self.geometry().height() / 2)
#
#         if self._hue_ring.isNull():
#             self._render_ring()
#
#         painter.drawPixmap(-self._outer_radius(), -self._outer_radius(), self._hue_ring)
#
#         self._draw_ring_editor(self._hue, painter, Qt.black)
#         if self._inner_selector.isNull():
#             self._render_inner_selector()
#
#         painter.rotate(self._selector_image_angle())
#         painter.translate(self._selector_image_offset())
#
#         selector_position = QPointF()
#         if self._selector_shape == self.WheelShape.SQUARE:
#             side = self._square_size()
#             selector_position = QPointF(self._sat * side, self._val * side)
#         elif self._selector_shape == self.WheelShape.TRIANGLE:
#             side = self._triangle_side()
#             height = self._triangle_height()
#             slice_h = side * self._val
#             y_min = side / 2 - slice_h / 2
#             selector_position = QPointF(self._val * height, y_min + self._sat * slice_h)
#             triangle = QPolygonF()
#             triangle.append(QPointF(0, side / 2))
#             triangle.append(QPointF(height, 0))
#             triangle.append(QPointF(height, side))
#             clip = QPainterPath()
#             clip.addPolygon(triangle)
#             painter.setClipPath(clip)
#
#         painter.drawImage(QRectF(QPointF(0, 0), self._selector_size()), self._inner_selector)
#         painter.setClipping(False)
#
#         if self._background_is_dark:
#             is_white = self._val < 0.65 or self._sat > 0.43
#             painter.setPen(QPen(Qt.white if is_white else Qt.black, 3))
#         else:
#             painter.setPen(QPen(Qt.black if self._val > 0.5 else Qt.white, 3))
#
#         painter.setBrush(Qt.NoBrush)
#         painter.drawEllipse(selector_position, self.SELECTOR_RADIUS, self.SELECTOR_RADIUS)
#
#     def mouseMoveEvent(self, event):
#         if self._mouse_status == self.MouseStatus.DRAG_CIRCLE:
#             hue = self._line_to_point(event.pos()).angle() / 360.0
#             self._hue = hue
#             self._render_inner_selector()
#             self.colorSelected.emit(self.color())
#             self.colorChanged.emit(self.color())
#             self.update()
#             return
#         elif self._mouse_status == self.MouseStatus.DRAW_SQUARE:
#             glob_mouse_ln = self._line_to_point(event.pos())
#             center_mouse_ln = QLineF(QPointF(0, 0), glob_mouse_ln.p2() - glob_mouse_ln.p1())
#             center_mouse_ln.setAngle(center_mouse_ln.angle() + self._selector_image_angle())
#             center_mouse_ln.setP2(center_mouse_ln.p2() - self._selector_image_offset())
#             if self._selector_shape == self.WheelShape.SQUARE:
#                 self._sat = utils.clamp(center_mouse_ln.x2() / self._square_size(), 0.0, 1.0)
#                 self._val = utils.clamp(center_mouse_ln.y2() / self._square_size(), 0.0, 1.0)
#             elif self._selector_shape == self.WheelShape.TRIANGLE:
#                 pt = center_mouse_ln.p2()
#                 side = self._triangle_side()
#                 self._val = utils.clamp(pt.x() / self._triangle_height(), 0.0, 1.0)
#                 slice_h = side * self._val
#                 y_center = side / 2
#                 y_min = y_center - slice_h / 2
#                 if slice_h > 0:
#                     self._sat = utils.clamp((pt.y() - y_min) / slice_h, 0.0, 1.0)
#
#         self.colorSelected.emit(self.color())
#         self.colorChanged.emit(self.color())
#         self.update()
#
#     def mousePressEvent(self, event):
#         if event.buttons() & Qt.LeftButton:
#             self.setFocus()
#             ray = self._line_to_point(event.pos())
#             if ray.length() <= self._inner_radius():
#                 self._mouse_status = self.MouseStatus.DRAW_SQUARE
#             elif ray.length() <= self._outer_radius():
#                 self._mouse_status = self.MouseStatus.DRAG_CIRCLE
#
#             super(ColorWheel, self).mouseMoveEvent(event)
#
#     def mouseReleaseEvent(self, event):
#         super(ColorWheel, self).mouseMoveEvent(event)
#         self._mouse_status = self.MouseStatus.NOTHING
#
#     def dragEnterEvent(self, event):
#         if event.mimeData().hasColor() or (event.mimeData().hasText() and QColor(event.mimeData().text()).isValid()):
#             event.acceptProposedAction()
#
#     def dropEvent(self, event):
#         if event.mimeData().hasColor():
#             self.set_color(event.mimeData().colorData().value())
#             event.accept()
#         elif event.mimeData().hasText():
#             col = QColor(event.mimeData().text())
#             if col.isValid():
#                 self.set_color(col)
#                 event.accept()
#
#     def color(self):
#         return self._color_from(self._hue, self._sat, self._val, 1)
#
#     def set_color(self, color):
#         old_hue = self._hue
#         self._set_color(color)
#         if not qFuzzyCompare(old_hue + 1, self._hue + 1):
#             self._render_inner_selector()
#         self.update()
#         self.colorChanged.emit(color)
#
#     def hue(self):
#         if self._color_space == self.WheelColorSpace.COLOR_LCH and self._sat > 0.01:
#             return self.color().hueF()
#
#         return self._hue
#
#     def set_hue(self, hue):
#         self._hue = utils.clamp(hue, 0.0, 1.0)
#         self._render_inner_selector()
#         self.update()
#
#     def saturation(self):
#         return self.color().hsvSaturationF()
#
#     def set_saturation(self, sat):
#         self._sat = utils.clamp(sat, 0.0, 1.0)
#         self.update()
#
#     def value(self):
#         return self.color().valueF()
#
#     def set_value(self, val):
#         self._val = utils.clamp(val, 0.0, 1.0)
#         self.update()
#
#     def color_space(self):
#         return self._color_space
#
#     def set_color_space(self, color_space):
#         if self._color_space != color_space:
#             self._color_space = color_space
#             old_color = self.color()
#             if color_space == self.WheelColorSpace.COLOR_HSL:
#                 self._hue = old_color.hueF()
#                 self._sat = core_color.color_hsl_saturation_float(old_color)
#                 self._val = core_color.color_lightnes_float(old_color)
#                 self._color_from = core_color.color_from_hsl
#                 self._rainbow_from_hue = core_color.rainbow_hsv
#             elif color_space == self.WheelColorSpace.COLOR_HSV:
#                 self._hue = old_color.hsvHueF()
#                 self._sat = old_color.hsvSaturationF()
#                 self._val = old_color.valueF()
#                 self._color_from = QColor.fromHsvF
#                 self._rainbow_from_hue = core_color.rainbow_hsv
#             elif color_space == self.WheelColorSpace.COLOR_LCH:
#                 self._hue = old_color.hueF()
#                 self._sat = core_color.color_chroma_float(old_color)
#                 self._val = core_color.color_luma_float(old_color)
#                 self._color_from = core_color.color_from_lch
#                 self._rainbow_from_hue = core_color.rainbow_lch
#
#             self._render_ring()
#             self._render_inner_selector()
#             self.update()
#             self.colorSpaceChanged.emit(color_space)
#
#     def rotating_selector(self):
#         return self._rotating_selector
#
#     def set_rotating_selector(self, rotating):
#         self._rotating_selector = rotating
#         self._render_inner_selector()
#         self.update()
#         self.rotatingSelectorChanged.emit(rotating)
#
#     def selector_shape(self):
#         return self._selector_shape
#
#     def set_selector_shape(self, shape):
#         if shape != self._selector_shape:
#             self._selector_shape = shape
#             self.update()
#             self._render_inner_selector()
#             self.selectorShapeChanged.emit(shape)
#
#     def wheel_width(self):
#         return self._wheel_width
#
#     def set_wheel_width(self, width):
#         self._wheel_width = width
#         self._render_inner_selector()
#         self.wheelWidthChanged.emit(width)
#
#     def _setup(self):
#         background_value = self.palette().window().color().valueF()
#         self._background_is_dark = background_value < 0.5
#
#     def _init_buffer(self, size):
#         """
#         Internal function that ensures the internal image buffer has the correct (and also the QImage associated to it)
#         :param size: QSize
#         """
#
#         linear_size = size.width() * size.height()
#
#         if len(self._inner_selector_buffer) == linear_size:
#             return
#
#         self._inner_selector_buffer = array.array('L', linear_size * [0])
#         self._inner_selector = QImage(self._inner_selector_buffer, size.width(), size.height(), QImage.Format_RGB32)
#
#     def _set_color(self, color):
#         if isinstance(color, (tuple, list)):
#             color = QColor(*color)
#         if self._color_space == self.WheelColorSpace.COLOR_HSV:
#             self._hue = max(0.0, color.hsvHueF())
#             self._sat = color.hsvSaturationF()
#             self._val = color.valueF()
#         elif self._color_space == self.WheelColorSpace.COLOR_HSL:
#             self._hue = max(0.0, color.hueF())
#             self._sat = core_color.color_hsl_saturation_float(color)
#             self._val = core_color.color_lightnes_float(color)
#         elif self._color_space == self.WheelColorSpace.COLOR_LCH:
#             self._hue = max(0.0, color.hsvHueF())
#             self._sat = core_color.color_chroma_float(color)
#             self._val = core_color.color_luma_float(color)
#
#     def _outer_radius(self):
#         """
#         Internal function that returns the outer wheel radius from the widget center
#         :return: float
#         """
#
#         return min(self.geometry().width(), self.geometry().height()) / 2
#
#     def _inner_radius(self):
#         """
#         Internal function that returns the inner wheel radius from the widget center
#         :return: float
#         """
#
#         return self._outer_radius() - self._wheel_width
#
#     def _square_size(self):
#         """
#         Internal function that calculates the edge length of the inner square
#         :return: float
#         """
#
#         return self._inner_radius() * math.sqrt(2)
#
#     def _triangle_height(self):
#         """
#         Internal function that returns the height of the inner triangle
#         :return: float
#         """
#
#         return self._inner_radius() * 3 / 2
#
#     def _triangle_side(self):
#         """
#         Internal function that returns the side of the inner triangle
#         :return: float
#         """
#
#         return self._inner_radius() * math.sqrt(3)
#
#     def _line_to_point(self, p):
#         """
#         Returns line from center to given point
#         :param p: QPoint
#         :return: QLineF
#         """
#
#         return QLineF(self.geometry().width() / 2, self.geometry().height() / 2, p.x(), p.y())
#
#     def _selector_size(self):
#         """
#         Returns the size of the selector when rendered to the screen
#         :return: QSizeF
#         """
#
#         if self._selector_shape == self.WheelShape.TRIANGLE:
#             return QSizeF(self._triangle_height(), self._triangle_side())
#
#         return QSizeF(self._square_size(), self._square_size())
#
#     def _selector_image_offset(self):
#         """
#         Returns the offset of the selector image
#         :return: QPointF
#         """
#
#         if self._selector_shape == self.WheelShape.TRIANGLE:
#             return QPointF(-self._inner_radius(), -self._triangle_side() / 2)
#
#         return QPointF(-self._square_size() / 2, -self._square_size() / 2)
#
#     def _selector_image_angle(self):
#         if self._selector_shape == self.WheelShape.TRIANGLE:
#             if self._rotating_selector:
#                 return -self._hue * 360 - 60
#             return -150
#         else:
#             if self._rotating_selector:
#                 return -self._hue * 360 - 45
#             else:
#                 return 100
#
#     def _render_square(self):
#         width = min(self._square_size(), self._max_size)
#         for y in range(width):
#             for x in range(width):
#                 color = self._color_from(self._hue, float(x) / width, float(y) / width, 1).rgb()
#                 self._inner_selector_buffer[width * y + x] = color
#
#     def _render_triangle(self):
#         """
#         Internal function that renders the selector as a triangle.
#         Same as the square with the edge with value 0 collapsed to a single point
#         """
#
#         size = self._selector_size()
#         if size.height() > self._max_size:
#             size *= self._max_size / size.height()
#         y_center = size.height() / 2
#         init_size = size.toSize()
#         self._init_buffer(init_size)
#
#         for x in range(init_size.width()):
#             point_val = x / size.height()
#             slice_h = size.height() * point_val
#             for y in range(init_size.height()):
#                 y_min = y_center - slice_h / 2
#                 point_sat = utils.clamp((y - y_min) / slice_h, 0.0, 1.0) if slice_h > 0 else 0
#                 color = self._color_from(self._hue, point_sat, point_val, 1).rgb()
#                 self._inner_selector_buffer[init_size.width() * y + x] = color
#
#     def _render_inner_selector(self):
#         """
#         Internal function that updates the inner image that displays the saturation-value selector
#         """
#
#         if self._selector_shape == self.WheelShape.TRIANGLE:
#             self._render_triangle()
#         else:
#             self._render_square()
#
#     def _render_ring(self):
#         """
#         Internal function that updates the outer ring that displays the hue selector
#         """
#
#         self._hue_ring = QPixmap(self._outer_radius() * 2, self._outer_radius() * 2)
#         self._hue_ring.fill(Qt.transparent)
#         painter = QPainter(self._hue_ring)
#         painter.setRenderHint(QPainter.Antialiasing)
#         painter.setCompositionMode(QPainter.CompositionMode_Source)
#
#         hue_stops = 24
#         gradient_hue = QConicalGradient(0, 0, 0)
#         if len(gradient_hue.stops()) < hue_stops:
#             for a in helpers.float_range(0.0, 1.0, 1.0 / (hue_stops - 1)):
#                 gradient_hue.setColorAt(a, self._rainbow_from_hue(a))
#             gradient_hue.setColorAt(1, self._rainbow_from_hue(0))
#
#         painter.translate(self._outer_radius(), self._outer_radius())
#         painter.setPen(Qt.NoPen)
#         painter.setBrush(QBrush(gradient_hue))
#         painter.drawEllipse(QPointF(0, 0), self._outer_radius(), self._outer_radius())
#         painter.setBrush(Qt.transparent)
#         painter.drawEllipse(QPointF(0, 0), self._inner_radius(), self._inner_radius())
#
#     def _draw_ring_editor(self, editor_hue, painter, color):
#         painter.setPen(QPen(color, 3))
#         painter.setBrush(Qt.NoBrush)
#         ray = QLineF(0, 0, self._outer_radius(), 0)
#         ray.setAngle(editor_hue * 360)
#         h1 = ray.p2()
#         ray.setLength(self._inner_radius())
#         h2 = ray.p2()
#         painter.drawLine(h1, h2)


class ColorPreview(QWidget):
	"""
	Widget that displays a color or compare two colors
	"""

	clicked = Signal()
	backgroundChanged = Signal(QBrush)
	displayModeChanged = Signal(int)
	colorChanged = Signal(QColor)
	comparisonColorChanged = Signal(QColor)

	class DisplayMode(object):
		NO_ALPHA = 0        # Show current color with no transparency
		ALL_ALPHA = 1       # Show current color with transparency
		SPLIT_ALPHA = 2     # Show both solid and transparent side by side
		SPLIT_COLOR = 3     # Show current and comparison colors side by side

	def __init__(self, parent=None):
		super(ColorPreview, self).__init__(parent)

		self._col = QColor(Qt.red)
		self._comparison = QColor()
		self._background = QBrush(Qt.darkGray, Qt.DiagCrossPattern)
		self._display_mode = self.DisplayMode.NO_ALPHA

		self._background.setTexture(QPixmap(resources.pixmap('alpha_back')))

	def sizeHint(self):
		return QSize(24, 24)

	def resizeEvent(self, event):
		self.update()

	def paintEvent(self, even):
		painter = QStylePainter(self)
		self._paint(painter, self.geometry())

	def mouseReleaseEvent(self, event):
		if QRect(QPoint(0, 0), self.size()).contains(event.pos()):
			self.clicked.emit()

	def mouseMoveEvent(self, event):
		if event.buttons() & Qt.LeftButton and not QRect(QPoint(0, 0), self.size()).contains(event.pos()):
			data = QMimeData()
			data.setColorData(self._col)
			drag = QDrag(self)
			drag.setMimeData(data)
			preview = QPixmap(24, 24)
			preview.fill(self._col)
			drag.setPixmap(preview)
			drag.exec_()

	def color(self):
		return self._col

	def set_color(self, color):
		if isinstance(color, (tuple, list)):
			color = QColor(*color)
		self._col = color
		self.update()
		self.colorChanged.emit(color)

	def comparison_color(self):
		return self._comparison

	def set_comparison_color(self, color):
		self._comparison = color
		self.update()
		self.comparisonColorChanged.emit(color)

	def background(self):
		return self._background

	def set_background(self, back):
		self._background = back
		self.update()
		self.backgroundChanged.emit(back)

	def display_mode(self):
		return self._display_mode

	def set_display_mode(self, mode):
		self._display_mode = mode
		self.update()
		self.displayModeChanged.emit(mode)

	def _paint(self, painter, rect):
		c1 = QColor()
		c2 = QColor()
		if self._display_mode == self.DisplayMode.NO_ALPHA:
			c1 = QColor(self._col.rgb())
			c2 = QColor(self._col.rgb())
		elif self._display_mode == self.DisplayMode.ALL_ALPHA:
			c1 = self._col
			c2 = self._col
		elif self._display_mode == self.DisplayMode.SPLIT_ALPHA:
			c1 = QColor(self._col.rgb())
			c2 = self._col
		elif self._display_mode == self.DisplayMode.SPLIT_COLOR:
			c1 = self._comparison
			c2 = self._col

		panel = QStyleOptionFrame()
		panel.initFrom(self)
		panel.lineWidth = 2
		panel.midLineWidth = 0
		panel.state |= QStyle.State_Sunken
		self.style().drawPrimitive(QStyle.PE_Frame, panel, painter, self)
		r = self.style().subElementRect(QStyle.SE_FrameContents, panel, self)
		painter.setClipRect(r)

		if c1.alpha() < 255 or c2.alpha() < 255:
			painter.fillRect(0, 0, rect.width(), rect.height(), self._background)

		w = rect.width() / 2
		h = rect.height()
		painter.fillRect(0, 0, w, h, c1)
		painter.fillRect(w, 0, w, h, c2)


# class ColorSelector(ColorPreview):
#     """
#     Widget that displays a color selector dialog when the user clicks on it
#     """
#
#     updateModeChanged = Signal(int)
#     showModeChanged = Signal(int)
#     dialogModalityChanged = Signal(Qt.WindowModality)
#     acceptedColor = Signal(object)
#     closedColor = Signal(object)
#
#     class UpdateMode(object):
#         CONFIRM = 0         # Update color only after the dialog has been accepted
#         CONTINUOUS = 1      # Update color as it is being modified in the dialog
#
#     class ShowMode(object):
#         DIALOG = 0          # Color select will appear in a new dialog
#         PANEL = 1           # Color select will appear in a slider panel
#
#     def __init__(self, parent=None):
#         super(ColorSelector, self).__init__(parent)
#
#         self._update_mode = None
#         self._old_color = QColor()
#         self._color_widget = ColorDialogWidget()
#         self._color_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self._dialog_modality = None
#         self._dialog = None
#         self._panel = None
#         self._show_mode = None
#         self._panel_parent = parent
#         self._reset_on_close = True
#
#         self.set_update_mode(self.UpdateMode.CONTINUOUS)
#         self.set_show_mode(self.ShowMode.PANEL)
#
#         self._old_color = self.color()
#
#         self.setAcceptDrops(True)
#
#         self.colorChanged.connect(self._on_update_old_color)
#
#         self.clicked.connect(self._on_show)
#
#     def dragEnterEvent(self, event):
#         if event.mimeData().hasColor() or (event.mimeData().hasText() and QColor(event.mimeData().text()).isValid()):
#             event.acceptProposedAction()
#
#     def dropEvent(self, event):
#         if event.mimeData().hasColor():
#             self.set_color(event.mimeData().colorData().value())
#             event.accept()
#         elif event.mimeData().hasText():
#             col = QColor(event.mimeData().text())
#             if col.isValid():
#                 self.set_color(col)
#                 event.accept()
#
#     def update_mode(self):
#         return self._update_mode
#
#     def set_update_mode(self, mode):
#         self._update_mode = mode
#         self.updateModeChanged.emit(mode)
#
#     def show_mode(self):
#         return self._show_mode
#
#     def set_show_mode(self, mode):
#         self._show_mode = mode
#         self.showModeChanged.emit(mode)
#
#     def dialog_modality(self):
#         return self._dialog_modality
#
#     def set_dialog_modality(self, modality):
#         self._dialog_modality = modality
#         self.dialogModalityChanged.emit(modality)
#
#     def set_reset_on_close(self, flag):
#         self._reset_on_close = flag
#
#     def wheel_shape(self):
#         return self._color_widget.wheel_shape()
#
#     def set_wheel_shape(self, shape):
#         self._color_widget.set_wheel_shape(shape)
#
#     def color_space(self):
#         return self._color_widget.color_space()
#
#     def set_color_space(self, color_space):
#         self._color_widget.set_color_space(color_space)
#
#     def wheel_rotating(self):
#         return self._color_widget.wheel_rotating()
#
#     def set_wheel_rotating(self, flag):
#         self._color_widget.set_wheel_rotation(flag)
#
#     def set_panel_parent(self, parent):
#         self._panel_parent = parent
#
#     def show_panel(self):
#         self._color_widget._select_color_btn.setVisible(True)
#         self._color_widget._cancel_btn.setVisible(True)
#         self._panel = panel.SliderPanel(
#             'Select Color', parent=self._panel_parent or self.parent(), closable=True)
#         self.set_update_mode(self.UpdateMode.CONTINUOUS)
#         self._panel.set_widget(self._color_widget)
#         self._panel.closed.connect(self._on_close_panel)
#         self._connect_panel()
#         self._panel.show()
#
#     def show_dialog(self):
#         self._color_widget._select_color_btn.setVisible(False)
#         self._color_widget._cancel_btn.setVisible(False)
#         self._dialog = ColorDialog(color_widget=self._color_widget, parent=self)
#         if self._dialog_modality:
#             self._dialog.setWindowModality(self._dialog_modality)
#         self._dialog.setWindowTitle('Select Color')
#         self._dialog.set_button_mode(ColorDialog.ButtonMode.OK_CANCEL)
#         self._dialog.set_color(self.color())
#         self._connect_dialog(self._dialog)
#         self._dialog.rejected.connect(self._on_rejected_dialog)
#         self._dialog.exec_()
#
#     def _connect_panel(self):
#         self._color_widget.colorSelected.connect(self._on_selected_panel_color)
#         self._color_widget.colorCancelled.connect(self._panel.close)
#         if self._update_mode == self.UpdateMode.CONTINUOUS:
#             self._color_widget.colorChanged.connect(self.set_color)
#         else:
#             self._disconnect_panel()
#
#     def _disconnect_panel(self):
#         self._color_widget.colorSelected.disconnect(self._on_selected_panel_color)
#         self._color_widget.colorCancelled.disconnect(self._panel.close)
#         if self._update_mode == self.UpdateMode.CONTINUOUS:
#             self._color_widget.colorChanged.disconnect(self.set_color)
#
#     def _disconnect_dialog(self, dialog):
#         dialog.colorChanged.disconnect(self.set_color)
#         dialog.accepted.disconnect(self._on_accepted_dialog)
#         dialog.rejected.disconnect(self._on_rejected_dialog)
#
#     def _connect_dialog(self, dialog):
#         if self._update_mode == self.UpdateMode.CONTINUOUS:
#             dialog.colorChanged.connect(self.set_color)
#             dialog.accepted.connect(self._on_accepted_dialog)
#             dialog.rejected.connect(self._on_rejected_dialog)
#         else:
#             self._disconnect_dialog(dialog)
#
#     def _on_update_old_color(self, color):
#         if (self._dialog and not self._dialog.isVisible()) or (self._panel and not self._panel.isVisible()):
#             self._old_color = color
#
#     def _on_selected_panel_color(self, color):
#         self.set_color(color)
#         self._panel.blockSignals(True)
#         try:
#             self._panel.close()
#         finally:
#             self._panel.blockSignals(False)
#         self.acceptedColor.emit(self.color())
#         self._disconnect_panel()
#
#     def _on_close_panel(self):
#         if self._reset_on_close:
#             self.set_color(self._old_color)
#             self._color_widget.set_color(self._old_color)
#         self.closedColor.emit(self.color())
#         self._disconnect_panel()
#
#     def _on_accepted_dialog(self):
#         self.set_color(self._dialog.color())
#         self._old_color = self.color()
#         self._dialog = None
#         self.acceptedColor.emit(self.color())
#
#     def _on_rejected_dialog(self):
#         self.set_color(self._old_color)
#         self._dialog = None
#
#     def _on_show(self):
#         self._old_color = self.color()
#         self._color_widget.set_color(self.color())
#         self._color_widget.set_comparison_color(self.comparison_color())
#         if self._show_mode == self.ShowMode.PANEL:
#             self.show_panel()
#         else:
#             self.show_dialog()


class GradientSlider(QSlider):
	"""
	Custom QSlider that uses a gradient as its background
	"""

	backgroundChanged = Signal(QBrush)

	def __init__(self, orientation=Qt.Horizontal, parent=None):
		super(GradientSlider, self).__init__(orientation, parent)

		self._gradient = QLinearGradient()
		self._background = QBrush(Qt.darkGray, Qt.DiagCrossPattern)
		self._background.setTexture(QPixmap(resources.pixmap('alpha_back')))
		self._gradient.setCoordinateMode(QGradient.StretchToDeviceMode)
		self._gradient.setSpread(QGradient.RepeatSpread)

		self.setMinimum(0)
		self.setMaximum(255)

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			event.accept()
			self.setSliderDown(True)
			self._mouse_event(event, self)
			self.update()
		else:
			super(GradientSlider, self).mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if event.buttons() & Qt.LeftButton:
			event.accept()
			self._mouse_event(event, self)
			self.update()
		else:
			super(GradientSlider, self).mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		if event.button() & Qt.LeftButton:
			event.accept()
			self.setSliderDown(False)
			self.update()
		else:
			super(GradientSlider, self).mousePressEvent(event)

	def paintEvent(self, event):
		painter = QPainter(self)
		panel = QStyleOptionFrame()
		panel.initFrom(self)
		panel.lineWidth = 1
		panel.midLineWidth = 0
		panel.state |= QStyle.State_Sunken
		self.style().drawPrimitive(QStyle.PE_Frame, panel, painter, self)
		r = self.style().subElementRect(QStyle.SE_FrameContents, panel, self)
		painter.setClipRect(r)

		gradient_direction = -1 if self.invertedAppearance() else 1
		if self.orientation() == Qt.Horizontal:
			self._gradient.setFinalStop(gradient_direction, 0)
		else:
			self._gradient.setFinalStop(0, -gradient_direction)

		painter.setPen(Qt.NoPen)
		painter.setBrush(self._background)
		painter.drawRect(1, 1, self.geometry().width() - 2, self.geometry().height() - 2)
		painter.setBrush(self._gradient)
		painter.drawRect(1, 1, self.geometry().width() - 2, self.geometry().height() - 2)

		pos = float(self.value() - self.minimum()) / self.maximum() if self.maximum() != 0 else 0
		color = QColor()
		stops = self._gradient.stops()

		index = 0
		for i in range(len(stops)):
			if stops[i][0] > pos:
				break
			index += 1

		if index == 0:
			color = self.first_color()
		elif i == len(stops):
			color = self.last_color()
		else:
			stop_a = stops[i - 1]
			stop_b = stops[i]
			stop_c = stop_b[0] - stop_a[0]
			factor = (pos - stop_a[0]) / stop_c if stop_c != 0 else 0
			color = QColor.fromRgbF(
				stop_b[1].redF() * factor + stop_a[1].redF() * (1.0 - factor),
				stop_b[1].greenF() * factor + stop_a[1].greenF() * (1.0 - factor),
				stop_b[1].blueF() * factor + stop_a[1].blueF() * (1.0 - factor),
				stop_b[1].alphaF() * factor + stop_a[1].alphaF() * (1.0 - factor))

		pos = pos * (self.geometry().width() - 5)
		if color.valueF() > 0.5 or color.alphaF() < 0.5:
			painter.setPen(QPen(Qt.black, 3))
		else:
			painter.setPen(QPen(Qt.white, 3))

		p1 = QPointF(2.5, 2.5) + QPointF(pos, 0)
		p2 = p1 + QPointF(0, self.geometry().height() - 5)
		painter.drawLine(p1, p2)

	def background(self):
		return self._background

	def set_background(self, back):
		self._background = back
		self.update()
		self.backgroundChanged.emit(back)

	def colors(self):
		return self._gradient.stops()

	def set_stop_colors(self, stop_colors):
		self._gradient.setStops(stop_colors)
		self.update()

	def set_colors(self, colors):

		stops = list()
		colors = colors if colors is not None else list()
		colors.reverse()

		total_colors = len(colors) - 1
		if total_colors == 0:
			stops.append((0, colors[0]))
		else:
			for i in range(len(colors)):
				stops.append((i / total_colors, colors[i]))

		self.set_stop_colors(stops)

	def first_color(self):
		stops = self.colors() or list()
		return QColor() if not stops else stops[0]

	def set_first_color(self, color):
		stops = self._gradient.stops() or list()
		if not stops:
			stops.append((0.0, color))
		else:
			stops[0] = (stops[0][0], color)
		self._gradient.setStops(stops)
		self.update()

	def last_color(self):
		stops = self._gradient.stops() or list()
		return QColor() if not stops else stops[-1]

	def set_last_color(self, color):
		stops = self._gradient.stops() or list()
		if len(stops) < 2:
			stops.append((1.0, color))
		else:
			stops[-1] = (stops[-1][0], color)
		self._gradient.setStops(stops)
		self.update()

	def gradient(self):
		return self._gradient

	def set_gradient(self, gradient):
		self._gradient = gradient
		self.update()

	def _mouse_event(self, event, slider_owner):
		if slider_owner.geometry().width() > 5:
			pos = float(event.pos().x() - 2.5) / (slider_owner.geometry().width() - 5)
		else:
			pos = 0
		slider_owner.setSliderPosition(
			round(slider_owner.minimum() + pos * (slider_owner.maximum() - slider_owner.minimum())))


# class HueSlider(GradientSlider):
#     """
#     Special gradient slider to select a hue
#     """
#
#     colorSaturationChanged = Signal(float)
#     colorValueChanged = Signal(float)
#     colorHueChanged = Signal(float)
#     colorAlphaChanged = Signal(float)
#     colorChanged = Signal(QColor)
#
#     def __init__(self, orientation=Qt.Horizontal, parent=None):
#         super(HueSlider, self).__init__(orientation=orientation, parent=parent)
#
#         self._saturation = 1
#         self._value = 1
#         self._alpha = 1
#
#         self.setRange(0, 359)
#         self.valueChanged.connect(self._on_value_changed)
#         self._update_gradient()
#
#     def color(self):
#         return QColor.fromHsvF(self.color_hue(), self._saturation, self._value, self._alpha)
#
#     def set_color(self, color):
#         self._saturation = color.saturationF()
#         self._value = color.valueF()
#         self._update_gradient()
#         self.set_color_hue(color.hueF())
#         self.colorValueChanged.emit(self._alpha)
#         self.colorSaturationChanged.emit(self._alpha)
#
#     def set_full_color(self, color):
#         self._alpha = color.alphaF()
#         self.set_color(color)
#         self.colorAlphaChanged.emit(self._alpha)
#
#     def color_saturation(self):
#         return self._saturation
#
#     def set_color_saturation(self, saturation):
#         self._saturation = utils.clamp(saturation, 0.0, 1.0)
#         self._update_gradient()
#         self.colorSaturationChanged.emit(saturation)
#
#     def color_value(self):
#         return self._value
#
#     def set_color_value(self, value):
#         self._value = utils.clamp(value, 0.0, 1.0)
#         self._update_gradient()
#         self.colorValueChanged.emit(value)
#
#     def color_hue(self):
#         if self.maximum() == self.minimum():
#             return 0
#         hue = float(self.value() - self.minimum()) / (self.maximum() - self.minimum())
#         if self.orientation() == Qt.Vertical:
#             hue = 1 - hue
#
#         return hue
#
#     def set_color_hue(self, color_hue):
#         if self.orientation() == Qt.Vertical:
#             color_hue = 1 - color_hue
#         self.setValue(self.maximum() + color_hue * (self.maximum() - self.minimum()))
#         self.colorHueChanged.emit(color_hue)
#         self.colorChanged.emit(self.color())
#
#     def color_alpha(self):
#         return self._alpha
#
#     def set_color_alpha(self, alpha):
#         self._alpha = alpha
#         self._update_gradient()
#         self.colorAlphaChanged.emit(alpha)
#
#     def _update_gradient(self):
#         num_colors = 6
#         colors = list()
#         for i in range(num_colors):
#             colors.append((i / num_colors, QColor.fromHsvF(i / num_colors, self._saturation, self._value)))
#         self.set_stop_colors(colors)
#
#     def _on_value_changed(self):
#         self.colorHueChanged.emit(self.color_hue())
#         self.colorChanged.emit(self.color())


# class ColorDialogWidget(QWidget):
#     """
#     Dialog similar to QColorDialog but more user friendly
#     """
#
#     colorSelected = Signal(QColor)
#     colorChanged = Signal(QColor)
#     colorCancelled = Signal()
#     alphaEnabledChanged = Signal(bool)
#     colorSpaceChanged = Signal(int)
#     rotatingSelectorChanged = Signal(bool)
#     selectorShapeChanged = Signal(int)
#
#     def __init__(self, parent=None):
#         self._color = QColor()
#         self._color_list = (0, 0, 0, 255)
#         self._alpha_enabled = False
#         self._pick_from_screen = False
#
#         super(ColorDialogWidget, self).__init__(parent)
#
#         self.setAcceptDrops(True)
#         self.set_alpha_enabled(True)
#
#     # =================================================================================================================
#     # OVERRIDES
#     # =================================================================================================================
#
#     def get_main_layout(self):
#         main_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0,))
#
#         return main_layout
#
#     def ui(self):
#         super(ColorDialogWidget, self).ui()
#
#         horizontal_lyt = layouts.HorizontalLayout(spacing=2, margins=(0, 0, 0, 0,))
#         preview_wheel_lyt = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0,))
#         self._buttons_lyt = layouts.HorizontalLayout(spacing=2, margins=(0, 0, 0, 0,))
#
#         self._color_wheel = ColorWheel()
#         self._color_preview = ColorPreview()
#         preview_wheel_lyt.addWidget(self._color_wheel)
#         preview_wheel_lyt.addWidget(self._color_preview)
#
#         colors_lyt = layouts.GridLayout()
#         hue_lbl = label.BaseLabel('Hue')
#         self._hue_slider = HueSlider()
#         self._hue_spinner = spinbox.BaseSpinBox()
#         saturation_lbl = label.BaseLabel('Saturation')
#         self._saturation_slider = GradientSlider()
#         self._saturation_spinner = spinbox.BaseSpinBox()
#         value_lbl = label.BaseLabel('Value')
#         self._value_slider = GradientSlider()
#         self._value_spinner = spinbox.BaseSpinBox()
#         red_lbl = label.BaseLabel('Red')
#         self._red_slider = GradientSlider()
#         self._red_spinner = spinbox.BaseSpinBox()
#         green_lbl = label.BaseLabel('Green')
#         self._green_slider = GradientSlider()
#         self._green_spinner = spinbox.BaseSpinBox()
#         blue_lbl = label.BaseLabel('Blue')
#         self._blue_slider = GradientSlider()
#         self._blue_spinner = spinbox.BaseSpinBox()
#         self._alpha_lbl = label.BaseLabel('Alpha')
#         self._alpha_slider = GradientSlider()
#         self._alpha_spinner = spinbox.BaseSpinBox()
#         hex_lbl = label.BaseLabel('Hex')
#         self._hex_line = ColorLineEdit()
#
#         for spn in [self._hue_spinner, self._saturation_spinner, self._value_spinner, self._red_spinner,
#                     self._green_spinner, self._blue_spinner, self._alpha_spinner]:
#             spn.setMinimum(0)
#             spn.setMaximum(255)
#
#         colors_lyt.addWidget(hue_lbl, 0, 0)
#         colors_lyt.addWidget(self._hue_slider, 0, 1)
#         colors_lyt.addWidget(self._hue_spinner, 0, 2)
#         colors_lyt.addWidget(saturation_lbl, 1, 0)
#         colors_lyt.addWidget(self._saturation_slider, 1, 1)
#         colors_lyt.addWidget(self._saturation_spinner, 1, 2)
#         colors_lyt.addWidget(value_lbl, 2, 0)
#         colors_lyt.addWidget(self._value_slider, 2, 1)
#         colors_lyt.addWidget(self._value_spinner, 2, 2)
#         colors_lyt.addWidget(dividers.Divider(), 3, 0, 1, 3)
#         colors_lyt.addWidget(red_lbl, 4, 0)
#         colors_lyt.addWidget(self._red_slider, 4, 1)
#         colors_lyt.addWidget(self._red_spinner, 4, 2)
#         colors_lyt.addWidget(green_lbl, 5, 0)
#         colors_lyt.addWidget(self._green_slider, 5, 1)
#         colors_lyt.addWidget(self._green_spinner, 5, 2)
#         colors_lyt.addWidget(blue_lbl, 6, 0)
#         colors_lyt.addWidget(self._blue_slider, 6, 1)
#         colors_lyt.addWidget(self._blue_spinner, 6, 2)
#         self._alpha_divider = dividers.Divider()
#         colors_lyt.addWidget(self._alpha_divider, 7, 0, 1, 3)
#         colors_lyt.addWidget(self._alpha_lbl, 8, 0)
#         colors_lyt.addWidget(self._alpha_slider, 8, 1)
#         colors_lyt.addWidget(self._alpha_spinner, 8, 2)
#         colors_lyt.addWidget(dividers.Divider(), 9, 0, 1, 3)
#         colors_lyt.addWidget(hex_lbl, 10, 0)
#         colors_lyt.addWidget(self._hex_line, 10, 1, 1, 2)
#         colors_lyt.addWidget(dividers.Divider(), 11, 0, 1, 3)
#
#         self._reset_btn = buttons.BaseToolButton().image('reset').text_under_icon()
#         self._pick_btn = buttons.BaseToolButton().image('color_dropper').text_under_icon()
#
#         horizontal_lyt.addLayout(preview_wheel_lyt)
#         horizontal_lyt.addLayout(colors_lyt)
#
#         self._buttons_lyt.addWidget(self._reset_btn)
#         self._buttons_lyt.addWidget(self._pick_btn)
#         self._buttons_lyt.addStretch()
#
#         bottom_layout = layouts.HorizontalLayout(spacing=1, margins=(0, 0, 0, 0))
#         self._select_color_btn = buttons.BaseButton('Select', resources.icon('palette'), parent=self)
#         self._cancel_btn = buttons.BaseButton('Cancel', resources.icon('cancel'), parent=self)
#         bottom_layout.addStretch()
#         bottom_layout.addWidget(self._select_color_btn)
#         bottom_layout.addWidget(self._cancel_btn)
#
#         self.main_layout.addLayout(horizontal_lyt)
#         self.main_layout.addWidget(dividers.Divider())
#         self.main_layout.addLayout(self._buttons_lyt)
#         self.main_layout.addStretch()
#         self.main_layout.addLayout(bottom_layout)
#
#     def setup_signals(self):
#         self._color_wheel.colorSpaceChanged.connect(self.colorSpaceChanged.emit)
#         self._color_wheel.selectorShapeChanged.connect(self.selectorShapeChanged.emit)
#         self._color_wheel.rotatingSelectorChanged.connect(self.rotatingSelectorChanged.emit)
#
#         self._color_wheel.colorSelected.connect(self._set_color)
#         self._value_spinner.valueChanged.connect(self._value_slider.setValue)
#         self._saturation_spinner.valueChanged.connect(self._saturation_slider.setValue)
#         self._hue_spinner.valueChanged.connect(self._hue_slider.setValue)
#         self._red_spinner.valueChanged.connect(self._red_slider.setValue)
#         self._green_spinner.valueChanged.connect(self._green_slider.setValue)
#         self._blue_spinner.valueChanged.connect(self._blue_slider.setValue)
#         self._alpha_spinner.valueChanged.connect(self._alpha_slider.setValue)
#
#         self._value_slider.valueChanged.connect(self.set_hsv)
#         self._value_slider.valueChanged.connect(self._value_spinner.setValue)
#         self._saturation_slider.valueChanged.connect(self.set_hsv)
#         # TODO: Check why this was causing crash when moving saturation slider
#         # self._saturation_slider.valueChanged.connect(self._saturation_spinner.setValue)
#         self._hue_slider.valueChanged.connect(self.set_hsv)
#         # TODO: Check why this was causing crash when moving hue slider
#         # self._hue_slider.valueChanged.connect(self._hue_spinner.setValue)
#         self._red_slider.valueChanged.connect(self.set_rgb)
#         self._red_slider.valueChanged.connect(self._red_spinner.setValue)
#         self._green_slider.valueChanged.connect(self.set_rgb)
#         self._green_slider.valueChanged.connect(self._green_spinner.setValue)
#         self._blue_slider.valueChanged.connect(self.set_rgb)
#         self._blue_slider.valueChanged.connect(self._blue_spinner.setValue)
#         self._alpha_slider.valueChanged.connect(self.set_alpha)
#         self._alpha_slider.valueChanged.connect(self._alpha_spinner.setValue)
#
#         self._hex_line.colorChanged.connect(self._on_edit_hex_color_changed)
#         self._hex_line.colorEditingFinished.connect(self._on_edit_hex_color_editing_finished)
#
#         self._pick_btn.clicked.connect(self._on_grab_color)
#         self._reset_btn.clicked.connect(self._on_reset)
#
#         self._select_color_btn.clicked.connect(self._on_select_color)
#         self._cancel_btn.clicked.connect(self.colorCancelled.emit)
#
#     def enable_select_cancel_buttons(self, flag):
#         self._cancel_btn.setVisible(flag)
#         self._cancel_btn.setEnabled(flag)
#         self._select_color_btn.setVisible(flag)
#         self._select_color_btn.setEnabled(flag)
#
#     def dragEnterEvent(self, event):
#         if event.mimeData().hasColor() or (event.mimeData().hasText() and QColor(event.mimeData().text()).isValid()):
#             event.acceptProposedAction()
#
#     def dropEvent(self, event):
#         if event.mimeData().hasColor():
#             self._set_color(event.mimeData().colorData().value())
#             event.accept()
#         elif event.mimeData().hasText():
#             col = QColor(event.mimeData().text())
#             if col.isValid():
#                 self._set_color(col)
#                 event.accept()
#
#     def mouseMoveEvent(self, event):
#         if self._pick_from_screen:
#             self._set_color(qtutils.get_screen_color(event.globalPos()))
#
#     def mouseReleaseEvent(self, event):
#         if self._pick_from_screen:
#             self._set_color(qtutils.get_screen_color(event.globalPos()))
#             self._pick_from_screen = False
#             self.releaseMouse()
#
#     # =================================================================================================================
#     # BASE
#     # =================================================================================================================
#
#     def get_color(self):
#         col = self._color
#         if not self._alpha_enabled:
#             col.setAlpha(255)
#
#         return col
#
#     def set_color(self, color):
#         self._color_preview.set_comparison_color(color)
#         self._hex_line.setModified(False)
#         self._set_color(color)
#
#     def get_color_list(self):
#         return self._color_list
#
#     def set_color_list(self, color_list):
#         self._color_list = color_list
#         self.blockSignals(True)
#         widgets = self.findChildren(QWidget)
#         for widget in widgets:
#             widget.blockSignals(True)
#         try:
#             self.set_color(QColor(*color_list))
#         finally:
#             self.blockSignals(False)
#             for widget in widgets:
#                 widget.blockSignals(False)
#
#     colorList = Property(tuple, get_color_list, set_color_list, user=True)
#
#     def comparison_color(self):
#         return self._color_preview.comparison_color()
#
#     def set_comparison_color(self, color):
#         self._color_preview.set_comparison_color(color)
#
#     def preview_display_mode(self):
#         return self._color_preview.display_mode()
#
#     def set_preview_display_mode(self, mode):
#         self._color_preview.set_display_mode(mode)
#
#     def alpha_enabled(self):
#         return self._alpha_enabled
#
#     def set_alpha_enabled(self, flag):
#         self._alpha_enabled = flag
#         self._hex_line.set_show_alpha(flag)
#         self._alpha_divider.setVisible(flag)
#         self._alpha_lbl.setVisible(flag)
#         self._alpha_slider.setVisible(flag)
#         self._alpha_spinner.setVisible(flag)
#         self.alphaEnabledChanged.emit(flag)
#         if flag:
#             self._color_preview.set_display_mode(ColorPreview.DisplayMode.SPLIT_ALPHA)
#         else:
#             self._color_preview.set_display_mode(ColorPreview.DisplayMode.NO_ALPHA)
#
#     def set_hsv(self):
#         if not self.signalsBlocked():
#             color = QColor.fromHsv(
#                 self._hue_slider.value(), self._saturation_slider.value(),
#                 self._value_slider.value(), self._alpha_slider.value())
#             self._color_wheel.set_color(color)
#             self._set_color(color)
#
#     def set_alpha(self):
#         if not self.signalsBlocked():
#             color = self._color
#             color.setAlpha(self._alpha_slider.value())
#             self._color_wheel.set_color(color)
#             self._set_color(color)
#
#     def set_rgb(self):
#         if not self.signalsBlocked():
#             color = QColor(
#                 self._red_slider.value(), self._green_slider.value(),
#                 self._blue_slider.value(), self._alpha_slider.value())
#             if color.saturation() == 0:
#                 color = QColor.fromHsv(self._hue_slider.value(), 0, color.value())
#             self._color_wheel.set_color(color)
#             self._set_color(color)
#
#     def wheel_shape(self):
#         return self._color_wheel.selector_shape()
#
#     def set_wheel_shape(self, shape):
#         self._color_wheel.set_selector_shape(shape)
#
#     def color_space(self):
#         return self._color_wheel.color_space()
#
#     def set_color_space(self, color_space):
#         self._color_wheel.set_color_space(color_space)
#
#     def wheel_rotating(self):
#         return self._color_wheel.rotating_selector()
#
#     def set_wheel_rotation(self, flag):
#         self._color_wheel.set_rotating_selector(flag)
#
#     def _set_color(self, color):
#
#         if isinstance(color, (tuple, list)):
#             color = QColor(*color)
#         alpha = self._color.alphaF()
#         self._color = color
#         self._color_list = color.red(), color.green(), color.blue(), color.alpha()
#
#         self._color_wheel.set_color(color)
#
#         blocked = self.signalsBlocked()
#         self.blockSignals(True)
#         for widget in self.findChildren(QWidget):
#             widget.blockSignals(True)
#
#         self._red_slider.setValue(color.red())
#         self._red_spinner.setValue(self._red_slider.value())
#         self._red_slider.set_first_color(QColor(0, color.green(), color.blue()))
#         self._red_slider.set_last_color(QColor(255, color.green(), color.blue()))
#
#         self._green_slider.setValue(color.green())
#         self._green_spinner.setValue(self._green_slider.value())
#         self._green_slider.set_first_color(QColor(color.red(), 0, color.blue()))
#         self._green_slider.set_last_color(QColor(color.red(), 255, color.blue()))
#
#         self._blue_slider.setValue(color.blue())
#         self._blue_slider.setValue(self._blue_slider.value())
#         self._blue_slider.set_first_color(QColor(color.red(), color.green(), 0))
#         self._blue_slider.set_last_color(QColor(color.red(), color.green(), 255))
#
#         self._hue_slider.setValue(round(self._color_wheel.hue() * 360.0))
#         self._hue_slider.set_color_saturation(self._color_wheel.saturation())
#         self._hue_slider.set_color_value(self._color_wheel.value())
#         self._hue_spinner.setValue(self._hue_slider.value())
#
#         self._saturation_slider.setValue(round(self._color_wheel.saturation() * 255.0))
#         self._saturation_spinner.setValue(self._saturation_slider.value())
#         self._saturation_slider.set_first_color(QColor.fromHsvF(self._color_wheel.hue(), 0, self._color_wheel.value()))
#         self._saturation_slider.set_last_color(QColor.fromHsvF(self._color_wheel.hue(), 1, self._color_wheel.value()))
#
#         self._value_slider.setValue(round(self._color_wheel.value() * 255.0))
#         self._value_spinner.setValue(self._value_slider.value())
#         self._value_slider.set_first_color(QColor.fromHsvF(self._color_wheel.hue(), self._color_wheel.saturation(), 0))
#         self._value_slider.set_last_color(QColor.fromHsvF(self._color_wheel.hue(), self._color_wheel.saturation(), 1))
#
#         color.setAlphaF(alpha)
#         alpha_color = QColor(color)
#         alpha_color.setAlpha(0)
#         self._alpha_slider.set_first_color(alpha_color)
#         alpha_color.setAlpha(255)
#         self._alpha_slider.set_last_color(alpha_color)
#         self._alpha_spinner.setValue(color.alpha())
#         self._alpha_slider.setValue(color.alpha())
#         if not self._hex_line.isModified():
#             self._hex_line.set_color(color)
#         self._color_preview.set_color(color)
#
#         self.blockSignals(blocked)
#         for w in self.findChildren(QWidget):
#             w.blockSignals(False)
#
#         self.colorChanged.emit(color)
#
#     # =================================================================================================================
#     # CALLBACKS
#     # =================================================================================================================
#
#     def _on_edit_hex_color_changed(self, color):
#         self._set_color(color)
#
#     def _on_edit_hex_color_editing_finished(self, color):
#         self._hex_line.setModified(False)
#         self._set_color(color)
#
#     def _on_grab_color(self):
#         self.grabMouse(Qt.CrossCursor)
#         self._pick_from_screen = True
#
#     def _on_reset(self):
#         self._set_color(self._color_preview.comparison_color())
#
#     def _on_select_color(self):
#         current_color = self.get_color()
#         self.colorSelected.emit(current_color)


# class ColorDialog(QDialog):
#
#     colorChanged = Signal(QColor)
#     colorSelected = Signal(QColor)
#
#     class ButtonMode(object):
#         OK_CANCEL = 0
#         OK_APPLY_CANCEL = 1
#         CLOSE = 2
#
#     def __init__(self, color_widget=None, parent=None):
#         super(ColorDialog, self).__init__(parent)
#
#         self.setWindowTitle('Color Selector')
#
#         self._button_mode = self.ButtonMode.OK_CANCEL
#
#         main_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
#         self.setLayout(main_layout)
#
#         self._color_widget = color_widget or ColorDialogWidget()
#         self._color_widget.colorChanged.connect(self.colorChanged.emit)
#         self._color_widget.colorSelected.connect(self.colorSelected.emit)
#         self._color_widget.enable_select_cancel_buttons(False)
#
#         self._button_box = QDialogButtonBox()
#         self._button_box.setStandardButtons(
#             QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply | QDialogButtonBox.Reset)
#
#         self._button_box.clicked.connect(self._on_button_box_clicked)
#         self._button_box.accepted.connect(self.accept)
#         self._button_box.rejected.connect(self.reject)
#
#         main_layout.addWidget(self._color_widget)
#         main_layout.addWidget(self._button_box)
#
#     # def sizeHint(self):
#     #     return QSize(400, 0)
#
#     def color(self):
#         return self._color_widget.get_color()
#
#     def set_color(self, color):
#         self._color_widget.set_color(color)
#
#     def button_mode(self):
#         return self._button_mode
#
#     def set_button_mode(self, mode):
#         self._button_mode = mode
#         _buttons = QDialogButtonBox.StandardButtons
#         if mode == self.ButtonMode.OK_CANCEL:
#             _buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
#         elif mode == self.ButtonMode.OK_APPLY_CANCEL:
#             _buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply | QDialogButtonBox.Reset
#         elif mode == self.ButtonMode.CLOSE:
#             _buttons = QDialogButtonBox.Close
#         self._button_box.setStandardButtons(_buttons)
#
#     def wheel_shape(self):
#         return self._color_widget.selector_shape()
#
#     def set_wheel_shape(self, shape):
#         self._color_widget.set_selector_shape(shape)
#
#     def color_space(self):
#         return self._color_widget.color_space()
#
#     def set_color_space(self, color_space):
#         self._color_widget.set_color_space(color_space)
#
#     def wheel_rotating(self):
#         return self._color_widget.rotating_selector()
#
#     def set_wheel_rotation(self, flag):
#         self._color_widget.set_rotating_selector(flag)
#
#     def _on_button_box_clicked(self, btn):
#         role = self._button_box.buttonRole(btn)
#         if role == QDialogButtonBox.AcceptRole or role == QDialogButtonBox.ApplyRole:
#             self._color_widget._color_preview.set_comparison_color(self._color_widget.get_color())
#             self._color_widget.colorSelected.emit(self._color_widget.get_color())


# class ColorRgbGradientSlider(sliders.DoubleSlider):
#     """
#     Custom slider to select a color by non editable gradient
#     """
#
#     def __init__(self, parent, color1=None, color2=None, slider_range=None, dragger_steps=None, main_color=None, *args):
#         if color1 is None:
#             color1 = [0, 0, 0]
#         if color2 is None:
#             color2 = [255, 255, 255]
#         if slider_range is None:
#             slider_range = (0.0, 255.0)
#         if dragger_steps is None:
#             dragger_steps = [5.0, 1.0, 0.25]
#         super(ColorRgbGradientSlider, self).__init__(
#             parent=parent, slider_range=slider_range, dragger_steps=dragger_steps, *args)
#
#         self._parent = parent
#         self._color1 = QColor(color1[0], color1[1], color1[2])
#         self._color2 = QColor(color2[0], color2[1], color2[2])
#         self._main_color = main_color if main_color else QColor(215, 128, 26).getRgb()
#
#         self.setStyleSheet(self._get_style_sheet())
#
#     def paintEvent(self, event):
#         painter = QPainter()
#         painter.begin(self)
#         self._draw_widget(painter)
#         painter.end()
#         super(ColorRgbGradientSlider, self).paintEvent(event)
#
#     def get_color(self):
#         """
#         Computes and returns current color
#         :return: list(float, float, float)
#         """
#
#         r1, g1, b1 = self._color1.getRgb()
#         r2, g2, b2 = self._color2.getRgb()
#         f_r = (r2 - r1) * self.mapped_value() + r1
#         f_g = (g2 - g1) * self.mapped_value() + g1
#         f_b = (b2 - b1) * self.mapped_value() + b1
#
#         return [f_r, f_g, f_b]
#
#     def _draw_widget(self, painter):
#         width = self.width()
#         height = self.height()
#
#         gradient = QLinearGradient(0, 0, width, height)
#         gradient.setColorAt(0, self._color1)
#         gradient.setColorAt(1, self._color2)
#         painter.setBrush(QBrush(gradient))
#
#         painter.drawRect(0, 0, width, height)
#
#     def _get_style_sheet(self):
#         return """
#         QSlider,QSlider:disabled,QSlider:focus{
#                                   background: qcolor(0,0,0,0);   }
#
#          QSlider::groove:horizontal {
#             border: 1px solid #999999;
#             background: qcolor(0,0,0,0);
#          }
#         QSlider::handle:horizontal {
#             background:  rgba(255, 255, 255, 150);
#             width: 10px;
#             border-radius: 4px;
#             border: 1.5px solid black;
#          }
#          QSlider::handle:horizontal:hover {
#             border: 2.25px solid %s;
#          }
#         """ % "rgba%s" % str(self._main_color)
#
#
# class ColorRgbSliders(base.BaseWidget):
#     """
#     Custom slider to choose a color by its components
#     """
#
#     colorChanged = Signal(tuple)
#
#     def __init__(self, parent=None, start_color=None, slider_type='float', alpha=False, height=50, *args):
#
#         self._parent = parent
#         self._type = slider_type
#         self._alpha = alpha
#         self._default_color = start_color or 0, 0, 0, 255
#         self._height = height
#         self._color = self._default_color
#         self._style_str = "QPushButton{ background-color: rgba(%f,%f,%f,%f);border-color: black;" \
#                           "border-radius: 2px;border-style: outset;border-width: 1px;}" \
#                           "\nQPushButton:pressed{ border-style: inset;border-color: beige}"
#
#         super(ColorRgbSliders, self).__init__(parent=parent, *args)
#
#     def _get_color(self):
#         return self._color
#
#     def _set_color(self, color_tuple):
#         self._color = color_tuple
#         with qt_contexts.block_signals(self):
#             self._red_slider.set_mapped_value(self._color[0], block_signals=True)
#             self._green_slider.set_mapped_value(self._color[1], block_signals=True)
#             self._blue_slider.set_mapped_value(self._color[2], block_signals=True)
#             try:
#                 self._alpha_slider.set_mapped_value(self._color[3], block_signals=True)
#             except Exception:
#                 pass
#
#     color = Property(tuple, _get_color, _set_color)
#
#     def get_main_layout(self):
#         return layouts.HorizontalLayout(spacing=5)
#
#     def ui(self):
#         super(ColorRgbSliders, self).ui()
#
#         self.setMaximumHeight(self._height)
#
#         self._menu = QMenu(self)
#         self._action_reset = self._menu.addAction('Reset Value')
#
#         self._red_dragger = sliders.DraggerSlider(slider_type=self._type)
#         self._green_dragger = sliders.DraggerSlider(slider_type=self._type)
#         self._blue_dragger = sliders.DraggerSlider(slider_type=self._type)
#         self._alpha_dragger = sliders.DraggerSlider(slider_type=self._type)
#         for dragger in [self._red_dragger, self._green_dragger, self._blue_dragger, self._alpha_dragger]:
#             dragger.setMinimum(0)
#             if self._type == 'int':
#                 dragger.setMaximum(255)
#             else:
#                 dragger.setMaximum(1.0)
#
#         self._red_slider = ColorRgbGradientSlider(parent=self, color2=[255, 0, 0])
#         self._green_slider = ColorRgbGradientSlider(parent=self, color2=[0, 255, 0])
#         self._blue_slider = ColorRgbGradientSlider(parent=self, color2=[0, 0, 255])
#         self._alpha_slider = ColorRgbGradientSlider(parent=self, color2=[255, 255, 255])
#
#         self._red_dragger.valueChanged.connect(lambda value: self._red_slider.set_mapped_value(float(value)))
#         self._red_slider.doubleValueChanged.connect(lambda value: self._red_dragger.setValue(value))
#         self._green_dragger.valueChanged.connect(lambda value: self._green_slider.set_mapped_value(float(value)))
#         self._green_slider.doubleValueChanged.connect(lambda value: self._green_dragger.setValue(value))
#         self._blue_dragger.valueChanged.connect(lambda value: self._blue_slider.set_mapped_value(float(value)))
#         self._blue_slider.doubleValueChanged.connect(lambda value: self._blue_dragger.setValue(value))
#         self._alpha_dragger.valueChanged.connect(lambda value: self._alpha_slider.set_mapped_value(float(value)))
#         self._alpha_slider.doubleValueChanged.connect(lambda value: self._alpha_dragger.setValue(value))
#
#         red_layout = layouts.HorizontalLayout()
#         green_layout = layouts.HorizontalLayout()
#         blue_layout = layouts.HorizontalLayout()
#         alpha_layout = layouts.HorizontalLayout()
#         red_layout.addWidget(self._red_dragger)
#         red_layout.addWidget(self._red_slider)
#         green_layout.addWidget(self._green_dragger)
#         green_layout.addWidget(self._green_slider)
#         blue_layout.addWidget(self._blue_dragger)
#         blue_layout.addWidget(self._blue_slider)
#         alpha_layout.addWidget(self._alpha_dragger)
#         alpha_layout.addWidget(self._alpha_slider)
#         self._sliders_layout = layouts.VerticalLayout()
#         self._sliders_layout.setSpacing(0)
#         layouts_list = [red_layout, green_layout, blue_layout]
#         if self._alpha:
#             layouts_list.append(alpha_layout)
#         else:
#             self._alpha_slider.hide()
#
#         self._alpha_slider.set_mapped_value(255)
#
#         self._color_btn = buttons.BaseButton(parent=self)
#         self._color_btn.setMaximumWidth(self._height)
#         self._color_btn.setMinimumWidth(self._height)
#         self._color_btn.setMaximumHeight(self._height - 12)
#         self._color_btn.setMinimumHeight(self._height - 12)
#         self._color_btn.setStyleSheet(
#             self._style_str % (
#                 self._red_slider.mapped_value(), self._green_slider.mapped_value(),
#                 self._blue_slider.mapped_value(), self._alpha_slider.mapped_value()))
#
#         for widget in [self._red_slider, self._green_slider, self._blue_slider, self._alpha_slider,
#                        self._red_dragger, self._green_dragger, self._blue_dragger, self._alpha_dragger]:
#             widget.setMaximumHeight(self._height / len(layouts_list) + 1)
#             widget.setMinimumHeight(self._height / len(layouts_list) + 1)
#
#         for slider in [self._red_slider, self._green_slider, self._blue_slider, self._alpha_slider]:
#             slider.doubleValueChanged.connect(self._on_color_changed)
#
#         for layout in layouts_list:
#             self._sliders_layout.addLayout(layout)
#
#         self.main_layout.addWidget(self._color_btn)
#         self.main_layout.addLayout(self._sliders_layout)
#
#         if isinstance(self._default_color, list) and len(self._default_color) >= 3:
#             self.set_color(self._default_color)
#
#         self._color_btn.clicked.connect(self._on_show_color_dialog)
#         self._action_reset.triggered.connect(self._on_reset_value)
#
#     def contextMenuEvent(self, event):
#         self._menu.exec_(event.globalPos())
#
#     def set_color(self, new_color):
#         self._red_slider.set_mapped_value(new_color[0])
#         self._green_slider.set_mapped_value(new_color[1])
#         self._green_slider.set_mapped_value(new_color[2])
#         if len(new_color) > 3:
#             self._alpha_slider.set_mapped_value(new_color[3])
#
#     def _on_color_changed(self):
#         self._color_btn.setStyleSheet(
#             self._style_str % (
#                 self._red_slider.mapped_value(), self._green_slider.mapped_value(),
#                 self._blue_slider.mapped_value(), self._alpha_slider.mapped_value()))
#         value_list = [
#             self._red_slider.mapped_value(), self._green_slider.mapped_value(), self._blue_slider.mapped_value()]
#         if self._alpha:
#             value_list.append(self._alpha_slider.mapped_value())
#         if self._type == 'int':
#             value_list = [utils.clamp(int(i), 0, 255) for i in value_list]
#         self._color = helpers.force_tuple(value_list)
#         self.colorChanged.emit(self._color)
#
#     def _on_show_color_dialog(self):
#         if self._alpha:
#             new_color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
#         else:
#             new_color = QColorDialog.getColor()
#         if new_color.isValid():
#             self._red_slider.set_mapped_value(
#                 utils.map_range_unclamped(
#                     new_color.redF(), 0.0, 1.0, self._red_slider.slider_range[0], self._red_slider.slider_range[1]))
#             self._green_slider.set_mapped_value(
#                 utils.map_range_unclamped(
#                     new_color.greenF(), 0.0, 1.0, self._green_slider.slider_range[0],
#                     self._green_slider.slider_range[1]))
#             self._blue_slider.set_mapped_value(
#                 utils.map_range_unclamped(
#                     new_color.blueF(), 0.0, 1.0, self._blue_slider.slider_range[0], self._blue_slider.slider_range[1]))
#             self._alpha_slider.set_mapped_value(
#                 utils.map_range_unclamped(
#                     new_color.alphaF(), 0.0, 1.0, self._alpha_slider.slider_range[0],
#                     self._alpha_slider.slider_range[1]))
#
#     def _on_reset_value(self):
#         if self._default_color:
#             self.set_color(self._default_color)


class ColorPaletteWidget(QWidget):
	def __init__(self, draggable=True, parent=None):
		super().__init__(parent=parent)

		self._draggable = draggable
		self._pressed = None
		self._drag_color = QColor()
		self._prev_button = None

		self._fill_default_color_list()

	def _fill_default_color_list(self):
		pass
