#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom QStackedWidget widgets.
"""

from __future__ import annotations

from typing import Tuple

from Qt.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve
from Qt.QtWidgets import (
    QSizePolicy, QWidget, QFrame, QStackedWidget, QGraphicsOpacityEffect, QVBoxLayout, QHBoxLayout, QSpacerItem
)
from Qt.QtGui import QColor, QMouseEvent

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
    toggleExpandRequested = Signal(bool)
    shiftUpPressed = Signal()
    shiftDownPressed = Signal()
    updateRequested = Signal()
    deletePressed = Signal()

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

        minimized = Signal()
        maximized = Signal()
        toggleExpandRequested = Signal()
        shiftUpPressed = Signal()
        shiftDownPressed = Signal()
        updateRequested = Signal()
        deletePressed = Signal()

        _ITEM_ICON = 'stream'
        _DELETE_ICON = 'multiply'
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

        @property
        def line_edit(self) -> lineedits.EditableLineEditOnClick:
            return self._line_edit

        @property
        def horizontal_layout(self) -> QHBoxLayout:
            return self._horizontal_layout

        @property
        def extras_layout(self) -> QHBoxLayout:
            return self._extras_layout

        @property
        def expand_toggle_button(self) -> buttons.BaseButton:
            return self._expand_toggle_button

        @property
        def item_icon(self) -> buttons.BaseButton:
            return self._item_icon

        @property
        def delete_button(self) -> buttons.BaseButton:
            return self._delete_button

        def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
            if self._title_editable:
                self._line_edit.edit_event(event)

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

            self._line_edit.textChanged.connect(self._on_line_edit_text_changed)
            self._line_edit.selectionChanged.connect(self._on_line_edit_selection_changed)
            self._shift_up_button.leftClicked.connect(self._on_shift_up_button_left_clicked)
            self._shift_down_button.leftClicked.connect(self._on_shift_down_button_left_clicked)
            self._delete_button.leftClicked.connect(self._on_delete_button_left_clicked)
            self._expand_toggle_button.leftClicked.connect(self._on_expand_toggle_button_left_clicked)

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

        def set_item_icon_color(self, color: QColor | Tuple[int, int, int]):
            """
            Sets item icon color.

            :param QColor or Tuple[int, int, int] color: item icon color.
            """

            self._item_icon.set_icon_color(color)

        def set_item_icon(self, name: str):
            """
            Sets item icon.

            :param str name: name of the icon to set.
            """

            self._item_icon.set_icon(name)

        def _on_line_edit_text_changed(self):
            """
            Internal callback function that is called each time, line edit text changes.
            Remove underscores from line edit if necessary.
            """

            if not self._spaces_to_underscore:
                return

            text = self._line_edit.text()
            pos = self._line_edit.cursorPosition()
            text = text.replace(' ', '_')
            self._line_edit.blockSignals(True)
            self._line_edit.setText(text)
            self._line_edit.blockSignals(False)
            self._line_edit.setCursorPosition(pos)

        def _on_line_edit_selection_changed(self):
            """
            Internal callback function that is called each time, line edit selection changes.
            Forces line edit text deselection if title is not editable.
            """

            if not self._title_editable:
                self._line_edit.deselect()

        def _on_shift_up_button_left_clicked(self):
            """
            Internal callback function that is called when Shift Up button is left-clicked by the user.
            Emits shiftUpPressed signal.
            """

            self.shiftUpPressed.emit()

        def _on_shift_down_button_left_clicked(self):
            """
            Internal callback function that is called when Shift Down button is left-clicked by the user.
            Emits shiftDownPressed signal.
            """

            self.shiftDownPressed.emit()

        def _on_delete_button_left_clicked(self):
            """
            Internal callback function that is called when Delete button is left-clicked by the user.
            Emits deletePressed signal.
            """

            self.deletePressed.emit()

        def _on_expand_toggle_button_left_clicked(self):
            """
            Internal callback function that is called when Expand Toggle button is left-clicked by the user.
            Emits toggleExpandRequested signal.
            """

            self.toggleExpandRequested.emit()

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

    @property
    def contents_layout(self) -> QVBoxLayout:
        return self._contents_layout

    @property
    def title_frame(self) -> StackItem.StackTitleFrame:
        return self._title_frame

    @property
    def hider_widget(self) -> StackItem.StackHiderWidget:
        return self._widget_hider

    @property
    def collapsed(self) -> bool:
        return self._collapsed

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

        self._title_frame.maximized.connect(self.maximized.emit)
        self._title_frame.minimized.connect(self.minimized.emit)
        self._title_frame.shiftUpPressed.connect(self.shiftUpPressed.emit)
        self._title_frame.shiftDownPressed.connect(self.shiftDownPressed.emit)
        self._title_frame.updateRequested.connect(self.updateRequested.emit)
        self._title_frame.deletePressed.connect(self.deletePressed.emit)
        self._title_frame.toggleExpandRequested.connect(self._on_title_frame_toggle_expand_requested)

    def title(self) -> str:
        """
        Returns title text.

        :return: title text.
        :rtype: str
        """

        return self._title_frame.line_edit.text()

    def set_title(self, title: str):
        """
        Sets title text.

        :param str title: title text.
        """

        self._title_frame.line_edit.setText(title)

    def set_item_icon(self, name: str):
        """
        Sets the item icon.

        :param str name: name of the icon to set.
        """

        self._title_frame.set_item_Icon(name)

    def set_item_icon_color(self, color: Tuple[int, int, int]):
        """
        Sets item icon color.

        :param Tuple[int, int, int] color: color of the icon to set.
        """

        self._title_frame.set_item_icon_color(color)

    def set_title_text_mouse_transparent(self, flag: bool):
        """
        Sets whether title text is ignored by mouse events.

        :param bool flag: True to ignore mouse events; False otherwise.
        """

        self._title_frame.line_edit.setAttribute(Qt.WA_TransparentForMouseEvents, flag)

    def show_expand_indicator(self, flag: bool):
        """
        Sets whether expand/toggle button is visible.

        :param bool flag: True to show expand/toggle button; False to hide it.
        """

        self._title_frame.expand_toggle_button.setVisible(flag)

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

    def toggle_contents(self, emit: bool = True) -> bool | None:
        """
        Shows and hides the hide widget that contains the layout which holds the custom contents specified by the user.

        :param bool emit: whether to emit expand or collapsed signals.
        :return: whether widget is collapsed after toggle contents. None if widget is not collapsable.
        :rtype: bool or None
        """

        if not self._collapsable:
            return None

        self.toggleExpandRequested.emit(not self._collapsed)

        if self._collapsed:
            self.expand(emit=emit)
            self._update_size()
            return not self._collapsed

        self.collapse(emit=emit)
        self._update_size()

        return self._collapsed

    def title_text_widget(self) -> lineedits.EditableLineEditOnClick:
        """
        Returns title text widget instance.

        :return: title text widget instance.
        :rtype: lineedits.EditableLineEditOnClick
        """

        return self._title_frame.line_edit

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

    def _update_size(self):
        """
        Internal function that updates the size of the widget.
        """

        self.updateRequested.emit()

    def _on_title_frame_toggle_expand_requested(self):
        """
        Internal callback function that is called each time title frame toggle expand requested signal is emitted.
        """

        self.toggle_contents()
