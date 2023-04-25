from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QMenu, QAction, QLineEdit
from Qt.QtGui import QCursor, QIntValidator, QDoubleValidator


class NumberValueMenu(QMenu):

	mouseMove = Signal(object)
	mouseRelease = Signal(object)
	stepChange = Signal()

	def __init__(self, parent=None):
		super(NumberValueMenu, self).__init__(parent)

		self.step = 1
		self.steps = list()
		self.last_action = None

	def __repr__(self):
		return '<{}() object at {}>'.format(self.__class__.__name__, hex(id(self)))

	def mousePressEvent(self, event):
		"""
		Disabling the mouse press event.
		"""

		return

	def mouseReleaseEvent(self, event):
		"""
		Additional functionality to emit signal.
		"""

		self.mouseRelease.emit(event)
		super(NumberValueMenu, self).mouseReleaseEvent(event)

	def mouseMoveEvent(self, event):
		"""
		Additional functionality to emit step changed signal.
		"""

		self.mouseMove.emit(event)
		super(NumberValueMenu, self).mouseMoveEvent(event)
		action = self.actionAt(event.pos())
		if action:
			if action is not self.last_action:
				self.stepChange.emit()
			self.last_action = action
			self.step = action.step
		elif self.last_action:
			self.setActiveAction(self.last_action)

	def _add_step_action(self, step):
		action = QAction(str(step), self)
		action.step = step
		self.addAction(action)

	def set_steps(self, steps):
		self.clear()
		self.steps = steps
		for step in steps:
			self._add_step_action(step)

	def set_data_type(self, data_type):
		if data_type is int:
			new_steps = []
			for step in self.steps:
				if '.' not in str(step):
					new_steps.append(step)
			self.set_steps(new_steps)
		elif data_type is float:
			self.set_steps(self.steps)


class NumberValueEdit(QLineEdit):

	valueChanged = Signal(object)

	def __init__(self, parent=None, data_type=float):
		super(NumberValueEdit, self).__init__(parent)

		self.setToolTip('"MMB + Drag Left/Right" to change values.')
		self.setText('0')

		self._MMB_STATE = False
		self._previous_x = None
		self._previous_value = None
		self._step = 1
		self._speed = 0.1
		self._data_type = float

		self._menu = NumberValueMenu()
		self._menu.mouseMove.connect(self.mouseMoveEvent)
		self._menu.mouseRelease.connect(self.mouseReleaseEvent)
		self._menu.stepChange.connect(self._reset_previous_x)
		self._menu.set_steps([0.001, 0.01, 0.1, 1, 10, 100, 1000])

		self.editingFinished.connect(self._on_text_changed)

		self.set_data_type(data_type)

	def __repr__(self):
		return '<{}() object at {}>'.format(self.__class__.__name__, hex(id(self)))

	def mouseMoveEvent(self, event):
		if self._MMB_STATE:
			if self._previous_x is None:
				self._previous_x = event.x()
				self._previous_value = self.value()
			else:
				self._step = self._menu.step
				delta = event.x() - self._previous_x
				value = self._previous_value
				value = value + int(delta * self._speed) * self._step
				self.set_value(value)
				self._on_text_changed()

		super(NumberValueEdit, self).mouseMoveEvent(event)

	def mousePressEvent(self, event):
		if event.button() == Qt.MiddleButton:
			self._MMB_STATE = True
			self._reset_previous_x()
			self._menu.exec_(QCursor.pos())

		super(NumberValueEdit, self).mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		self._menu.close()
		self._MMB_STATE = False

		super(NumberValueEdit, self).mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		super(NumberValueEdit, self).keyPressEvent(event)

		if event.key() == Qt.Key_Up:
			return
		elif event.key() == Qt.Key_Down:
			return

	def set_data_type(self, data_type):
		self._data_type = data_type
		self._menu.set_data_type(data_type)
		if data_type is int:
			self.setValidator(QIntValidator())
		elif data_type is float:
			self.setValidator(QDoubleValidator())

	def set_steps(self, steps=None):
		steps = steps or [0.001, 0.01, 0.1, 1, 10, 100, 1000]
		self._menu.set_steps(steps)

	def value(self):
		if self.text().startswith('.'):
			text = '0' + self.text()
			self.setText(text)
		return self._convert_text(self.text())

	def set_value(self, value):
		if value != self.value():
			self.setText(str(self._convert_text(value)))

	def _reset_previous_x(self):
		self._previous_x = None

	def _on_text_changed(self):
		self.valueChanged.emit(self.value())

	def _convert_text(self, text):
		try:
			value = float(text)
		except Exception:
			value = 0.0
		if self._data_type is int:
			value = int(value)
		return value


class IntValueEdit(NumberValueEdit):

	def __init__(self, parent=None):
		super(IntValueEdit, self).__init__(parent, data_type=int)


class FloatValueEdit(NumberValueEdit):

	def __init__(self, parent=None):
		super(FloatValueEdit, self).__init__(parent, data_type=float)
