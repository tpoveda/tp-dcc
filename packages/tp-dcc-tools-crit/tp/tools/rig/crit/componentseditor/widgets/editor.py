from __future__ import annotations

import typing

from tp.core import log
from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.tools.rig.crit.componentseditor.widgets.editors import base, inputs

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.componentseditor.controller import CritComponentsEditorController

logger = log.rigLogger


class ComponentsEditor(qt.QWidget):

	def __init__(self, controller: CritComponentsEditorController, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._controller = controller

		main_layout = qt.vertical_layout()
		self.setLayout(main_layout)

		self._main_tab = qt.LineTabWidget(alignment=qt.Qt.AlignLeft, parent=self)
		main_layout.addWidget(self._main_tab)

		descriptor_widget = qt.widget(qt.vertical_layout(spacing=2, margins=(2, 2, 2, 2)), parent=self)
		self._accordion = qt.AccordionWidget(parent=self)
		self._accordion.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
		self._base_settings_widget = base.BaseSettingsWidget(controller=self._controller, parent=self)
		layers_widget = qt.widget(layout=qt.vertical_layout(spacing=2), parent=self)
		layers_widget.setMinimumHeight(450)
		self._layers_tab = qt.LineTabWidget(alignment=qt.Qt.AlignLeft, parent=self)
		self._input_layer_settings_widget = inputs.InputLayerSettingsWidget(parent=self)
		# self._output_layer_settings_widget = outputhook.RigOutputHooksLayerSettingsWidget(parent=self)
		# self._rig_layer_settings_widget = rig.RigLayerSettingsWidget(parent=self)
		self._layers_tab.add_tab(self._input_layer_settings_widget, {'text': 'Inputs', 'image': 'import'})
		# self._layers_tab.add_tab(self._output_layer_settings_widget, {'text': 'Output Hooks', 'image': 'export'})
		# self._layers_tab.add_tab(self._rig_layer_settings_widget, {'text': 'Rig', 'image': 'build'})
		layers_widget.layout().addWidget(self._layers_tab)
		self._accordion.add_item('Base', self._base_settings_widget, collapsed=False)
		self._accordion.add_item('Layers', layers_widget, collapsed=False)
		descriptor_buttons_layout = qt.horizontal_layout(spacing=2)
		self._save_descriptor_button = qt.base_button(text='Save', icon=resources.icon('save'), parent=self)
		self._reset_descriptor_button = qt.base_button(text='Reset', icon=resources.icon('reset'), parent=self)
		self._reset_descriptor_button.setEnabled(False)
		self._revert_descriptor_button = qt.base_button(text='Revert', icon=resources.icon('trash'), parent=self)
		self._revert_descriptor_button.setEnabled(False)
		descriptor_buttons_layout.addWidget(self._save_descriptor_button)
		descriptor_buttons_layout.addWidget(self._reset_descriptor_button)
		descriptor_buttons_layout.addWidget(self._revert_descriptor_button)
		descriptor_buttons_layout.addStretch()
		descriptor_widget.layout().addWidget(self._accordion)
		descriptor_widget.layout().addWidget(qt.divider(parent=self))
		descriptor_widget.layout().addLayout(descriptor_buttons_layout)

		skeleton_widget = qt.widget(layout=qt.vertical_layout(spacing=2), parent=self)
		skeleton_widget.setMinimumHeight(450)
		# self._skeleton_settings_widget = skeleton.SkeletonSettingsWidget(hub=self._hub, parent=self)
		# skeleton_widget.main_layout.addWidget(self._skeleton_settings_widget)

		publish_widget = qt.widget(layout=qt.vertical_layout(spacing=2), parent=self)
		publish_buttons_layout = qt.horizontal_layout(spacing=2)
		self._publish_button = qt.base_button(text='Publish New Version', icon=resources.icon('package'), parent=self)
		self._publish_button.setEnabled(False)
		publish_buttons_layout.addStretch()
		publish_buttons_layout.addWidget(self._publish_button)
		publish_widget.layout().addLayout(publish_buttons_layout)

		self._main_tab.add_tab(descriptor_widget, {'text': 'Descriptor', 'image': 'file'})
		self._main_tab.add_tab(skeleton_widget, {'text': 'Joints', 'image': 'skeleton'})
		publish_tab = self._main_tab.add_tab(publish_widget, {'text': 'Publish', 'image': 'package'})
		publish_tab.setEnabled(False)

		self._controller.startEditingComponent.connect(self._on_controller_start_editing_component)

	def _on_controller_start_editing_component(self, success: bool):
		"""
		Internal callback function that is called each time a component is being edited by the controller.

		:param bool success: whether start editing component operation was successful.
		"""

		if not success:
			return

		active_component = self._controller.active_component
		if not active_component:
			return

		component_class = self._controller.components_managers.find_component_by_type(self._controller.active_component)
		if not component_class:
			logger.warning(f'Rig Component "{self._controller.active_component}" class was not found!')
			return

		self._controller.refresh_editor()
