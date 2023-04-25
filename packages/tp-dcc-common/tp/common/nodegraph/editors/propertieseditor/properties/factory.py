from tp.common.python import decorators
from tp.common.nodegraph.core import consts
from tp.common.nodegraph.editors.propertieseditor.properties import base, color, numbers, paths, vector


@decorators.add_metaclass(decorators.Singleton)
class NodePropertyWidgetFactory(object):

	def __init__(self):
		super(NodePropertyWidgetFactory, self).__init__()

		self._widget_mapping = {
			consts.PropertiesEditorWidgets.HIDDEN: None,
			consts.PropertiesEditorWidgets.LABEL: base.PropLabel,
			consts.PropertiesEditorWidgets.LINE_EDIT: base.PropLineEdit,
			consts.PropertiesEditorWidgets.TEXT_EDIT: base.PropTextEdit,
			consts.PropertiesEditorWidgets.COMBOBOX: base.PropComboBox,
			consts.PropertiesEditorWidgets.CHECKBOX: base.PropCheckBox,
			consts.PropertiesEditorWidgets.SPINBOX: base.PropSpinBox,
			consts.PropertiesEditorWidgets.DOUBLE_SPINBOX: base.PropDoubleSpinBox,
			consts.PropertiesEditorWidgets.COLOR_PICKER: color.PropColorPickerRGB,
			consts.PropertiesEditorWidgets.SLIDER: base.PropSlider,
			consts.PropertiesEditorWidgets.FILE: paths.PropFilePath,
			consts.PropertiesEditorWidgets.FILE_SAVE: paths.PropFileSavePath,
			consts.PropertiesEditorWidgets.VECTOR2: vector.PropVector2,
			consts.PropertiesEditorWidgets.VECTOR3: vector.PropVector3,
			consts.PropertiesEditorWidgets.VECTOR4: vector.PropVector4,
			consts.PropertiesEditorWidgets.FLOAT: numbers.FloatValueEdit,
			consts.PropertiesEditorWidgets.INT: numbers.IntValueEdit,
			consts.PropertiesEditorWidgets.BUTTON: base.PropPushButton,
		}

	def get_widget(self, widget_type):
		"""
		Returns a new instance of a node property widget.

		:param int widget_type: widget type index.
		:return: node property widget instance.
		:rtype: tp.common.nodegraph.editors.propertieseditor.base.BaseProperty or None
		"""

		if widget_type not in self._widget_mapping:
			return None

		return self._widget_mapping[widget_type]()
