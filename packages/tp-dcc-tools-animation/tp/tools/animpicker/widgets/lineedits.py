from __future__ import annotations

from typing import List

from overrides import override

from tp.common.qt import api as qt
from tp.common.python.decorators import accepts, returns
from tp.tools.animpicker import consts


class PopupLineEdit(qt.QLineEdit):

	labelRenamed = qt.Signal(str, str)
	waitStart = qt.Signal()
	labelSelected = qt.Signal(str)
	labelsChanged = qt.Signal(list)
	requestRenamable = qt.Signal(str)

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._timer_id = None
		self._pos = qt.QPoint()
		self._labels = []
		self._editable = True
		self._wait = consts.WaitState.Proceed
		self._previous_text = ''

		self.setReadOnly(True)
		self.setFocusPolicy(qt.Qt.NoFocus)
		self.setValidator(qt.QRegExpValidator(consts.NAME_REGEX))
		self.setToolTip(
			'To choose a map group, click and select one from the pull-down menu.\nTo rename, hold Alt and click, then '
			'type in.')

	@property
	@returns(bool)
	def editable(self) -> bool:
		return self._editable

	@editable.setter
	@accepts(bool)
	def editable(self, flag: bool):
		self._editable = flag

	@property
	@returns(int)
	def wait(self) -> int:
		return self._wait

	@wait.setter
	@accepts(int)
	def wait(self, value: int):
		self._wait = value

	@override
	def event(self, arg__1: qt.QEvent) -> bool:
		if not self.isReadOnly():
			if arg__1.type() in (
					qt.QEvent.NonClientAreaMouseButtonPress, qt.QEvent.KeyPress) and arg__1.key() == qt.Qt.Key_Escape:
				self.setText(self._previous_text)
				self._previous_text = ''
				self.setReadOnly(True)

		return super().event(arg__1)

	@override
	def mousePressEvent(self, arg__1: qt.QMouseEvent) -> None:
		button = arg__1.button()
		modifier = arg__1.modifiers()
		if self.isReadOnly() and self._editable:
			if button == qt.Qt.LeftButton and modifier == qt.Qt.NoModifier:
				if self._labels:
					menu = qt.QMenu(parent=self)
					for label in self._labels:
						action = menu.addAction(label)
						action.triggered.connect(self._on_label_action_triggered)
					menu.exec_(arg__1.globalPos())
				else:
					super().mousePressEvent(arg__1)
		else:
			super().mousePressEvent(arg__1)

	@override
	def mouseDoubleClickEvent(self, arg__1: qt.QMouseEvent) -> None:
		pass

	@override
	def mouseReleaseEvent(self, arg__1: qt.QMouseEvent) -> None:
		self._remove_timer()
		super().mouseReleaseEvent(arg__1)

	@override
	def timerEvent(self, event: qt.QTimerEvent) -> None:
		if event.timerId() == self._timer_id:
			self._remove_timer()
			menu = qt.QMenu(parent=self)
			for label in self._labels:
				action = menu.addAction(label)
				action.triggered.connect(self._on_label_action_triggered)
			menu.exec_(self._pos)

	@override
	def contextMenuEvent(self, arg__1: qt.QContextMenuEvent) -> None:
		if self._labels and self.isReadOnly():
			self._wait = consts.WaitState.Wait
			self.requestRenamable.emit(self.text())
			while not self._wait:
				pass
			if self._wait == consts.WaitState.Proceed:
				menu = qt.QMenu(parent=self)
				action = menu.addAction('Rename')
				action.triggered.connect(self._on_rename_action_triggered)
				menu.exec_(arg__1.globalPos())

	@override
	def clear(self) -> None:
		super().clear()
		self._labels.clear()

	def labels(self) -> List[str]:
		"""
		Returns labels.

		:return: List[str]
		"""
		return self._labels

	def set_labels(self, value: List[str]):
		"""
		Set labels.

		:param List[str] value: labels.
		"""

		self._labels = value
		if value:
			self.setText(value[0])
		self.labelsChanged.emit(self._labels)

	def append_label(self, label: str):
		"""
		Appends a new label to the line edit.

		:param str label: label to add.
		"""

		self._labels.append(label)
		self.setText(label)
		self.labelsChanged.emit(self._labels)

	def _remove_timer(self):
		"""
		Internal function that removes the internal timer.
		"""

		if self._timer_id:
			self.killTimer(self._timer_id)
			self._timer_id = None

	def _select_text(self, change_text: str):
		"""
		Internal function that compares the current text with the given one and updates it if necessary.

		:param str change_text: text to set.
		"""

		if self.text() != change_text:
			self.setText(change_text)
			self.labelSelected.emit(change_text)

	def _on_label_action_triggered(self):
		"""
		Internal callback function that is called each time a label action is triggered by the user.
		Updates the line edit text with the pressed label text.
		"""

		prev_text = self.text()
		change_text = self.sender().text()
		self._wait = consts.WaitState.Wait
		self.waitStart.emit()
		while not self._wait:
			pass
		if self._wait == consts.WaitState.Proceed:
			self._select_text(change_text)
		elif self._wait == consts.WaitState.GoBack:
			self.setText(prev_text)

	def _on_rename_action_triggered(self):
		"""
		Internal callback function that is called each time rename action is triggered by the user.
		"""

		self.setFocusPolicy(qt.Qt.StrongFocus)
		self.setFocus()
		self.setReadOnly(False)
		self._previous_text = self.text()
		self.returnPressed.connect(self._on_return_pressed)

	def _on_return_pressed(self):
		"""
		Internal callback function that is called text is renamed.
		"""

		new_text = self.text()
		if self._previous_text != new_text:
			self.labelRenamed.emit(self._previous_text, new_text)
			index = self._labels.index(self._previous_text)
			self._previous_text = ''
			self._labels[index] = new_text
		self.returnPressed.disconnect()
		self.setReadOnly(True)
		self.setFocusPolicy(qt.Qt.NoFocus)
		self.clearFocus()
