from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import (
	QSizePolicy, QWidget, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QSlider,
	QAbstractSpinBox, QHBoxLayout, QPushButton
)

from tp.common.python import decorators


class BaseProperty(QWidget):
	"""
	Base class for a custom node property widget to be displayed in the PropertiesBin widget.
	"""

	valueChanged = Signal(str, object)

	def __repr__(self):
		return '<{}() object at {}>'.format(
			self.__class__.__name__, hex(id(self)))

	@decorators.abstractmethod
	def value(self):
		raise NotImplementedError

	@decorators.abstractmethod
	def set_value(self, value):
		raise NotImplementedError


class PropLabel(QLabel):
	"""
	Displays a node property as a "QLabel" widget in the PropertiesBin widget.
	"""

	valueChanged = Signal(str, object)

	def __repr__(self):
		return '<{}() object at {}>'.format(
			self.__class__.__name__, hex(id(self)))

	def value(self):
		return self.text()

	def set_value(self, value):
		if value != self.value():
			self.setText(str(value))
			self.valueChanged.emit(self.toolTip(), value)


class PropLineEdit(QLineEdit):
	"""
	Displays a node property as a "QLineEdit" widget in the PropertiesBin
	widget.
	"""

	valueChanged = Signal(str, object)

	def __init__(self, parent=None):
		super(PropLineEdit, self).__init__(parent)
		self.editingFinished.connect(self._on_editing_finished)

	def __repr__(self):
		return '<{}() object at {}>'.format(
			self.__class__.__name__, hex(id(self)))

	def _on_editing_finished(self):
		self.valueChanged.emit(self.toolTip(), self.text())

	def value(self):
		return self.text()

	def set_value(self, value):
		_value = str(value)
		if _value != self.value():
			self.setText(_value)
			self.valueChanged.emit(self.toolTip(), _value)


class PropTextEdit(QTextEdit):
	"""
	Displays a node property as a "QTextEdit" widget in the PropertiesBin
	widget.
	"""

	valueChanged = Signal(str, object)

	def __init__(self, parent=None):
		super(PropTextEdit, self).__init__(parent)
		self._prev_text = ''

	def __repr__(self):
		return '<{}() object at {}>'.format(
			self.__class__.__name__, hex(id(self)))

	def focusInEvent(self, event):
		super(PropTextEdit, self).focusInEvent(event)
		self._prev_text = self.toPlainText()

	def focusOutEvent(self, event):
		super(PropTextEdit, self).focusOutEvent(event)
		if self._prev_text != self.toPlainText():
			self.valueChanged.emit(self.toolTip(), self.toPlainText())
		self._prev_text = ''

	def value(self):
		return self.toPlainText()

	def set_value(self, value):
		_value = str(value)
		if _value != self.value():
			self.setPlainText(_value)
			self.valueChanged.emit(self.toolTip(), _value)


class PropComboBox(QComboBox):
	"""
	Displays a node property as a "QComboBox" widget in the PropertiesBin
	widget.
	"""

	valueChanged = Signal(str, object)

	def __init__(self, parent=None):
		super(PropComboBox, self).__init__(parent)
		self.currentIndexChanged.connect(self._on_index_changed)

	def __repr__(self):
		return '<{}() object at {}>'.format(
			self.__class__.__name__, hex(id(self)))

	def _on_index_changed(self):
		self.valueChanged.emit(self.toolTip(), self.value())

	def items(self):
		"""
		Returns items from the combobox.

		Returns:
			list[str]: list of strings.
		"""
		return [self.itemText(i) for i in range(self.count())]

	def set_items(self, items):
		"""
		Set items on the combobox.

		Args:
			items (list[str]): list of strings.
		"""
		self.clear()
		self.addItems(items)

	def value(self):
		return self.currentText()

	def set_value(self, value):
		if value != self.value():
			idx = self.findText(value, Qt.MatchExactly)
			self.setCurrentIndex(idx)
			if idx >= 0:
				self.valueChanged.emit(self.toolTip(), value)


class PropCheckBox(QCheckBox):
	"""
	Displays a node property as a "QCheckBox" widget in the PropertiesBin
	widget.
	"""

	valueChanged = Signal(str, object)

	def __init__(self, parent=None):
		super(PropCheckBox, self).__init__(parent)
		self.clicked.connect(self._on_clicked)

	def __repr__(self):
		return '<{}() object at {}>'.format(
			self.__class__.__name__, hex(id(self)))

	def _on_clicked(self):
		self.valueChanged.emit(self.toolTip(), self.value())

	def value(self):
		return self.isChecked()

	def set_value(self, value):
		_value = bool(value)
		if _value != self.value():
			self.setChecked(_value)
			self.valueChanged.emit(self.toolTip(), _value)


class PropSpinBox(QSpinBox):
	"""
	Displays a node property as a "QSpinBox" widget in the PropertiesBin widget.
	"""

	valueChanged = Signal(str, object)

	def __init__(self, parent=None):
		super(PropSpinBox, self).__init__(parent)
		self.setButtonSymbols(self.NoButtons)
		self.valueChanged.connect(self._on_value_change)

	def __repr__(self):
		return '<{}() object at {}>'.format(
			self.__class__.__name__, hex(id(self)))

	def _on_value_change(self, value):
		self.valueChanged.emit(self.toolTip(), value)

	def value(self):
		return self.value()

	def set_value(self, value):
		if value != self.value():
			self.setValue(value)


class PropDoubleSpinBox(QDoubleSpinBox):
	"""
	Displays a node property as a "QDoubleSpinBox" widget in the PropertiesBin
	widget.
	"""

	valueChanged = Signal(str, object)

	def __init__(self, parent=None):
		super(PropDoubleSpinBox, self).__init__(parent)
		self.setButtonSymbols(self.NoButtons)
		self.valueChanged.connect(self._on_value_change)

	def __repr__(self):
		return '<{}() object at {}>'.format(
			self.__class__.__name__, hex(id(self)))

	def _on_value_change(self, value):
		self.valueChanged.emit(self.toolTip(), value)

	def value(self):
		return self.value()

	def set_value(self, value):
		if value != self.value():
			self.setValue(value)


class PropSlider(BaseProperty):
	"""
	Displays a node property as a "Slider" widget in the PropertiesBin
	widget.
	"""

	def __init__(self, parent=None):
		super(PropSlider, self).__init__(parent)
		self._block = False
		self._slider = QSlider()
		self._spinbox = QSpinBox()
		self._init()

	def _init(self):
		self._slider.setOrientation(Qt.Horizontal)
		self._slider.setTickPosition(QSlider.TicksBelow)
		self._slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		self._spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(self._spinbox)
		layout.addWidget(self._slider)
		self._spinbox.valueChanged.connect(self._on_spnbox_changed)
		self._slider.valueChanged.connect(self._on_slider_changed)
		# store the original press event.
		self._slider_mouse_press_event = self._slider.mousePressEvent
		self._slider.mousePressEvent = self._on_slider_mouse_press
		self._slider.mouseReleaseEvent = self._on_slider_mouse_release

	def _on_slider_mouse_press(self, event):
		self._block = True
		self._slider_mouse_press_event(event)

	def _on_slider_mouse_release(self, event):
		self.valueChanged.emit(self.toolTip(), self.value())
		self._block = False

	def _on_slider_changed(self, value):
		self._spinbox.setValue(value)

	def _on_spnbox_changed(self, value):
		if value != self._slider.value():
			self._slider.setValue(value)
			if not self._block:
				self.valueChanged.emit(self.toolTip(), self.value())

	def value(self):
		return self._spinbox.value()

	def set_value(self, value):
		if value != self.value():
			self._block = True
			self._spinbox.setValue(value)
			self.valueChanged.emit(self.toolTip(), value)
			self._block = False

	def set_min(self, value=0):
		self._spinbox.setMinimum(value)
		self._slider.setMinimum(value)

	def set_max(self, value=0):
		self._spinbox.setMaximum(value)
		self._slider.setMaximum(value)


class PropPushButton(QPushButton):
	"""
	Displays a node property as a "QPushButton" widget in the properties editor widget.
	"""

	valueChanged = Signal(str, object)
	button_clicked = Signal(str, object)

	def __init__(self, parent=None):
		super(PropPushButton, self).__init__(parent)
		self.clicked.connect(self.button_clicked.emit)

	def set_on_click_func(self, func, node):
		if not callable(func):
			raise TypeError('var func is not a function.')
		self.clicked.connect(lambda: func(node))

	def value(self):
		return

	def set_value(self, value):
		return
