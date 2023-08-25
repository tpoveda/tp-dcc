from __future__ import annotations

from typing import List, Any

from tp.common.qt import api as qt
from tp.common.python.decorators import accepts, returns


class ItemSignals(qt.QObject):

	sendCommandData = qt.Signal(str, list, list, list, str)


class AbstractDropItem(qt.QGraphicsItem):

	def __init__(
			self, color: qt.QColor = qt.QColor(), width: int = 20, height: int = 20, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self.setAcceptDrops(True)
		self.setFlags(
			qt.QGraphicsItem.ItemClipsChildrenToShape | qt.QGraphicsItem.ItemIsSelectable |
			qt.QGraphicsItem.ItemSendsGeometryChanges | qt.QGraphicsItem.ItemIsFocusable)
		self.setAcceptHoverEvents(True)

		self._target_node = []
		self._target_channel = []
		self._target_value = []
		self._signals = ItemSignals()
		self._ignore = False

	@property
	@returns(ItemSignals)
	def signals(self) -> ItemSignals:
		return self._signals

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
	@returns(bool)
	def ignore(self) -> bool:
		return self._ignore

	@ignore.setter
	@accepts(bool)
	def ignore(self, flag: bool):
		self._ignore = flag

	def emit_command(self, command: str = '', channel_flag: str = '', modifier: str = 'No'):
		"""
		Emits command to item scene.

		:param str command: command name to execute.
		:param str channel_flag: channel flag to pass to the command to run.
		:param str modifier: optional modifier to pass to the command.
		"""

		if channel_flag.lower() == 'transform':
			channel = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
		elif channel_flag.lower() == 'All':
			channel = ''
		elif channel_flag == '':
			channel = self.target_channel
		if command.lower() == 'reset' and hasattr(self, 'set_value'):
			self.set_value(0, False)
		self.signals.sendCommandData.emit(command, self.target_node, channel, self.target_value, modifier)


class AbstractHandle(qt.QGraphicsItem):
	pass
