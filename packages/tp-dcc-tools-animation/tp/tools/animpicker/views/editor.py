from __future__ import annotations

import typing

from tp.common.qt import api as qt
from tp.tools.animpicker import consts
from tp.tools.animpicker.views import viewer
from tp.tools.animpicker.widgets import buttons, tabs

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.controller import AnimPickerViewerController


class AnimPickerEditorWidget(viewer.AnimPickerViewerWidget):

	TAB_WIDGET_CLASS = tabs.EditableTabWidget

	def __init__(
			self, controller: AnimPickerViewerController, parent: qt.QWidget | None = None):
		super().__init__(controller=controller, parent=parent)

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
