from __future__ import annotations

import copy
import typing
import weakref
from functools import partial
from typing import Union, Tuple, List, Iterator

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.preferences.interfaces import core
from tp.common.resources import icon, api as resources

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.builder.core.command import CritUiCommand
	from tp.tools.rig.crit.builder.controller import CritBuilderController
	from tp.tools.rig.crit.builder.models.rig import RigModel
	from tp.tools.rig.crit.builder.models.component import ComponentModel

logger = log.rigLogger


class ComponentsOutliner(qt.BaseFrame):

	COLOR_BAR_WIDTH = None						# type: int
	ACTION_WIDTH = None							# type: int
	ICON_PADDING = None							# type: int
	ICON_WIDTH = None							# type: int
	ICON_TOP_OFFSET = None						# type: int
	EXPANDED_ARROW = None						# type: Tuple[qt.QPointF]
	COLLAPSED_ARROW = None						# type: Tuple[qt.QPointF]
	DRAG_HANDLE_IMAGE = None					# type: qt.QPixmap
	NO_DRAG_HANDLE_IMAGE = None					# type: qt.QPixmap
	DISABLED_BACKGROUND_IMAGE = None			# type: qt.QPixmap
	DISABLED_HIGHLIGHT_IMAGE = None				# type: qt.QPixmap
	ENABLED_IMAGE = None						# type: qt.QPixmap
	ENABLED_SELECTED_IMAGE = None				# type: qt.QPixmap
	MENU_IMAGE = None							# type: qt.QPixmap
	DISABLED_IMAGE = None						# type: qt.QPixmap
	CLOSE_IMAGE = None							# type: qt.QPixmap
	ARROW_COLOR = qt.QColor(189, 189, 189)

	def __init__(self, controller: CritBuilderController | None = None, parent: qt.QWidget | None = None):
		super().__init__(parent)

		self._main_layout = None			# type: qt.QVBoxLayout
		self._toolbar_layout = None			# type: qt.QHBoxLayout
		self._refresh_button = None			# type: qt.QToolButton
		self._tree_widget = None			# type: ComponentsTreeWidget
		self._controller = controller

		if not ComponentsOutliner.COLOR_BAR_WIDTH:
			ComponentsOutliner.COLOR_BAR_WIDTH = qt.dpi_scale(2.5)
		if not ComponentsOutliner.ACTION_WIDTH:
			ComponentsOutliner.ACTION_WIDTH = qt.dpi_scale(15)
		if not ComponentsOutliner.ICON_PADDING:
			ComponentsOutliner.ICON_PADDING = qt.dpi_scale(5)
		if not ComponentsOutliner.ICON_WIDTH:
			ComponentsOutliner.ICON_WIDTH = qt.dpi_scale(10)
		if not ComponentsOutliner.ICON_TOP_OFFSET:
			ComponentsOutliner.ICON_TOP_OFFSET = qt.dpi_scale(2)
		if not ComponentsOutliner.EXPANDED_ARROW:
			ComponentsOutliner.EXPANDED_ARROW = (
				qt.dpi_scale(qt.QPointF(9.0, 11.0)), qt.dpi_scale(qt.QPointF(19.0, 11.0)),
				qt.dpi_scale(qt.QPointF(14.0, 16.0)))
		if not ComponentsOutliner.COLLAPSED_ARROW:
			ComponentsOutliner.COLLAPSED_ARROW = (
				qt.dpi_scale(qt.QPointF(12.0, 8.0)), qt.dpi_scale(qt.QPointF(17.0, 13.0)),
				qt.dpi_scale(qt.QPointF(12.0, 18.0)))
		if not ComponentsOutliner.DRAG_HANDLE_IMAGE:
			ComponentsOutliner.DRAG_HANDLE_IMAGE = resources.icon('crit_outliner_drag').pixmap(qt.QSize(24, 24))
		if not ComponentsOutliner.NO_DRAG_HANDLE_IMAGE:
			ComponentsOutliner.NO_DRAG_HANDLE_IMAGE = resources.icon('crit_outliner_no_drag').pixmap(qt.QSize(24, 24))
		if not ComponentsOutliner.DISABLED_BACKGROUND_IMAGE:
			ComponentsOutliner.DISABLED_BACKGROUND_IMAGE = resources.icon('chevron_bg').pixmap(qt.QSize(24, 24))
		if not ComponentsOutliner.DISABLED_HIGHLIGHT_IMAGE:
			ComponentsOutliner.DISABLED_HIGHLIGHT_IMAGE = resources.icon('chevron_bg_selected').pixmap(qt.QSize(24, 24))
		if not ComponentsOutliner.ENABLED_IMAGE:
			ComponentsOutliner.ENABLED_IMAGE = resources.icon('crit_enable').pixmap(qt.QSize(24, 24))
		if not ComponentsOutliner.ENABLED_SELECTED_IMAGE:
			ComponentsOutliner.ENABLED_SELECTED_IMAGE = resources.icon('crit_enable_selected').pixmap(qt.QSize(24, 24))
		if not ComponentsOutliner.MENU_IMAGE:
			ComponentsOutliner.MENU_IMAGE = resources.icon('menu_dots').pixmap(qt.QSize(24, 24))
		if not ComponentsOutliner.DISABLED_IMAGE:
			ComponentsOutliner.DISABLED_IMAGE = resources.icon('crit_disable').pixmap(qt.QSize(24, 24))
		if not ComponentsOutliner.CLOSE_IMAGE:
			ComponentsOutliner.CLOSE_IMAGE = resources.icon('close').pixmap(qt.QSize(24, 24))

		self._setup_ui()

	@property
	def tree_widget(self) -> ComponentsTreeWidget:
		return self._tree_widget

	def apply_rig(self, rig_model: RigModel):
		"""
		Applies given rig model instance and fills tree widget.

		:param RigModel rig_model: rig model instance.
		"""

		self.setUpdatesEnabled(False)
		try:
			for component_model in rig_model.component_models:
				self.add_component(component_model, sync=False)
			self._tree_widget.sync()
			self._tree_widget.clearSelection()
		except Exception:
			logger.error('Something went wrong while applying rig to rig components outliner', exc_info=True)
		finally:
			self.setUpdatesEnabled(True)

		self._tree_widget.expandAll()

	def add_component(self, component_model: ComponentModel, sync: bool = True):
		"""
		Adds given component model instance into the tree widget.

		:param ComponentModel component_model: component model instance.
		:param bool sync: whether to sync outliner data after adding component model.
		"""

		self._tree_widget.add_component(component_model, sync=sync)

	def sync(self):
		"""
		Syncs tree widget with the current model.
		"""

		self._tree_widget.sync()

	def clear(self):
		"""
		Clears out the tree widget.
		"""

		self._tree_widget.clear()

	def _setup_ui(self):
		"""
		Internal function that setup components outliner widgets.
		"""

		self._main_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))

		self._refresh_button = qt.tool_button(parent=self).image('refresh')
		self._toolbar_layout = qt.horizontal_layout(spacing=0, margins=(0, 0, 0, 0))
		self._tree_widget = ComponentsTreeWidget(controller=self._controller, parent=self)

		self._main_layout.addLayout(self._toolbar_layout)
		self._main_layout.addWidget(qt.divider(parent=self))
		self._main_layout.addWidget(self._tree_widget)


class ComponentsTreeWidget(qt.QTreeWidget):
	"""
	Custom Qt Tree Widget that shows available components within current scene for a specific rig.
	"""

	class ComponentsTreeWidgetDelegate(qt.QItemDelegate):
		"""
		Custom delegate used to paint component tree widget items.
		"""

		ROW_HEIGHT = 20

		class ComponentPainter:
			"""
			Helper Class that handles the painting of the tree widget items.
			"""

			def __init__(
					self, painter: qt.QPainter, option: qt.QStyleOptionViewItem,
					item: ComponentsTreeWidget.ComponentTreeItem, tree_widget: ComponentsTreeWidget):

				self._painter = painter
				self._item = item
				self._rect = copy.deepcopy(option.rect)
				self._is_highlighted = (option.showDecorationSelected and option.state & qt.QStyle.State_Selected)
				self._is_highlighted = self._is_highlighted or self._item.isSelected() if self._item else self._is_highlighted
				self._is_hover = option.state & qt.QStyle.State_MouseOver
				self._highlight_color = option.palette.color(qt.QPalette.Highlight)
				self._parent = weakref.ref(tree_widget)

			def paint_row(self):
				"""
				Paints a component row.
				"""

				self._draw_background()
				self._draw_color_bar()
				self._draw_fill()
				self._draw_arrow_drag_lock()
				text_rect = self._draw_text()
				self._draw_icon(text_rect)
				self._draw_action_icons()

			def _draw_background(self):
				"""
				Internal function that draws component tree widget item background.
				"""

				rect2 = copy.deepcopy(self._rect)
				rect2.setTop(rect2.top() + qt.dpi_scale(1))
				if self._item.is_enabled():
					color = self._highlight_color if self._is_highlighted else self._item.background_color()
					self._painter.fillRect(rect2, color)
				else:
					if self._is_highlighted:
						pixmap = ComponentsOutliner.DISABLED_HIGHLIGHT_IMAGE
					else:
						pixmap = ComponentsOutliner.DISABLED_BACKGROUND_IMAGE
					self._painter.drawTiledPixmap(rect2, pixmap, qt.QPoint(self._rect.left(), 0))

			def _draw_color_bar(self):
				"""
				Internal function that draws color bar.
				"""

				bar_color = self._item.label_color()
				rect2 = copy.deepcopy(self._rect)
				rect2.setRight(rect2.left() + ComponentsOutliner.COLOR_BAR_WIDTH)
				rect2.setTop(rect2.top() + qt.dpi_scale(1))
				self._painter.fillRect(rect2, bar_color)

			def _draw_fill(self):
				"""
				Internal function that draws background fill border.
				"""

				rect2 = copy.deepcopy(self._rect)
				old_pen = self._painter.pen()
				if self._is_hover:
					self._painter.setPen(qt.QPen(self._item.hover_color(), qt.dpi_scale(1)))
				else:
					self._painter.setPen(qt.QPen(self._item.window_background_color(), qt.dpi_scale(1)))
				rect2.setLeft(rect2.left())
				rect2.setRight(rect2.right())
				rect2.setTop(rect2.top() + qt.dpi_scale(1))
				rect2.setBottom(rect2.bottom())
				self._painter.drawRect(rect2)
				self._painter.setPen(old_pen)

			def _draw_arrow_drag_lock(self):
				"""
				Internal function that draws drag and expand/collapse button.
				"""

				self._painter.save()

				old_brush = self._painter.brush()
				rect2 = copy.deepcopy(self._rect)
				padding = qt.dpi_scale(11)
				new_rect = qt.QRect()
				new_rect.setRight(rect2.left() + padding)
				new_rect.setLeft(new_rect.right() - ComponentsOutliner.ICON_WIDTH)
				new_rect.setBottom(rect2.top() - ComponentsOutliner.ICON_WIDTH + qt.dpi_scale(5))
				new_rect.setTop(int(new_rect.bottom() + (ComponentsOutliner.ICON_WIDTH / 2) + 1))
				icon = ComponentsOutliner.DRAG_HANDLE_IMAGE
				# if self._item.is_locked():
				#     icon = ComponentsOutliner..NO_DRAG_HANDLE_IMAGE
				self._painter.drawPixmap(new_rect, icon)
				self._painter.setBrush(old_brush)

				if self._item.has_children():
					self._painter.translate(self._rect.left(), self._rect.top() - qt.dpi_scale(3))
					arrow = ComponentsOutliner.COLLAPSED_ARROW
					if self._item.isExpanded():
						arrow = ComponentsOutliner.EXPANDED_ARROW
					old_brush = self._painter.brush()
					self._painter.setBrush(ComponentsOutliner.ARROW_COLOR)
					self._painter.setPen(qt.Qt.NoPen)
					self._painter.drawPolygon(arrow)
					self._painter.setBrush(old_brush)
					self._painter.translate(-(self._rect.left()), -(self._rect.top() - qt.dpi_scale(3)))

				self._painter.restore()

			def _draw_text(self) -> qt.QRect:
				"""
				Internal function that draw item text.

				:return: text rect.
				:rtype: qt.QRect
				"""

				old_pen = self._painter.pen()
				if self._item.is_enabled():
					# self._painter.setPen(QPen(self._item.parent().palette().text().color(), qt.dpi_scale(1)))
					self._painter.setPen(qt.QPen(self._parent().palette().text().color(), 1))
				else:
					self._painter.setPen(qt.QPen(self._item.inactive_color(), 0.5))

				padding = qt.dpi_scale(30) if self._item.has_children() else qt.dpi_scale(19)
				text_rect = copy.deepcopy(self._rect)
				text_rect.setBottom(text_rect.bottom() + qt.dpi_scale(1))
				text_rect.setLeft(text_rect.left() + padding + ComponentsOutliner.ICON_PADDING)
				text_rect.setRight(text_rect.right() - qt.dpi_scale(6))
				self._painter.drawText(text_rect, qt.Qt.AlignLeft | qt.Qt.AlignVCenter, self._item.name().split(':')[0])
				self._painter.setPen(old_pen)

				return text_rect

			def _draw_icon(self, text_rect: qt.QRect):
				"""
				Internal function that draws item icon.

				:param qt.QRect text_rect: text rect.
				"""

				rect2 = copy.deepcopy(text_rect)
				pixmap = self._item.pixmap()
				if pixmap:
					new_rect = qt.QRect()
					new_rect.setRight(rect2.left() - qt.dpi_scale(2))
					new_rect.setLeft(new_rect.right() - ComponentsOutliner.ICON_WIDTH)
					new_rect.setBottom(int(rect2.top() - ComponentsOutliner.ICON_WIDTH + qt.dpi_scale(2) + 2))
					new_rect.setTop(new_rect.bottom() + ComponentsOutliner.ICON_WIDTH)
					if not self._item.is_enabled():
						self._painter.setOpacity(0.5)
					self._painter.drawPixmap(new_rect, pixmap)

			def _draw_action(self, action_name: str, pixmap: qt.QPixmap, left: int, top: int):
				if pixmap is not None:
					if action_name == 'Close':
						icon_rect = qt.QRect(left, top + 3, 16, 16)
					else:
						icon_rect = qt.QRect(left, top, 24, 24)
					pos = self._parent().mapFromGlobal(qt.QCursor.pos())
					if not icon_rect.contains(pos):
						self._painter.setOpacity(1.0)
					else:
						self._parent().last_hit_action = action_name
						pixmap = self._rollover_icon(pixmap)
					self._painter.drawPixmap(icon_rect, pixmap)
					self._painter.setOpacity(1.0)

			def _rollover_icon(self, pixmap: qt.QPixmap) -> qt.QPixmap:
				img = qt.QImage(pixmap.toImage().convertToFormat(qt.QImage.Format_ARGB32))
				image_height = img.height()
				image_width = img.width()
				for y in range(0, image_height, 1):
					for x in range(0, image_width, 1):
						pixel = img.pixel(x, y)
						color = qt.QColor(pixel)
						img.setPixel(x, y, qt.qRgba(color.red(), color.green(), color.blue(), qt.qAlpha(pixel)))

				return qt.QPixmap(img)

			def _draw_action_icons(self):
				top = self._rect.top() + ComponentsOutliner.ICON_TOP_OFFSET
				start = 0
				count = self._item.action_button_count()

				for i in range(count):
					extra_padding = 0
					pixmap = None
					action_name = self._item.action_button(i)
					if action_name == 'Enabled':
						show_enabled_button = self._item.has_enable_toggle()
						if not show_enabled_button:
							start += ComponentsOutliner.ACTION_WIDTH + extra_padding
							continue
						extra_padding = qt.dpi_scale(5)
						pixmap = ComponentsOutliner.ENABLED_IMAGE
						checked = self._item.is_enabled()
						if not checked:
							pixmap = ComponentsOutliner.DISABLED_IMAGE
						if self._is_highlighted and checked:
							pixmap = ComponentsOutliner.ENABLED_SELECTED_IMAGE
					elif action_name == 'Close':
						pixmap = ComponentsOutliner.CLOSE_IMAGE
					elif action_name == 'Menu':
						pixmap = ComponentsOutliner.MENU_IMAGE

					start += ComponentsOutliner.ACTION_WIDTH + extra_padding
					self._draw_action(action_name, pixmap, self._rect.right() - start, top)

		def __init__(self, tree_widget: ComponentsTreeWidget):
			super().__init__()

			self._tree_widget = weakref.ref(tree_widget)

		@property
		def tree_widget(self) -> ComponentsTreeWidget:
			return self._tree_widget()

		@override
		def sizeHint(self, option: qt.QStyleOptionViewItem, index: qt.QModelIndex) -> qt.QSize:
			size_hint = super().sizeHint(option, index)
			size_hint.setHeight(qt.dpi_scale(ComponentsTreeWidget.ComponentsTreeWidgetDelegate.ROW_HEIGHT))

			return size_hint

		@override
		def paint(self, painter: qt.QPainter, option: qt.QStyleOptionViewItem, index: qt.QModelIndex) -> None:
			if not index.isValid():
				return
			item = self._get_item(index)
			painter = ComponentsTreeWidget.ComponentsTreeWidgetDelegate.ComponentPainter(
				painter, option, item, self._tree_widget())
			painter.paint_row()

		@override
		def createEditor(
				self, parent: Union[qt.QWidget, None], option: qt.QStyleOptionViewItem,
				index: qt.QModelIndex) -> qt.QWidget:
			editor = qt.line_edit(parent=parent)
			editor.setAlignment(qt.Qt.AlignLeft | qt.Qt.AlignVCenter)
			return editor

		@override
		def setEditorData(self, editor: qt.QWidget, index: qt.QModelIndex) -> None:
			item = self._get_item(index)
			editor.setText(item.name().split(':')[0])

		@override
		def updateEditorGeometry(
				self, editor: qt.QWidget, option: qt.QStyleOptionViewItem, index: qt.QModelIndex) -> None:
			indent = self.tree_widget.indent(index)
			rect = copy.deepcopy(option.rect)				# type: qt.QRect
			rect.setLeft(indent + qt.dpi_scale(23))
			rect.setTop(rect.top() + qt.dpi_scale(2))
			rect.setBottom(rect.bottom() - qt.dpi_scale(1))
			rect.setRight(rect.right() - qt.dpi_scale(48))
			editor.setGeometry(rect)

		@override
		def setModelData(self, editor: qt.QWidget, model: qt.QAbstractItemModel, index: qt.QModelIndex) -> None:
			old_value = index.data()
			new_value = editor.text()
			if new_value == old_value:
				return
			item = self._get_item(index)
			item.rename(new_value)

		def _get_item(self, index: qt.QModelIndex) -> qt.QTreeWidgetItem:
			"""
			Internal function that returns corresponding tree widget item for given model index.

			:param qt.QModelIndex index: model index.
			:return: tree widget item instance.
			:rtype: qt.QTreeWidgetItem
			"""

			return self._tree_widget().itemFromIndex(index)

	class ComponentTreeItem(qt.QTreeWidgetItem):

		class ComponentTreeItemSignals:
			syncRequested = qt.Signal()

		def __init__(
				self, component_model: ComponentModel, controller: CritBuilderController | None = None,
				parent: ComponentsTreeWidget | None = None):
			super().__init__(parent=parent)

			self._signals = ComponentsTreeWidget.ComponentTreeItem.ComponentTreeItemSignals()

			self._icon_pixmap = None								# type: qt.QIcon
			self._context_menu = None								# type: qt.QMenu
			self._component_model = component_model
			self._controller = controller
			self._parent = parent
			self._theme_prefs = core.theme_preference_interface()

		@property
		def model(self) -> ComponentModel:
			return self._component_model

		def set_parent(self, parent: qt.QWidget):
			"""
			Sets current component tree item internal parent widget.

			:param qt.QWidget parent: internal parent widget.
			"""

			self._parent = parent

		def is_enabled(self) -> bool:
			"""
			Returns whether component tree item is enabled.
			"""

			return self._component_model.enabled

		def toggle_enabled(self):
			"""
			Toggles component tree item status.
			"""

			self._component_model.enabled = not self._component_model.enabled

		def name(self) -> str:
			"""
			Returns component tree item name.

			:return: component name.
			:rtype: str
			"""

			return self._component_model.name

		def set_name(self, name: str):
			"""
			Sets component tree item name.

			:param str name: new name.
			"""

			self._component_model.name = name

		def side(self) -> str:
			"""
			Returns component tree item side.

			:return: component side.
			:rtype: str
			"""

			return self._component_model.side

		def has_children(self) -> bool:
			"""
			Returns whether component tree item has children.

			:return: True if component tree item is parent of other component tree items; False otherwise.
			:rtype: bool
			"""

			return self._component_model.has_children()

		def background_color(self) -> qt.QColor:
			"""
			Returns component tree item default background color.

			:return: background color.
			:rtype: qt.QColor
			"""

			return qt.QColor('#1B1B1B')

		def window_background_color(self) -> qt.QColor:
			"""
			Returns component tree item default window background color.

			:return: window backgroudn color.
			:rtype: qt.QColor
			"""

			return qt.QColor(43, 43, 43)

		def hover_color(self) -> qt.QColor:
			"""
			Returns component tree item default hover color.

			:return: hover color.
			:rtype: qt.QColor
			"""

			return qt.QColor('#26BBFF')

		def inactive_color(self) -> qt.QColor:
			"""
			Returns component tree item default inactive color.

			:return: inactive color.
			:rtype: qt.QColor
			"""

			return qt.QColor(150, 150, 150)

		def label_color(self) -> qt.QColor:
			"""
			Returns component tree item default label color.

			:return: label color.
			:rtype: qt.QColor
			"""

			if self.side().lower() in ('left', 'l'):
				return qt.QColor('#1471CD')
			elif self.side().lower() in ('right', 'r'):
				return qt.QColor('#DE262A')

			return qt.QColor('#FFFF00')

		def pixmap(self) -> qt.QPixmap:
			"""
			Returns component tree item icon.

			:return: component pixmap.
			:rtype: qt.QPixmap
			"""

			if not self._icon_pixmap:
				color = self._theme_prefs.CRIT_COMPONENT_COLOR
				background_icon = resources.icon('rounded_square_filled')
				component_icon = resources.icon(self._component_model.icon)
				self._icon_pixmap = icon.colorize_layered_icon(
					[background_icon, component_icon], size=qt.dpi_scale(16), colors=[color],
					scaling=[1, 0.7]).pixmap(qt.QSize(16, 16))

			return self._icon_pixmap

		def action_button_count(self) -> int:
			"""
			Returns the total number of action buttons for this component tree item.

			:return: total action button count.
			:rtype: int
			"""

			return 3

		def action_button(self, index: int) -> str:
			"""
			Returns the action button name for the given index.

			:param int index: action button index.
			:return: action button name.
			:rtype: str
			"""

			return ['Close', 'Enabled', 'Menu'][index]

		def has_enable_toggle(self) -> bool:
			"""
			Returns whether component tree item toggle functionality is enabled.

			:return: True if toggle functionality is enabled; False otherwise.
			:rtype: bool
			"""

			return True

		def context_menu(self) -> qt.QMenu:
			"""
			Returns component tree item context menu.

			:return: context menu instance.
			:rtype: qt.QMenu
			"""

			if self._context_menu:
				return self._context_menu

			self._context_menu = qt.searchable_menu()
			self._context_menu.set_search_visible(False)
			for command_ui, command_ui_type, _ in self._controller.ui_commands_manager.iterate_ui_commands_from_ids(
					self._component_model.menu_actions()):
				if command_ui_type == 'PLUGIN':
					new_command_ui = command_ui(logger, ui_interface=self._controller.ui_interface)
					self._add_menu_action_ui_command(new_command_ui, self._context_menu)
				elif command_ui_type == 'SEPARATOR':
					self._context_menu.addSeparator()
			self._context_menu.setToolTipsVisible(True)

			return self._context_menu

		def _add_menu_action_ui_command(self, ui_command: CritUiCommand, menu: qt.QMenu):
			"""
			Internal function that adds the given Crit UI command into the given Qt QMenu instance.

			:param CritUiCommand ui_command: CRIT UI command to add into the given menu.
			:param qt.QMenu menu: Qt menu instance.
			"""

			ui_data = ui_command.UI_DATA
			action = qt.QAction()
			action.setText(ui_data['label'])
			action.setProperty('ui_command', ui_command)
			try:
				action_icon = resources.icon(ui_data['icon'])
				action.setIcon(action_icon)
			except AttributeError:
				pass
			menu.addAction(action)
			action.triggered.connect(partial(self._on_ui_command_action_triggered, ui_command))

			ui_command.refreshRequested.connect(self._signals.syncRequested.emit)
			ui_command.attached_widget = action

		def _on_ui_command_action_triggered(self, ui_command: CritUiCommand, variant_id: str | None = None):
			"""
			Internal callback function that is called when a CRIT UI command action is triggered by the user.

			:param CritUiCommand ui_command: CRIT UI command to execute.
			"""

			ui_command.set_selected(self._controller.selection_model)
			ui_command.component_model = self._component_model
			ui_command.process(variant_id)

	def __init__(self, controller: CritBuilderController | None = None, parent: ComponentsOutliner | None = None):
		super().__init__(parent=parent)

		self._controller = controller
		self._expand_width = qt.dpi_scale(40)
		self._last_hit_action = None
		self._action_button_pressed = False

		self.setHeaderHidden(True)
		self.setIndentation(10)
		self.setMouseTracking(True)
		self.setSelectionMode(qt.QAbstractItemView.SingleSelection)
		self.setRootIsDecorated(False)
		self.setStyleSheet(
			'QTreeWidget::branch {border-image: url(none.png);}QTreeWidget::branch:open:has-children{image:none;}'
			'QTreeWidget::branch:close:has-children{image:none;}')

		self.setItemDelegate(ComponentsTreeWidget.ComponentsTreeWidgetDelegate(self))

	@property
	def last_hit_action(self) -> str | None:
		return self._last_hit_action

	@last_hit_action.setter
	def last_hit_action(self, value: str | None):
		self._last_hit_action = value

	@override
	def mousePressEvent(self, event: qt.QMouseEvent) -> None:

		if event.button() == qt.Qt.LeftButton:
			index = self.indexAt(event.pos())

			if index.row() == -1:
				super().mousePressEvent(event)
				self.clearSelection()
				self._controller.set_selected_components([])
				return

			item = self.itemFromIndex(index) if index.isValid() else None
			action_name = self._current_action(event.pos(), item)
			self.setCurrentItem(item)
			self._controller.set_selected_components([item.model])
			self.selectionModel().setCurrentIndex(index, qt.QItemSelectionModel.NoUpdate)

			print(action_name)

			if action_name is not None:
				self._handle_action(item, action_name)

		super().mousePressEvent(event)

	@override
	def mouseMoveEvent(self, event: qt.QMouseEvent) -> None:

		if not self._action_button_pressed:
			super().mouseMoveEvent(event)

		modifiers = qt.QApplication.keyboardModifiers()
		if modifiers == qt.Qt.AltModifier:
			qt.QWidget.setCursor(self, (qt.QCursor(qt.Qt.DragCopyCursor)))
		else:
			qt.QWidget.unsetCursor(self)
		self._last_hit_action = None
		region = self.childrenRegion()
		self.setDirtyRegion(region)

	@override
	def mouseReleaseEvent(self, event: qt.QMouseEvent) -> None:
		qt.restore_cursor()
		if not self._action_button_pressed:
			super().mouseReleaseEvent(event)
		else:
			self._action_button_pressed = False
		region = self.childrenRegion()
		self.setDirtyRegion(region)

	@override
	def leaveEvent(self, event: qt.QEvent) -> None:
		self._last_hit_action = None
		self.window().repaint()

	def indent(self, index: qt.QModelIndex) -> int:
		"""
		Returns the indent value of the given model index.

		:param qt.QModelIndex index: model index to get indent value of.
		:return: indent value.
		:rtype: int
		"""

		indent = 0
		while index and index.parent().isValid():
			index = index.parent()
			indent += self.indentation()

		return indent

	def add_component(self, component_model: ComponentModel, sync: bool = True) -> ComponentsTreeWidget.ComponentTreeItem:
		"""
		Adds a component widget to this tree widget based on the given component model.

		:param ComponentModel component_model: component model instance.
		:param bool sync: whether to sync outliner data after adding component model.
		:return: newly created component tree item instance.
		:rtype: ComponentsTreeWidget.ComponentTreeItem
		"""

		new_item = ComponentsTreeWidget.ComponentTreeItem(component_model, controller=self._controller, parent=self)
		new_item.setFlags(new_item.flags() | qt.Qt.ItemIsEditable | qt.Qt.ItemIsDropEnabled)
		new_item.setFlags(new_item.flags() & ~qt.Qt.ItemIsDragEnabled)

		self.addTopLevelItem(new_item)
		if sync:
			self.sync()

		return new_item

	def iterator(self) -> Iterator[ComponentTreeItem]:
		"""
		Generator function that iterates over all component tree items.

		:return: iterated component tree items.
		:rtype: Iterator[ComponentTreeItem]
		"""

		for item in qt.safe_tree_widget_iterator(self):
			yield item

	def tree_items(self) -> List[ComponentTreeItem]:
		"""
		Returns lit of tree widget items.

		:return: list of tree widget items.
		:rtype: List[ComponentTreeItem]
		"""

		return list(self.iterator())

	def sync(self):
		"""
		Updates component tree items making sure parenting of the component tree items matches current scene.
		"""

		parent_map = {}
		expand_map = {}

		for item in self.iterator():
			component_name = item.model.component.name().split(':')[0]
			component_side = item.model.component.side()
			parent_map[':'.join((component_name, component_side))] = item
			expand_map[':'.join((component_name, component_side))] = item.isExpanded()

		for item in self.iterator():
			pass

		for item in self.iterator():
			component_name = item.model.component.name().split(':')[0]
			component_side = item.model.component.side()
			is_expanded = expand_map.get(':'.join((component_name, component_side)), True)
			if is_expanded:
				self.setItemExpanded(item, True)
				item.setExpanded(True)

	def minimize_all(self):
		"""
		Minimizes all component tree widget items.
		"""

		for tree_item in self.tree_items():
			tree_item.setExpanded(False)

	def maximize_all(self):
		"""
		Maximizes all component tree widget items.
		"""

		for tree_item in self.tree_items():
			tree_item.setExpanded(True)

	def _current_action(self, pos: qt.QPoint, item: ComponentTreeItem) -> str | None:
		"""
		Intenral function that returns the action located under the given position.

		:param qt.QPoint pos: mouse position.
		:param ComponentTreeItem item: tree widget item we are looking actions for.
		:return: found action name.
		:rtype: str or None
		"""

		if not item:
			return None

		if item.childCount() > 0 and pos.x() < self._expand_width:
			return 'ExpandCollapse'

		return self._last_hit_action

	def _handle_action(self, item: ComponentTreeItem, action_name: str):
		"""
		Internal function that handles the action with given name.

		:param ComponentTreeItem item: component tree item instance.
		:param str action_name: action name to handle.
		"""

		if not action_name:
			return

		if action_name == 'Menu':
			context_menu = item.context_menu()
			if context_menu:
				context_menu.exec_(qt.QCursor.pos())
		elif action_name == 'Enabled':
			item.toggle_enabled()
		elif action_name == 'Close':
			component_name = item.model.name
			print(component_name)
		elif action_name == 'ExpandCollapse':
			self._toggle_expand_collapse()
			return
