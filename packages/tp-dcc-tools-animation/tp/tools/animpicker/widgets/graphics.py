from __future__ import annotations

import math
from typing import List

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.common.python.decorators import accepts, returns
from tp.tools.animpicker import consts, uiutils
from tp.tools.animpicker.widgets import items

logger = log.animLogger


class DropScene(qt.QGraphicsScene):

	sceneChanged = qt.Signal()
	sendCommandData = qt.Signal(str, list, list, list, str, qt.QGraphicsScene)
	redefineMember = qt.Signal(items.AbstractDropItem)
	changeMember = qt.Signal(items.AbstractDropItem, str, bool, str)
	editRemote = qt.Signal(items.AbstractDropItem)
	undoOpen = qt.Signal()
	undoClose = qt.Signal()
	poseGlobalVarSet = qt.Signal(items.AbstractDropItem)
	poseGlobalVarUnset = qt.Signal(items.AbstractDropItem)

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self.setItemIndexMethod(qt.QGraphicsScene.NoIndex)

		self._press_pos = qt.QPointF()
		self._marquee = None								# type: qt.QRect
		self._move_marquee_pos = qt.QPointF()
		self._move_marquee_offset = qt.QPointF()
		self._marquee_rect = qt.QRectF()
		self._marquee_modifier = qt.Qt.NoModifier
		self._image_path = ''
		self._map_size = qt.QSizeF(0.0, 0.0)
		self._pixmap = qt.QPixmap()
		self._color = consts.DEFAULT_MAP_BACKGROUND_COLOR
		self._use_background_image = False
		self._coop = False
		self._is_handle_working = False

	@property
	@returns(qt.QSizeF)
	def map_size(self):
		return self._map_size

	@map_size.setter
	@accepts(qt.QSizeF)
	def map_size(self, value: qt.QSizeF):
		self._map_size = value
		self.update()

	@property
	@returns(qt.QPixmap)
	def pixmap(self) -> qt.QPixmap:
		return self._pixmap

	@pixmap.setter
	@accepts(qt.QPixmap)
	def pixmap(self, value: qt.QPixmap):
		self._pixmap = value
		self.update()

	@property
	@returns(qt.QColor)
	def color(self) -> qt.QColor:
		return self._color

	@color.setter
	@accepts(qt.QColor)
	def color(self, value: qt.QColor):
		self._color = value
		self.update()

	@property
	@returns(bool)
	def use_background_image(self) -> bool:
		return self._use_background_image

	@use_background_image.setter
	@accepts(bool)
	def use_background_image(self, flag: bool):
		self._use_background_image = flag
		self.update()

	@property
	@returns(bool)
	def coop(self) -> bool:
		return self._coop

	@coop.setter
	@accepts(bool)
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
		if not self._marquee_rect.isNull():
			rect = self._marquee_rect.normalized()
			self._marquee_rect = qt.QRectF()
			mode = ''
			if self._marquee_modifier == qt.Qt.NoModifier:
				mode = 'replace'
			elif self._marquee_modifier == qt.Qt.ControlModifier:
				mode = 'remove'
			elif self._marquee_modifier == qt.Qt.ShiftModifier:
				mode = 'toggle'
			elif self._marquee_modifier == qt.Qt.ControlModifier | qt.Qt.ShiftModifier:
				mode = 'add'
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

	@override
	def keyReleaseEvent(self, event: qt.QKeyEvent) -> None:
		if event.key() == qt.Qt.Key_Alt:
			if not self._move_marquee_pos.isNull():
				self._move_marquee_pos = qt.QPointF()
				self._move_marquee_offset = qt.QPointF()
		super().keyReleaseEvent(event)

	@override
	def helpEvent(self, event: qt.QGraphicsSceneHelpEvent) -> None:
		pos = event.scenePos()
		item = self.itemAt(pos, qt.QTransform())
		if item and isinstance(item, items.AbstractDropItem):
			cmd = item.command
			if cmd.lower().startswith('exec'):
				split = cmd.split(' ', 1)
				tool_tip_text = '<b>%s</b>' % split[0]
				tool_tip_text += '<br>%s' % split[1]
			elif cmd.lower().startswith('visibility'):
				tool_tip_text = '<b>%s</b>' % cmd
				tool_tip_text += '<br>%s' % item.states[item.current_index()].name
			else:
				tool_tip_text = '<b>%s</b>' % cmd
				if item.target_node:
					tool_tip_text += '<br>' + item.target_node[0] + (item.target_node[1:] and '...' or '')
				if item.target_channel:
					tool_tip_text += '<br>%s' % self._elide_text(', '.join(item.target_channel), 120)
				if item.linked_items():
					tool_tip_text += '<br><font color=#ff0000>Has linked items</font>'
			qt.QToolTip.showText(event.screenPos(), tool_tip_text)
		else:
			qt.QToolTip.hideText()

	@override
	def drawBackground(self, painter: qt.QPainter, rect: qt.QRectF) -> None:
		painter.setRenderHint(qt.QPainter.Antialiasing)
		painter.fillRect(rect, self._color)
		painter.setPen(qt.QPen(qt.Qt.black, 0.5, qt.Qt.DashLine))
		painter.drawRect(qt.QRectF(qt.QPointF(0.0, 0.0), self._map_size))
		if self._use_background_image and not self._pixmap.isNull():
			painter.drawPixmap(qt.QPointF(0.0 ,0.0), self._pixmap)
		if self._coop:
			map_rect = qt.QRectF(qt.QPointF(0.0, 0.0), self._map_size)
			painter.setPen(qt.Qt.NoPen)
			painter.setBrush(qt.QColor(67, 255, 163))
			painter.drawPolygon(self._corner_polygon(map_rect.topLeft(), 0))
			painter.drawPolygon(self._corner_polygon(map_rect.topRight(), 1))
			painter.drawPolygon(self._corner_polygon(map_rect.bottomRight(), 2))
			painter.drawPolygon(self._corner_polygon(map_rect.bottomLeft(), 3))

	def set_background_pixmap(self, path: str):
		"""
		Sets the pixmap to paint as background image.

		:param str path: path pointing to an image file in disk.
		"""

		pixmap = qt.QPixmap(path)
		if not pixmap.isNull():
			self._image_path = path
			self._pixmap = pixmap
		else:
			self._image_path = ''
			self._pixmap = qt.QPixmap()
		self._use_background_image = True

	def set_movable_selected_items(self, movable: bool):
		"""
		Sets whether selected item are movable.

		:param bool movable: True to make selected items movable; False otherwise.
		"""

		for item in [x for x in self.selectedItems() if isinstance(x, items.AbstractDropItem)]:
			if movable:
				item.setFlags(item.flags() | qt.QGraphicsItem.ItemIsMovable)
			else:
				item.setFlags(item.flags() & ~qt.QGraphicsItem.ItemIsMovable)

	def primary_view(self) -> DropView | None:
		"""
		Returns current primary view.

		:return: primary view instance.
		:rtype: DropView or None
		"""

		views = self.views()
		return views[0] if views else None

	def window(self) -> qt.QWidget | None:
		"""
		Retunrs window widget of the primary view.

		:return: window instance.
		:rtype: qt.QWidget or None
		"""

		view = self.primary_view()
		return view.window() if view else None

	def items_by_z_value_order(self, rect: qt.QRectF = qt.QRectF()) -> List[items.AbstractDropItem | items.GroupItem]:
		"""
		Returns the item within the given rectangle ordered by its Z value.

		:param qt.QRectF rect: rectangle where items we are looking for are located.
		:return: found items.
		:rtype: List[items.AbstractDropItem]
		"""

		scene_items = [x for x in rect.isValid() and self.items(rect) or self.items() if isinstance(
			x, (items.AbstractDropItem, items.GroupItem))]
		if scene_items:
			scene_items.sort(key=lambda x: x.zValue())
		return scene_items

	def top_item(self) -> items.AbstractDropItem | items.GroupItem | None:
		"""
		Returns top item.

		:return: top item.
		:rtype: items.AbstractDropItem or items.GroupItem or None
		"""

		scene_items = self.items_by_z_value_order()
		return scene_items[-1] if scene_items else None

	def select_in_rect(self, rect: qt.QRectF, mode: str = 'add'):
		"""
		Select all items with given mode within the given rectangle.

		:param qt.RectF rect: rectangle where items are located.
		:param str mode: selection mode.
		"""

		scene_items = [x for x in self.items(rect) if isinstance(x, items.AbstractDropItem)]
		selected_items = [x for x in self.selectedItems() if isinstance(x, items.AbstractDropItem)]
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
		"""
		Runs given command and applies it to given channels.

		:param str command: command name to run on all items within scene.
		:param str channel_flag: channel flag to apply command to.
		:return:
		"""

		scene_items = [x for x in self.items() if isinstance(x, items.AbstractDropItem) and x.target_node]
		if channel_flag.lower() == 'defined':
			channel_flag = ''
			scene_items = [x for x in scene_items if x.target_channel]
		if not scene_items:
			return
		for item in scene_items:
			item.emit_command(command, channel_flag)

	def add_vars_item(self, **kwargs):
		"""
		Adds a new item into the scene.

		:param Dict kwargs: new item creation keyword arguments.
		:return:
		"""

		if 'size' not in kwargs and 'width' in kwargs and 'height' in kwargs:
			w = kwargs['width']
			h = kwargs['height']
			del kwargs['width']
			del kwargs['height']
			kwargs['size'] = [w, h]
		item_type = items.DropItemType.from_string(kwargs.get('type', ''))
		if not item_type:
			logger.error(f'Item type is not valid: {kwargs.get("type", "")}')
			return

		item = None
		if item_type in [
			items.DropItemType.Rectangle, items.DropItemType.RectangleSlider, items.DropItemType.DragPose,
			items.DropItemType.EditableRectangle, items.DropItemType.EditableRectangleSlider,
			items.DropItemType.EditableDragPose]:
			item = self._add_rectangle_item(**kwargs)

		return item

	def _add_rectangle_item(self, **kwargs) -> items.RectangleDropItem | None:
		"""
		Intenral function that adds a new retangle item into the scene.

		:param Dict kwargs: item creation keyword arguments.
		:return: newly created item instance.
		:rtype: items.RectangleDropItem or None
		"""

		if 'type' not in kwargs:
			logger.error('Type is not defined')
			return None

		type_value = items.DropItemType.from_string(kwargs.get('type'))

		item = items.RectangleDropItem(color=kwargs.get('color', qt.Qt.red))
		self._setup_item_data(item, **kwargs)

		return item

	def _setup_item_data(self, item: items.AbstractDropItem, **kwargs) -> items.AbstractDropItem:

		if 'size' in kwargs:
			width, height = kwargs['size']
			item.width = width
			item.height = height
		if item.width < item.DEFAULT_MIN_SIZE:
			item.min_width = item.width
		if item.height < item.DEFAULT_MIN_SIZE:
			item.min_height = item.height
		if 'command' in kwargs:
			item.command = kwargs['command']
		if 'node' in kwargs:
			item.target_node = kwargs['node']
		if 'channel' in kwargs:
			item.target_channel = kwargs['channel']
		if 'value' in kwargs:
			item.target_value = kwargs['value']
		if kwargs.get('type', '').lower() != 'path' and 'icon' in kwargs and kwargs.get('icon'):
			path, rect = kwargs.get('icon')
			item.icon_path = path
			if rect.isValid():
				item.icon_rect = rect
				max_rect = item.inbound_rect()
				if not max_rect.contains(item.icon_rect):
					item.set_default_icon_rect()
			else:
				item.set_default_icon_rect()
		if 'label' in kwargs and kwargs.get('label'):
			label, rect, font = kwargs.get('label')
			item.label = label
			if font:
				item.font = font
			if rect.isValid():
				item.label_rect = rect
				max_rect = item.boundingRect().adjusted(
					item.BORDER_MARGIN, item.BORDER_MARGIN, -item.BORDER_MARGIN, -item.BORDER_MARGIN)
				if not max_rect.contains(item.label_rect):
					rect = item.set_default_label_rect()
					if rect:
						item.label_rect = rect
			else:
				rect = item.set_default_label_rect()
				if rect:
					item.label_rect = rect
			item.match_min_size_to_subordinate()
		top_item = self.top_item()
		self.addItem(item)
		item.setPos(kwargs.get('pos', qt.QPointF(0, 0)))
		if 'hashcode' in kwargs and kwargs.get('hashcode'):
			item.hash_code = kwargs['hashcode']
		else:
			item.hash_code = uiutils.generate_hash_code(item)
		if top_item:
			item.setZValue(top_item.zValue() + 0.001)
		self._connect_item_signals(item)

		return item

	def _connect_item_signals(self, item: items.AbstractDropItem):
		"""
		Intenral function that setup given item signals.

		:param items.AbstractDropItem item: item to setup signals for.
		"""

		item.signals.sendCommandData.connect(lambda *args: self.sendCommandData.emit(*list(args) + [self]))
		item.signals.itemChanged.connect(lambda: self.sceneChanged.emit())
		item.signals.redefineMember.connect(self.redefineMember.emit)
		item.signals.changeMember.connect(self.changeMember.emit)
		item.signals.editRemote.connect(self.editRemote.emit)
		if item.command.lower() == 'pose':
			item.signals.mousePressed.connect(lambda: self.poseGlobalVarSet.emit(item))
			item.signals.mouseReleased.connect(lambda: self.poseGlobalVarUnset.emit(item))

	def _elide_text(self, text: str, width: int) -> str:
		"""
		Internal function that returns the elid text of the given one.

		:param str text: text to elide.
		:param int width: text width.
		:return: elided text.
		:rtype: str
		"""

		font_metrics = qt.QFontMetrics(self.font())
		return font_metrics.elidedText(text, qt.Qt.ElideRight, width)

	def _corner_polygon(self, pos: qt.QPointF, coord: int = 0) -> qt.QPolygonF:
		"""
		Internal function that returns polygon shape for given coordinate.

		:param qt.QPointF pos: start position for the polygon.
		:param coord: coordinate index.
		:return: polygon instance.
		:rtype: qt.QPolygonF
		"""

		if coord == 0:
			p1 = pos + qt.QPointF(9, 0)
			p2 = p1 + qt.QPointF(0, 3)
			p3 = p2 - qt.QPointF(6, 0)
			p4 = p3 + qt.QPointF(0, 6)
			p5 = p4 - qt.QPointF(3, 0)
		elif coord == 1:
			p1 = pos + qt.QPointF(0, 9)
			p2 = p1 - qt.QPointF(3, 0)
			p3 = p2 - qt.QPointF(0, 6)
			p4 = p3 - qt.QPointF(6, 0)
			p5 = p4 - qt.QPointF(0, 3)
		elif coord == 2:
			p1 = pos - qt.QPointF(9, 0)
			p2 = p1 - qt.QPointF(0, 3)
			p3 = p2 + qt.QPointF(6, 0)
			p4 = p3 - qt.QPointF(0, 6)
			p5 = p4 + qt.QPointF(3, 0)
		else:
			p1 = pos - qt.QPointF(0, 9)
			p2 = p1 + qt.QPointF(3, 0)
			p3 = p2 + qt.QPointF(0, 6)
			p4 = p3 + qt.QPointF(6, 0)
			p5 = p4 + qt.QPointF(0, 3)

		return qt.QPolygonF.fromList([pos, p1, p2, p3, p4, p5])


class EditableDropScene(DropScene):

	selectedItemsChanged = qt.Signal(list)
	addItemOn = qt.Signal(qt.QPointF, qt.QColor, int)

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._editable = True
		self.selectionChanged.connect(lambda: self.selectedItemsChanged.emit(self.selectedItems()))

	@property
	@returns(bool)
	def editable(self) -> bool:
		return self._editable

	@editable.setter
	@accepts(bool)
	def editable(self, flag: bool):
		self._editable = flag
		self.update()

	@override
	def mousePressEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
		scene_items = [x for x in self.items(event.scenePos()) if isinstance(x, items.AbstractDropItem)]
		item = scene_items[0] if scene_items else None
		button = event.button()
		modifier = event.modifiers()
		if item and button == qt.Qt.MiddleButton and modifier == qt.Qt.ControlModifier:
			pos = event.scenePos()
		else:
			super().mousePressEvent(event)

	@override
	def mouseReleaseEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
		scene_items = [x for x in self.items(event.scenePos()) if isinstance(x, items.AbstractDropItem)]
		item = scene_items[0] if scene_items else None

		super().mouseReleaseEvent(event)

	@override
	def dragEnterEvent(self, event: qt.QGraphicsSceneDragDropEvent) -> None:
		if not self._editable:
			event.ignore()
			return

		mime_data = event.mimeData()
		if mime_data.hasFormat(
				consts.MIME_COLOR_MODIFIER) or mime_data.hasUrls() or mime_data.hasFormat(
			consts.MIME_TEMPLATE) or mime_data.hasFormat(consts.MIME_NEW_BUTTON) or mime_data.hasFormat(
			consts.MIME_COLOR) or mime_data.hasFormat(consts.MIME_IMAGE_PATH) or mime_data.hasFormat(
			consts.MIME_SLIDER_COMMAND):
			event.setDropAction(qt.Qt.CopyAction)
			event.accept()
			if mime_data.hasFormat(consts.MIME_TEMPLATE):
				size_str = str(mime_data.data(consts.MIME_TEMPLATE_SIZE))
				size = qt.QSizeF(*[float(v) for v in size_str.split()])
				pen = qt.QPen(qt.Qt.black, 0, qt.Qt.DashLine)
				self._marquee = self.addRect(qt.QRectF(qt.QPointF(0.0, 0.0), size), pen, qt.QBrush(qt.Qt.NoBrush))
				self._marquee.setZValue(65536)
			elif mime_data.hasFormat('text/plain') or mime_data.hasFormat(
					consts.MIME_DRAG_COMBO_TEXT) or mime_data.hasFormat(consts.MIME_COMMAND) or mime_data.hasFormat(
				consts.MIME_LABEL) or mime_data.hasFormat(consts.MIME_FONT_FAMILY) or mime_data.hasFormat(
				consts.MIME_CUSTOM_LABEL):
				event.setDropAction(qt.Qt.CopyAction)
				event.ignore()

		super().dragEnterEvent(event)

	@override
	def dragMoveEvent(self, event: qt.QGraphicsSceneDragDropEvent) -> None:
		if not self._editable:
			event.ignore()
			return

		mime_data = event.mimeData()
		if mime_data.hasFormat(consts.MIME_TEMPLATE) or mime_data.hasFormat(
				consts.MIME_NEW_BUTTON) or mime_data.hasFormat(consts.MIME_SLIDER_COMMAND):
			event.setDropAction(qt.Qt.CopyAction)
			event.accept()
			if mime_data.hasFormat(consts.MIME_TEMPLATE):
				self._marquee.setPos(event.scenePos())
		elif mime_data.hasFormat(consts.MIME_COLOR_MODIFIER) or mime_data.hasUrls() or mime_data.hasFormat(
				consts.MIME_COLOR) or mime_data.hasFormat(consts.MIME_IMAGE_PATH):
			event.setDropAction(qt.Qt.CopyAction)
			event.accept()
			if self.itemAt(event.scenePos(), qt.QTransform()):
				super().dragMoveEvent(event)
		else:
			super().dragMoveEvent(event)

	@override
	def dragLeaveEvent(self, event: qt.QGraphicsSceneDragDropEvent) -> None:
		mime_data = event.mimeData()
		super().dragLeaveEvent(event)
		if mime_data.hasFormat(consts.MIME_TEMPLATE):
			if self._marquee:
				self.removeItem(self._marquee)
				self._marquee = None

	@override
	def dropEvent(self, event: qt.QGraphicsSceneDragDropEvent) -> None:
		mime_data = event.mimeData()
		pos = event.scenePos()
		if mime_data.hasFormat(consts.MIME_COLOR_MODIFIER):
			if not self.itemAt(pos, qt.QTransform()):
				modifier = mime_data.data(consts.MIME_COLOR_MODIFIER).toLong()[0]
				self.addItemOn.emit(pos, mime_data.colorData(), modifier)

	@override
	def _add_rectangle_item(self, **kwargs) -> items.RectangleDropItem | None:
		if 'type' not in kwargs:
			logger.error('Type is not defined')
			return None

		type_value = items.DropItemType.from_string(kwargs.get('type'))

		item = items.RectangleEditableDropItem(color=kwargs.get('color', qt.Qt.red))
		self._setup_item_data(item, **kwargs)

		return item


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

		self._scale_factor_func = lambda x: self.matrix().scale(x, x).mapRect(qt.QRectF(0, 0, 1, 1)).width()
		self._mid_pos = qt.QPointF()
		self._is_track = False
		self._is_zoom = False
		self._block_context_menu = False
		self._current_zoom_factor = 1.0
		self._rubber_band = qt.QRubberBand(qt.QRubberBand.Rectangle, self)
		self._picker_node = None
		self._loaded = False

		self._timer = qt.QTimer()
		self._timer.setSingleShot(consts.SCROLL_WAITING_TIME)
		self._timer.timeout.connect(self._on_timer_timeout)

		horizontal_scroll = self.horizontalScrollBar()
		self._horizontal_scrollbar = qt.QScrollBar(qt.Qt.Horizontal, self)
		self._horizontal_scrollbar.actionTriggered.connect(lambda: self._timer.start(consts.SCROLL_WAITING_TIME))
		self._horizontal_scrollbar.valueChanged.connect(horizontal_scroll.setValue)
		self._horizontal_scrollbar.hide()
		self._horizontal_scrollbar.setCursor(qt.Qt.ArrowCursor)
		horizontal_scroll.rangeChanged.connect(lambda x, y: self._match_scroll(horizontal_scroll, x, y))
		horizontal_scroll.valueChanged.connect(self._horizontal_scrollbar.setValue)
		horizontal_scroll.valueChanged.connect(self._show_scroll)
		vertical_scroll = self.verticalScrollBar()
		self._vertical_scrollbar = qt.QScrollBar(qt.Qt.Vertical, self)
		self._vertical_scrollbar.actionTriggered.connect(lambda: self._timer.start(consts.SCROLL_WAITING_TIME))
		self._vertical_scrollbar.valueChanged.connect(vertical_scroll.setValue)
		self._vertical_scrollbar.hide()
		self._vertical_scrollbar.setCursor(qt.Qt.ArrowCursor)
		vertical_scroll.rangeChanged.connect(lambda x, y: self._match_scroll(vertical_scroll, x, y))
		vertical_scroll.valueChanged.connect(self._vertical_scrollbar.setValue)
		vertical_scroll.valueChanged.connect(self._show_scroll)

	@property
	def picker_node(self) -> str:
		return self._picker_node

	@picker_node.setter
	def picker_node(self, value: str):
		self._picker_node = value

	@property
	@returns(bool)
	def loaded(self) -> bool:
		return self._loaded

	@loaded.setter
	@accepts(bool)
	def loaded(self, flag: bool):
		self._loaded = flag

	@override
	def enterEvent(self, event: qt.QEvent) -> None:
		self.setFocus()
		super().enterEvent(event)

	@override
	def resizeEvent(self, event: qt.QResizeEvent) -> None:
		super().resizeEvent(event)
		scene = self.scene()						# type: DropScene
		map_size = scene.map_size
		content_size = self.contentsRect().size()
		rect = qt.QRectF(
			0.0, 0.0, max(map_size.width(), content_size.width()), max(map_size.height(), content_size.height()))
		self.setSceneRect(rect)
		w, h = self.width(), self.height()
		self._horizontal_scrollbar.setGeometry(
			qt.QRect(0, h - consts.SCROLL_THICKNESS, w - consts.SCROLL_THICKNESS, consts.SCROLL_THICKNESS))
		self._vertical_scrollbar.setGeometry(
			qt.QRect(w - consts.SCROLL_THICKNESS, 0, consts.SCROLL_THICKNESS, h - consts.SCROLL_THICKNESS))

	@override
	def mousePressEvent(self, event: qt.QMouseEvent) -> None:
		pos = qt.QPointF(event.pos())
		button = event.button()
		modifier = event.modifiers()
		if button in (qt.Qt.LeftButton, qt.Qt.MiddleButton) and modifier == qt.Qt.AltModifier:
			self._mid_pos = pos
			self._block_context_menu = True
			self._is_track = True
			icon = resources.icon('track')
			self.setCursor(qt.QCursor(icon.pixmap(icon.availableSizes()[-1]) if not icon.isNull else None))
		elif button == qt.Qt.RightButton and modifier == qt.Qt.AltModifier:
			self._mid_pos = pos
			self._block_context_menu = True
			self._is_zoom = True
			self._current_zoom_factor = self._scale_factor_func(1)
			icon = resources.icon('dolly')
			self.setCursor(qt.QCursor(icon.pixmap(icon.availableSizes()[-1]) if not icon.isNull else None))
			self.setResizeAnchor(qt.QGraphicsView.AnchorViewCenter)
			self.setTransformationAnchor(qt.QGraphicsView.AnchorViewCenter)

		super().mousePressEvent(event)

	@override
	def mouseMoveEvent(self, event: qt.QMouseEvent) -> None:
		pos = qt.QPointF(event.pos())
		if self._is_zoom:
			sign = qt.QVector2D.dotProduct(
				qt.QVector2D(1, 1).normalized(), qt.QVector2D(pos - self._mid_pos).normalized()) >= 0 and 1 or -1
			dist = self._distance_point_to_line(pos, self._mid_pos, self._mid_pos + qt.QPointF(1, -1))
			increment = sign * dist * 0.001
			self._set_scale_view(self._current_zoom_factor + increment)
		elif self._is_track:
			offset = pos - self._mid_pos
			factor = 0.667 * self._scale_factor_func(1)
			hsb = self.horizontalScrollBar()
			vsb = self.verticalScrollBar()
			if abs(offset.x()) > 1:
				increment = offset.x() * factor
				hsb.setValue(int(hsb.value() - increment))
			if abs(offset.y()) > 1:
				increment = offset.y() * factor
				vsb.setValue(int(vsb.value() - increment))
			self._mid_pos = pos
		super().mouseMoveEvent(event)

	@override
	def mouseReleaseEvent(self, event: qt.QMouseEvent) -> None:
		self.setCursor(qt.Qt.ArrowCursor)
		self.setResizeAnchor(qt.QGraphicsView.AnchorUnderMouse)
		self.setTransformationAnchor(qt.QGraphicsView.AnchorUnderMouse)
		self._mid_pos = qt.QPointF()
		if self._is_track or self._is_zoom:
			self._is_track = False
			self._is_zoom = False
		else:
			super().mouseReleaseEvent(event)

	@override
	def keyPressEvent(self, event: qt.QKeyEvent) -> None:
		key = event.key()
		modifier = event.modifiers()
		if modifier == qt.Qt.NoModifier and (key == qt.Qt.Key_A or key == qt.Qt.Key_F):
			scene = self.scene()
			if key == qt.Qt.Key_A:
				rect = scene.itemsBoundingRect()
			else:
				scene_items = scene.selectedItems()
				if not scene_items:
					return
				rect = qt.QRectF()
				for i in scene_items:
					rect = rect.united(i.sceneBoundingRect())
			rect.adjust(-10, -10, 10, 10)
			self.fitInView(rect, qt.Qt.KeepAspectRatio)
		elif modifier == qt.Qt.ControlModifier and key == qt.Qt.Key_0:
			self._set_scale_view(1)
		elif event.matches(qt.QKeySequence.ZoomIn):
			self._set_scale_view(self._scale_factor_func(1) + 0.1)
		elif event.matches(qt.QKeySequence.ZoomOut):
			self._set_scale_view(self._scale_factor_func(1) - 0.1)
		else:
			super().keyPressEvent(event)

	def wheelEvent(self, event: qt.QWheelEvent) -> None:
		self._scale_view(math.pow(1.15, event.delta() / 240.0))

	def dragEnterEvent(self, event: qt.QDragEnterEvent) -> None:
		event.accept()
		super().dragEnterEvent(event)

	def dragMoveEvent(self, event: qt.QDragMoveEvent) -> None:
		event.accept()
		super().dragMoveEvent(event)

	def dropEvent(self, event: qt.QDropEvent) -> None:
		event.accept()
		super().dropEvent(event)

	def contextMenuEvent(self, event: qt.QGraphicsSceneContextMenuEvent) -> None:
		if self._block_context_menu:
			self._block_context_menu = False
		else:
			super().contextMenuEvent(event)

	def show_rubber_band(self, rect: qt.QRectF):
		"""
		Shows rubber band.

		:param qt.QRectF rect: rubber band rectangle.
		"""

		pos1 = self.mapFromScene(rect.topLeft())
		pos2 = self.mapFromScene(rect.bottomRight())
		self._rubber_band.setGeometry(qt.QRect(pos1, pos2))
		self._rubber_band.show()

	def hide_rubber_band(self):
		"""
		Hides rubber band.
		"""

		self._rubber_band.hide()

	def _scale_view(self, scale_factor: float):
		"""
		Internal function that scales view by given factor.

		:param float scale_factor: scale factor.
		"""

		factor = self._scale_factor_func(scale_factor)
		if factor < 0.07 or factor > 100:
			return
		self.scale(scale_factor, scale_factor)

	def _set_scale_view(self, scale: float):
		"""
		Internal function that sets the scale of the view.

		:param float scale: new view scale.
		"""

		f = scale / self._scale_factor_func(1)
		self._scale_view(f)

	def _distance_point_to_line(self, p: qt.QPointF, v0: qt.QPointF, v1: qt.QPointF) -> float:
		"""
		Internal function that returns the distance between a point and a line define by two given vectors.

		:param qt.QPointF p: point.
		:param qt.QPointF v0: first point of line.
		:param qt.QPointF v1: second point of line.
		:return: distance between point and line.
		:rtype: float
		"""

		v = qt.QVector2D(v1 - v0)
		w = qt.QVector2D(p - v0)
		c1 = qt.QVector2D.dotProduct(w, v)
		c2 = qt.QVector2D.dotProduct(v, v)
		b = c1 * 1.0 / c2
		pb = v0 + v.toPointF() * b
		return qt.QVector2D(p - pb).length()

	def _show_scroll(self):
		"""
		Internal function that shows horizontal and vertical scroll bars.
		"""

		if not self.isVisible():
			return
		horizontal_scroll = self.horizontalScrollBar()
		flag = False
		if horizontal_scroll.minimum() == horizontal_scroll.maximum() == 0:
			flag = flag or False
			self._horizontal_scrollbar.hide()
		else:
			flag = flag or True
			self._horizontal_scrollbar.show()
		vertical_scroll = self.verticalScrollBar()
		if vertical_scroll.minimum() == vertical_scroll.maximum() == 0:
			flag = flag or False
			self._vertical_scrollbar.hide()
		else:
			flag = flag or True
			self._vertical_scrollbar.show()
		if flag:
			self._timer.start(consts.SCROLL_WAITING_TIME)

	def _hide_scroll(self):
		"""
		Internal function that hides horizontal and vertical scroll bars.
		"""

		self._horizontal_scrollbar.hide()
		self._vertical_scrollbar.hide()

	def _match_scroll(self, scroll: qt.QScrollBar, minimum_value: int, maximum_value: int):
		"""
		Internal function that matches scrollbar values.

		:param qt.QScrollBar scroll: scrollbar to match.
		:param int minimum_value: minimum value.
		:param int maximum_value: maximum value.
		"""

		if scroll.orientation() == qt.Qt.Horizontal:
			self._horizontal_scrollbar.setRange(minimum_value, maximum_value)
			self._horizontal_scrollbar.setSingleStep(scroll.singleStep())
			self._horizontal_scrollbar.setPageStep(scroll.pageStep())
		elif scroll.orientation() == qt.Qt.Vertical:
			self._vertical_scrollbar.setRange(minimum_value, maximum_value)
			self._vertical_scrollbar.setSingleStep(scroll.singleStep())
			self._vertical_scrollbar.setPageStep(scroll.pageStep())

	def _on_timer_timeout(self):
		"""
		Internal callback function that is called when scroll timer timeouts.
		Hides scroll.
		"""

		self._hide_scroll()
