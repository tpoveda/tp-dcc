#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt stack widgets
"""

from Qt.QtCore import Qt, Signal, QPoint, QEasingCurve, QPropertyAnimation, QParallelAnimationGroup
from Qt.QtWidgets import QFrame, QStackedWidget

from tp.core.managers import resources
from tp.common.qt import consts, qtutils, base, dpi, mixin
from tp.common.qt.widgets import layouts, buttons, lineedits


def sliding_opacity_stacked_widget(parent=None):
    """
    Creates a new QStackWidget that uses opacity animation to switch between stack widgets.

    :param QWidget parent: parent widget.
    :return: stack widget.
    :rtype: SlidingOpacityStackedWidget
    """

    new_stack_widget = SlidingOpacityStackedWidget(parent=parent)
    return new_stack_widget


class SlidingStackedWidget(QStackedWidget, object):
    """
    QStackedWidget width sliding functionality
    """

    animFinished = Signal(int)

    def __init__(self, parent=None, **kwargs):
        super(SlidingStackedWidget, self).__init__(parent)

        # This variable holds the current widget without taking into account if the animation has finished or not
        self._speed = kwargs.pop('speed', 500)
        self._current_widget = None
        self._animation_type = kwargs.pop('animation_type', QEasingCurve.OutCubic)
        self._wrap = kwargs.pop('wrap', True)
        self._vertical = kwargs.pop('vertical', False)
        self._active_state = False
        self._blocked_page_list = list()
        self._now = 0
        self._next = 1

    @property
    def current_widget(self):
        return self._current_widget

    def set_speed(self, speed):
        """
        Sets the animation speed of the sliding
        :param speed: int
        """

        self._speed = speed

    def set_animation(self, animation_type):
        """
        Set the curve animation type of the sliding
        :param animation_type: QEasingCurve
        """

        self._animation_type = animation_type

    def set_vertical_mode(self, vertical=True):
        """
        Sets whether the sliding animation is done vertically or horizontally
        :param vertical: bool
        """

        self._vertical = vertical

    def set_wrap(self, wrap):
        """
        Sets whether the page index is restarted when we arrive the last one or not
        :param wrap: bool
        """

        self._wrap = wrap

    def slide_in_next(self):
        """
        Slides into the next widget
        """

        now = self.currentIndex()
        if self._wrap or now < self.count() - 1:
            self.slide_in_index(now + 1)

    def slide_in_prev(self):
        """
        Slides into the previous widget
        """

        now = self.currentIndex()
        if self._wrap or now > 0:
            self.slide_in_index(now - 1)

    def slide_in_index(self, next, force=False):
        """
        Slides to the given widget index
        :param next: int, index of the widget to slide
        """

        now = self.currentIndex()
        if (self._active_state or next == now) and not force:
            return

        self._active_state = True
        width, height = self.frameRect().width(), self.frameRect().height()
        next %= self.count()
        if next > now:
            if self._vertical:
                offset_x, offset_y = 0, height
            else:
                offset_x, offset_y = width, 0
        else:
            if self._vertical:
                offset_x, offset_y = 0, -height
            else:
                offset_x, offset_y = -width, 0
        self.widget(next).setGeometry(0, 0, width, height)
        pnow, pnext = self.widget(now).pos(), self.widget(next).pos()
        self._point_now = pnow

        self.widget(next).move(pnext.x() + offset_x, pnext.y() + offset_y)
        self.widget(next).show()
        self.widget(next).raise_()
        self._current_widget = self.widget(next)

        anim_now = QPropertyAnimation(self.widget(now), b'pos')
        anim_now.setDuration(self._speed)
        anim_now.setStartValue(pnow)
        anim_now.setEndValue(QPoint(pnow.x() - offset_x, pnow.y() - offset_y))
        anim_now.setEasingCurve(self._animation_type)

        anim_next = QPropertyAnimation(self.widget(next), b'pos')
        anim_next.setDuration(self._speed)
        anim_next.setStartValue(QPoint(offset_x + pnext.x(), offset_y + pnext.y()))
        anim_next.setEndValue(pnext)
        anim_next.setEasingCurve(self._animation_type)

        self._anim_group = QParallelAnimationGroup()
        self._anim_group.addAnimation(anim_now)
        self._anim_group.addAnimation(anim_next)
        self._anim_group.finished.connect(self._animation_done_slot)
        self._anim_group.start()

        self._next = next
        self._now = now

    def _animation_done_slot(self):
        self.setCurrentIndex(self._next)
        self.widget(self._now).hide()
        self.widget(self._now).move(self._point_now)
        try:
            self.widget(self._now).update()
        except Exception:
            pass
        self._active_state = False
        self.animFinished.emit(self._next)


@mixin.stacked_opacity_animation_mixin
class SlidingOpacityStackedWidget(QStackedWidget, object):
    """
    Custom stack widget that activates opacity animation when current stack index changes
    """

    def __init__(self, parent=None):
        super(SlidingOpacityStackedWidget, self).__init__(parent)


class StackItem(QFrame, object):

    updateRequested = Signal()

    def __init__(self, title, parent, icon=None, title_editable=True, icon_size=12,
                 title_frame=None, show_item_icon=True):
        super(StackItem, self).__init__(parent)

        self._stack_widget = parent
        self._icon_size = icon_size
        self._title = title
        self._title_editable = title_editable
        self._icon = icon
        self._color = consts.DARK_BG_COLOR
        self._contents_margins = (0, 0, 0, 0)
        self._contents_spacing = 0
        self._title_frame = title_frame
        self._show_item_icon = show_item_icon

        self.ui()
        self.setup_signals()

    @property
    def contents_layout(self):
        return self._contents_layout

    def ui(self):
        # theme = tpDcc.ToolsMgr().get_tool_theme('tpDcc-tools-hub')
        # border_width = qtutils.dpi_scale_divide(theme.STACK_BORDER_WIDTH)
        margin = qtutils.dpi_scale_divide(1)
        self.main_layout = layouts.VerticalLayout(margins=(margin, margin, margin, margin), spacing=0)
        # self.main_layout = layouts.VerticalLayout(margins=(0, 0, 0, 0), spacing=0)

        self.setLayout(self.main_layout)

        if not self._title_frame:
            self._title_frame = StackTitleFrame(
                title=self._title, icon=self._icon, title_editable=self._title_editable, item_icon_size=self._icon_size)
        if not self._show_item_icon:
            self._title_frame.item_icon_button.hide()

        self._contents_widget = QFrame(parent=self)
        self._contents_layout = layouts.VerticalLayout(spacing=self._contents_spacing, margins=self._contents_margins)
        self._contents_widget.setLayout(self._contents_layout)

        self.main_layout.addWidget(self._title_frame)
        self.main_layout.addWidget(self._contents_widget)

    def setup_signals(self):
        self._title_frame.updateRequested.connect(self.updateRequested.emit)

    def title_text_widget(self):
        """
        Returns title text widget
        :return: QLineEdit
        """

        return self._title_frame.line_edit

    def get_title(self):
        """
        Returns title text
        :return: str
        """

        return self._title_frame.line_edit.text()

    def set_title(self, text):
        """
        Function that sets title text
        :param text: str
        """

        self._title_frame.line_edit.setText(text)

    def add_widget(self, widget):
        """
        Adds a new widget to the contents layout
        :param widget: QWidget
        """

        self._contents_layout.addWidget(widget)

    def add_layout(self, layout):
        """
        Adds a new layout to the contents layout
        :param layout: QLayout
        """

        self._contents_layout.addLayout(layout)

    def set_title_text_mouse_transparent(self, flag):
        """
        Sets whether or not title text mouse is transparent
        :param flag: bool
        """

        self._title_frame.line_edit.setAttribute(Qt.WA_TransparentForMouseEvents, flag)

    def set_item_icon_color(self, color):
        """
        Sets the color of the item in title
        :param color: tuple(int, int, int), RGB color in 0-255 range
        """

        self._title_frame.set_item_icon_color(color)

    def set_item_icon(self, icon):
        """
        Sets the icon of the item in title
        :param icon: QIcon
        """

        self.title_frame.set_item_icon(icon)

    def update_size(self):
        """
        Updates the size of the widget, to fit to new size depending on its contents
        """

        self.updateRequested.emit()


class StackTitleFrame(QFrame, dpi.DPIScaling):

    updateRequested = Signal()

    def __init__(self, title='', title_editable=False, icon=None, item_icon_size=16, parent=None):
        super(StackTitleFrame, self).__init__(parent)

        self._title = title
        self._item_icon = icon or 'tpdcc'
        self._title_editable = title_editable
        self._spaces_to_underscore = False
        self._item_icon_size = item_icon_size

        self.setObjectName('title')

        self.ui()
        self.setup_signals()

        self.setFixedHeight(self.sizeHint().height())
        self.setMinimumSize(self.sizeHint().width(), self.sizeHint().height() + 1)

    @property
    def horizontal_layout(self):
        return self._horizontal_layout

    @property
    def item_icon(self):
        return self._item_icon

    @property
    def item_icon_button(self):
        return self._item_icon_btn

    @property
    def line_edit(self):
        return self._line_edit

    def mouseDoubleClickEvent(self, event):
        if self._title_editable:
            self._line_edit.editEvent(event)

    def ui(self):
        item_icon = resources.icon(self._item_icon)
        if item_icon.isNull():
            item_icon = resources.icon('tpdcc')
        delete_icon = resources.icon('delete')

        self.setContentsMargins(*qtutils.margins_dpi_scale(0, 0, 0, 0))
        self._extras_layout = layouts.HorizontalLayout(margins=(0, 0, 0, 0), spacing=0)
        self._horizontal_layout = layouts.HorizontalLayout(spacing=0)
        self.setLayout(self._horizontal_layout)

        self._line_edit = lineedit.ClickLineEdit(self._title)
        self._line_edit.setObjectName('lineEdit')
        self._line_edit.setFocusPolicy(Qt.NoFocus)
        self._line_edit.setVisible(False)
        self._line_edit.setAttribute(Qt.WA_TransparentForMouseEvents)
        if not self._title_editable:
            self._line_edit.setReadOnly(True)

        self._item_icon_btn = buttons.BaseMenuButton(parent=self)

        self._item_icon_btn.set_icon(icon=item_icon, size=self._item_icon_size)
        self._item_icon_btn.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._horizontal_layout.addWidget(self._item_icon_btn)
        self._horizontal_layout.addStretch()
        self._horizontal_layout.addWidget(self._line_edit)
        self._horizontal_layout.addLayout(self._extras_layout)
        self._horizontal_layout.setStretchFactor(self._line_edit, 4)

    def setup_signals(self):
        self._line_edit.textChanged.connect(self._on_title_validate)
        self._line_edit.selectionChanged.connect(self._on_select_check)

    def set_item_icon_color(self, color):
        self._item_icon_btn.set_icon_color(color)

    def set_item_icon(self, icon):
        self._item_icon_btn.set_icon(icon)

    def _on_title_validate(self):
        """
        Internal callback function that is called when line edit text changes
        Removes invalid characters and replaces spaces with underscores
        """

        if self._spaces_to_underscore:
            line_edit = self._line_edit
            text = self._line_edit.text()
            pos = line_edit.cursorPosition()
            text = text.replace(' ', '_')
            line_edit.blockSignals(True)
            try:
                line_edit.setText(text)
            finally:
                line_edit.blockSignals(False)
            line_edit.setCursorPosition(pos)

    def _on_select_check(self):
        """
        Internal callback function that is called when user deselects line edit
        Stops any selection from happening if title is not editable
        """

        if not self._title_editable:
            self._line_edit.deselect()
