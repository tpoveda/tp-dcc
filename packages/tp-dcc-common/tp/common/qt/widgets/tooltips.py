#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for icons
"""

from Qt.QtCore import Qt, Signal, QObject, QSize, QTimer, QPoint
from Qt.QtWidgets import QWidget, QStyle
from Qt.QtGui import QFont, QCursor

from tp.core import dcc
from tp.common.resources import icon
from tp.common.qt.widgets import layouts, dialog, parsers, labels

EXPANDED_TOOLTIP_INJECTOR_ATTRIBUTE = '_expandedTooltips_'


def install_tooltips(widget, tooltip_dict):
    """
    Intsalls the expanded tooltip onto a widget
    :param QWidget widget:
    :param dict tooltip_dict:
    :return:
    """

    tooltip = tooltip_dict['tooltip']
    widget.setToolTip(tooltip)
    widget._expandedTooltips_ = ExpandedTooltips(tooltip_dict)


def has_expanded_tooltips(widget):
    """
    Returns whether given widget has the injected _expandedToolTips_ object present in the widget
    :param widget: QWidget
    :return: bool
    """

    return hasattr(widget, EXPANDED_TOOLTIP_INJECTOR_ATTRIBUTE) and widget._expandedTooltips_.text != ''


def copy_expanded_tooltips(source, target):
    """
    Copy the _expandedTooltips_ attribute from source widget into target one
    :param QWidget source:
    :param QWidget target:
    :return:
    """

    target._expandedTooltips_ = source._expandedTooltips_


class ExpandedTooltipPopup(dialog.BaseDialog):

    popupKey = Qt.Key_Control

    ETT_ICON_COLOR = (82, 133, 166)
    ETT_LINK_COLOR = (255, 255, 255)
    ETT_THEME_COLOR = (82, 133, 166)

    def __init__(self, widget, width=450, height=50, icon_size=40, parent=None, show_on_initialize=False,
                 stylesheet='', popup_release=Qt.Key_Control, show_at_cursor=True):

        self._tooltip_icon = None
        self._widget = widget
        self._icon_color = self.ETT_ICON_COLOR
        self._theme_color = self.ETT_THEME_COLOR
        self._link_color = self.ETT_LINK_COLOR
        self._popup_key = popup_release
        self._icon_size = icon_size
        self._font = QFont('sans')
        self._title_font = QFont('sans')

        super(ExpandedTooltipPopup, self).__init__(
            width=width, height=height, show_on_initialize=show_on_initialize, parent=parent
        )

        if stylesheet != '':
            self.setStyleSheet(stylesheet)

        if show_at_cursor:
            self.move(QCursor.pos())

        self.setStyle(self.style())

    def keyReleaseEvent(self, event):
        if event.key() == self._popup_key:
            self.close()

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout(margins=(6, 4, 6, 8))
        return main_layout

    def ui(self):
        super(ExpandedTooltipPopup, self).ui()

        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self._title_layout = layouts.HorizontalLayout(spacing=2, margins=(1, 1, 1, 1))
        self._title_label = label.BaseLabel(parent=self)
        self._title_label.setObjectName('title')
        self._title_layout.addWidget(self._title_label)
        self._title_layout.setStretch(1, 3)
        self._title_layout.addWidget(self._title_label)
        self._widgets_layout = layouts.VerticalLayout()
        self.main_layout.addLayout(self._title_layout)
        self.main_layout.addLayout(self._widgets_layout)

        self.set_icon(self._widget._expandedTooltips_.icon)
        self.set_title(self._widget._expandedTooltips_.title)
        self.set_text(self._widget_expandedTooltips_.text)

    def center(self, to_cursor=False):
        pass

    def set_text(self, text, apply_style=True):
        if apply_style:
            text = self._apply_style(text)

        parser = parsers.WidgetsFromTextParser(text)

        self.add_widgets(parser.widgets())

    def add_widgets(self, widgets):
        for w in widgets:
            self._widgets_layout.addWidget(w)

    def clear(self):
        for i in reversed(range(self._widgets_layout.count())):
            self._widgets_layout.itemAt(i).widget().setParent(None)

    def set_icon(self, new_icon):

        from tp.common.qt.widgets import buttons

        new_icon = icon.colorize_icon(icon=new_icon, size=self._icon_size, color=self._icon_color)
        icon_widget = buttons.BaseToolButton(parent=self)
        icon_widget.setIconSize(QSize(self._icon_size, self._icon_size))
        icon_widget.setIcon(new_icon)
        self._tooltip_icon = icon_widget

    def set_title(self, title, apply_style=True):
        if apply_style:
            title = self._apply_style(title)
        self._title_label.setText(title)

    def _apply_style(self, text):
        text = text.replace("class=\"link\"", "style=\"color: rgb{}\" ".format(self._link_color))
        text = text.replace("class=\"highlight\"",
                            "style=\"color: rgb{}; font-weight: bold\" ".format(self._theme_color))
        text = text.replace("<a href=", "<a style=\"color: rgb{}; font-weight: bold\" href=".format(self._theme_color))
        return text


class ExpandedTooltips(QObject):
    """
    Acts as a Data storage for the Expanded tooltips.
    """

    icon = ""
    text = ""
    title = ""

    def __init__(self, dict):
        """
        Distribute the data into the strings

        :param dict:
        """
        try:
            self.title = dict['title']
        except KeyError:
            pass

        try:
            self.text = dict['expanded']
        except KeyError:
            pass

        try:
            self.icon = dict['icon']
        except KeyError:
            pass


class ToolTipWidget(QWidget, object):

    hidden = Signal()

    def __init__(self, parent=None):
        super(ToolTipWidget, self).__init__(parent)

        self._layout = None
        self._content = None
        self._content_parent = None
        self._hide_timer = QTimer(self)

        self._init()

    def enterEvent(self, event):
        if self.hide_delay() > 0:
            self._hide_timer.stop()
        else:
            self.hide()

    def hideEvent(self, event):
        self._remove_widget()
        QTimer.singleShot(0, self.hidden.emit)

    def leaveEvent(self, event):
        self.hide()

    # def paintEvent(self, event):
    #     painter = QStylePainter(self)
    #     painter.setClipRegion(event.region())
    #     option = QStyleOptionFrame()
    #     option.init(self)
    #     painter.drawPrimitive(QStyle.PE_PanelTipLabel, option)
    #     painter.end()
    #
    #     super(ToolTipWidget, self).paintEvent(event)

    def show_at(self, pos, content, parent_window=None):
        """
        Shows tooltip in given position and with given widget
        :param pos: QPoint
        :param content: QWidget
        :param parent_window: QWindow
        """

        parent_window = parent_window or dcc.get_main_window().windowHandle()

        self._add_widget(content)
        self._show(pos, parent_window)

    def show_below(self, rect, content, parent_window=None):
        """
        Shows tooltip below given rect and with given content
        :param rect: QRect
        :param content: QWidget
        :param parent_window: QWindow
        """

        parent_window = parent_window or dcc.get_main_window().windowHandle()

        self._add_widget(content)
        margin_size = QSize(
            2 * content.style().pixelMetric(QStyle.PM_DefaultTopLevelMargin),
            2 * content.style().pixelMetric(QStyle.PM_DefaultTopLevelMargin)
        )
        content.setMaximumSize(parent_window.screen().geometry().size() - margin_size)
        self._show(self._center_below(rect, parent_window.screen()), parent_window)

    def hide_delay(self):
        """
        Returns timer hide interval
        :return: float
        """

        return self._hide_timer.interval()

    def set_hide_delay(self, hide_delay_interval):
        """
        Sets the delay timer value
        :param hide_delay_interval: float
        """

        self._hide_timer.setInterval(hide_delay_interval)

    def hide_later(self):
        """
        Hides tooltip if timer is over
        """

        if not self.isVisible():
            return

        if self.hide_delay() > 0:
            self._hide_timer.start()
        else:
            self.hide()

    def _init(self):
        """
        Internal function that initializes tooltip widget
        """

        self.setMouseTracking(True)
        self._layout = layouts.VerticalLayout(parent=self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(500)
        self._hide_timer.timeout.connect(self._on_timer_timeout)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)

    def _add_widget(self, widget):
        """
        Internal function that adds replaces current contained wiget with the given one
        :param widget: QWidget
        """

        self._remove_widget()
        self._content = widget
        self._store_parent()
        self._layout.addWidget(self._content)
        widget.destroyed.connect(widget.hide)

    def _remove_widget(self):
        """
        Internal function that removes current contained widget from the tooltip
        """

        self._layout.removeWidget(self._content)
        self._restore_parent()

    def _show(self, pos, parent_window):

        if not pos or pos.isNull():
            return

        offset_pos = QPoint(pos.x() - 5, pos.y() - 5)

        self.move(offset_pos)
        self.createWinId()
        self.windowHandle().setProperty('ENABLE_BLUR_BEHIND_HINT', True)
        self.windowHandle().setTransientParent(parent_window)

        self.show()

    def _store_parent(self):
        """
        Internal function that stores parent of current contained widget
        """

        if not self._content:
            return

        self._content_parent = self._content.parent()

    def _restore_parent(self):
        """
        Internal function that reparent current contained widget to current tooltip parent widget
        """

        if not self._content or not self._content_parent:
            return

        self._content.setParent(self._content_parent)

    def _center_below(self, rect, screen):
        """
        Internal function that returns a position for the tooltip ensuring that:
            1) The content is fully visible
            2) The content is not drawn inside rect
        :param rect: QRect
        :param screen: QScreen
        :return: QPoint
        """

        size = self.sizeHint()
        margin = self.style().pixelMetric(QStyle.PM_ToolTipLabelFrameWidth)
        screen_geometry = screen.geometry()

        has_room_to_left = (rect.left() - size.width() - margin >= screen_geometry.left())
        has_room_to_right = (rect.right() + size.width() + margin <= screen_geometry.right())
        has_room_above = (rect.top() - size.height() - margin >= screen_geometry.top())
        has_room_below = (rect.bottom() + size.height() + margin <= screen_geometry.bottom())
        if not has_room_above and not has_room_below and not has_room_to_left and not has_room_to_right:
            return QPoint()

        x = 0
        y = 0
        if has_room_below or has_room_above:
            x = max(screen_geometry.left(), rect.center().x() - size.width() / 2)
            if x + size.width() >= screen_geometry.right():
                x = screen_geometry.right() - size.width() + 1
            assert x >= 0
            if has_room_below:
                y = rect.bottom() + margin
            else:
                y = rect.top() - size.height() - margin + 1
        else:
            assert has_room_to_left or has_room_to_right
            if has_room_to_right:
                x = rect.right() + margin
            else:
                x = rect.left() - size.width() - margin + 1

            # Put tooltip at the bottom of the screen. The x-coordinate has already been adjusted,
            # so no overlapping with rect occurs
            y = screen_geometry.bottom() - size.height() + 1

        return QPoint(x, y)

    def _on_timer_timeout(self):
        self.hide()
