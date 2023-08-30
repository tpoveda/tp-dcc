from __future__ import annotations

from typing import List, Iterator

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.tools.animpicker import consts, utils
from tp.tools.animpicker.widgets import graphics

logger = log.animLogger


class TabWidget(qt.QTabWidget):

	tabAdded = qt.Signal()
	tearOff = qt.Signal(int, qt.QPoint)
	saveToFile = qt.Signal(int)
	selectMapMode = qt.Signal(int)

	SCENE_CLASS = graphics.DropScene

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
		self._setup_custom_tab_bar()

	@override
	def dragEnterEvent(self, event: qt.QDragEnterEvent) -> None:
		event.accept()
		super().dragEnterEvent(event)

	@override
	def dragMoveEvent(self, event: qt.QDragMoveEvent) -> None:
		event.accept()
		super().dragMoveEvent(event)

	def add_graphics_tab(self, text = consts.DEFAULT_MAP_NAME, change_current: bool = True) -> qt.QWidget:
		"""
		Adds a new graphics tab into the tab widget.

		:param str text: name of the tab.
		:param bool change_current: whether to change current selected tab.
		:return: created tab widget.
		:rtype: qt.QWidget
		"""

		names = [self.tabText(i) for i in range(self.count())]
		text = utils.numeric_name(text, names)
		tab = qt.QWidget()
		tab.prefix = ''
		tab.use_prefix = False
		layout = qt.horizontal_layout(margins=(3, 3, 3, 3), parent=tab)
		if change_current:
			index = self.currentIndex()
			index = self.insertTab(index + 1, tab, text)
			self.setCurrentIndex(index)
		else:
			index = self.count()
			index = self.insertTab(index, tab, text)
		self.setTabToolTip(index, f'Map : {text} To tear-off a map, hold Ctrl and drag.\n')
		view = graphics.DropView(parent=tab)
		view.installEventFilter(self)
		scene = self.SCENE_CLASS()
		view.setScene(scene)
		layout.addWidget(view)
		if change_current:
			self.tabAdded.emit()
		for signal_name in [d[0] for d in qt.signal_names(scene.__class__)]:
			if hasattr(self, signal_name):
				eval(f'scene.{signal_name}.connect(self.{signal_name}.emit)')

		return tab

	def add_view(self, text: str, index: int, view: graphics.DropView, prefix: str, use_prefix: bool):
		"""
		Adds a new view within this tab.

		:param str text: tab text.
		:param int index: index where the view will be added.
		:param graphics.DropView view: view instance.
		:param str prefix: view prefix.
		:param bool use_prefix: whether to use prefix or not.
		"""

		tab = qt.QWidget()
		tab.prefix = prefix
		tab.use_prefix = use_prefix
		index = self.insertTab(index, tab, text)
		self.setCurrentIndex(index)
		self.setTabToolTip(index, f'Map : {text} To tear-off a map, hold Ctrl and drag.\n')
		layout = qt.horizontal_layout(margins=(3, 3, 3, 3), parent=tab)
		layout.addWidget(view)
		scene = view.scene()
		if hasattr(scene, 'editable') and not scene.editable:
			self.setTabIcon(index, resources.icon('lock'))

	def view_at_index(self,  index: int) -> graphics.DropView | None:
		"""
		Returns the view instance at given index.

		:param int index: view index to get.
		:return: view instance.
		:rtype: graphics.DropView or None
		"""

		found_view = self.widget(index)
		return found_view.findChild(graphics.DropView) if found_view else None

	def scene_at_index(self, index: int) -> graphics.DropScene | graphics.EditableDropScene | None:
		"""
		Returns the scene instance at given index.

		:param int index: scene index to get.
		:return: scene instance.
		:rtype: graphics.DropScene or graphics.EditableDropScene or None
		"""

		found_view = self.view_at_index(index)
		return found_view.scene() if found_view else None

	def iterate_all_views(self) -> Iterator[graphics.DropView]:
		"""
		Generator function that iterates over all views within this tab.

		:return: iterated views.
		:rtype: Iterator[graphics.DropView]
		"""

		for i in range(self.count()):
			view = self.widget(i).findChild(graphics.DropView)
			if not view:
				continue
			yield view

	def all_views(self) -> List[graphics.DropView]:
		"""
		Returns all views within this tab.

		:return: list of views.
		:rtype: List[graphics.DropView]
		"""

		return list(self.iterate_all_views())

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


class EditableTabWidget(TabWidget):

	tabLabelRenamed = qt.Signal(str, str)
	windowModified = qt.Signal()
	addItemOn = qt.Signal(qt.QPointF, qt.QColor, int)

	SCENE_CLASS = graphics.EditableDropScene

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
	def event(self, arg__1: qt.QEvent) -> bool:
		if isinstance(arg__1, qt.QHelpEvent):
			pos = arg__1.pos()
			rect = self._button_rect()
			if rect.contains(pos):
				qt.QToolTip.showText(arg__1.globalPos(), 'Add Map:\nClick this to add a new map')
			else:
				qt.QToolTip.hideText()

		return super().event(arg__1)

	@override
	def eventFilter(self, watched: qt.QObject, event: qt.QEvent) -> bool:
		if isinstance(watched, graphics.DropView):
			self._hilite = False

		return super().eventFilter(watched, event)

	@override
	def leaveEvent(self, event: qt.QEvent) -> None:
		self._hover_tab = -1
		super().leaveEvent(event)

	@override
	def mousePressEvent(self, event: qt.QMouseEvent) -> None:
		pos = event.pos()
		rect = self._button_rect()
		modifier = event.modifiers()
		if rect.contains(pos) and self._editable and event.button() == qt.Qt.LeftButton and modifier == qt.Qt.NoModifier:
			index = self.indexOf(self.add_graphics_tab())
			scene = self.scene_at_index(index)
			scene.map_size = qt.QSizeF(400, 400)
			self.tabBar().edit_tab(index)
		else:
			super().mouseMoveEvent(event)

	@override
	def mouseMoveEvent(self, event: qt.QMouseEvent) -> None:
		pos = event.pos()
		if self._button_rect().contains(pos):
			self._hilite = True
			self._hover_tab = -1
		else:
			self._hilite = False
			for i in range(self.count()):
				if self.tabBar().tabRect(i).contains(pos):
					self._hover_tab = i
					break

		super().mouseMoveEvent(event)

	@override
	def dropEvent(self, event: qt.QDropEvent) -> None:
		if not self.count():
			logger.warning('No ma: to create item, have to create a map first')
			return

	@override
	def paintEvent(self, arg__1: qt.QPaintEvent) -> None:
		rect = self._button_rect()
		painter = qt.QPainter(self)
		painter.setRenderHint(qt.QPainter.Antialiasing)
		if self._editable:
			painter.setPen(qt.QPen(self._base_border_color, 0.1))
			painter.setBrush(self._hilite and self._base_button_color.lighter(115) or self._base_button_color)
			painter.drawPath(self._button_path(rect))
			cross_hair = qt.QRectF(0, 0, 7, 7)
			cross_hair.moveCenter(rect.center() + qt.QPointF(1, 1))
			painter.setPen(qt.QPen(self._hilite and qt.Qt.white or qt.Qt.lightGray, 2, qt.Qt.SolidLine, qt.Qt.RoundCap))
			painter.drawLine(
				qt.QPointF(cross_hair.center().x(), cross_hair.top()),
				qt.QPointF(cross_hair.center().x(), cross_hair.bottom()))
			painter.drawLine(
				qt.QPointF(cross_hair.left(), cross_hair.center().y()),
				qt.QPointF(cross_hair.right(), cross_hair.center().y()))
		if self.count():
			current_index = self.currentIndex()
			for i in range(self.count()):
				brush = current_index == i and self._base_color.darker(120) or self._base_color
				painter.setBrush(self._hover_tab == i and brush.lighter(110) or brush)
				rect = self.tabBar().tabRect(i).adjusted(*(current_index == i and (0, 1, 0, 0) or (1, 2, -1, 0)))
				path = self._button_path(rect)
				painter.drawPath(path)
			super().paintEvent(arg__1)
		elif self._editable:
			r = arg__1.rect()
			r.setTop(rect.bottom())
			painter.setPen(self._border_color)
			painter.setBrush(self._fill_color)
			painter.drawRoundedRect(r, 2, 2)

	@override
	def clear(self) -> None:
		all_tabs = [self.widget(i) for i in range(self.count())]
		with qt.block_signals(self):
			for tab in all_tabs:
				tab.deleteLater()
			super().clear()

	@override
	def add_graphics_tab(self, text = consts.DEFAULT_MAP_NAME, change_current: bool = True) -> qt.QWidget:
		tab = super().add_graphics_tab(text=text, change_current=change_current)

		self.current_scene().sceneChanged.connect(self.windowModified.emit)

		return tab

	@override
	def _setup_custom_tab_bar(self):
		tab_bar = EditableTabBar(parent=self)
		self.setTabBar(tab_bar)
		tab_bar.tabMoved.connect(lambda: self.windowModified.emit())
		tab_bar.tabLabelRenamed.connect(lambda: self.windowModified.emit())
		tab_bar.tabLabelRenamed.connect(self.tabLabelRenamed.emit)
		tab_bar.saveToFile.connect(self.saveToFile.emit)
		tab_bar.selectMapMode.connect(self.selectMapMode.emit)
		# tab_bar.requestRemove.connect(self._eliminate_tab)
		tab_bar.tearOff.connect(self.tearOff.emit)

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

	def _button_rect(self) -> qt.QRectF:
		"""
		Internal function that returns tab button rect.

		:return: button rect.
		:rtype: qt.QRectF
		"""

		r = self.tabBar().tabRect(self.count() - 1)
		if r.isValid():
			rect = qt.QRectF(0, 0, 30, r.height())
			rect.moveTopLeft(r.topRight() + qt.QPoint(2, 2))
		else:
			rect = qt.QRectF(2, 2, 30, 19)

		return rect

	def _button_path(self, rect: qt.QRectF) -> qt.QPainterPath:
		"""
		Internal function that returns the tab button path.

		:param qt.QRectF rect: button rect.
		:return: button path.
		:rtype: qt.QPainterPath
		"""

		path = qt.QPainterPath()
		path.setFillRule(qt.Qt.WindingFill)
		path.addRoundedRect(rect, 2, 2)
		path.addRect(rect.adjusted(0, 4, 0, 0))
		return path.simplified()


class EditableTabBar(TearOffTabBar):

	tabLabelRenamed = qt.Signal(str, str)

	def __init__(self, parent: EditableTabWidget | None = None):
		super().__init__(parent=parent)

		self._editor = qt.line_edit(parent=self)
		self._editor.setWindowFlags(qt.Qt.Popup)
		self._editor.setFocusProxy(self)
		self._editor.setFocusPolicy(qt.Qt.StrongFocus)
		self._editor.editingFinished.connect(self._on_editor_editing_finished)
		self._editor.installEventFilter(self)
		self._editor.setValidator(qt.QRegExpValidator(qt.QRegExp('\\w+')))
		self._edit_index = -1

	@override
	def eventFilter(self, watched: qt.QObject, event: qt.QEvent) -> bool:
		if event.type() == qt.QEvent.MouseButtonPress and not self._editor.geometry().contains(event.globalPos()) or \
				event.type() == qt.QEvent.KeyPress and event.key() == qt.Qt.Key_Escape:
			self._editor.hide()
			return False
		return super().eventFilter(watched, event)

	@override
	def mouseDoubleClickEvent(self, event: qt.QMouseEvent) -> None:
		if event.button() == qt.Qt.LeftButton:
			index = self.tabAt(event.pos())
			if index >= 0:
				self.selectMapMode.emit(index)

	def edit_tab(self, index: int):
		"""
		Sets given tab index as the current active edit tab.

		:param int index: tab index.
		"""

		rect = self.tabRect(index)
		self._editor.setFixedSize(rect.size())
		self._editor.move(self.parent().mapToGlobal(rect.topLeft()))
		self._editor.setText(self.tabText(index))
		if not self._editor.isVisible():
			self._editor.show()
			self._edit_index = index

	def _on_editor_editing_finished(self):
		"""
		Internal callback function that is called each time editor line edit is changed by the user.
		"""

		if self._edit_index >= 0:
			self._editor.hide()
			old_text = self.tabText(self._edit_index)
			new_text = self._editor.text()
			if old_text != new_text:
				names = [self.tabText(i) for i in range(self.count())]
				new_text = utils.numeric_name(new_text, names)
				self.setTabText(self._edit_index, new_text)
				self.tabLabelRenamed.emit(old_text, new_text)
				self._edit_index = -1