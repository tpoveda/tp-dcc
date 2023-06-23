#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom QStackedWidget widgets.
"""

from __future__ import annotations

from Qt.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve
from Qt.QtWidgets import (
	QSizePolicy, QWidget, QFrame, QStackedWidget, QGraphicsOpacityEffect, QVBoxLayout, QHBoxLayout, QSpacerItem
)

from tp.preferences.interfaces import core
from tp.common.qt import dpi, consts
from tp.common.qt.widgets import layouts, lineedits, buttons


def sliding_opacity_stacked_widget(parent: QWidget | None = None) -> SlidingOpacityStackedWidget:
	"""
	Creates a new QStackWidget that uses opacity animation to switch between stack widgets.

	:param QWidget parent: parent widget.
	:return: stack widget.
	:rtype: SlidingOpacityStackedWidget
	"""

	new_stack_widget = SlidingOpacityStackedWidget(parent=parent)
	return new_stack_widget


class SlidingOpacityStackedWidget(QStackedWidget):
	"""
	Custom stack widget that activates opacity animation when current stack index changes
	"""

	def __init__(self, parent: QWidget | None = None):
		super(SlidingOpacityStackedWidget, self).__init__(parent)

		self._prev_index = 0
		self._to_show_pos_anim = QPropertyAnimation()
		self._to_show_pos_anim.setDuration(400)
		self._to_show_pos_anim.setPropertyName(b'pos')
		self._to_show_pos_anim.setEndValue(QPoint(0, 0))
		self._to_show_pos_anim.setEasingCurve(QEasingCurve.OutCubic)
		self._to_hide_pos_anim = QPropertyAnimation()
		self._to_hide_pos_anim.setDuration(400)
		self._to_hide_pos_anim.setPropertyName(b'pos')
		self._to_hide_pos_anim.setEndValue(QPoint(0, 0))
		self._to_hide_pos_anim.setEasingCurve(QEasingCurve.OutCubic)
		self._opacity_effect = QGraphicsOpacityEffect()
		self._opacity_anim = QPropertyAnimation()
		self._opacity_anim.setDuration(400)
		self._opacity_anim.setEasingCurve(QEasingCurve.InCubic)
		self._opacity_anim.setPropertyName(b'opacity')
		self._opacity_anim.setStartValue(0.0)
		self._opacity_anim.setEndValue(1.0)
		self._opacity_anim.setTargetObject(self._opacity_effect)
		self._opacity_anim.finished.connect(self._on_disable_opacity)

		self.currentChanged.connect(self._on_play_anim)

	def _on_play_anim(self, index: int):
		"""
		Internal callback function that is called when an animated is played.

		:param int index: new stack index.
		"""

		current_widget = self.widget(index)
		if self._prev_index < index:
			self._to_show_pos_anim.setStartValue(QPoint(self.width(), 0))
			self._to_show_pos_anim.setTargetObject(current_widget)
			self._to_show_pos_anim.start()
		else:
			self._to_hide_pos_anim.setStartValue(QPoint(-self.width(), 0))
			self._to_hide_pos_anim.setTargetObject(current_widget)
			self._to_hide_pos_anim.start()
		current_widget.setGraphicsEffect(self._opacity_effect)
		current_widget.graphicsEffect().setEnabled(True)
		self._opacity_anim.start()
		self._prev_index = index

	def _on_disable_opacity(self):
		"""
		Internal callbakc function that is called when opacity animation finishes
		"""

		self.currentWidget().graphicsEffect().setEnabled(False)


class StackItem(QFrame):

	minimized = Signal()
	maximized = Signal()

	_BORDER_WIDTH = None

	class StackHiderWidget(QFrame):
		"""
		Stylesheet purposes
		"""

		pass

	class StackTitleFrame(QFrame, dpi.DPIScaling):
		"""
		Stack item title frame widget
		"""

		_ITEM_ICON = 'stream'
		_DELETE_ICON = 'trash'
		_COLLAPSED_ICON = 'sort_closed'
		_EXPAND_ICON = 'sort_down'
		_UP_ICON = 'arrow_up'
		_DOWN_ICON = 'arrow_down'
		_ICON_SIZE = 12
		_HIGHLIGHT_OFFSET = 40

		def __init__(
				self, title: str = '', title_editable: bool = False, icon: str | None = None, item_icon_size: int = 16,
				collapsed: bool = True, shift_arrows_enabled: bool = True, delete_button_enabled: bool = True,
				delete_icon: str | None = None, upper: bool = False, parent: StackItem | None = None):

			super().__init__(parent)

			self._collapsed = collapsed
			self._item_icon_size = item_icon_size
			self._title_editable = title_editable
			self._item_icon = icon or self._ITEM_ICON
			self._delete_icon_name = delete_icon or self._DELETE_ICON
			self._spaces_to_underscore = True
			self._horizontal_layout = None								# type: QHBoxLayout
			self._contents_layout = None								# type: QVBoxLayout

			self._extras_layout = layouts.horizontal_layout(spacing=0, margins=(0, 0, 0, 0))
			self._line_edit_layout = layouts.vertical_layout(spacing=0, margins=(0, 1, 0, 0))
			self._line_edit = lineedits.EditableLineEditOnClick(title, upper=upper)
			self._line_edit.setAttribute(Qt.WA_TransparentForMouseEvents)
			self._line_edit.setReadOnly(True if not title_editable else False)

			self._expand_toggle_button = buttons.BaseButton(parent=self)
			self._item_icon = buttons.BaseButton(parent=self)
			self._shift_down_button = buttons.BaseButton(parent=self)
			self._shift_up_button = buttons.BaseButton(parent=self)
			self._delete_button = buttons.BaseButton(parent=self)

			if not shift_arrows_enabled:
				self._shift_down_button.hide()
				self._shift_up_button.hide()

			if not delete_button_enabled:
				self._delete_button.hide()

			self.setup_ui()
			self.setup_signals()

		def setup_ui(self):
			"""
			Function that setup stack title frame UI.
			"""

			self.setObjectName('title')
			self.setContentsMargins(*dpi.margins_dpi_scale(0, 0, 0, 0))

			self._item_icon.set_icon(self._ITEM_ICON, colors=None, size=self._item_icon_size)
			self._item_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
			self._horizontal_layout = layouts.horizontal_layout(spacing=0, parent=self)
			self.setLayout(self._horizontal_layout)
			self._expand_toggle_button.setParent(self)
			self._expand_toggle_button.set_icon(self._COLLAPSED_ICON if self._collapsed else self._EXPAND_ICON)

			self.set_delete_button_icon(self._DELETE_ICON)
			self._shift_up_button.set_icon(
				self._UP_ICON, colors=None, size=self._ICON_SIZE, color_offset=self._HIGHLIGHT_OFFSET)
			self._shift_down_button.set_icon(
				self._DOWN_ICON, colors=None, size=self._ICON_SIZE, color_offset=self._HIGHLIGHT_OFFSET)
			self._expand_toggle_button.set_icon(self._EXPAND_ICON, colors=(192, 192, 192), size=self._ICON_SIZE)

			size = dpi.dpi_scale(10)
			spacer_item = QSpacerItem(size, size, QSizePolicy.Expanding, QSizePolicy.Minimum)

			self._horizontal_layout.addWidget(self._expand_toggle_button)
			self._horizontal_layout.addWidget(self._item_icon)
			self._horizontal_layout.addItem(spacer_item)

			self.setFixedHeight(self.sizeHint().height() + dpi.dpi_scale(2))
			self.setMinimumSize(self.sizeHint().width(), self.sizeHint().height() + dpi.dpi_scale(1))

			self._line_edit_layout.addWidget(self._line_edit)
			self._horizontal_layout.addLayout(self._line_edit_layout, stretch=4)
			self._horizontal_layout.addLayout(self._extras_layout)
			self._horizontal_layout.addWidget(self._shift_up_button)
			self._horizontal_layout.addWidget(self._shift_down_button)
			self._horizontal_layout.addWidget(self._delete_button)

		def setup_signals(self):
			"""
			Function that setup stack title frame signal connections.
			"""

			pass

		def set_delete_button_icon(self, icon_name: str):
			"""
			Sets the icon for the delete icon.

			:param str icon_name: name of the icon to set.
			"""

			self._delete_button.set_icon(
				icon_name, colors=None, size=self._ICON_SIZE, color_offset=self._HIGHLIGHT_OFFSET)

		def collapse(self):
			"""
			Updates icon size for the expand toggle button to use the collapse icon.
			"""

			self._expand_toggle_button.set_icon(self._COLLAPSED_ICON)

		def expand(self):
			"""
			Updates icon size for the expand toggle button to use the expand icon.
			"""

			self._expand_toggle_button.set_icon(self._EXPAND_ICON)

	def __init__(
			self, title: str, parent: QWidget, collapsed: bool = False, collapsable: bool = True,
			icon: str | None = None, start_hidden: bool = False, shift_arrows_enabled: bool = True,
			delete_button_enabled: bool = True, title_editable: bool = True, item_icon_size: int = 12,
			title_frame: StackTitleFrame | None = None, title_upper: bool = False):
		super().__init__(parent)

		if start_hidden:
			self.hide()

		self._stack_widget = parent
		self._item_icon_size = item_icon_size
		self._title = title
		self._collapsable = collapsable
		self._collapsed = collapsed
		self._color = consts.DARK_BG_COLOR
		self._contents_margins = (0, 0, 0, 0)
		self._content_spacing = 0

		self.hide()

		if StackItem._BORDER_WIDTH is None:
			theme_pref = core.theme_preference_interface()
			StackItem._BORDER_WIDTH = dpi.dpi_scale_divide(theme_pref.STACK_BORDER_WIDTH)

		self._main_layout = layouts.vertical_layout(
			spacing=0,
			margins=(StackItem._BORDER_WIDTH, StackItem._BORDER_WIDTH, StackItem._BORDER_WIDTH, StackItem._BORDER_WIDTH))
		self.setLayout(self._main_layout)

		self._title_frame = title_frame or StackItem.StackTitleFrame(
			title=title, icon=icon, title_editable=title_editable, item_icon_size=item_icon_size, collapsed=collapsed,
			shift_arrows_enabled=shift_arrows_enabled, delete_button_enabled=delete_button_enabled, upper=title_upper,
			parent=self)

		self._init()

		self.setup_ui()
		self.setup_signals()

		if not collapsable:
			self._collapsed = False

		self.collapse() if self._collapsed else self.expand()

	def setup_ui(self):
		"""
		Function that setup stack UI.
		"""

		self._build_hider_widget()

		self._main_layout.setSpacing(0)
		self._main_layout.addWidget(self._title_frame)
		self._main_layout.addWidget(self._widget_hider)

	def setup_signals(self):
		"""
		Function that setup stack title frame signal connections.
		"""

		pass

	def expand(self, emit: bool = True):
		"""
		Expands stack contents and shows all the widgets.

		:param bool emit: whether to emit expand signal.
		"""

		self._widget_hider.setHidden(False)
		self._title_frame.expand()
		if emit:
			self.maximized.emit()
		self._collapsed = False

	def collapse(self, emit: bool = True):
		"""
		Collapses stack contents amd hides all widgets.

		:param bool emit: whether to emit expand signal.
		"""

		self._widget_hider.setHidden(True)
		self._title_frame.collapse()
		if emit:
			self.minimized.emit()
		self._collapsed = True

	def _init(self):
		"""
		Internal function that initializes stack item widget.
		"""

		self._widget_hider = StackItem.StackHiderWidget(parent=self)
		self._contents_layout = layouts.vertical_layout(spacing=0, parent=self._widget_hider)
		self._widget_hider.setLayout(self._contents_layout)

	def _build_hider_widget(self):
		"""
		Intenral function that builds the widget that allows to collapse/expand the stack contents.
		"""

		self._widget_hider.setContentsMargins(0, 0, 0, 0)
		self._contents_layout.setContentsMargins(*self._contents_margins)
		self._contents_layout.setSpacing(self._content_spacing)
		self._widget_hider.setHidden(self._collapsed)
		self._widget_hider.setObjectName('stackbody')
