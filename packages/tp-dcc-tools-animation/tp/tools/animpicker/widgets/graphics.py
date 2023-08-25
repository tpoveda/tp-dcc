from __future__ import annotations

from overrides import override

from tp.common.qt import api as qt
from tp.tools.animpicker.widgets import items


class DropScene(qt.QGraphicsScene):

	sendCommandData = qt.Signal(str, list, list, list, str, qt.QGraphicsScene)
	undoOpen = qt.Signal()
	undoClose = qt.Signal()

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self.setItemIndexMethod(qt.QGraphicsScene.NoIndex)

		self._press_pos = qt.QPointF()
		self._move_marquee_pos = qt.QPointF()
		self._move_marquee_offset = qt.QPointF()
		self._marquee_rect = qt.QRectF()
		self._marquee_modifier = qt.Qt.NoModifier
		self._coop = False
		self._is_handle_working = False

	@property
	def coop(self) -> bool:
		return self._coop

	@coop.setter
	def coop(self, flag: bool):
		self._coop = flag

	@override
	def mousePressEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
		scene_items = [x for x in self.items(event.scenePos()) if isinstance(x, items.AbstractDropItem)]
		item = scene_items[0] if scene_items else None
		selected_items = []
		button = event.button()
		modifier = event.modifiers()
		if button != qt.Qt.LeftButton and button != qt.Qt.MiddleButton:
			return

		if button == qt.Qt.LeftButton and modifier in (
				qt.Qt.NoModifier, qt.Qt.ShiftModifier, qt.Qt.ControlModifier, qt.Qt.ControlModifier | qt.Qt.ShiftModifier):
			if hasattr(item, 'is_in_slider_effect') and item.is_in_slider_effect(item.mapFromScene(event.scenePos())):
				super().mousePressEvent(event)
				return
			edit_handles = [x for x in self.items(event.scenePos()) if isinstance(x, items.AbstractHandle)]
			if edit_handles:
				super().mousePressEvent(event)
				return
			selected_items = [x for x in list(set(self.selectedItems()) - {item}) if isinstance(x, items.AbstractDropItem)]
			for x in selected_items:
				x.ignore = True
			self._press_pos = event.scenePos()
			self._marquee_modifier = modifier
		super().mousePressEvent(event)
		for x in selected_items:
			x.setSelected(True)
			x.ignore = False

	@override
	def mouseMoveEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
		if not self._press_pos.isNull():
			pos2 = event.scenePos()
			if event.modifiers() == qt.Qt.AltModifier:
				if self._move_marquee_pos.isNull():
					self._move_marquee_pos = pos2
				else:
					self._move_marquee_offset = pos2 - self._move_marquee_pos
					self._move_marquee_pos = pos2
					self._press_pos += self._move_marquee_offset
			self._marquee_rect = qt.QRectF(self._press_pos, pos2).normalized()
			self.primary_view().show_rubber_band(self._marquee_rect)
		super().mouseMoveEvent(event)

	@override
	def mouseReleaseEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
		selected_items = []
		scene_items = [x for x in self.items(event.scenePos()) if isinstance(x, items.AbstractDropItem)]
		item = scene_items[0] if scene_items else None
		modifier = event.modifiers()
		modes = {
			qt.Qt.NoModifier: 'replace',
			qt.Qt.ControlModifier: 'remove',
			qt.Qt.ShiftModifier: 'toggle',
			qt.Qt.ControlModifier |
			qt.Qt.ShiftModifier: 'add'
		}

		if not self._marquee_rect.isNull():
			rect = self._marquee_rect.normalized()
			self._marquee_rect = qt.QRectF()
			mode = modes.get(self._marquee_modifier, '')
			if mode:
				self.select_in_rect(rect, mode)
			self.primary_view().hide_rubber_band()
		elif not item and modifier == qt.Qt.NoModifier and not self._is_handle_working:
			self.clearSelection()
			self.sendCommandData.emit('Deselect', [None], [], [], 'No', self)

		self._press_pos = qt.QPointF()
		self._move_marquee_pos = qt.QPointF()
		self._move_marquee_offset = qt.QPointF()
		self._marquee_modifier = qt.Qt.NoModifier
		self._is_handle_working = False

		if modifier == qt.Qt.ShiftModifier:
			selected_items = list(set(self.selectedItems()) - {item})
			for x in selected_items:
				x.ignore = True

		super().mouseReleaseEvent(event)

		if modifier == qt.Qt.ShiftModifier:
			for x in selected_items:
				x.setSelected(True)
				x.ignore = True

	def primary_view(self) -> DropView | None:
		"""
		Returns current primary view.

		:return: primary view instance.
		:rtype: DropView or None
		"""

		views = self.views()
		return views[0] if views else None

	def select_in_rect(self, rect: qt.QRectF, mode: str = 'add'):
		"""
		Select all items with given mode within the given rectangle.

		:param qt.RectF rect: rectangle where items are located.
		:param str mode: selection mode.
		"""

		scene_items = [x for x in self.items(rect) if isinstance(x, items.AbstractDropItem)]
		selected_items = [x for x in self.selectedItems() if isinstance(i, items.AbstractDropItem)]
		items_set = set(scene_items)
		selected_items_set = set(selected_items)

		if scene_items and mode:
			self.undoOpen.emit()
			try:
				if mode == 'add':
					scene_items[0].setSelected(True)
					for item in scene_items[1:]:
						item.setSelected(True, True)
				elif mode == 'replace':
					self.clearSelection()
					scene_items[0].setSelected(True)
					for item in scene_items:
						item.setSelected(True, True)
				elif mode == 'toggle':
					selected = list(items_set - selected_items_set)
					deselect = list(items_set & selected_items_set)
					for item in deselect:
						item.setSelected(False, True)
					for item in selected:
						item.setSelected(True, True)
				elif mode == 'remove':
					deselect = list(items_set & selected_items_set)
					for item in deselect:
						item.setSelected(False, True)
			finally:
				self.undoClose.emit()
		elif mode == 'add' or mode == 'replace':
			self.clearSelection()
			self.sendCommandData.emit('Deselect', [None], [], [], 'No', self)

	def do_all_items(self, command: str, channel_flag: str):

		scene_items = [x for x in self.items() if isinstance(x, items.AbstractDropItem) and x.target_node]
		if channel_flag.lower() == 'defined':
			channel_flag = ''
			scene_items = [x for x in scene_items if x.target_channel]
		if not scene_items:
			return
		for item in scene_items:
			item.emit_command(command, channel_flag)


class DropView(qt.QGraphicsView):

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self.setRenderHint(qt.QPainter.Antialiasing)
		self.setViewportUpdateMode(qt.QGraphicsView.FullViewportUpdate)
		self.setResizeAnchor(qt.QGraphicsView.AnchorUnderMouse)
		self.setTransformationAnchor(qt.QGraphicsView.AnchorUnderMouse)
		self.setFrameStyle(qt.QGraphicsView.NoFrame)
		self.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
