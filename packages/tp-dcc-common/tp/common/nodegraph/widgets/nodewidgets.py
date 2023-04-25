from tp.common.python import helpers, decorators
from tp.common.qt import api as qt
from tp.common.nodegraph.core import consts, exceptions


class NodeBaseWidget(qt.QGraphicsProxyWidget):
	"""
	Main wrapper class that allows a qt.QWidget to be added into a BaseNode class.
	"""

	valueChanged = qt.Signal(str, object)

	def __init__(self, name=None, label='', parent=None):
		super(NodeBaseWidget, self).__init__(parent=parent)

		self._name = name
		self._label = label
		self._node = None

		self.setZValue(consts.WIDGET_Z_VALUE)

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def type_(self):
		"""
		Returns the node widget type.

		:return: widget type.
		:rtype: str
		"""

		return str(self.__class__.__name__)

	@property
	def node(self):
		"""
		Returns the node instance this widget is embedded in.

		:return: node widget.
		:rtype: tp.common.nodegraph.core.node.BaseNode or None
		"""

		return self._node

	# ==================================================================================================================
	# ABSTRACT METHODS
	# ==================================================================================================================

	@decorators.abstractmethod
	def value(self):
		"""
		Returns the widget current value.

		:return: widget value.
		:rtype: object
		"""

		raise NotImplementedError

	def set_value(self, value):
		"""
		Sets widget current value.

		:param object value: new widget value.
		"""

		raise NotImplementedError

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def name(self):
		"""
		Returns parent node property name.

		:return: node name.
		:rtype: str
		"""

		return self._name

	def set_name(self, value):
		"""
		Sets the property name ofr the parent node.

		:param str value: node name.
		:raises exception.NodeWidgetError: if widget is already assigned to any node yet.
		"""

		if not value:
			return
		if self.node:
			raise exceptions.NodeWidgetError('Cannot set property name widget already added to a node')
		self._name = value

	def label(self):
		"""
		Returns the label text displayed above the embedded node widget.

		:return: label text.
		:rtype: str
		"""

		return self._label

	def set_label(self, label):
		"""
		Sets the label text displayed above the embedded node widget.

		:param str label: label text.
		"""

		if self.widget():
			self.widget().setTitle(label)
		self._label = label

	def icon(self, name):
		"""
		Returns default icon for the widget.

		:param str name: icon name.
		:return: widget icon.
		:rtype: qt.QIcon
		"""

		return self.style().standardIcon(qt.QStyle.StandardPixmap(name))

	def custom_widget(self):
		"""
		Returns the embedded QWidget used in the node.

		:return: custom widget.
		:rtype: qt.QWidget
		"""

		return self.widget().node_widget()

	def set_custom_widget(self, widget):
		"""
		Sets the custom widget used in the node.

		:param qt.QWidget widget: custom widget.
		:raises exceptions.NodeWidgetError: if a widget is already set.
		"""

		if self.widget():
			raise exceptions.NodeWidgetError('Custom node widget already set.')

		group = NodeGroupBox(self._label)
		group.add_node_widget(widget)
		self.setWidget(group)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def setToolTip(self, tooltip):
		tooltip = tooltip.replace('\n', '<br/>')
		tooltip = '<b>{}</b><br/>{}'.format(self.name, tooltip)
		super(NodeBaseWidget, self).setToolTip(tooltip)

	# ==================================================================================================================
	# CALLBACKS
	# ==================================================================================================================

	def _on_value_changed(self, *args, **kwargs):
		"""
		Internal callback function that is called each time widget value changes.
		"""

		self.valueChanged.emit(self.name(), self.value())


class NodeComboBox(NodeBaseWidget):
	"""
	Custom node widget to display a qt.QComboBox.
	"""

	def __init__(self, name='', label='', items=None, parent=None):
		super(NodeComboBox, self).__init__(name=name, label=label, parent=parent)

		self.setZValue(consts.WIDGET_Z_VALUE + 1)
		combo = qt.QComboBox()
		combo.setMinimumHeight(24)
		combo.addItems(items or [])
		combo.currentIndexChanged.connect(self._on_value_changed)
		combo.clearFocus()
		self.set_custom_widget(combo)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	@property
	def type_(self):
		return 'ComboNodeWidget'

	def value(self):
		return str(self.custom_widget().currentText())

	def set_value(self, value):
		combo_widget = self.custom_widget()
		if isinstance(value, list):
			combo_widget.clear()
			combo_widget.addItems(value)
			return
		if value != self.value():
			index = combo_widget.findText(value, qt.Qt.MatchExactly)
			combo_widget.setCurrentIndex(index)

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def add_item(self, item):
		self.custom_widget().addItem(item)

	def add_items(self, items):
		self.custom_widget().addItems(items)

	def all_items(self):
		combo_widget = self.custom_widget()
		return [combo_widget.itemText(i) for i in range(combo_widget.count())]

	def sort_items(self, reversed=False):
		items = sorted(self.all_items(), reverse=reversed)
		combo_widget = self.custom_wigdet()
		combo_widget.clear()
		combo_widget.addItems(items)

	def clear(self):
		self.custom_widget().clear()


class NodeLineEdit(NodeBaseWidget):
	"""
	Custom node widget to display a qt.QLineEdit.
	"""

	def __init__(self, name='', label='', text='', parent=None):
		super(NodeLineEdit, self).__init__(name=name, label=label, parent=parent)

		palette = self.palette()
		bg_color = palette.alternateBase().color().getRgb()
		text_color = palette.text().color().getRgb()
		text_sel_color = palette.highlightedText().color().getRgb()
		style_dict = {
			'QLineEdit': {
				'background': 'rgba({0},{1},{2},20)'.format(*bg_color),
				'border': '1px solid rgb({0},{1},{2})'
					.format(*consts.NodeGraphViewStyle.GRID_COLOR),
				'border-radius': '3px',
				'color': 'rgba({0},{1},{2},150)'.format(*text_color),
				'selection-background-color': 'rgba({0},{1},{2},100)'
					.format(*text_sel_color),
			}
		}
		stylesheet = ''
		for css_class, css in style_dict.items():
			style = '{} {{\n'.format(css_class)
			for elm_name, elm_val in css.items():
				style += '  {}:{};\n'.format(elm_name, elm_val)
			style += '}\n'
			stylesheet += style
		line_edit = qt.QLineEdit()
		line_edit.setText(text)
		line_edit.setStyleSheet(stylesheet)
		line_edit.setAlignment(qt.Qt.AlignCenter)
		line_edit.editingFinished.connect(self._on_value_changed)
		line_edit.clearFocus()
		self.set_custom_widget(line_edit)
		self.widget().setMaximumWidth(140)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	@property
	def type_(self):
		return 'LineEditNodeWidget'

	def value(self):
		return str(self.custom_widget().text())

	def set_value(self, value):
		if value != self.value():
			self.custom_widget().setText(value)
			self._on_value_changed()


class NodeCheckBox(NodeBaseWidget):
	"""
	Custom node widget to display a qt.QCheckBox.
	"""

	def __init__(self, name='', label='', text='', state=False, parent=None):
		super(NodeCheckBox, self).__init__(name=name, label=label, parent=parent)

		check_box = qt.QCheckBox(text)
		check_box.setChecked(state)
		check_box.setMinimumWidth(80)

		font = check_box.font()
		font.setPointSize(11)
		check_box.setFont(font)
		check_box.stateChanged.connect(self._on_value_changed)
		self.set_custom_widget(check_box)
		self.widget().setMaximumWidth(140)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	@property
	def type_(self):
		return 'CheckboxNodeWidget'

	def value(self):
		return str(self.custom_widget().isChecked())

	def set_value(self, value):
		if value != self.value():
			self.custom_widget().setChecked(value)


class NodeGroupBox(qt.QGroupBox):

	def __init__(self, label, parent=None):
		super(NodeGroupBox, self).__init__(parent)
		layout = qt.QVBoxLayout(self)
		layout.setSpacing(1)
		self.setTitle(label)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def setTitle(self, text):
		margin = (0, 2, 0, 0) if text else (0, 0, 0, 0)
		self.layout().setContentsMargins(*margin)
		super(NodeGroupBox, self).setTitle(text)

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def set_title_align(self, align='center'):
		text_color = self.palette().text().color().getRgb()
		style_dict = {
			'QGroupBox': {
				'background-color': 'rgba(0, 0, 0, 0)',
				'border': '0px solid rgba(0, 0, 0, 0)',
				'margin-top': '1px',
				'padding-bottom': '2px',
				'padding-left': '1px',
				'padding-right': '1px',
				'font-size': '8pt',
			},
			'QGroupBox::title': {
				'subcontrol-origin': 'margin',
				'subcontrol-position': 'top center',
				'color': 'rgba({0}, {1}, {2}, 100)'.format(*text_color),
				'padding': '0px',
			}
		}
		if self.title():
			style_dict['QGroupBox']['padding-top'] = '14px'
		else:
			style_dict['QGroupBox']['padding-top'] = '2px'

		if align == 'center':
			style_dict['QGroupBox::title']['subcontrol-position'] = 'top center'
		elif align == 'left':
			style_dict['QGroupBox::title']['subcontrol-position'] += 'top left'
			style_dict['QGroupBox::title']['margin-left'] = '4px'
		elif align == 'right':
			style_dict['QGroupBox::title']['subcontrol-position'] += 'top right'
			style_dict['QGroupBox::title']['margin-right'] = '4px'
		stylesheet = ''
		for css_class, css in style_dict.items():
			style = '{} {{\n'.format(css_class)
			for elm_name, elm_val in css.items():
				style += '  {}:{};\n'.format(elm_name, elm_val)
			style += '}\n'
			stylesheet += style
		self.setStyleSheet(stylesheet)

	def add_node_widget(self, widget):
		self.layout().addWidget(widget)

	def node_widget(self):
		return self.layout().itemAt(0).widget()