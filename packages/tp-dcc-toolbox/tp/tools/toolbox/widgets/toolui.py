from __future__ import annotations

import typing
from typing import Tuple, List, Dict

from overrides import override

from tp.core import log
from tp.common.python import color
from tp.common.qt import api as qt
from tp.common.qt.widgets import buttons

if typing.TYPE_CHECKING:
	from tp.tools.toolbox.widgets.toolboxtree import ToolboxTreeWidget

logger = log.tpLogger


class ToolUiWidget(qt.StackItem):
	"""
	Main widget class that is placed within toolbox tree widget items.
	"""

	id = 'toolUi'
	ui_data = {
		'label': 'Toolset', 'icon': 'tpdcc', 'tooltip': '', 'defaultActionDoubleClick': False, 'helpUrl': '',
		'autoLinkProperties': True}
	tags = []							# type: List[str]
	creator = ''

	class DisplayModeButton(buttons.BaseButton):

		FIRST_INDEX = 1
		LAST_INDEX = -1

		def __init__(
				self, size: int = 16, color: Tuple[int, int, int] = (255, 255, 255), initial_index: int = FIRST_INDEX,
				parent: ToolUiWidget | None = None):
			super().__init__(parent=parent)

	displaySwitched = qt.Signal()
	updatePropertyRequested = qt.Signal()
	savePropertyRequested = qt.Signal()
	toolUiShown = qt.Signal()
	toolUiActivated = qt.Signal()
	toolUiHidden = qt.Signal()
	toolUiMousePressed = qt.Signal()
	toolUiDragged = qt.Signal()
	toolUiDropped = qt.Signal()
	toolUiDragCancelled = qt.Signal()
	toolUiDeactivated = qt.Signal()
	toolUiClosed = qt.Signal()

	def __init__(
			self, icon_color: Tuple[int, int, int] = (255, 255, 255), tree_widget: ToolboxTreeWidget | None = None,
			widget_item: ToolboxTreeWidget.ToolboxTreeWidgetItem | None = None, parent: qt.QWidget | None = None):

		self._icon_color = icon_color
		self._tree_widget = tree_widget
		self._tool_ui_widget_item = widget_item
		self._icon_name = self.ui_data['icon']
		self._block_save = False
		self._show_warnings = True
		self._stacked_widget = None							# type: qt.QStackedWidget
		self._display_mode_button = None					# type: ToolUiWidget.DisplayModeButton
		self._help_button = None							# type: qt.BaseButton
		self._widgets = []									# type: List[qt.QWidget]
		self._properties = self.setup_properties()

		super().__init__(
			title=self.ui_data['label'], collapsed=True, icon=self._icon_name, shift_arrows_enabled=False,
			title_editable=False, title_upper=True, parent=parent or tree_widget)

	@property
	def stacked_widget(self) -> qt.QStackedWidget:
		return self._stacked_widget

	@property
	def display_mode_button(self) -> ToolUiWidget.DisplayModeButton:
		return self._display_mode_button

	@property
	def properties(self):
		return self._properties

	@override
	def setup_ui(self):
		super().setup_ui()

		self.setContentsMargins(0, 0, 0, 0)
		# self.show_expand_indicator(False)
		self.set_title_text_mouse_transparent(True)

		self._stacked_widget = qt.QStackedWidget(self._widget_hider)
		self._stacked_widget.setContentsMargins(0, 0, 0, 0)
		self._stacked_widget.setLineWidth(0)
		self._stacked_widget.setMidLineWidth(0)
		self._contents_layout.addWidget(self._stacked_widget)
		self._contents_layout.setContentsMargins(0, 0, 0, 0)
		self._contents_layout.setSpacing(0)

		self._display_mode_button = ToolUiWidget.DisplayModeButton(size=16, color=self._icon_color, parent=self)
		self._display_mode_button.setIconSize(qt.QSize(20, 20))
		self._help_button = qt.base_button(icon='help', parent=self)
		self._help_button.setIconSize(qt.QSize(15, 15))

		self._contents_layout.addWidget(qt.QPushButton('Hello Friend'))

		self.set_icon_color(self._icon_color)

		self._visual_update(collapse=False)

		if not self.ui_data.get('helpUrl', ''):
			self._help_button.hide()

		display_button_pos = 7
		self._title_frame.horizontal_layout.setSpacing(0)
		self._title_frame.horizontal_layout.setContentsMargins(0, 0, 0, qt.dpi_scale(1))
		self._title_frame.delete_button.setIconSize(qt.QSize(12, 12))
		self._title_frame.item_icon.setIconSize(qt.QSize(20, 20))
		self._title_frame.horizontal_layout.insertWidget(display_button_pos, self._help_button)
		self._title_frame.horizontal_layout.insertWidget(display_button_pos, self._display_mode_button)
		self._title_frame.mouseReleaseEvent = self._on_activate_event

		self.toolUiHidden.connect(self.toolUiDeactivated.emit)
		self.toolUiDragged.connect(self.toolUiDeactivated.emit)
		self.toolUiShown.connect(self.toolUiActivated.emit)
		self.toolUiDragCancelled.connect(self.toolUiActivated.emit)
		if self._tree_widget:
			self.toolUiDeactivated.connect(self._tree_widget.toolbox_frame.update_colors)

	def block_save(self, flag: bool):
		"""
		Whether to block the saving of properties.

		:param bool flag: True to block the saving of properties; False otherwise.
		:rtype: bool
		"""

		self._block_save = flag

	def count(self) -> int:
		"""
		Returns the total number of stacked widgets.

		:return: number of stacked widgets.
		:rtype: int
		"""

		return self._stacked_widget.count()

	def setup_properties(self, properties: Dict | None = None):
		"""
		Initializes all the properties dictionaries for this tool ui.

		:param Dict or None properties:
		:return:
		"""

		pass

	def auto_link_properties(self, widgets: List[qt.QWidget]):
		"""
		Auto link properties of the given content widgets if allowed.

		:param List[qt.QWidget] widgets: list of content widgets.
		"""

		if not self.ui_data.get('autoLinkProperties', True):
			return

		print('Auto Linking Properties ...')

	def save_properties(self, current_widget: ToolUiWidget | None = None):
		"""
		Saves the properties from the tool ui into the tool ui widget properties.

		:param ToolUiWidget or None current_widget: optional widget to save properties for.
		"""

		pass

	def populate_widgets(self):
		"""
		Makes the connection for all widgets linked in the tool ui based on the saved properties.
		"""

		pass

	def set_current_index(self, index: int):
		"""
		Sets the current index of the stacked widget.

		:param int index: index of the stacked widget.
		"""

		self.block_save(True)
		try:
			for i in range(self._stacked_widget.count()):
				w = self._stacked_widget.widget(i)
				w.setSizePolicy(w.sizePolicy().horizontalPolicy(), qt.QSizePolicy.Ignored)
			self._stacked_widget.setCurrentIndex(index)
			widget = self._stacked_widget.widget(index)
			if widget is not None:
				widget.setSizePolicy(widget.sizePolicy().horizontalPolicy(), qt.QSizePolicy.Ignored)
			else:
				logger.warning(f'Widget not found for given index: {index}')
		finally:
			self.block_save(False)

	def set_active(self, active: bool = True, emit: bool = True):
		"""
		Sets whether this tool ui instance is active.

		:param bool active: True to expand tool ui; False to collapse it.
		:param bool emit: whether to emit singals.
		"""

		if active:
			self.expand(emit=emit)
		else:
			self.collapse(emit=emit)
			qt.single_shot_timer(lambda: self.toolUiHidden.emit())

		self._visual_update(collapse=not active)

	def set_icon_color(self, color: Tuple[int, int, int] = (255, 255, 255), set_color: bool = True):
		"""
		Sets the icon color for al the icons including the item, move and close icons.

		:param Tuple[int, int, int] color: icon color.
		:param bool set_color: whether to store the new set color internally.
		"""

		if set_color:
			self._icon_color = color

		darken = 0.8
		self.set_item_icon_color(color)
		self._display_mode_button.set_icon_color(color)
		self._help_button.set_icon_color((int(color[0] * darken), int(color[1] * darken), int(color[2] * darken)))
		self._title_frame.delete_button.set_icon_color(color)

	def pre_content_setup(self):
		"""
		Function that is executed before tool Ui contents are created. Should be overriden by subclasses.
		"""

		pass

	def post_content_setup(self):
		"""
		Function that is executed after the contents are created. Should be overriden by subclasses.
		"""

		pass

	def contents(self) -> List[qt.QWidget]:
		"""
		Function that returns list of widgets that should be added to the contents stack. Each widget should correspond
		to a different widget display mode.

		:return: list of content widgets.
		:rtype: List[qt.QWidget]
		"""

		return []

	def add_stacked_widget(self, widget: qt.QWidget):
		"""
		Adds given widget into the tool ui widget stack.

		:param qt.QWidget widget: widget to add into the stack.
		:raises ValueError: if no widget to add is given.
		"""

		if widget is None:
			raise ValueError(f'No widget to add into Tool Ui "{self.__class__.__name__}" widgets stack!')

		self._widgets.append(widget)
		widget.setParent(self._widget_hider)
		widget.setProperty('color', self._icon_color)
		self._stacked_widget.addWidget(widget)

	def update_display_button(self):
		"""
		Updates the display button based on the number of widgets within the stacked widget layout.
		"""

		pass

	def _visual_update(self, collapse: bool = True):
		"""
		Internal function that update visual of the tool ui.

		:param bool collapse: whether to collapse or expand tool ui.
		"""

		if collapse:
			self.set_icon_color(color.desaturate(self._icon_color, 0.75), set_color=False)
			self.title_text_widget().setObjectName('disabled')
			self.title_text_widget().setStyleSheet('')
		else:
			self.set_icon_color(self._icon_color)
			self.title_text_widget().setObjectName('active')

		qt.update_widget_style(self.title_text_widget())

		self.setUpdatesEnabled(False)
		try:
			self.updatePropertyRequested.emit()
		finally:
			self.setUpdatesEnabled(True)

	def _on_activate_event(self, event: qt.QMouseEvent, emit: bool = True):
		"""
		Internal callback function that is called when tool ui should be activated.

		:param qt.QMouseEvent event: qt mouse event.
		:param bool emit: whether signals should be emitted.
		"""

		self.toggle_contents(emit=emit)
		event.ignore()
