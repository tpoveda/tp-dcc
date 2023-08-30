from __future__ import annotations

import typing
from typing import List

from overrides import override

from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.tools.animpicker import consts, uiutils
from tp.tools.animpicker.views import viewer
from tp.tools.animpicker.widgets import buttons, tabs, dialogs

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.controller import AnimPickerController
	from tp.tools.animpicker.widgets.graphics import EditableDropScene
	from tp.tools.animpicker.events import PreAssignDataToNodeEvent, AssignDataToNodeEvent


class AnimPickerEditorWidget(viewer.AnimPickerViewerWidget):

	TAB_WIDGET_CLASS = tabs.EditableTabWidget

	def __init__(
			self, controller: AnimPickerController, parent: qt.QWidget | None = None):

		self._tool_dialog = None
		self._palette_dialog = None
		self._item_editor = None
		self._guide_widget = None

		super().__init__(controller=controller, parent=parent)

	@override
	def setWindowModified(self, arg__1: bool) -> None:
		super().setWindowModified(arg__1)
		self._save_data_to_node_action.setEnabled(arg__1)

	@override
	def setup_ui(self):
		super().setup_ui()

		bottom_menu_toggle_layout = qt.horizontal_layout(margins=(1, 0, 1, 1))
		self._bottom_menu_toggle_button = buttons.ArrowToggleButton(parent=self)
		self._bottom_menu_toggle_button.setToolButtonStyle(qt.Qt.ToolButtonIconOnly)
		self._bottom_menu_toggle_button.setIconSize(qt.QSize(8, 8))
		self._bottom_menu_toggle_button.setMinimumSize(qt.QSize(0, 12))
		bottom_menu_toggle_layout.addWidget(self._bottom_menu_toggle_button)

		self._bottom_menu_widget = qt.widget(layout=qt.horizontal_layout(), parent=self)
		self._color_button = buttons.ColorButton(parent=self)
		self._color_button.setToolTip(
			'To create a new button, drag and drop onto map. \nTo create multi buttons horizontally, hold Alt and drag. '
			'\nTo create multi buttons vertically, hold Ctrl and drag.\nTo create multi buttons by a captured view from '
			'the camera, hold Ctrl+Alt and drag.\n---------------------------------------------------------------------'
			'----\nTo change Color, click this.\nIf click with holding Ctrl, you can use predefined palette.')
		self._color_button.setFixedSize(qt.QSize(20, 20))
		self._command_type_combo = qt.combobox(
			items=consts.COMMAND_TYPES, tooltip='Select a designated command',
			parent=self)
		self._command_type_combo.setFixedWidth(60)
		self._geo_button = qt.tool_button(
			'Geo', tooltip='Map to Geo:\nTo convert current map to geo, click.', parent=self)
		self._map_button = qt.tool_button(
			'Map', tooltip='Geo to Map:\nTo transfer geo buttons to map, click.', parent=self)
		self._bring_to_front_button = qt.tool_button(
			icon='send_to_front', tooltip='Bring selected buttons to front.', parent=self)
		self._bring_to_forward_button = qt.tool_button(
			icon='bring_forward', tooltip='Bring selected buttons forward.', parent=self)
		self._bring_to_backward_button = qt.tool_button(
			icon='bring_backward', tooltip='Send selected buttons backward.', parent=self)
		self._send_to_back_button = qt.tool_button(
			icon='send_to_back', tooltip='Send selected buttons to back.', parent=self)
		self._align_horizontal_button = qt.tool_button(
			icon='align_horizontal', tooltip='Align Horizontal:\nTo align items horizontally, select items and click.',
			parent=self)
		self._align_vertical_button = qt.tool_button(
			icon='align_vertical', tooltip='Align Vertical:\nTo align items vertically, select items and click.',
			parent=self)
		self._average_gap_x_button = qt.tool_button(
			icon='align_x',
			tooltip='Average Gap Horizontal:\nTo locate items with equal horizontal space, select geo buttons and click.',
			parent=self)
		self._average_gap_y_button = qt.tool_button(
			icon='align_x',
			tooltip='Average Gap Vertical:\nTo locate items with equal vertical space, select geo buttons and click.',
			parent=self)
		self._toolbox_button = qt.tool_button(
			icon='tool', tooltip='Click to show tools dialog.\nThis would give more options to manage.', parent=self)

		for btn in [
			self._geo_button, self._map_button, self._bring_to_front_button, self._bring_to_forward_button,
			self._bring_to_backward_button, self._send_to_back_button, self._align_horizontal_button,
			self._align_vertical_button, self._average_gap_x_button, self._average_gap_y_button, self._toolbox_button]:
			btn.setFixedWidth(30)
			btn.setMinimumHeight(0)
			btn.setFocusPolicy(qt.Qt.NoFocus)

		self._bottom_menu_widget.layout().addWidget(self._color_button)
		self._bottom_menu_widget.layout().addWidget(self._command_type_combo)
		self._bottom_menu_widget.layout().addStretch()
		self._bottom_menu_widget.layout().addWidget(self._geo_button)
		self._bottom_menu_widget.layout().addWidget(self._map_button)
		self._bottom_menu_widget.layout().addWidget(self._bring_to_front_button)
		self._bottom_menu_widget.layout().addWidget(self._bring_to_forward_button)
		self._bottom_menu_widget.layout().addWidget(self._bring_to_backward_button)
		self._bottom_menu_widget.layout().addWidget(self._send_to_back_button)
		self._bottom_menu_widget.layout().addWidget(self._align_horizontal_button)
		self._bottom_menu_widget.layout().addWidget(self._align_vertical_button)
		self._bottom_menu_widget.layout().addWidget(self._average_gap_x_button)
		self._bottom_menu_widget.layout().addWidget(self._average_gap_y_button)
		self._bottom_menu_widget.layout().addWidget(self._toolbox_button)

		self.layout().addLayout(bottom_menu_toggle_layout)
		self.layout().addWidget(self._bottom_menu_widget)

		self._geo_button.setVisible(False)
		self._map_button.setVisible(False)

	@override
	def setup_signals(self):
		super().setup_signals()

		# controller
		self._command_type_combo.currentTextChanged.connect(self._controller.updater('command'))
		self._controller.listen(
			'command', self._command_type_combo.setCurrentText, value=self._command_type_combo.currentText())

		self._controller.preAssignDataToNode.connect(self._on_pre_assign_data_to_node)
		self._controller.assignDataToNode.connect(self._on_assign_data_to_node)

		# bottom bar signals
		self._color_button.clicked.connect(lambda: self._show_color_picker(self._color_button))

	@override
	def _setup_tab_signals(self):
		super()._setup_tab_signals()

		# tab signals
		tab_widget = self._tab_widget			# type: tabs.EditableTabWidget
		tab_widget.tabAdded.connect(self._on_tab_added)
		tab_widget.addItemOn.connect(self._on_scene_add_item_on)

	@override
	def _setup_actions(self):
		super()._setup_actions()

		self._create_character_action = self._create_action(
			'Create Character', self._on_create_character_action_triggered, icon=resources.icon('create'),
			tooltip='Create a new map within map group.\nTo load data file, click RMB.')
		self._edit_current_map_action = self._create_action(
			'Edit Current Map', self._on_edit_current_map_action_triggered, icon=resources.icon('edit'),
			tooltip='Edit current selected map.')
		self._save_data_to_node_action = self._create_action(
			'Assign Data to Node', self._on_save_data_to_node_action_triggered, icon=resources.icon('save'),
			tooltip='Save current map to picker node.\nTo Save map to picker node, click RMB.')
		self._save_data_to_node_action.setEnabled(False)
		self._save_map_to_file_action = self._create_action(
			'Save Map File', self._on_save_map_to_file_action_triggered, icon=resources.icon('save'),
			tooltip='Save the current map to a data file.\nTo save all the maps of the current map group, hold Alt and click')

	@override
	def _setup_upper_toolbar_menu(self):
		for action in [
			self._create_character_action, self._edit_current_map_action, self._save_data_to_node_action,
			self._info_action, self._refresh_action]:
			self._upper_toolbar.addAction(action)
			self._upper_toolbar.widgetForAction(action).setFixedSize(24, 24)

		self._setup_upper_common_actions()
		self._upper_toolbar.widgetForAction(self._create_character_action).installEventFilter(self)
		self._upper_toolbar.widgetForAction(self._save_data_to_node_action).installEventFilter(self)

	def is_current_scene_coop(self) -> bool:
		"""
		Returns whether current scene is in coop mode.

		:return: True if scene is in coop mode; False otherwise.
		:rtype: bool
		"""

		tab_widget = self._tab_widget					# type: tabs.EditableTabWidget
		scene = tab_widget.current_scene()
		if not scene:
			return False

		return scene.coop

	def is_item_selected(self) -> bool:
		"""
		Returns whether current scene has items selected.

		:return: True if scene items are selected; False otherwise.
		:rtype: bool
		"""

		tab_widget = self._tab_widget					# type: tabs.EditableTabWidget
		scene = tab_widget.current_scene()
		if not scene:
			return False

		return bool(scene.selectedItems())

	def _show_color_picker(self, color_button: buttons.ColorButton):
		"""
		Internal function that shows color picker for the given color button.

		:param buttons.ColorButton color_button: color button instance to show picker for.
		"""

		modifier = qt.QApplication.keyboardModifiers()
		button_color = color_button.color()
		if modifier == qt.Qt.NoModifier:
			color_value = self._controller.show_color_editor(button_color.getRgbF()[:3])
			color_button.set_color(qt.QColor.fromRgbF(*color_value))
		elif modifier == qt.Qt.ControlModifier and (
				not self._tool_dialog or color_button != self._tool_dialog.custom_color_button):
			if not self._palette_dialog:
				custom_colors = [
					consts.default_color('RtIK'), consts.default_color('RtFK'), consts.default_color('CnIK'),
					consts.default_color('CnFK'), consts.default_color('LfIK'), consts.default_color('LfFK')]
				self._palette_dialog = dialogs.ColorPaletteDialog(custom_colors=custom_colors, parent=self)
			self._palette_dialog.clear_selection()
			self._palette_dialog.show()
			self._palette_dialog.designated_button = color_button

	def _add_items(
			self, item_type: str, selected: List[str], scene: EditableDropScene, modifier: int, pos: qt.QPointF,
			color: qt.QColor, command_type: str, attach: consts.Attachment | None = None,
			channel: List[str] | None = None, **kwargs):
		"""
		Internal function that handles the addition of a new item into picker scene.

		:param str item_type:
		:param List[str] selected:
		:param EditableDropScene scene:
		:param int modifier:
		:param qt.QPointF pos:
		:param qt.QColor color:
		:param str command_type:
		:param consts.Attachment or None attach:
		:param List[str] or None channel:
		"""

		channel = channel or []

		# Single Button
		if modifier == qt.Qt.NoModifier:
			if item_type == 'Rectangle' or item_type == 'DragPose':
				item = scene.add_vars_item(type=item_type, pos=pos, color=color, command=command_type, **kwargs)
				print(item)

	def _on_tab_added(self):
		"""
		Internal callback function that is called each time a new picker tab is added.
		"""

		if not self._group_line_edit.labels():
			self._group_line_edit.set_labels([consts.DEFAULT_GROUP_NAME])
		self.tab_widget.current_view().loaded = True
		self._controller.assign_data_to_node(self.map_name())
		self.setWindowModified(True)

	def _on_scene_add_item_on(self, pos: qt.QPointF, color: qt.QColor, modifier: int):
		"""
		Internal callback function that is called when a new item is dropped into tab widget scene.

		:param qt.QPointF pos: scene position where the item was dropped.
		:param qt.QColor color: item color.
		:param int modifier: optional drop modifier.
		"""

		selected = self._controller.selected_node_names()
		if not self._controller.check_proper_channels():
			return False

		tab_widget = self._tab_widget				# type: tabs.EditableTabWidget
		scene = tab_widget.current_scene()			# type: EditableDropScene
		command_type = self._controller.state.command
		if command_type != 'Select' and not selected:
			return uiutils.warning('Please select nodes first, then try again!', parent=self)
		if command_type in ('Select', 'Toggle', 'Key', 'Reset'):
			item_type = 'Rectangle'
		elif command_type == 'Pose':
			item_type = 'DragPose'
		else:
			item_type = 'RectangleSlider'
		if item_type == 'Rectangle':
			self._add_items(item_type, selected, scene, modifier, pos, color, command_type)
		else:
			self._add_items(item_type, selected, modifier, pos, color, command_type, attach=consts.Attachment.TOP)
		self.setWindowModified(True)

	def _on_create_character_action_triggered(self):
		"""
		Internal callback function that is called each time Create Character action is triggered by the user.
		"""

		print('Creating character ...')

	def _on_edit_current_map_action_triggered(self):
		"""
		Internal callback function that is called each time Edit Current Map action is triggered by the user.
		"""

		print('Editing current map ...')

	def _on_save_data_to_node_action_triggered(self):
		"""
		Internal callback function that is called each time Assign Data to Node action is triggered by the user.
		"""

		result = self._controller.assign_data_to_node()
		self.setWindowModified(False)
		return result

	def _on_save_map_to_file_action_triggered(self):
		"""
		Internal callback function that is called each time Save Map File action is triggered by the user.
		"""

		print('Saving Map file ...')

	def _on_pre_assign_data_to_node(self, event: PreAssignDataToNodeEvent):
		"""
		Internal callback function that is called when controller is going to assign data to node.

		:param PreAssignDataToNodeEvent event: event.
		"""

		event.total_maps = self.tab_widget.count()
		for i in range(event.total_maps):
			event.views.append(self.tab_widget.view_at_index(i))
			event.map_names.append(self.map_name(i))

		if event.specific_map:
			event.index = -1
			for i in range(self.tab_widget.count()):
				if event.specific_map == self.map_name(i):
					event.index = i
					break
			else:
				event.result = False
				return uiutils.warning(f'Tab is not existing: {event.specific_map}', parent=self)

		event.result = True

	def _on_assign_data_to_node(self, event: AssignDataToNodeEvent):
		"""
		Internal callback function that is called when controller already added assign data to node.

		:param AssignDataToNodeEvent event: event.
		"""

		event.result = True
		if event.is_referenced:
			return

		print('Assigning data to node ...', event.picker_node, event.index)
