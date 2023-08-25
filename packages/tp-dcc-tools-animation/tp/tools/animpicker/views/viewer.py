from __future__ import annotations

import typing
from typing import List

from overrides import override

from tp.common.qt import api as qt
from tp.tools.animpicker import uiutils
from tp.tools.animpicker.views import main
from tp.tools.animpicker.widgets import buttons, tabs, dialogs

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.widgets.graphics import DropScene
	from tp.tools.animpicker.controller import AnimPickerViewerController


class AnimPickerViewer(qt.FramelessWindow):

	def __init__(self, controller: AnimPickerViewerController, parent: qt.QWidget | None = None):

		self._controller = controller

		super().__init__(
			title=f'Animation Picker Launcher {main.AnimPickerView.VERSION}', width=800, height=600, parent=parent)

	@override
	def setup_ui(self):
		super().setup_ui()

		self.set_main_layout(qt.vertical_layout(margins=(0, 0, 0, 0)))
		main_layout = self.main_layout()
		self._viewer_widget = AnimPickerViewerWidget(controller=self._controller, parent=self)
		main_layout.addWidget(self._viewer_widget)


class AnimPickerViewerWidget(qt.QWidget):

	TAB_WIDGET_CLASS = tabs.TabWidget

	def __init__(
			self, controller: AnimPickerViewerController, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._controller = controller

		main_layout = qt.vertical_layout(margins=(2, 2, 2, 2))
		self.setLayout(main_layout)

		self.setWindowFlags(self.windowFlags() ^ qt.Qt.WindowContextHelpButtonHint)
		self.setLocale(qt.QLocale(qt.QLocale.English))
		self.setFocusPolicy(qt.Qt.StrongFocus)
		self._upper_toolbar = qt.QToolBar(parent=self)
		self._upper_toolbar.setContextMenuPolicy(qt.Qt.PreventContextMenu)
		self._upper_toolbar.setFloatable(False)
		self._upper_toolbar.setIconSize(qt.QSize(16, 16))
		self._lower_toolbar = qt.QToolBar(parent=self)
		self._lower_toolbar.setContextMenuPolicy(qt.Qt.PreventContextMenu)
		self._lower_toolbar.setFloatable(False)
		self._lower_toolbar.setIconSize(qt.QSize(32, 32))
		top_menu_toggle_layout = qt.horizontal_layout(margins=(1, 0, 1, 1))
		self._top_menu_toggle_button = buttons.ArrowToggleButton(parent=self)
		self._top_menu_toggle_button.setToolButtonStyle(qt.Qt.ToolButtonIconOnly)
		self._top_menu_toggle_button.setIconSize(qt.QSize(8, 8))
		self._top_menu_toggle_button.setMinimumSize(qt.QSize(0, 12))
		self._top_menu_toggle_button.upside_down = False
		top_menu_toggle_layout.addWidget(self._top_menu_toggle_button)
		self._tab_widget = self.TAB_WIDGET_CLASS(parent=self)

		main_layout.addWidget(self._upper_toolbar)
		main_layout.addWidget(self._lower_toolbar)
		main_layout.addLayout(top_menu_toggle_layout)
		main_layout.addWidget(self._tab_widget)

	@property
	def tab_widget(self) -> tabs.TabWidget | tabs.EditableTabWidget:
		return self._tab_widget

	def refresh(self, *args):
		"""
		Refreshes viewer.
		"""

		if args and args[0]:
			for dlg in self.tear_off_dialogs():
				dlg.setParent(None)
				dlg.close()

		self._tab_widget.clear()

		nodes = self.determine_page()
		if nodes is None:
			return

		print('gogogogogogo')

	def determine_page(self) -> List[str]:
		return self._controller.filter_picker_nodes()

	def tear_off_dialogs(self) -> List[dialogs.TearOffDialog]:
		"""
		Returns all tear off dialogs attached to this viewer.

		:return: list of tear off dialogs.
		:rtype: List[dialogs.TearOffDialog]
		"""

		return self.findChildren(dialogs.TearOffDialog)

	@uiutils.scene_exists
	def select_current_all_items(self, scene: DropScene = None):
		"""
		Selects all scene items if it exists.

		:param DropScene scene: argument that is filled with the scene whose items we want to select.
		"""

		if not scene:
			return

		scene.select_in_rect(scene.itemsBoundingRect())
		scene.do_all_items('Select', 'All')

	@uiutils.scene_exists
	def reset_all(self, scene: DropScene = None):
		"""
		Deselects all scene items if it exists.

		:param DropScene scene: argument that is filled with the scene whose items we want to select.
		"""

		if not scene:
			return

		scene.select_in_rect(scene.itemsBoundingRect())
		scene.do_all_items('Select', 'All')

	@uiutils.scene_exists
	def reset_transform(self, scene: DropScene = None):
		"""
		Reset all scene items transforms.

		:param DropScene scene: argument that is filled with the scene whose items we want to select.
		"""

		if not scene:
			return

		scene.do_all_items('Reset', 'Transform')

	@uiutils.scene_exists
	def reset_defined(self, scene: DropScene = None):
		"""
		Reset all scene items defined attributes.

		:param DropScene scene: argument that is filled with the scene whose items we want to select.
		"""

		if not scene:
			return

		scene.do_all_items('Reset', 'Defined')

	@uiutils.scene_exists
	def key_all(self, scene: DropScene = None):
		"""
		Key all scene items transforms.

		:param DropScene scene: scene where items are located.
		"""

		if not scene:
			return

		scene.do_all_items('Key', 'All')

	@uiutils.scene_exists
	def key_transform(self, scene: DropScene = None):
		"""
		Key all scene items transforms.

		:param DropScene scene: scene where items are located.
		"""

		if not scene:
			return

		scene.do_all_items('Key', 'Transform')

	@uiutils.scene_exists
	def key_defined(self, scene: DropScene = None):
		"""
		Key all scene items user defined attributes.

		:param DropScene scene: scene where items are located.
		"""

		if not scene:
			return

		scene.do_all_items('Key', 'Defined')

	def show_selected_list(self, *args):
		"""
		Shows a dialog with all current selected nodes.
		"""

		raise NotImplementedError
