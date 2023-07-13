from __future__ import annotations

from typing import Iterable, Tuple, List

from overrides import override
from Qt.QtCore import Qt, QSize, QObject
from Qt.QtWidgets import QWidget, QFrame, QLayout
from Qt.QtGui import QResizeEvent

from tp.common.resources import api as resources
from tp.common.qt import qtutils, dpi
from tp.common.qt.widgets import layouts, dialogs, buttons


class FlowToolBar(QFrame):
	"""
	Custom toolbar whose buttons will flow from left to right and wrap to next row if there is no space.
	"""

	class FlowToolbarMenu(dialogs.BaseDialog):
		"""
		Custom dialog used by flow toolbar.
		"""

		def __init__(self, parent: FlowToolBar | None = None):
			super().__init__(show_on_initialize=False, parent=parent)

			self._main_layout = layouts.vertical_layout(spacing=0, margins=(0, 0, 0, 0), parent=self)
			self._setup_ui()

		@override
		def sizeHint(self) -> QSize:
			return self.minimumSize()

		@override
		def show(self) -> None:
			super().show()
			self.resize(self.sizeHint())

		@override
		def layout(self) -> QLayout:
			return self._main_layout

		def _setup_ui(self):
			"""
			Internal function that setups toolbar menu dialog UI.
			"""

			self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

	def __init__(
			self, menu_indicator_icon: str = 'arrow_menu', icon_size: int = 20, icon_padding: int = 2,
			parent: QWidget | None = None):
		super(FlowToolBar, self).__init__(parent)

		self._icon_size = icon_size
		self._icon_padding = icon_padding
		self._overflow_button_color = (128, 128, 128)
		self._menu_indicator_icon = resources.icon(menu_indicator_icon)
		self._overflow_icon = resources.icon('sort_down')
		self._overflow_menu = False
		self._overflow_menu_button = None

		self._main_layout = layouts.horizontal_layout(margins=(0, 0, 0, 0), spacing=0)
		self._main_layout.setAlignment(Qt.AlignTop)
		self._flow_layout = layouts.FlowLayout(margin=0, spacing_x=1, spacing_y=1)
		self._main_layout.addLayout(self._flow_layout)
		self.setLayout(self._main_layout)

		self._overflow_menu = FlowToolBar.FlowToolbarMenu(parent=self)
		self._overflow_layout = self._overflow_menu.layout()

		self._setup_ui()

	@property
	def flow_layout(self) -> layouts.FlowLayout:
		return self._flow_layout

	@property
	def overflow_layout(self) -> QLayout:
		return self._overflow_layout

	@override
	def resizeEvent(self, event: QResizeEvent) -> None:
		self.update_widgets_overflow(event.size())

	@override
	def sizeHint(self) -> QSize:
		spacing_x = self._flow_layout.spacing_x
		next_x = 0
		for item in self._flow_layout.items_list:
			widget = item.widget()
			next_x += widget.sizeHint().width() + spacing_x

		return QSize(next_x + 3, super(FlowToolBar, self).sizeHint().height())

	def _setup_ui(self):
		"""
		Internal function that setup overflow layout UI.
		"""

		self._overflow_menu_button = self._setup_overflow_menu_button()
		self._flow_layout.addWidget(self._overflow_menu_button)

	def icon_size(self) -> QSize:
		"""
		Returns the icon size.

		:return: icon size.
		:rtype: QSize
		"""

		return QSize(self._icon_size + self._icon_padding, self._icon_size + self._icon_padding)

	def set_icon_size(self, size: int):
		"""
		Sets the size of the icons of the toolbar.

		:param QSize size: icon size.
		"""

		self._icon_size = size

		for i in range(0, self._flow_layout.count()):
			widget = self._flow_layout.itemAt(i).widget()
			widget.setIconSize(self.icon_size())

		self._overflow_menu_button = self._setup_overflow_menu_button(btn=self._overflow_menu_button)

	def set_icon_padding(self, padding: int):
		"""
		Sets the padding for the icons of the toolbar.

		:param int padding: icon padding value.
		"""

		self._icon_padding = dpi.dpi_scale(padding)

	def set_overflow_button_color(self, button_color: Iterable[int, int, int]):
		"""
		Sets the color used for the overflow button.

		:param Iterable[int, int, int] button_color: overflow button color.
		"""

		self._overflow_button_color = button_color

	def set_height(self, height: int):
		"""
		Sets fixed height for the toolbar.

		:param int height: toolbar fixed height.
		"""

		self.setFixedHeight(height)

	def set_spacing_x(self, value: int):
		"""
		Sets spacing of items in layout in X.

		:param int value: X spacing value.
		"""

		self._flow_layout.set_spacing_x(value)

	def set_spacing_y(self, value: int):
		"""
		Sets spacing of items in layout in Y.

		:param value: Y spacing value.
		"""

		self._flow_layout.set_spacing_y(value)

	def items_list(self) -> List[QObject]:
		"""
		Returns list of item in toolbar without the overflow menu button

		:return: list of toolbar items.
		:rtype: List[QObject]
		"""

		return self._flow_layout.items_list[:-1]

	def items(self) -> List[QObject]:
		"""
		Returns all items in the toolbar.

		:return: list of toolbar items.
		:rtype: List[QObject]
		"""

		return self._flow_layout.items()

	def update_widgets_overflow(self, size: QSize | None = None) -> List[QObject] | None:
		"""
		Function that hides or show widgets based on the size of the flow toolbar
		If it is too small, it will move widgets to overflow menu and if there are widget in the overflow menu,
		place it back into the flow toolbar if there is space.

		:param QSize size: new size.
		:return: list of hidden widget items.
		:rtype: List[QObject] or None
		"""

		if not self._overflow_menu_button or not self._overflow_menu:
			return None

		spacing_x = self._flow_layout.spacing_x
		spacing_y = self._flow_layout.spacing_y

		if not size:
			size = self.size()
		if len(self.items_list()) == 0:
			return None

		overflow_button_width = self._overflow_menu_button.sizeHint().width()
		width = size.width() - overflow_button_width - spacing_x
		height = size.height()
		hidden = []

		self.setUpdatesEnabled(False)

		next_x = 0
		next_y = self.items_list()[0].widget().height()

		for item in self.items_list():
			item_widget = item.widget()
			widget_width = item_widget.sizeHint().width() + spacing_x
			next_x += widget_width
			if next_x > width:
				next_y += item_widget.height() + (spacing_y * 2)
				next_x = 0
			if next_y > height:
				item_widget.hide()
				hidden.append(item_widget)
			else:
				item_widget.show()

		menu = self._overflow_menu_button.menu(mouse_menu=Qt.LeftButton)
		for a in menu.actions():
			a.setVisible(False)

		for hidden_widget in hidden:
			for a in menu.actions():
				if a.text() == hidden_widget.property('name'):
					a.setVisible(True)
					break

		self._overflow_menu_button.setVisible(len(hidden) > 0)
		self.setUpdatesEnabled(True)

		return hidden

	def clear(self):
		"""
		Clears all toolbar widgets
		"""

		self._overflow_menu_button.clear_menu(Qt.LeftButton)
		self._flow_layout.removeWidget(self._overflow_menu_button)
		self._flow_layout.clear()
		qtutils.clear_layout(self._overflow_layout)

	def overflow_menu_active(self, flag: bool):
		"""
		Sets whether overflow men is active.

		:param bool flag: True to enable overflow menu; False to disable it.
		"""

		self._overflow_menu = flag
		self._overflow_menu_button.setVisible(flag)

	def add_tool_button(
			self, icon_name: str, name: str = '', icon_color: Tuple[int, int, int] = (255, 255, 255),
			double_click_enabled: bool = False) -> buttons.IconMenuButton:
		"""
		Creates a new tool button.

		:param str icon_name: name of the icon to set.
		:param str name: name of the tool.
		:param Tuple[int, int, int] icon_color: optional color for the tool icon.
		:param bool double_click_enabled: whether double click functionality is enabled.
		:return: newly created tool button.
		:rtype: buttons.IconMenuButton
		"""

		name = name or icon_name
		new_button = buttons.IconMenuButton(theme_updates=False, parent=self)
		new_button.set_icon(icon_name, colors=icon_color, size=self._icon_size, color_offset=40)
		new_button.double_click_enabled = double_click_enabled
		new_button.double_click_interval = 150
		new_button.setProperty('name', name)
		new_button.setIconSize(self.icon_size())
		new_button.leftClicked.connect(self._on_tool_button_left_clicked)

		self._flow_layout.addWidget(new_button)
		self._overflow_menu_button.setParent(None)
		self._flow_layout.addWidget(self._overflow_menu_button)
		self._flow_layout.setAlignment(new_button, Qt.AlignVCenter)

		if name != 'overflow':
			tool_icon = resources.icon(icon_name, color=icon_color)
			self._overflow_menu_button.addAction(name, action_icon=tool_icon, connect=new_button.leftClicked.emit)

		return new_button

	def _setup_overflow_menu_button(self, btn: buttons.IconMenuButton | None = None) -> buttons.IconMenuButton:
		"""
		Internal function that setup overflow menu and connects it to given button. If button is not given, it will be
		created.

		:param buttons.IconMenuButton or None btn: optional button instance to set up.
		:return: setup button instance.
		:rtype: buttons.IconMenuButton
		"""

		overflow_color = self._overflow_button_color
		overflow_icon = self._overflow_icon
		btn = btn or buttons.IconMenuButton(parent=self)
		btn.set_icon(overflow_icon, colors=overflow_color, size=self._icon_size, color_offset=40)
		btn.double_click_enabled = False
		btn.setProperty('name', 'overflow')
		btn.setIconSize(self.icon_size())
		btn.setVisible(False)

		return btn

	def _button_clicked(self, tool_button: buttons.IconMenuButton, tool_name: str):
		"""
		Internal function that can be overriden by subclasses to customize what happens when a tool button is clicked
		by the user.

		:param buttons.IconMenuButton tool_button: clicked tool button.
		:param str tool_name: name of the clicked tool.
		"""

		pass

	def _on_tool_button_left_clicked(self):
		"""
		Internal callback function that is called each time a tool button is clicked by the user.
		"""

		tool_name = self.sender().property('name')
		self._button_clicked(self.sender(), tool_name)