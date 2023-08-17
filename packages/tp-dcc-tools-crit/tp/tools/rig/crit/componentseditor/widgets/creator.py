from __future__ import annotations

import typing
from typing import List

from tp.common.python import path
from tp.common.qt import api as qt
from tp.common.resources import api as resources

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.componentseditor.controller import CritComponentsEditorController


class ComponentsCreator(qt.QWidget):

	cancelled = qt.Signal()

	def __init__(self, controller: CritComponentsEditorController, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._controller = controller
		self._is_loaded = False

		main_layout = qt.vertical_layout()
		self.setLayout(main_layout)

		self._paths_combo = qt.ComboBoxRegularWidget('Paths', parent=self)
		self._accordion = qt.AccordionWidget(parent=self)
		self._files_tree = qt.QTreeWidget(parent=self)
		self._files_tree.setHeaderLabel('Rig Component Files')
		self._ok_cancel_buttons = qt.OkCancelButtons(ok_text='Add', parent=self)
		self._ok_cancel_buttons.ok_button.setEnabled(False)

		base_widget_layout = qt.grid_layout(spacing=2)
		base_widget = qt.widget(layout=base_widget_layout, parent=self)
		self._accordion.add_item('Base', base_widget, collapsible=False)
		self._name_line = qt.line_edit(parent=self)
		self._side_combo = qt.combobox(parent=self)
		self._icon_path = qt.PathWidget(
			mode=qt.PathWidget.Mode.EXISTING_FILE, dialog_label='Select Rig Module Icon File', filters='*.png',
			clear=True, parent=self)
		self._description_text = qt.QPlainTextEdit(parent=self)
		self._description_text.setMaximumHeight(qt.dpi_scale(40))
		base_widget_layout.addWidget(qt.label('Name', parent=self), 0, 0, qt.Qt.AlignRight)
		base_widget_layout.addWidget(self._name_line, 0, 1)
		base_widget_layout.addWidget(qt.label('Side', parent=self), 1, 0, qt.Qt.AlignRight)
		base_widget_layout.addWidget(self._side_combo, 1, 1)
		base_widget_layout.addWidget(qt.label('Icon', parent=self), 2, 0, qt.Qt.AlignRight)
		base_widget_layout.addWidget(self._icon_path, 2, 1)
		base_widget_layout.addWidget(qt.label('Description', parent=self), 3, 0, qt.Qt.AlignRight)
		base_widget_layout.addWidget(self._description_text, 3, 1)

		main_layout.addWidget(self._paths_combo)
		main_layout.addWidget(qt.divider(parent=self))
		main_layout.addWidget(self._accordion)
		main_layout.addWidget(qt.divider(parent=self))
		main_layout.addWidget(self._files_tree)
		main_layout.addWidget(qt.divider(parent=self))
		main_layout.addWidget(self._ok_cancel_buttons)

		self._controller.availableComponentPathsChanged.connect(self._on_controller_available_paths_changed)
		self._controller.availableSidesChanged.connect(self._on_controller_available_sides_changed)
		self._controller.activePathChanged.connect(self._on_controller_active_path_changed)
		self._controller.newComponentNameChanged.connect(self._on_controller_new_component_name_changed)
		self._controller.newComponentAdded.connect(self._on_controller_new_component_added)

		self._paths_combo.currentTextChanged.connect(self._on_paths_combo_text_changed)
		self._name_line.textChanged.connect(self._on_name_line_text_changed)
		self._side_combo.currentTextChanged.connect(self._on_side_combo_current_text_changed)
		self._description_text.textChanged.connect(self._on_description_text_changed)
		self._ok_cancel_buttons.okButtonPressed.connect(self._on_ok_button_pressed)
		self._ok_cancel_buttons.cancelButtonPressed.connect(self._on_cancel_button_pressed)

	def refresh(self):
		"""
		Refreshes UI from controller.
		"""

		if not self._controller.active_path:
			self._controller.clear_creator()

		self._refresh_tree()

	def _refresh_tree(self):
		"""
		Internal function that refreshes tree files widget.
		"""

		self._files_tree.clear()
		module_name = self._controller.new_component_name.lower().replace(' ', '')
		icon_path = self._controller.new_component_icon_path
		if not self._controller.active_path or not module_name:
			return

		root_folder_item = qt.QTreeWidgetItem([path.basename(self._controller.active_path)])
		root_folder_item.setIcon(0, resources.icon('folder'))
		module_folder_item = qt.QTreeWidgetItem([module_name])
		module_folder_item.setIcon(0, resources.icon('folder'))
		version_folder_item = qt.QTreeWidgetItem(['v001'])
		version_folder_item.setIcon(0, resources.icon('folder'))
		module_init_file_item = qt.QTreeWidgetItem(['__init__.py'])
		module_init_file_item.setIcon(0, resources.icon('python'))
		version_init_file_item = qt.QTreeWidgetItem(['__init__.py'])
		version_init_file_item.setIcon(0, resources.icon('python'))
		descriptor_file_item = qt.QTreeWidgetItem(['{}.descriptor'.format(module_name)])
		descriptor_file_item.setIcon(0, resources.icon('file'))
		module_file_item = qt.QTreeWidgetItem(['{}.py'.format(module_name)])
		module_file_item.setIcon(0, resources.icon('python'))

		icon_item = None
		if path.is_file(icon_path):
			icon_item = qt.QTreeWidgetItem(['thumb.png'])
			icon_item.setIcon(0, resources.icon('image'))

		self._files_tree.addTopLevelItem(root_folder_item)
		root_folder_item.addChild(module_folder_item)
		module_folder_item.addChildren([version_folder_item, module_init_file_item])
		version_folder_item.addChildren([version_init_file_item, descriptor_file_item, module_file_item])
		if icon_item:
			version_folder_item.addChild(icon_item)

		self._files_tree.expandAll()

	def _on_controller_available_paths_changed(self, paths: List[str]):
		"""
		Internal callback function that is called each time available components path is changed by the controller.

		:param List[str] paths: list of absolute paths where components can be located.
		"""

		with qt.block_signals(self._paths_combo):
			self._paths_combo.clear()
			self._paths_combo.add_items(paths)

	def _on_controller_available_sides_changed(self, sides: List[str]):
		"""
		Internal callback function that is called each time available component sides are changed by the controller.

		:param List[str] sides: list of sides.
		"""

		with qt.block_signals(self._side_combo):
			self._side_combo.addItems(sides)
			self._side_combo.setCurrentText(self._controller.new_component_side)

	def _on_controller_active_path_changed(self, active_path: str):
		"""
		Internal callback function that is called each time active components path is changed by the controller.

		:param str active_path: current active path.
		"""

		with qt.block_signals(self._paths_combo):
			self._paths_combo.setCurrentText(active_path)

	def _on_controller_new_component_name_changed(self, new_component_name: str):
		"""
		Internal callback function that is called each time new component name value is changed by the controller.

		:param str new_component_name: new component name.
		"""

		with qt.block_signals(self._name_line):
			self._name_line.setText(new_component_name)

		if not new_component_name or not self._controller.active_path:
			self._ok_cancel_buttons.ok_button.setEnabled(False)
			self._refresh_tree()
			return

		component_module_path = self._controller.module_path
		self._ok_cancel_buttons.ok_button.setEnabled(True if not path.is_dir(component_module_path) else False)
		self._refresh_tree()

	def _on_controller_new_component_side_changed(self, new_component_side: str):
		"""
		Internal callback function that is called each time new component side value is changed by the controller.

		:param str new_component_side: new component side.
		"""

		with qt.block_signals(self._side_combo):
			self._side_combo.setCurrentText(new_component_side)

	def _on_controller_new_component_description_changed(self, new_component_description: str):
		"""
		Internal callback function that is called each time new component description value is changed by the controller.

		:param str new_component_description: new component description.
		"""

		with qt.block_signals(self._description_text):
			self._description_text.setPlainText(new_component_description)

	def _on_controller_new_component_added(self):
		"""
		Internal callback function that is called each time a new component was added by the controller.
		"""

		self.refresh()

	def _on_paths_combo_text_changed(self, active_path: str):
		"""
		Internal callback function that is called when rig modules path combo index is changed by the user.

		:param str active_path: selected active path.
		"""

		self._controller.active_path = active_path

	def _on_name_line_text_changed(self, name: str):
		"""
		Internal callback function that is called each time user changes component name text.

		:param str name: component name.
		"""

		self._controller.new_component_name = name

	def _on_side_combo_current_text_changed(self, side: str):
		"""
		Internal callback function that is called each time user changes component side combo box.

		:param str side: component side.
		"""

		self._controller.new_component_side = side

	def _on_description_text_changed(self):
		"""
		Internal callback function that is called each time user changes component description text.
		"""

		self._controller.new_component_description = self._description_text.toPlainText()

	def _on_ok_button_pressed(self):
		"""
		Internal callback function that is called each time Add button is clicked by the user.
		Adds a new rig module.
		"""

		self._controller.add_rig_component()

	def _on_cancel_button_pressed(self):
		"""
		Internal callback function that is called each time Cancel button is clicked by the user.
		"""

		self._controller.clear_creator()
		self.cancelled.emit()
