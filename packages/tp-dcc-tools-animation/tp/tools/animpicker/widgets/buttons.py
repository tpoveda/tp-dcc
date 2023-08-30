from __future__ import annotations

import ast

from overrides import override

from tp.core import dcc
from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.tools.animpicker import consts


class ArrowToggleButton(qt.QToolButton):

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._upside_down = True
		self._hover = False

		self.setMouseTracking(True)
		self.setFixedHeight(12)
		self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Fixed)
		self.setFocusPolicy(qt.Qt.NoFocus)
		self.setIconSize(qt.QSize(8, 8))
		self.setIcon(resources.icon('down_arrow'))
		self.setAutoFillBackground(True)

	@property
	def upside_down(self) -> bool:
		return self._upside_down

	@upside_down.setter
	def upside_down(self, flag: bool):
		self._upside_down = flag
		self._update_icon()

	@override
	def enterEvent(self, arg__1: qt.QEvent) -> None:
		self._hover = True
		self._update_icon()
		super().enterEvent(arg__1)

	def leaveEvent(self, arg__1: qt.QEvent) -> None:
		self._hover = False
		self._update_icon()
		super().leaveEvent(arg__1)

	def _update_icon(self):
		"""
		Internal function that updates based on button internal state.
		"""

		if self._upside_down:
			self.setIcon(resources.icon('down_arrow hover' if self._hover else 'down_arrow'))
		else:
			self.setIcon(resources.icon('up_arrow hover' if self._hover else 'up_arrow'))


class ColorButton(qt.QPushButton):

	colorChanged = qt.Signal(qt.QColor)

	def __init__(
			self, color: qt.QColor = qt.QColor(qt.Qt.red), enable_drag_drop: bool = True,
			parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._enable_drag_drop = enable_drag_drop
		self._pressed = False
		self._mime_type_string = consts.MIME_COLOR_MODIFIER

		self.setAcceptDrops(True)
		self.setMouseTracking(True)
		self.setFixedSize(qt.QSize(20, 20))

		self.set_color(color)

	@property
	def enable_drag_drop(self) -> bool:
		return self._enable_drag_drop

	@enable_drag_drop.setter
	def enable_drag_drop(self, flag: bool):
		self._enable_drag_drop = flag

	@override
	def mousePressEvent(self, e: qt.QMouseEvent) -> None:
		if self._enable_drag_drop:
			self._pressed = True
		super().mousePressEvent(e)

	@override
	def mouseMoveEvent(self, e: qt.QMouseEvent) -> None:
		if self._pressed:
			drag = qt.QDrag(self)
			data = qt.QMimeData()
			data.setColorData(self.color())
			data.setData(self._mime_type_string, qt.QByteArray.number(qt.QApplication.keyboardModifiers()))
			drag.setMimeData(data)
			pixmap = qt.QPixmap(20, 20)
			pixmap.fill(self.color())
			drag.setDragCursor(pixmap, qt.Qt.CopyAction)
			drag.start()
			self._pressed = False
			if self.isDown():
				self.setDown(False)
		super().mouseMoveEvent(e)

	@override
	def mouseReleaseEvent(self, e: qt.QMouseEvent) -> None:
		self._pressed = False
		super().mouseReleaseEvent(e)

	@override
	def dragEnterEvent(self, event: qt.QDragEnterEvent) -> None:
		mime_data = event.mimeData()
		if mime_data.hasFormat(self._mime_type_string):
			event.accept()
		super().dragEnterEvent(event)

	@override
	def dropEvent(self, event: qt.QDropEvent) -> None:
		mime_data = event.mimeData()
		if mime_data.hasFormat(self._mime_type_string):
			modifier = qt.QApplication.keyboardModifiers()
			pos = event.pos()
			mouse_event = qt.QMouseEvent(qt.QEvent.MouseButtonRelease, pos, qt.Qt.LeftButton, qt.Qt.LeftButton, modifier)
			super().mouseReleaseEvent(mouse_event)
			if self.isDown():
				self.setDown(False)
		else:
			super().dropEvent(event)

	@override
	def childEvent(self, event: qt.QChildEvent) -> None:
		if event.type() == qt.QEvent.ChildRemoved:
			self._pressed = False
			if self.isDown():
				self.setDown(False)
		super().childEvent(event)

	@override
	def paintEvent(self, arg__1: qt.QPaintEvent) -> None:
		painter = qt.QPainter(self)
		painter.setRenderHint(qt.QPainter.Antialiasing)
		rect = arg__1.rect()
		painter.setPen(qt.Qt.NoPen)
		painter.setBrush(self.color().darker())
		painter.drawRoundRect(rect, 2, 2)
		if self._pressed:
			rect.adjust(1, 1, 0, 0)
		else:
			rect.adjust(0, 0, -1, -1)
		painter.setBrush(self.color())
		painter.setOpacity(1.0)
		painter.drawRoundRect(rect, 2, 2)

	def color(self) -> qt.QColor:
		"""
		Returns the active color.

		:return: active color.
		:rtype: qt.QColor
		"""

		style = self.styleSheet()
		index = style.index('rgb')
		data = ast.literal_eval(style[index + 3:])
		return qt.QColor(*data)

	def set_color(self, color: qt.QColor):
		"""
		Sets the button color.

		:param qt.QColor color: color to set.
		"""

		try:
			current_color = self.color()
		except ValueError:
			current_color = None
		self.setStyleSheet(f'background-color: rgb(%d, %d, %d)' % color.getRgb()[:3])
		if color != current_color:
			self.colorChanged.emit(color)
