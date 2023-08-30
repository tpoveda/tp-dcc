from __future__ import annotations

import typing
from typing import Tuple, List, Union, Any

from overrides import override

from tp.common.qt import api as qt
from tp.common.python.decorators import accepts, returns
from tp.tools.animpicker import consts

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.widgets.graphics import DropScene


class DropItemType:

	Rectangle = qt.QGraphicsItem.UserType + 1
	EditableRectangle = qt.QGraphicsItem.UserType + 2
	RectangleSlider = qt.QGraphicsItem.UserType + 3
	EditableRectangleSlider = qt.QGraphicsItem.UserType + 4
	Path = qt.QGraphicsItem.UserType + 5
	EditablePath = qt.QGraphicsItem.UserType + 6
	Group = qt.QGraphicsItem.UserType + 7
	EditableGroup = qt.QGraphicsItem.UserType + 8
	DragPose = qt.QGraphicsItem.UserType + 9
	EditableDragPose = qt.QGraphicsItem.UserType + 10
	Line = qt.QGraphicsItem.UserType + 11
	VisToggle = qt.QGraphicsItem.UserType + 12
	EditableVisToggle = qt.QGraphicsItem.UserType + 13

	@classmethod
	def from_string(cls, type_str: str, editable: bool = True) -> int | None:
		"""
		Returns the item class for given string.

		:param str type_str: item type.
		:param bool editable: whether item is editable.
		:return: item type.
		:rtype: int or None
		"""

		if type_str == 'Rectangle':
			return cls.EditableRectangle if editable else cls.Rectangle
		if type_str == 'RectangleSlider':
			return cls.EditableRectangleSlider if editable else cls.RectangleSlider
		if type_str == 'Path':
			return cls.EditablePath if editable else cls.Path
		if type_str == 'Group':
			return cls.EditableGroup if editable else cls.Group
		if type_str == 'DragPose':
			return cls.EditableDragPose if editable else cls.DragPose
		if type_str == 'VisToggle':
			return cls.EditableVisToggle if editable else cls.VisToggle

		return None


class GrahicsLayeredBlurEffect(qt.QGraphicsBlurEffect):

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._inner_radius = 0
		self._outer_radius = 0

	def set_inner_radius(self, radius: int):
		"""
		Sets blur inner radius.

		:param int radius: inner radius.
		"""

		self._inner_radius = radius

	def set_outer_radius(self, radius: int):
		"""
		Sets blur outer radius.

		:param int radius: outer radius.
		"""

		self._outer_radius = radius

	@override
	def draw(self, painter: qt.QPainter) -> None:
		if self._outer_radius > 0:
			self.setBlurRadius(self._outer_radius)
			super().draw(painter)
		if self._inner_radius > 0:
			self.setBlurRadius(self._inner_radius)
			super().draw(painter)
		super().drawSource(painter)


class ClickTimer(qt.QObject):

	execute = qt.Signal()

	def __init__(self):
		super().__init__()

		self.button = None
		self.modifier = None
		self.pos = None
		self.is_selected = False
		self._timer_id = None

	@override
	def timerEvent(self, event: qt.QTimerEvent) -> None:
		if self._timer_id == event.timerId():
			self.execute.emit()
		self.remove_timer()

	def start(self, interval: int):
		"""
		Starts timer.

		:param int interval: timer interval.
		"""

		self._timer_id = self.startTimer(interval)

	def set_data(self, button: qt.Qt.MouseButton, modifier: qt.Qt.KeyboardModifier, pos: qt.QPointF, selected: bool):
		"""
		Updates internal data.

		:param qt.Qt.MouseButton button: pressed button.
		:param qt.Qt.KeyboardModifier modifier: keyboard modifier.
		:param qt.QPointF pos: event position.
		:param bool selected: whether item is selected.
		"""

		self.button = button
		self.modifier = modifier
		self.pos = pos
		self.is_selected = selected

	def remove_timer(self):
		"""
		Removes timer.
		"""

		if self._timer_id:
			self.killTimer(self._timer_id)
		self._timer_id = None


class ItemSignals(qt.QObject):

	sendCommandData = qt.Signal(str, list, list, list, str)
	itemChanged = qt.Signal(str)
	sizeChanged = qt.Signal()
	redefineMember = qt.Signal(qt.QGraphicsItem)
	changeMember = qt.Signal(qt.QGraphicsItem, str, bool, str)
	editRemote = qt.Signal(qt.QGraphicsItem)
	mousePressed = qt.Signal()
	mouseReleased = qt.Signal()
	aboutToRemove = qt.Signal(qt.QGraphicsItem)


class AbstractDropItem(qt.QGraphicsItem):

	BORDER_MARGIN = 0
	EDITABLE_MARGIN = 4
	BLUR_OUTER_RADIUS = 6
	BLUR_INNER_RADIUS = 2
	ICON_MIN_SIZE = 4
	DEFAULT_MIN_SIZE = 10

	def __init__(
			self, color: qt.QColor = qt.QColor(), width: int = 20, height: int = 20, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self.setAcceptDrops(True)
		self.setFlags(
			qt.QGraphicsItem.ItemClipsChildrenToShape | qt.QGraphicsItem.ItemIsSelectable |
			qt.QGraphicsItem.ItemSendsGeometryChanges | qt.QGraphicsItem.ItemIsFocusable)
		self.setAcceptHoverEvents(True)

		self._color = color
		self._width = width
		self._height = height
		self._min_width = self.DEFAULT_MIN_SIZE
		self._min_height = self.DEFAULT_MIN_SIZE
		self._command = ''
		self._target_node = []
		self._target_channel = []
		self._target_value = []
		self._font = qt.QFont('Roboto', 9.0)
		self._font_color = qt.QColor(qt.Qt.black)
		self._label = ''
		self._label_rect = qt.QRectF()
		self._icon = qt.QPixmap()
		self._icon_rect = qt.QRectF()
		self._icon_path = ''
		self._hash_code = ''
		self._signals = ItemSignals()
		self._add = False
		self._hover = False
		self._ignore = False
		self._press_region = 0
		self._press_pos = qt.QPointF()
		self._double_clicking = False
		self._ignore_start_value = False
		self._linked_items = []
		self._lines = {}

		self._effect = GrahicsLayeredBlurEffect()
		self.setGraphicsEffect(self._effect)

		self._timer = ClickTimer()
		self._timer.execute.connect(self._on_timer_execute)

	@property
	@returns(qt.QColor)
	def color(self) -> qt.QColor:
		return self._color

	@color.setter
	@accepts(qt.QColor)
	def color(self, value: qt.QColor):
		self._color = value
		if value.lightnessF() > 0.5:
			self._font_color = qt.QColor(qt.Qt.black)
		else:
			self._font_color = qt.QColor(qt.Qt.white)

	@property
	@returns(float)
	def width(self) -> float:
		return self._width

	@width.setter
	@accepts(float)
	def width(self, value: float):
		self.prepareGeometryChange()
		self._width = value
		self.signals.sizeChanged.emit()

	@property
	@returns(float)
	def height(self) -> float:
		return self._height

	@height.setter
	@accepts(float)
	def height(self, value: float):
		self.prepareGeometryChange()
		self._height = value
		self.signals.sizeChanged.emit()

	@property
	@returns(float)
	def min_width(self) -> float:
		return self._min_width

	@min_width.setter
	@accepts(float)
	def min_width(self, value: float):
		self._min_width = value

	@property
	@returns(float)
	def min_height(self) -> float:
		return self._min_height

	@min_height.setter
	@accepts(float)
	def min_height(self, value: float):
		self._min_height = value

	@property
	@returns(str)
	def command(self) -> str:
		return self._command

	@command.setter
	@accepts(str)
	def command(self, value: str):
		self._command = value

	@property
	@returns(list)
	def target_node(self) -> List[AbstractDropItem]:
		return self._target_node

	@target_node.setter
	@accepts(list)
	def target_node(self, value: List[AbstractDropItem]):
		self._target_node = value

	@property
	@returns(list)
	def target_channel(self) -> List[str]:
		return self._target_channel

	@target_channel.setter
	@accepts(list)
	def target_channel(self, value: List[str]):
		self._target_channel = value

	@property
	@returns(list)
	def target_value(self) -> List[Any]:
		return self._target_value

	@target_value.setter
	@accepts(list)
	def target_value(self, value: List[Any]):
		self._target_value = value

	@property
	@returns(qt.QFont)
	def font(self) -> qt.QFont:
		return self._font

	@font.setter
	@accepts(qt.QFont)
	def font(self, value: qt.QFont):
		if value.family() in consts.FONT_FAMILIES:
			self._font = value
			self.update()

	@property
	@returns(qt.QColor)
	def font_color(self) -> qt.QColor:
		return self._font_color

	@font_color.setter
	@accepts(qt.QColor)
	def font_color(self, value: qt.QColor):
		self._font_color = value
		self.update()

	@property
	@returns(str)
	def label(self) -> str:
		return self._label

	@label.setter
	@accepts(str)
	def label(self, value: str):
		self._label = value
		self.update()

	@property
	@returns(qt.QRectF)
	def label_rect(self) -> qt.QRectF:
		return self._label_rect

	@label_rect.setter
	@accepts(qt.QRectF)
	def label_rect(self, value: qt.QRectF):
		self.prepareGeometryChange()
		self._label_rect = value

	@property
	@returns(qt.QPixmap)
	def icon(self) -> qt.QPixmap:
		return self._icon

	@icon.setter
	@accepts(qt.QPixmap)
	def icon(self, value: qt.QPixmap):
		self._icon = value

	@property
	@returns(qt.QRectF)
	def icon_rect(self) -> qt.QRectF:
		return self._icon_rect

	@icon_rect.setter
	@accepts(qt.QRectF)
	def icon_rect(self, value: qt.QRectF):
		self.prepareGeometryChange()
		self._icon_rect = value

	@property
	@returns(str)
	def icon_path(self) -> str:
		return self._icon_path

	@icon_path.setter
	@accepts(str)
	def icon_path(self, value: str):
		self._icon_path = value
		self._icon = qt.QPixmap(value)
		self.set_default_icon_rect()
		self.set_default_icon_rect()
		if self._icon_rect.isEmpty():
			self._icon_path = ''
			self._icon = qt.QPixmap()
		self.match_min_size_to_subordinate()
		self.update()

	@property
	@returns(str)
	def hash_code(self) -> str:
		return self._hash_code

	@hash_code.setter
	@accepts(str)
	def hash_code(self, value: str):
		self._hash_code = value

	@property
	@returns(ItemSignals)
	def signals(self) -> ItemSignals:
		return self._signals

	@property
	@returns(bool)
	def hover(self) -> bool:
		return self._hover

	@hover.setter
	@accepts(bool)
	def hover(self, flag: bool):
		self._hover = flag

	@property
	@returns(bool)
	def ignore(self) -> bool:
		return self._ignore

	@ignore.setter
	@accepts(bool)
	def ignore(self, flag: bool):
		self._ignore = flag

	@property
	@returns(int)
	def press_region(self) -> int:
		return self._press_region

	@press_region.setter
	@accepts(int)
	def press_region(self, value: int):
		self._press_region = value

	@property
	@returns(qt.QPointF)
	def press_pos(self) -> qt.QPointF:
		return self._press_pos

	@press_pos.setter
	@accepts(qt.QPointF)
	def press_pos(self, value: qt.QPointF):
		self._press_pos = value

	@property
	@returns(GrahicsLayeredBlurEffect)
	def effect(self) -> GrahicsLayeredBlurEffect:
		return self._effect

	@property
	@returns(ClickTimer)
	def timer(self) -> ClickTimer:
		return self._timer

	@override
	def boundingRect(self) -> qt.QRectF:
		return qt.QRectF(0, 0, self.width, self.height)

	@override
	def setVisible(self, visible: bool) -> None:
		super().setVisible(visible)
		for line in self._lines.values():
			line.setVisible(visible)
		for i in self.scene().find_linked_parent_items(self):
			i.lines[self].setVisible(visible)

	@override(check_signature=False)
	def setSelected(self, selected: bool, add: bool = False) -> None:
		self._add = add
		super().setSelected(selected)
		self._add = False

	@override
	def setParentItem(self, parent: qt.QGraphicsItem) -> None:
		pos = self.scenePos() - parent.pos() if parent else self.scenePos()
		super().setParentItem(parent)
		self.setPos(pos)

	@override
	def itemChange(self, change: qt.QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
		if change == qt.QGraphicsItem.ItemSelectedHasChanged:
			modifier = self._keyboard_modifier()
			if self.isSelected() and self.command.lower().startswith('select'):
				if not self._ignore:
					self.emit_command(self.command, modifier=modifier)
			elif not self.isSelected() and self.command.lower().startswith('select'):
				if not self._ignore:
					self.emit_command(f'De{self.command}'.capitalize(), modifier=modifier)
		return super().itemChange(change, value)

	@override
	def hoverEnterEvent(self, event: qt.QGraphicsSceneHoverEvent) -> None:
		self.hover = True
		self._toggle_shadow(True)

	@override
	def hoverLeaveEvent(self, event: qt.QGraphicsSceneHoverEvent) -> None:
		self.hover = False
		self._toggle_shadow(False)

	@override
	def mousePressEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
		is_selected = self.isSelected()
		self.ignore = True
		super().mousePressEvent(event)
		self.setSelected(is_selected)
		self.ignore = False
		self._timer.set_data(event.button(), event.modifiers(), event.pos(), is_selected)
		self._timer.start(0)

	@override(check_signature=False)
	def mouseReleaseEvent(self, event: qt.QGraphicsSceneMouseEvent) -> bool:
		if self._double_clicking:
			self._double_clicking = False
			return False
		button = event.button()
		modifier = event.modifiers()
		if button == qt.Qt.LeftButton and modifier == qt.Qt.AltModifier | qt.Qt.ControlModifier | qt.Qt.ShiftModifier:
			self.signals.redefineMember.emit(self)
			return False
		if self.command.lower() == 'pose':
			self.signals.mouseReleased.emit()
		is_selected = self.isSelected()
		if modifier == qt.Qt.ControlModifier or modifier == qt.Qt.ShiftModifier:
			if not is_selected:
				self.ignore = False
		super().mouseReleaseEvent(event)
		if modifier == qt.Qt.ShiftModifier:
			if not is_selected:
				self.setSelected(False)
		elif modifier == qt.Qt.ControlModifier | qt.Qt.ShiftModifier:
			if is_selected:
				self.setSelected(True)
		self.ignore = False
		if modifier == qt.Qt.ControlModifier:
			self.setSelected(False)
		if button == qt.Qt.LeftButton and modifier == qt.Qt.AltModifier:
			if not is_selected:
				self.setSelected(False)
			self.ignore = False

		return True

	@override
	def mouseDoubleClickEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
		self._double_clicking = True
		self._timer.remove_timer()
		for item in self.linked_items():
			item.setSelected(True, True)

	@override
	def paint(
			self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem, widget: Union[qt.QWidget,None] = ...) -> None:
		# painter.setClipRect(option.exposedRect.adjusted(-1, -1, -1, -1))
		painter.setRenderHints(
			qt.QPainter.Antialiasing | qt.QPainter.TextAntialiasing | qt.QPainter.SmoothPixmapTransform)
		painter.setPen(qt.QPen(consts.SELECTED_BORDER_COLOR, 1.5, j=qt.Qt.RoundJoin) if self.isSelected() else qt.Qt.NoPen)
		painter.setBrush(self.color.lighter(105) if self.isSelected() else self.color)

	def iterate_linked_items(self):

		for linked_item in self._linked_items:
			yield linked_item

	def linked_items(self):

		return list(self.iterate_linked_items())

	def inbound_rect(self) -> qt.QRectF:
		"""
		Returns bounding rect without the margins.

		:return: bound rect without margins.
		:rtype: qt.QRectF
		"""

		return self.boundingRect().adjusted(
			self.BORDER_MARGIN, self.BORDER_MARGIN, -self.BORDER_MARGIN, -self.BORDER_MARGIN)

	def set_default_icon_rect(self):
		"""
		Sets default icon rect for current item.
		"""

		self.prepareGeometryChange()
		rect = self.inbound_rect()
		if rect.isEmpty():
			self.icon_rect = qt.QRectF()
		else:
			if self.icon:
				icon_size = self.icon.size()
				icon_ratio = icon_size.width() * 1.0 / icon_size.height()
				rect_size = rect.size()
				rect_ratio = rect_size.width() * 1.0 / rect_size.height()
				if icon_ratio > rect_ratio:
					offset = (rect.height() - rect.width() / icon_ratio) / 2
					rect.adjust(0, offset, 0, -offset)
				elif icon_size < rect_ratio:
					offset = (rect.width() - rect.height() * icon_ratio) / 2
					rect.adjust(offset, 0, -offset, 0)
			self.icon_rect = rect

	def default_label_rect(self) -> Tuple[qt.QRectF, qt.QRectF]:
		"""
		Returns tuple with default rect and bounding rect for the label rectangle.

		:return: label rectangles.
		:rtype: Tuple[qt.QRectF, qt.QRectF]
		"""

		font_metrics = qt.QFontMetricsF(self.font)
		bounding_rect = self.inbound_rect()
		return font_metrics.boundingRect(
			bounding_rect, qt.Qt.AlignHCenter | qt.Qt.AlignBottom | qt.Qt.TextWordWrap, f'{self.label}*'), bounding_rect

	def set_default_label_rect(self) -> qt.QRectF | None:
		"""
		Sets the default label rect for current item.

		:return: new set rect.
		:rtype: qt.QRectF or None
		"""

		rect, bounding_rect = self.default_label_rect()
		if bounding_rect.contains(rect):
			self.label_rect = rect
			return None
		else:
			if rect.height() > bounding_rect.height():
				rect.moveTopLeft(bounding_rect.topLeft())
			else:
				rect.moveBottomLeft(bounding_rect.bottomLeft())
			return rect

	def match_min_size_to_subordinate(self):
		"""
		Updates width and height based on minimum width and height.
		"""

		self.prepareGeometryChange()
		rect = self.icon_rect.united(self.label_rect)
		self.min_width = max(rect.width() + self.BORDER_MARGIN * 2, self.DEFAULT_MIN_SIZE)
		self.min_height = max(rect.height() + self.BORDER_MARGIN * 2, self.DEFAULT_MIN_SIZE)
		if self.min_width > self.width:
			self.width = self.min_width
		if self.min_height > self.height:
			self.height = self.min_height

	def emit_command(self, command: str = '', channel_flag: str = '', modifier: str = 'No'):
		"""
		Emits command to item scene.

		:param str command: command name to execute.
		:param str channel_flag: channel flag to pass to the command to run.
		:param str modifier: optional modifier to pass to the command.
		"""

		channel = []
		if channel_flag.lower() == 'transform':
			channel = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
		elif channel_flag.lower() == 'All':
			channel = ''
		elif channel_flag == '':
			channel = self.target_channel
		if command.lower() == 'reset' and hasattr(self, 'set_value'):
			self.set_value(0, False)
		self.signals.sendCommandData.emit(command, self.target_node, channel, self.target_value, modifier)

	def _toggle_shadow(self, toggle: bool):
		"""
		Internal function that toggles blur shadow effect.

		:param bool toggle: True to enable effect; False to disable it.
		"""

		if toggle:
			self.effect.set_outer_radius(self.BLUR_OUTER_RADIUS)
			self.effect.set_inner_radius(self.BLUR_INNER_RADIUS)
			self.setFocus()
		else:
			self.effect.set_outer_radius(0)
			self.effect.set_inner_radius(0)
			self.clearFocus()
		self.update()

	def _keyboard_modifier(self) -> str:
		"""
		Internal function that returns current keyboard modifier as a string.

		:return: keyboard modifijer name.
		:rtype: str
		"""

		if self._add:
			return 'Ctrl+Shift'
		modifier = qt.QApplication.keyboardModifiers()
		if modifier == qt.Qt.NoModifier:
			return 'No'
		elif modifier == qt.Qt.ControlModifier:
			return 'Ctrl'
		elif modifier == qt.Qt.ShiftModifier:
			return 'Shift'
		elif modifier == qt.Qt.AltModifier:
			return 'Alt'
		elif modifier == qt.Qt.ControlModifier | qt.Qt.ShiftModifier:
			return 'Ctrl+Shift'
		else:
			return 'No'

	def _on_timer_execute(self):
		"""
		Internal callback function that is called each time clicker timer timeouts.
		"""

		button = self._timer.button
		modifier = self._timer.modifier
		command = self.command.lower()
		if button == qt.Qt.LeftButton and modifier == qt.Qt.NoModifier and not command.startswith('select'):
			if command == 'pose':
				self._ignore_start_value = True
				self.signals.mousePressed.emit()
				self.emit_command(self.command, modifier='1.0')
			elif command == 'range':
				self.emit_command('Toggle')
			else:
				self.emit_command(self.command)
		elif button == qt.Qt.LeftButton and modifier == qt.Qt.AltModifier:
			self.emit_command('Key')
		elif button == qt.Qt.LeftButton and modifier == qt.Qt.ShiftModifier:
			self.ignore = False
			self.setSelected(not self._timer.is_selected)


class AbstractEditableDropItem(AbstractDropItem):
	def __init__(
			self, color: qt.QColor = qt.QColor(), width: int = 20, height: int = 20, parent: qt.QWidget | None = None):
		super().__init__(color=color, width=width, height=height, parent=parent)

		self._label_move_handle = None
		self._icon_top_handle = None
		self._icon_left_handle = None
		self._icon_bottom_handle = None
		self._icon_right_handle = None
		self._icon_center_handle = None
		self._editable = True
		self._is_moving = False

	@property
	@returns(bool)
	def editable(self) -> bool:
		return self._editable

	@editable.setter
	@accepts(bool)
	def editable(self, flag: bool):
		self._editable = flag

	@override
	def setZValue(self, z: float) -> None:
		super().setZValue(z)
		self.signals.itemChanged.emit('zValue')

	@override
	def mouseMoveEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
		if not self.editable:
			return
		if self.press_region:
			self._resize_to_position(event.pos())
		else:
			if event.modifiers() == qt.Qt.AltModifier | qt.Qt.ShiftModifier:
				self._is_moving = True
			super().mouseMoveEvent(event)

	@override
	def mouseReleaseEvent(self, event: qt.QGraphicsSceneMouseEvent) -> bool:
		if not super().mouseReleaseEvent(event):
			return False
		if self._is_moving:
			scene = self.scene()								# type: DropScene
			scene.set_movable_selected_items(False)
			self.setFlags(self.flags() & ~qt.QGraphicsItem.ItemIsMovable)
		self._is_moving = False
		if self.press_region:
			self._restore_item_geometry()

	@override
	def _on_timer_execute(self):

		print('gogogogogog')

		button = self.timer.button
		modifier = self.timer.modifier
		if self.editable and button == qt.Qt.LeftButton and modifier == qt.Qt.AltModifier | qt.Qt.ShiftModifier:
			scene = self.scene()  # type: DropScene
			scene.set_movable_selected_items(True)
			self.setFlags(self.flags() | qt.QGraphicsItem.ItemIsMovable)
			self._is_moving = True
			self.setCursor(qt.Qt.ClosedHandCursor)
		elif self.editable and button == qt.Qt.LeftButton and modifier == qt.Qt.AltModifier | qt.Qt.ControlModifier:
			pos = self.timer.pos
			cursor_pos = self._check_cursor_position(pos)
			if cursor_pos:
				self._setup_item_resize(pos, cursor_pos)
				self._resize_to_position(pos)
		else:
			super()._on_timer_execute()


class AbstractHandle(qt.QGraphicsItem):
	pass


class GroupItem(qt.QGraphicsItem):

	DEFAULT_MIN_SIZE = 100
	PADDING = 10


class RectangleDropItem(AbstractDropItem):

	def type(self) -> int:
		return DropItemType.Rectangle

	@override
	def shape(self) -> qt.QPainterPath:
		path = qt.QPainterPath()
		path.addRect(self.boundingRect())
		return path

	@override
	def paint(
			self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem, widget: Union[qt.QWidget,None] = ...) -> None:
		super().paint(painter, option, widget)

		rect = self.boundingRect().normalized()
		painter.drawRect(rect)
		if self.icon:
			painter.setPen(qt.Qt.NoPen)
			icon_rect = self.icon_rect.translated(rect.topLeft())
			source_rect = qt.QRectF(self.icon.rect())
			painter.drawPixmap(icon_rect, self.icon, source_rect)
		if self.label:
			label_rect = self.label_rect.translated(rect.topLeft())
			painter.setFont(self.font)
			painter.setPen(self.font_color)
			painter.drawText(label_rect, qt.Qt.AlignHCenter | qt.Qt.AlignBottom | qt.Qt.TextWordWrap, self.label)


class RectangleEditableDropItem(RectangleDropItem, AbstractEditableDropItem):

	@override
	def type(self) -> int:
		return DropItemType.EditableRectangle

	@override
	def paint(
			self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem, widget: Union[qt.QWidget,None] = ...) -> None:
		RectangleDropItem.paint(self, painter, option, widget)
		if self._label_move_handle:
			painter.setPen(qt.QPen(qt.Qt.black, 0.5, qt.Qt.DashLine))
			painter.setBrush(qt.Qt.NoBrush)
			painter.drawRect(self.label_rect.adjusted(-2, -2, 2, 2))
