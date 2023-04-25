from Qt.QtWidgets import QHBoxLayout

from tp.common.nodegraph.editors.propertieseditor.properties import base, numbers


class BasePropVector(base.BaseProperty):
	"""
	Base widget for the PropVector widgets.
	"""

	def __init__(self, parent=None, fields=0):
		super(BasePropVector, self).__init__(parent)

		self._value = list()
		self._items = list()
		self._can_emit = True

		layout = QHBoxLayout(self)
		layout.setSpacing(2)
		layout.setContentsMargins(0, 0, 0, 0)
		for i in range(fields):
			self._add_item(i)

	def _add_item(self, index):
		_ledit = numbers.NumberValueEdit()
		_ledit.index = index
		_ledit.valueChanged.connect(lambda: self._on_value_change(_ledit.value(), _ledit.index))

		self.layout().addWidget(_ledit)
		self._value.append(0.0)
		self._items.append(_ledit)

	def set_data_type(self, data_type):
		for item in self._items:
			item.set_data_type(data_type)

	def value(self):
		return self._value

	def set_value(self, value=None):
		value = list(value)
		if value != self.value():
			self._value = value
			self._can_emit = False
			self._update_items()
			self._can_emit = True
			self._on_value_change()

	def _update_items(self):
		if not isinstance(self._value, (list, tuple)):
			raise TypeError('Value "{}" must be either list or tuple.'
							.format(self._value))
		for index, value in enumerate(self._value):
			if (index + 1) > len(self._items):
				continue
			if self._items[index].value() != value:
				self._items[index].set_value(value)

	def _on_value_change(self, value=None, index=None):
		if self._can_emit:
			if index is not None:
				self._value[index] = value
			self.valueChanged.emit(self.toolTip(), self._value)
		self.valueChanged.emit(self.toolTip(), self._value)


class PropVector2(BasePropVector):
	"""
	Displays a node property as a "Vector2" widget in the properties editor widget.
	"""

	def __init__(self, parent=None):
		super(PropVector2, self).__init__(parent, 2)


class PropVector3(BasePropVector):
	"""
	Displays a node property as a "Vector3" widget in the properties editor widget.
	"""

	def __init__(self, parent=None):
		super(PropVector3, self).__init__(parent, 3)


class PropVector4(BasePropVector):
	"""
	Displays a node property as a "Vector4"  widget in the properties editor widget.
	"""

	def __init__(self, parent=None):
		super(PropVector4, self).__init__(parent, 4)
