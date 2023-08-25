from __future__ import annotations

from overrides import override

from tp.common.qt import api as qt
from tp.tools.animpicker.widgets import graphics


class TabWidget(qt.QTabWidget):

	tearOff = qt.Signal(int, qt.QPoint)
	saveToFile = qt.Signal(int)
	selectMapMode = qt.Signal(int)

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._border_color = None						# type: qt.QColor
		self._button_color = None						# type: qt.QColor
		self._fill_color = None							# type: qt.QColor
		self._highlight_color = None					# type: qt.QColor
		self._base_color = None							# type: qt.QColor
		self._base_border_color = None					# type: qt.QColor
		self._base_button_color = None					# type: qt.QColor

		self.setTabsClosable(False)
		self.setMouseTracking(True)
		self.setObjectName('TabWidget')
		self._update_colors_from_palette()

	@override
	def dragEnterEvent(self, event: qt.QDragEnterEvent) -> None:
		event.accept()
		super().dragEnterEvent(event)

	@override
	def dragMoveEvent(self, event: qt.QDragMoveEvent) -> None:
		event.accept()
		super().dragMoveEvent(event)

	def _update_colors_from_palette(self):
		"""
		Internal function that update internal colors based on current palette.
		"""

		palette = self.palette()
		self._border_color = qt.QColor(qt.Qt.black)
		self._button_color = palette.color(qt.QPalette.Window)
		self._fill_color = palette.color(qt.QPalette.Button)
		self._highlight_color = palette.color(qt.QPalette.Highlight)
		self._base_color = palette.color(qt.QPalette.Midlight)
		self._base_border_color = palette.color(qt.QPalette.Dark)
		self._base_button_color = palette.color(qt.QPalette.Mid)

	def _setup_custom_tab_bar(self):
		"""
		Internal function that setups custom tab bar.
		"""

		tab_bar = TearOffTabBar(parent=self)
		self.setTabBar(tab_bar)
		tab_bar.tearOff.connect(self.tearOff.emit)
		tab_bar.saveToFile.connect(self.saveToFile.emit)
		tab_bar.selectMapMode.connect(self.selectMapMode.emit)


class TearOffTabBar(qt.QTabBar):

	tearOff = qt.Signal(int, qt.QPoint)
	saveToFile = qt.Signal(int)
	selectMapMode = qt.Signal(int)

	def __init__(self, parent: TabWidget | None = None):
		super().__init__(parent=parent)

		self._pressed_index = -1

		self.setCursor(qt.Qt.ArrowCursor)
		self.setMouseTracking(True)
		self.setMovable(True)
		self.setIconSize(qt.QSize(12, 12))

	def event(self, arg__1: qt.QEvent) -> bool:
		if arg__1.type() == qt.QEvent.MouseButtonRelease:
			if self._pressed_index > -1:
				self.tearOff.emit(self._pressed_index, arg__1.globalPos())
				self._pressed_index = -1
				self.setCursor(qt.Qt.ArrowCursor)
		return super().event(arg__1)

	@override
	def enterEvent(self, event: qt.QEvent) -> None:
		self.grabKeyboard()
		super().enterEvent(event)

	@override
	def leaveEvent(self, event: qt.QEvent) -> None:
		self.releaseKeyboard()
		super().leaveEvent(event)

	@override
	def mousePressEvent(self, arg__1: qt.QMouseEvent) -> None:
		button = arg__1.button()
		modifier = arg__1.modifiers()
		if not (button == qt.Qt.LeftButton and (modifier == qt.Qt.NoModifier or modifier == qt.Qt.ControlModifier)):
			return

		if modifier == qt.Qt.ControlModifier:
			pos = arg__1.pos()
			self._pressed_index = self.tabAt(pos)
			rect = self.tabRect(self._pressed_index)
			pixmap = qt.QPixmap.grabWidget(self, rect)
			painter = qt.QPainter(pixmap)
			cursor_pixmap  = qt.QPixmap(':/closehand')
			cursor_pos = qt.QPoint(*[(x - y) / 2 for x, y in zip(rect.size().toTuple(), qt.QSize(32, 24).toTuple())])
			painter.drawPixmap(cursor_pos, cursor_pixmap)
			painter.end()
			cursor = qt.QCursor(pixmap)
			self.setCursor(cursor)

		super().mousePressEvent(arg__1)

	@override
	def mouseMoveEvent(self, arg__1: qt.QMouseEvent) -> None:
		if self._pressed_index != -1:
			if arg__1.modifiers() == qt.Qt.ControlModifier:
				self.setCursor(qt.Qt.OpenHandCursor)
			else:
				self.setCursor(qt.Qt.ArrowCursor)
		super().mouseMoveEvent(arg__1)

	@override
	def keyPressEvent(self, arg__1: qt.QKeyEvent) -> None:
		if arg__1.modifiers() == qt.Qt.ControlModifier:
			self.setCursor(qt.Qt.OpenHandCursor)

			super().keyPressEvent(arg__1)

	@override
	def keyReleaseEvent(self, event: qt.QKeyEvent) -> None:
		if self.cursor().shape() != qt.Qt.ArrowCursor:
			self.setCursor(qt.Qt.ArrowCursor)
		super().keyReleaseEvent(event)


class EditableTabWidget(qt.QTabWidget):

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._editable = True
		self._hilite = False
		self._hover_tab = -1

		self.setAcceptDrops(True)
		self.setObjectName('EditableTabWidget')
		palette = self.palette()
		palette.setColor(qt.QPalette.Midlight, qt.QColor(0, 0, 0, 0))
		self.setPalette(palette)

	@override
	def clear(self) -> None:
		all_tabs = [self.widget(i) for i in range(self.count())]
		with qt.block_signals(self):
			for tab in all_tabs:
				tab.deleteLater()
			super().clear()

	def current_view(self) -> graphics.DropView | None:
		"""
		Returns current view.

		:return: current view.
		:rtype: graphics.DropView or None
		"""

		current_widget = self.currentWidget()
		return current_widget.findChild(graphics.DropView) if current_widget else None

	def current_scene(self) -> graphics.DropScene | None:
		"""
		Returns current scene.

		:return: current view scene.
		:rtype: graphics.DropScene or None
		"""

		view = self.current_view()
		return view.scene() if view else None
