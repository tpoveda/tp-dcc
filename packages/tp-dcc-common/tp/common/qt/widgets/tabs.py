#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt tab widgets
"""

from Qt.QtCore import Qt, Signal, Property, QPoint, QPointF, QRect, QSize
from Qt.QtWidgets import QWidget, QTabWidget, QMainWindow
from Qt.QtGui import QColor, QPalette

from tp.core import dcc
from tp.common.resources import theme
from tp.common.qt import qtutils, base
from tp.common.qt.widgets import layouts, window, tabbars, buttons, group, dividers, stack


class BaseTabWidget(QTabWidget, object):
    """
    Base class for tab widgets
    """

    deletedTab = Signal(object)

    def __init__(self, parent=None):
        super(BaseTabWidget, self).__init__(parent=parent)

        self._set_custom_tab_bar()
        self.tabCloseRequested.connect(self.close_tab)

        self._show_close_message = False
        self._show_text = ''
        self._show_title = ''
        self._show_fn = None
        self._show_can_cancel = False

    def removeTab(self, index):
        """
        Function that is called when a tab is removed
        :param index: int, index of the removed tab
        """

        if self._show_close_message:
            can_close = qtutils.get_permission(
                message='Save before closing tab?',
                cancel=self._show_can_cancel, title='Closing tab', parent=self)
            if can_close is None:
                return
            elif can_close:
                if self._show_fn:
                    self._show_fn(index, self.widget(index))

        super(BaseTabWidget, self).removeTab(index)
        self.deletedTab.emit(index)

    def close_tab(self, index):
        """
        Function that is called before
        :param index:
        :return:
        """

        return self.removeTab(index)

    def set_close_message(self, message_text, message_title, cancel=False, accept_fn_call=None):
        self._show_close_message = True
        self._show_text = message_text
        self._show_title = message_title
        self._show_can_cancel = cancel
        self._show_fn = accept_fn_call

    def get_unique_tab_name(self, name, curr_index=0):
        """
        Returns a unique tab name for the current tab widget
        :param name: str, base name to get a unique name
        :param curr_index: int, starting index to start searching for unique names
        :return:
        """

        curr_index = curr_index
        new_name = name
        index = 0
        if curr_index > 0:
            new_name = name + '_' + str(curr_index)
        for i in range(self.tabBar().count()):
            curr_tab_name = self.tabBar().tabText(i)
            if curr_tab_name == new_name:
                index = index + 1
        if index > 0:
            return self.get_unique_tab_name(name, curr_index=curr_index + index)
        return new_name

    def update_tab_bar_signals(self):
        """
        Override functionality if necessary
        Updates teh tab bar signals
        """

        pass

    def _set_custom_tab_bar(self):
        """
        Sets a custom tab bar with editable functionality for the widget
        """

        pass


class BaseEditableTabWidget(BaseTabWidget, object):
    """
    Tab widget with basic editable functionality
    """

    def __init__(self, parent=None):
        super(BaseEditableTabWidget, self).__init__(parent=parent)

        self.setMovable(True)
        self.setTabsClosable(True)
        self._edit_mode = True

    def set_edit_mode(self, value):
        if self._edit_mode != value:
            self._edit_mode = value
            self.setMovable(value)
            self.setTabsClosable(value)

    def get_edit_mode(self):
        return self._edit_mode

    edit_mode = property(get_edit_mode, set_edit_mode)

    def mousePressEvent(self, event):
        pos = event.pos()
        rect = self._add_tab_btn_rect()
        if rect.contains(pos):
            pass
        # super(BaseEditableTabWidget, self).mousePressEvent(event)

    def _add_tab_btn_rect(self):
        """
        Returns the visual rect of the current selected tab
        :return: QRect
        """

        return self.tabBar().add_tab_btn.rect()

    def _set_custom_tab_bar(self):
        """
        Sets a custom tab bar with editable functionality for the widget
        """

        self.setTabBar(tabbars.EditableTabBar(self))
        self.update_tab_bar_signals()


class TearOffTabWidget(BaseTabWidget, object):
    """
    Tab widget with basic tear off functionality
    """

    class TabWidgetStorage(object):
        def __init__(self, index, widget, title, visible=True):
            self.index = index
            self.widget = widget
            self.title = title
            self.visible = visible
            self.detached = None

        def set_detached(self, detached):
            self.detached = detached

        def __repr__(self):
            return 'index %d, widget %r, title %s, visible %r, detached %r' % (
                self.index, self.widget, self.title, self.visible, self.detached)

    tabAdded = Signal()
    tabDetached = Signal(int, QPoint)
    tabBarRenamed = Signal(str, str)
    requestRemove = Signal(int)
    tabChanged = Signal(int)
    undoOpen = Signal()
    undoClose = Signal()

    def __init__(self, parent=None):
        super(TearOffTabWidget, self).__init__(parent=parent)

        self._previous_tab_id = 0
        self.tab_idx = dict()

        self.setMovable(False)
        self.setTabsClosable(True)
        self.setMouseTracking(True)
        self.setObjectName('BaseTabWidget')

        self._set_palette_color()

        # don't draw a frame around the tab contents
        self.setStyleSheet('QTabWidget:tab:disabled{width:0;height:0;margin:0;padding:0;border:none}')
        self.setDocumentMode(True)

    def update_tab_bar_signals(self):
        """
        Updates the signals attached to the tab bar
        """

        tab_bar = self.tabBar()
        if tab_bar is None:
            return
        self.tabBar().tabDetached.connect(self.tabDetached.emit)
        self.tabBar().tabDetached.connect(self._on_detach_tab)
        self.tabBar().tabMoved.connect(self._on_move_tab)
        self.currentChanged.connect(self._on_tab_changed_tab)

    def addTab(self, *args, **kwargs):
        added_tab_index = super(TearOffTabWidget, self).addTab(*args, **kwargs)
        self.tab_inserted(added_tab_index)

    def removeTab(self, index):
        super(TearOffTabWidget, self).removeTab(index)
        self.tab_idx.pop(index)

    def tab_inserted(self, index):
        w = self.widget(index)
        for i in self.tab_idx.values():
            if i.widget == w:
                return
        self.tab_idx[index] = self.TabWidgetStorage(index, self.widget(index), self.tabText(index))

    def set_widget_visible(self, widget, visible):
        w = self._find_first_window(widget)
        for i in self.tab_idx.values():
            if i.widget == w:
                if visible:
                    if not i.visible:
                        new_index = -1
                        for j in self.tab_idx.values():
                            if j.visible and j.index > i.index:
                                c_idx = self._tab_widget_index(j.widget)
                                if c_idx < i.index and c_idx != -1:
                                    new_index = c_idx
                                else:
                                    new_index = i.index
                                break
                        self.insertTab(new_index, i.widget, i.title)
                else:
                    i.visible = False
                    index = self._tab_widget_index(i.widget)
                    self.removeTab(index)

    def add_panel(self, widget, label):

        # TODO: We should not storing the detach config here
        # sg_group = window.DetachedWindow.SettingGroup(label)
        # with sg_group as settings:
        #     detached = settings.value('detached', False)
        detached = False

        index = len(self.tab_idx)
        self.tab_idx[index] = self.TabWidgetStorage(index, widget, label)
        if not detached:
            index = self.addTab(widget, label)
            for i in self.tab_idx.values():
                if i.widget == widget:
                    i.set_detached(None)
        else:
            detach_window = window.DetachedWindow(label, self.parentWidget())
            detach_window.tab_idx = index
            detach_window.setAttribute(Qt.WA_DeleteOnClose, True)
            self.tab_idx[index].set_detached(detach_window)
            detach_window.windowClosed.connect(self._on_attach_tab)

            panel = self._get_widget(widget)
            panel.widgetVisible.disconnect(self.set_widget_visible)
            panel.widgetVisible.connect(detach_window.set_widget_visible)
            widget.setParent(detach_window)

            detach_window.set_widget(widget)
            detach_window.destroyed.connect(detach_window.deleteLater)
            # detach_window.restoreGeometry(settings.value('geometry', ''))
            detach_window.show()

    def clear(self):
        """
        Delete all the tabs added to this tab widget
        """

        all_tabs = [self.widget(i) for i in range(self.count())]
        self.blockSignals(True)
        for tab in all_tabs:
            tab.deleteLater()
        super(TearOffTabWidget, self).clear()
        self.blockSignals(False)

    def dragEnterEvent(self, event):
        """
        Override drag enter behaviour
        """

        event.accept()
        super(TearOffTabWidget, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """
        Override drag move behaviour
        """

        event.accept()
        super(TearOffTabWidget, self).dragMoveEvent(event)
    # endregion

    # region Private Functions
    def _set_palette_color(self):
        """
        Sets the initial for the different elements of the tab widget
        Override to create custom color styles for this widget
        """

        palette = self.palette()
        self.border_color = QColor(Qt.black)
        self.button_color = palette.color(QPalette.Button)
        self.fill_color = palette.color(QPalette.Window)
        self.highlight_color = palette.color(QPalette.Highlight)

    def _set_custom_tab_bar(self):
        """
        Sets a custom tab bar with tear off functionality for the widget
        Override to add a custom tab bar for this widget
        """

        tab_bar = tabbars.TearOffTabBar()
        self.setTabBar(tab_bar)
        self.update_tab_bar_signals()

    def _find_first_window(self, w):
        widget = w
        while True:
            parent = widget.parent()
            if not parent:
                break
            widget = parent
            if isinstance(widget, QMainWindow):
                break

        return widget

    def _tab_widget_index(self, widget):
        for i in range(self.tabBar().count()):
            if self.widget(i) == widget:
                return i

        return -1

    def _get_widget(self, widget):
        panel = widget
        if isinstance(widget, QMainWindow):
            panel = widget.centralWidget()
            if panel.layout():
                panel = panel.layout().itemAt(0).widget()
        elif isinstance(widget, window.DetachedWindow.DetachPanel):
            if panel.layout():
                panel = panel.layout().itemAt(0).widget()

        return panel

    def _on_attach_tab(self, detach_window):
        detach_window.windowClosed.disconnect(self._on_attach_tab)
        detach_window.save_settings(False)
        panel = detach_window.centralWidget()
        tear_off_widget = self._get_widget(panel)
        try:
            panel.widgetVisible.disconnect(detach_window.set_widget_visible)
        except Exception:
            pass
        tear_off_widget.setParent(self)
        panel.widgetVisible.connect(self.set_widget_visible)

        new_index = -1

        for i in range(self.tabBar().count()):
            w = self.widget(i)
            for j in self.tab_idx.values():
                if j.widget == w and j.index > detach_window.tab_idx:
                    new_index = i
                    break
            else:
                continue
            break

        if new_index == -1:
            new_index = self.tabBar().count()

        new_index = self.insertTab(new_index, tear_off_widget, detach_window.windowTitle())

        if new_index != -1:
            self.setCurrentIndex(new_index)

        self.tab_idx[new_index].detached = None

    def _on_detach_tab(self, index, point):
        detach_window = window.DetachedWindow(self.tabText(index), self.parentWidget())
        w = self.widget(index)
        for i in self.tab_idx.values():
            if i.widget == w:
                detach_window.tab_idx = self.tab_idx[i.index].index
                self.tab_idx[i.index].detached = detach_window
                break

        detach_window.windowClosed.connect(self._on_attach_tab)

        tear_off_widget = self.widget(index)
        # panel = detach_window.centralWidget()
        # panel.widgetVisible.disconnect(self.set_widget_visible)
        # panel.widgetVisible.connect(detach_window.set_widget_visible)
        tear_off_widget.setParent(detach_window)

        if self.count() < 0:
            self.setCurrentIndex(0)

        detach_window.set_widget(tear_off_widget)
        detach_window.resize(tear_off_widget.size())
        detach_window.move(point)
        detach_window.show()

    def _on_move_tab(self, from_index, to_index):
        w = self.widget(from_index)
        text = self.tabText(from_index)
        self.removeTab(from_index)
        self.insertTab(to_index, w, text)
        self.setCurrentIndex(to_index)

    def _on_tab_changed_tab(self, index):
        self._previous_tab_id = index


class EditableTearOffTabWidget(TearOffTabWidget, object):
    """
    Custom tab widget with editable functionality
    """

    tab_size_changed = Signal(QSize)
    tab_label_renamed = Signal(str, str)
    tab_removed_text = Signal(str)
    window_modified = Signal()
    add_item_on = Signal(QPointF, QColor, int)
    add_item_with_set = Signal(QPointF, QColor, str, int)
    add_previewed_item = Signal(QPointF, QColor, str, int)
    copy_items = Signal(list)
    selected_items_changed = Signal(list)

    def __init__(self, parent=None):
        super(EditableTearOffTabWidget, self).__init__(parent=parent)

        self._is_editable = True
        self._has_highlight = False
        self.setAcceptDrops(True)
        self.setObjectName('EditableTabWidget')

    def set_is_editable(self, value):
        if self._is_editable != value:
            self._is_editable = value
            self.setMovable(value)
            self.update()

    def get_is_editable(self):
        return self._is_editable

    def set_has_highlight(self, value):
        if self._has_highlight != value:
            self._has_highlight = value
            self.update()

    def get_has_highlight(self):
        return self._has_highlight

    is_editable = property(get_is_editable, set_is_editable)
    has_highlight = property(get_has_highlight, set_has_highlight)

    def toggle_editable(self):
        """
        Toggles editable property of the tab widget
        """

        self.is_editable = not self.is_editable

    def delete_tab(self, index):
        """
        Deletes a tab with given index
        :param index: index of the tab to delete
        """

        if index < 0:
            return
        widget = self.widget(index)
        tab_text = self.tabText(index)
        super(EditableTearOffTabWidget, self).removeTab(index)
        widget.deleteLater()
        self.window_modified.emit()
        self.tab_removed_text.emit(tab_text)

    def button_rect(self):
        r = self.tabBar().tabRect(self.count() - 1)

        if dcc.is_maya() and dcc.get_version() > 2015:
            rect = QRect(2, 0, 30, 31)
        else:
            rect = QRect(6, 3, 26, 17)
        if r.isValid():
            if dcc.is_maya() and dcc.get_version() > 2015:
                rect.moveBottomLeft(r.bottomRight() + QPoint(1, 1))
            else:
                rect.moveBottomLeft(r.bottomRight() + QPoint(3, -1))
        return rect

    def update_tab_bar_signals(self):
        """
        Updates the signals attached to the tab bar
        """

        super(EditableTearOffTabWidget, self).update_tab_bar_signals()
        tab_bar = self.tabBar()
        if tab_bar is None:
            return
        tab_bar.tabMoved.connect(lambda: self.window_modified.emit())
        tab_bar.tab_label_renamed.connect(lambda: self.window_modified.emit())
        tab_bar.tab_label_renamed.connect(self.tab_label_renamed.emit)
        tab_bar.request_remove.connect(self.delete_tab)

    def _set_custom_tab_bar(self):
        """
        Sets a custom tab bar with editable and tear off functionality for the widget
        """

        tabBar = tabbars.EditableTearOffTabBar(self)
        self.setTabBar(tabBar)
        self.update_tab_bar_signals()
        self.setTabsClosable(True)


class MenuTabBlockButton(buttons.BaseToolButton, object):
    def __init__(self, parent=None):
        super(MenuTabBlockButton, self).__init__(parent=parent)

        self.setCheckable(True)


@theme.mixin
class MenuTabBlockButtonGroup(group.BaseButtonGroup, object):
    checkedChanged = Signal(int)

    def __init_(self, parent=None):
        super(MenuTabBlockButtonGroup, self).__init__(parent=parent)

        self.set_spacing(1)
        self._button_group.setExclusive(True)
        self._button_group.buttonClicked[int].connect(self.checkedChanged)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_checked(self):
        """
        Returns current checked button's ID
        :return:  int
        """

        return self._button_group.checkedId()

    def _set_checked(self, value):
        """
        Sets current checked button's ID
        :param value: int
        """

        btn = self._button_group.button(value)
        btn.setChecked(True)
        self.checkedChanged.emit(value)

    checked = Property(int, _get_checked, _set_checked, notify=checkedChanged)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def create_button(self, data_dict):
        button_theme = self.theme()

        btn = MenuTabBlockButton()
        if data_dict.get('image'):
            btn.image(data_dict.get('image'))
        if data_dict.get('text'):
            if data_dict.get('image') or data_dict.get('icon'):
                btn.text_beside_icon()
            else:
                btn.text_only()
        btn.theme_size = button_theme.large if button_theme else theme.Theme.Sizes.LARGE

        return btn


class MenuTabWidget(base.BaseWidget, object):
    def __init__(self, parent=None):
        super(MenuTabWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))

        return main_layout

    def ui(self):
        super(MenuTabWidget, self).ui()

        self.tool_btn_grp = MenuTabBlockButtonGroup()

        bar_widget = QWidget()
        bar_widget.setObjectName('bar_widget')
        self._bar_layout = layouts.HorizontalLayout(margins=(10, 0, 10, 0))
        bar_widget.setLayout(self._bar_layout)
        self._bar_layout.addWidget(self.tool_btn_grp)
        self._bar_layout.addStretch()

        self.main_layout.addWidget(bar_widget)
        self.main_layout.addWidget(dividers.Divider())
        self.main_layout.addSpacing(5)

    def append_widget(self, widget):
        """
        Adds a new widget to the end of the toolbar
        :param widget: QWidget
        """

        self._bar_layout.addWidget(widget)

    def insert_widget(self, widget):
        """
        Inserts the widget to the start of the toolbar
        :param widget: QWidget
        """

        self._bar_layout.insertWidget(0, widget)

    def add_menu(self, data_dict, index=None):
        """
        Adds a new menu
        :param data_dict: dict
        :param index: int
        """

        self.tool_btn_grp.add_button(data_dict, index)


class MenuLineButton(buttons.BaseToolButton, object):
    def __init__(self, parent=None):
        super(MenuLineButton, self).__init__(parent=parent)

        self.setCheckable(True)


class MenuLineButtonGroup(group.BaseButtonGroup, object):
    checkedChanged = Signal(int)

    def __init__(self, parent=None):
        super(MenuLineButtonGroup, self).__init__(parent=parent)

        self.set_spacing(1)
        self._button_group.setExclusive(True)
        self._button_group.buttonClicked[int].connect(self.checkedChanged)

    def create_button(self, data_dict):
        new_button = MenuLineButton(parent=self)
        if data_dict.get('image'):
            new_button.image(data_dict.get('image'))
        if data_dict.get('text'):
            if data_dict.get('image') or data_dict.get('icon'):
                new_button.text_beside_icon()
            else:
                new_button.text_only()

        return new_button

    def _get_checked(self):
        """
        Returns current checked button's ID
        :return: int
        """

        return self._button_group.checkedId()

    def _set_checked(self, value):
        """
        Sets current checked button's ID
        :param value: int
        """

        btn = self._button_group.button(value)
        btn.setChecked(True)
        self.checkedChanged.emit(value)

    theme_checked = Property(int, _get_checked, _set_checked, notify=checkedChanged)


class MenuLineTabWidget(base.BaseWidget, object):
    def __init__(self, alignment=Qt.AlignCenter, parent=None):
        self._alignment = alignment
        super(MenuLineTabWidget, self).__init__(parent=parent)

    @property
    def tool_button_group(self):
        return self._tool_button_group

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))

        return main_layout

    def ui(self):
        super(MenuLineTabWidget, self).ui()

        self._tool_button_group = MenuLineButtonGroup()
        self._bar_layout = layouts.HorizontalLayout(margins=(0, 0, 0, 0))
        if self._alignment == Qt.AlignCenter:
            self._bar_layout.addStretch()
            self._bar_layout.addWidget(self._tool_button_group)
            self._bar_layout.addStretch()
        elif self._alignment == Qt.AlignLeft:
            self._bar_layout.addWidget(self._tool_button_group)
            self._bar_layout.addStretch()
        elif self._alignment == Qt.AlignRight:
            self._bar_layout.addStretch()
            self._bar_layout.addWidget(self._tool_button_group)
        self._stack = stack.SlidingOpacityStackedWidget()
        self._tool_button_group.checkedChanged.connect(self._stack.setCurrentIndex)
        self.main_layout.addLayout(self._bar_layout)
        self.main_layout.addWidget(dividers.Divider())
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(self._stack)

    def add_tab(self, widget, data_dict):
        """
        Adds a new tab with given data
        :param widget: QWidget
        :param data_dict: dict
        """

        self._stack.addWidget(widget)
        self._tool_button_group.add_button(data_dict, self._stack.count() - 1)
