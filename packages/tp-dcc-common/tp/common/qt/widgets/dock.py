#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Qt dock behaviour
"""

import logging

from Qt.QtCore import Qt, Signal, QPoint, QRect, QPropertyAnimation, QParallelAnimationGroup, QAbstractAnimation
from Qt.QtWidgets import QApplication, QSizePolicy, QBoxLayout, QStackedLayout, QWidget, QFrame, QSplitter, QLabel
from Qt.QtWidgets import QPushButton, QScrollArea, QGraphicsDropShadowEffect, QStyle, QMenu, QAction
from Qt.QtGui import QCursor, QIcon

from tpDcc.libs.qt.widgets import layouts, drop

LOGGER = logging.getLogger('tpDcc-libs-qt')

USE_ANIMATIONS = True


# ===================================================================================================================

def new_dock_splitter(orientation=Qt.Horizontal, parent=None):
    s = QSplitter(orientation, parent)
    s.setProperty('dock-splitter', True)
    s.setChildrenCollapsible(False)
    s.setOpaqueResize(False)

    return s


def splitter_contains_section_widget(splitter):
    for i in range(splitter.count()):
        w = splitter.widget(i)
        if splitter and splitter_contains_section_widget(splitter):
            return True
        else:
            if issubclass(w, DockSectionWidget):
                return True

    return False


def delete_empty_splitter(container):
    do_again = False
    while do_again:
        do_again = False
        splitters = container.findChildren(QSplitter)
        for i in range(len(splitters)):
            sp = splitters.at(i)
            if not sp.property('dock-splitter').toBool():
                continue
            if sp.countT() > 0 and splitter_contains_section_widget(sp):
                continue

            del splitters[i]
            do_again = True
            break


def find_parent_container_widget(widget):
    next_widget = widget
    while next_widget:
        if isinstance(next_widget, DockContainer):
            break
        next_widget = next_widget.parentWidget()

    return next_widget


def find_parent_section_widget(widget):
    next_widget = widget
    while next_widget:
        if isinstance(next_widget, DockSectionWidget):
            break
        next_widget = next_widget.parentWidget()

    return next_widget


def find_parent_splitter(widget):
    next_widget = widget
    while next_widget:
        if isinstance(next_widget, QSplitter):
            break
        next_widget = next_widget.parentWidget()

    return next_widget


def find_inmediate_splitter(widget):
    sp = None
    layout = widget.layout()
    if not layout or layout.count() <= 0:
        return sp

    for i in range(layout.count()):
        layout_item = layout.itemAt(0)
        if not layout_item.widget():
            continue
        if isinstance(layout_item.widget(), QSplitter):
            sp = layout_item.widget()
            break

    return sp


# ===================================================================================================================

class DockInternalContentData(object):
    content = None
    title_widget = None
    content_widget = None


class DockHiddenSectionItem(object):
    def __init__(self):
        self.preferred_section_id = -1
        self.preferred_section_index = -1
        self.data = DockInternalContentData()


class DockFlags(object):
    NoFlag = 0
    Closeable = 1
    AllFlags = Closeable


class DockSectionContent(object):

    next_uid = 0

    def __init__(self):
        super(DockSectionContent, self).__init__()

        self._uid = self.get_next_uid()
        self._unique_name = ''
        self._title = ''
        self._flags = [DockFlags.AllFlags]
        self._container_widget = None
        self._content_widget = None
        self._title_widget = None

        LOGGER.debug('Creating DockSectionContent {}'.format(self._uid))

    def get_next_uid(self):
        next_id = DockSectionContent.next_uid
        DockSectionContent.next_uid += 1
        return next_id

    def uid(self):
        return self._uid

    def unique_name(self):
        return self._unique_name

    def container_widget(self):
        return self._container_widget

    def content_widget(self):
        return self._content_widget

    def title_widget(self):
        return self._title_widget

    def flags(self):
        return self._flags

    def title(self):
        return self._title

    def set_title(self, title):
        self._title = title

    def set_flags(self, flags):
        self._flags = flags

    def clean(self):
        if self._container_widget:
            del self._container_widget._section_container_lookup_map_by_id[self._uid]
            del self._container_widget._section_container_lookup_map_by_name[self._unique_name]
            self._title_widget.deleteLater()
            del self._title_widget
            self._content_widget.deleteLater()
            del self._content_widget

    @staticmethod
    def new_section_content(unique_name, container, title, content):
        """
        Creates a new DockSectionWidget an register it into its DockContainer
        :param unique_name: str, unique name for the DockSectionWidget
        :param container: DockContainer, container where DockSectionWidget is stored
        :param title: str, title of the DockSectionWidget
        :param content: QWidget, widget that DockSectionWidget should store and manage
        :return: QDockSectionWidget
        """

        if unique_name == '':
            LOGGER.error('Cannot create DockSectionContent with empty unique_name')
            return None
        elif DockContainer.check_section_container_lookup_map_by_name(container, unique_name):
            LOGGER.error('Cannot create DockSectionContent with already used unique_name')
            return None
        elif not container or not title or not content:
            LOGGER.error('Cannot create DockSectionContent with None values')
            return None

        section_content = DockSectionContent()
        section_content._unique_name = unique_name
        section_content._container_widget = container
        section_content._title_widget = QLabel(title)
        section_content._content_widget = content
        container.register_section_content(section_content)

        return section_content

    def visible_title(self):
        if self._title == '':
            return self._unique_name

        return self._title


class DockSectionContentWidget(QFrame, object):
    def __init__(self, section_content, parent=None):
        super(DockSectionContentWidget, self).__init__(parent=parent)

        self._content = section_content

        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self._content.content_widget())
        self.setLayout(self.main_layout)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def clean(self):
        self.main_layout.removeWidget(self._content.content_widget())


class DockSectionTitleWidget(QFrame, object):

    clicked = Signal()
    activeTabChanged = Signal(bool)

    def __init__(self, section_content, parent=None):
        super(DockSectionTitleWidget, self).__init__(parent=parent)

        self._content = section_content
        self._tab_moving = False
        self._active_tab = False
        self._drag_start_pos = QPoint()
        self._floating_widget = None

        self.main_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(section_content.title_widget())
        self.setLayout(self.main_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
            self._drag_start_pos = event.pos()
            LOGGER.debug('Starting to drag Dock from pos: {}'.format(self._drag_start_pos))
            return

        super(DockSectionTitleWidget, self).mousePressEvent(event)

    def _on_anim_move(self, data, container_widget, section_widget=None, loc=None):
        if section_widget:
            move_anim = QPropertyAnimation(self._floating_widget, 'pos', self)
            move_anim.setStartValue(self._floating_widget.pos())
            move_anim.setEndValue(section_widget.mapToGlobal(section_widget.rect().topLeft()))
            move_anim.setDuration(150)
            resize_anim = QPropertyAnimation(self._floating_widget, 'size', self)
            resize_anim.setStartValue(self._floating_widget.size())
            resize_anim.setEndValue(section_widget.size())
            resize_anim.setDuration(150)
            anim_grp = QParallelAnimationGroup(self)
            anim_grp.finished.connect(lambda: self._on_move_widget(data, container_widget, section_widget, loc))
            anim_grp.addAnimation(move_anim)
            anim_grp.addAnimation(resize_anim)
            anim_grp.start(QAbstractAnimation.DeleteWhenStopped)
        else:
            self._on_move_widget(data, container_widget, section_widget, loc)

    def _on_move_widget(self, data, container_widget, section_widget=None, loc=None):
        data = self._floating_widget.take_content(data)
        self._floating_widget.deleteLater()
        self._floating_widget.clean()
        self._floating_widget = None
        if loc and section_widget:
            container_widget.drop_content(data, section_widget, loc, True)

    def mouseReleaseEvent(self, event):
        container_widget = find_parent_container_widget(widget=self)

        # If we are dragging a widget
        if self._floating_widget:

            # We detect if we are over a DockContentWidget
            section_widget = container_widget.section_at(container_widget.mapFromGlobal(event.globalPos()))
            if section_widget:
                container_widget.drop_overlay().set_allowed_areas(drop.DropArea.AllAreas)
                loc = container_widget.drop_overlay().show_drop_overlay(section_widget)

                # If the drop is in an invalid area we put by default the container in the center
                if loc == drop.DropArea.InvalidDropArea:
                    loc = drop.DropArea.CenterDropArea

                if loc != drop.DropArea.InvalidDropArea:
                    data = DockInternalContentData()
                    if USE_ANIMATIONS:
                        self._on_anim_move(data, container_widget, section_widget, loc)
                    else:
                        self._on_move_widget(data, container_widget, section_widget, loc)
            else:
                drop_area = drop.DropArea.InvalidDropArea
                if container_widget.outer_top_drop_rect().contains(container_widget.mapFromGlobal(event.globalPos())):
                    drop_area = drop.DropArea.TopDropArea
                if container_widget.outer_right_drop_rect().contains(container_widget.mapFromGlobal(event.globalPos())):
                    drop_area = drop.DropArea.RightDropArea
                if container_widget.outer_bottom_drop_rect().contains(
                        container_widget.mapFromGlobal(event.globalPos())):
                    drop_area = drop.DropArea.BottomDropArea
                if container_widget.outer_left_drop_rect().contains(container_widget.mapFromGlobal(event.globalPos())):
                    drop_area = drop.DropArea.LeftDropArea

                # If the drop is in an invalid area we put by default the container in the center
                if drop_area == drop.DropArea.InvalidDropArea:
                    drop_area = drop.DropArea.CenterDropArea

                if drop_area != drop.DropArea.InvalidDropArea:
                    data = DockInternalContentData()
                    if USE_ANIMATIONS:
                        self._on_anim_move(data, container_widget)
                    else:
                        self._on_move_widget(data, container_widget)

                    container_widget.drop_content(data, None, drop_area, True)
        elif self._tab_moving and find_parent_section_widget(self) is not None:
            section = find_parent_section_widget(widget=self)
            pos = event.globalPos()
            pos = section.mapFromGlobal(pos)
            from_index = section.index_of_content(self._content)
            to_index = section.index_of_content_by_title_pos(pos, self)
            section.move_content(from_index, to_index)

        if not self._drag_start_pos.isNull():
            self.clicked.emit()

        self._drag_start_pos = QPoint()
        self._tab_moving = False
        container_widget.drop_overlay().hide_drop_overlay()
        super(DockSectionTitleWidget, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):

        # Get the DockContainer where this title is stored
        container_widget = find_parent_container_widget(widget=self)
        if container_widget is None:
            LOGGER.warning('Title is not stored in DockContainer! This should never happen!')
            return

        # Get the DockSectionWidget where this title is stored
        section_widget = find_parent_section_widget(widget=self)

        if self._floating_widget and (event.buttons() & Qt.LeftButton):
            event.accept()
            move_to_pos = event.globalPos() - (self._drag_start_pos + QPoint(7, 7))
            self._floating_widget.move(move_to_pos)

            # Mouse is over a section widget
            section = container_widget.section_at(container_widget.mapFromGlobal(QCursor.pos()))
            if section:
                container_widget.drop_overlay().set_allowed_areas(drop.DropArea.AllAreas)
                container_widget.drop_overlay().show_drop_overlay(section)

            # Mouse is at the edge of the Container Widget
            elif container_widget.outer_top_drop_rect().contains(container_widget.mapFromGlobal(QCursor.pos())):
                container_widget.drop_overlay().set_allowed_areas([drop.DropArea.TopDropArea])
                container_widget.drop_overlay().show_drop_overlay(
                    container_widget, container_widget.outer_top_drop_rect())
            elif container_widget.outer_right_drop_rect().contains(container_widget.mapFromGlobal(QCursor.pos())):
                container_widget.drop_overlay().set_allowed_areas([drop.DropArea.RightDropArea])
                container_widget.drop_overlay().show_drop_overlay(
                    container_widget, container_widget.outer_right_drop_rect())
            elif container_widget.outer_bottom_drop_rect().contains(container_widget.mapFromGlobal(QCursor.pos())):
                container_widget.drop_overlay().set_allowed_areas([drop.DropArea.BottomDropArea])
                container_widget.drop_overlay().show_drop_overlay(
                    container_widget, container_widget.outer_bottom_drop_rect())
            elif container_widget.outer_left_drop_rect().contains(container_widget.mapFromGlobal(QCursor.pos())):
                container_widget.drop_overlay().set_allowed_areas([drop.DropArea.LeftDropArea])
                container_widget.drop_overlay().show_drop_overlay(
                    container_widget, container_widget.outer_left_drop_rect())
            else:
                container_widget.drop_overlay().hide_drop_overlay()
            return
        elif not self._floating_widget and not self._drag_start_pos.isNull() and (
                event.buttons() & Qt.LeftButton) and section_widget is not None and \
                not section_widget.title_area_geometry().contains(section_widget.mapFromGlobal(event.globalPos())):
            event.accept()

            # We get the new dock info for the current section
            # DockSectionTitleWidget and DockSectionContentWidgets are reparented to the DockContainer and are ready
            # to be moved to a new DockSectionWidget
            LOGGER.debug('Creating new floating dock data ...')
            data = section_widget.take_content(self._content.uid())
            if data is None:
                LOGGER.error(
                    'This should not happen! {} - {}'.format(self._content.uid(), self._content.unique_name()))
                return

            # Create floating widget and add it to the list of Container floatters
            LOGGER.debug('Creating Floating Widget ...')
            self._floating_widget = DockFloatingWidget(container=container_widget, section_content=data.content,
                                                       section_title_widget=data.title_widget,
                                                       content_widget=data.content_widget, parent=container_widget)
            self._floating_widget.resize(section_widget.size())
            container_widget.floatings().append(self._floating_widget)

            move_to_pos = event.globalPos() - (self._drag_start_pos + QPoint(7, 7))
            self._floating_widget.move(move_to_pos)
            self._floating_widget.show()

            # Delete old section, if it is empty now
            if section_widget.is_empty():
                section_widget.clean()
                section_widget.deleteLater()
                del section_widget

            delete_empty_splitter(container=container_widget)
            return
        elif self._tab_moving and find_parent_section_widget(self):
            event.accept()
            move_to_pos = self.mapToParent(event.pos()) - self._drag_start_pos
            move_to_pos.setY(0)
            self.move(move_to_pos)
            return
        elif not self._drag_start_pos.isNull() and (
                event.buttons() & Qt.LeftButton) and (event.pos() - self._drag_start_pos).manhattanLength() >= \
                QApplication.startDragDistance() and find_parent_section_widget(self) is not None \
                and find_parent_section_widget(self).title_area_geometry().contains(
                find_parent_section_widget(self).mapFromGlobal(event.globalPos())):
            event.accept()
            self._tab_moving = True
            self.raise_()
            return

        super(DockSectionTitleWidget, self).mouseMoveEvent(event)

    def clean(self):
        self.main_layout.removeWidget(self._content.title_widget())

    def content(self):
        return self._content

    def is_active_tab(self):
        return self._active_tab

    def set_active_tab(self, active):
        if active != self._active_tab:
            self._active_tab = active
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()
            self.activeTabChanged.emit(active)

    def _on_anim_finished(self, content_widget, data, section_widget, loc):
        data = self._floating_widget.take_content(data)
        self._floating_widget.clean()
        self._floating_widget.deleteLater()
        self._floating_widget = None
        content_widget.drop_content(data, section_widget, loc)


class DockSectionWidgetTabsScrollArea(QScrollArea, object):
    """
    Custom scrollable implementation for tabs
    """

    def __init__(self, section_widget, parent=None):
        super(DockSectionWidgetTabsScrollArea, self).__init__(parent=parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFrameStyle(QFrame.NoFrame)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setMaximumHeight(15)

    def wheelEvent(self, event):
        event.accept()
        try:
            # For Qt >= 5.0.0
            direction = event.angleDelta().y()
        except Exception:
            direction = event.delta()

        if direction < 0:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 20)
        else:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - 20)


class DockSectionWidget(QFrame, object):

    next_uid = 0

    def __init__(self, container_widget=None):
        super(DockSectionWidget, self).__init__(parent=container_widget)

        self._uid = self.get_next_uid()
        self._container = container_widget
        self._tabs_layout_init_count = 0
        self._mouse_press_title_widget = None

        self._contents = list()
        self._section_titles = list()
        self._section_contents = list()

        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self._top_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self._top_layout.setContentsMargins(0, 0, 0, 0)
        self._top_layout.setSpacing(0)
        self.main_layout.addLayout(self._top_layout)

        self._tabs_scroll_area = DockSectionWidgetTabsScrollArea(section_widget=self)
        self._top_layout.addWidget(self._tabs_scroll_area, 1)

        self._tabs_container_widget = QWidget()
        self._tabs_container_widget.setObjectName('tabsContainerWidget')
        self._tabs_scroll_area.setWidget(self._tabs_container_widget)

        self._tabs_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self._tabs_layout.setContentsMargins(0, 0, 0, 0)
        self._tabs_layout.setSpacing(0)
        self._tabs_layout.addStretch(1)
        self._tabs_container_widget.setLayout(self._tabs_layout)

        self._tabs_menu_button = QPushButton()
        self._tabs_menu_button.setObjectName('tabsMenuButton')
        self._tabs_menu_button.setFlat(True)
        self._tabs_menu_button.setIcon(self.style().standardIcon(QStyle.SP_TitleBarUnshadeButton))
        self._tabs_menu_button.setMaximumWidth(self._tabs_menu_button.iconSize().width())
        self._top_layout.addWidget(self._tabs_menu_button, 0)

        self._close_btn = QPushButton()
        self._close_btn.setObjectName('closeButton')
        self._close_btn.setFlat(True)
        self._close_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        self._close_btn.setMaximumWidth(self._close_btn.iconSize().width())
        self._top_layout.addWidget(self._close_btn, 0)
        self._close_btn.clicked.connect(self._on_close_button_clicked)

        self._tabs_layout_init_count = self._tabs_layout.count()

        # Central area with contents
        self._contents_layout = QStackedLayout()
        self._contents_layout.setContentsMargins(0, 0, 0, 0)
        self._contents_layout.setSpacing(0)
        self.main_layout.addLayout(self._contents_layout, 1)

        shadow_effect = QGraphicsDropShadowEffect(self)
        shadow_effect.setOffset(0, 0)
        shadow_effect.setBlurRadius(8)
        self.setGraphicsEffect(shadow_effect)

    @staticmethod
    def get_next_uid():
        next_id = DockSectionWidget.next_uid
        DockSectionWidget.next_uid += 1
        return next_id

    def uid(self):
        return self._uid

    def container_widget(self):
        return self._container

    def contents(self):
        return self._contents

    def is_empty(self):
        return len(self._contents) <= 0

    def showEvent(self, event):
        """
        When the DockSectionWidget is showed, we make need to make sure that the widget is visible
        :param event: QShowEvent
        """

        try:
            self._tabs_scroll_area.ensureWidgetVisible(self._section_titles[self.current_index()])
        except Exception:
            pass

    def title_area_geometry(self):
        return self._top_layout.geometry()

    def content_area_geometry(self):
        return self._contents_layout.geometry()

    def clean(self):
        if self._container:
            del self._container._section_widget_lookup_map_by_id[self._uid]
            self._container._sections.remove(self)

        splitter = find_parent_splitter(self)
        if splitter and splitter.count() == 0:
            splitter.deleteLater()
            del splitter

    def current_index(self):
        """
        Returns the widget index that QStackedWidget is showing right now
        :return: int
        """

        return self._contents_layout.currentIndex()

    def set_current_index(self, index):
        if index < 0 or index > len(self._contents) - 1:
            LOGGER.warning('Invalid index: {}'.format(index))
            return

        for i in range(self._tabs_layout.count()):
            item = self._tabs_layout.itemAt(i)
            if item.widget():
                section_title_widet = item.widget()
                if isinstance(section_title_widet, DockSectionTitleWidget):
                    if i == index:
                        section_title_widet.set_active_tab(True)
                        self._tabs_scroll_area.ensureWidgetVisible(section_title_widet)
                        if DockFlags.Closeable in section_title_widet._content.flags():
                            self._close_btn.setEnabled(True)
                        else:
                            self._close_btn.setEnabled(False)
                    else:
                        section_title_widet.set_active_tab(False)

        # Set active content
        self._contents_layout.setCurrentIndex(index)

    def update_tabs_menu(self):
        m = QMenu()
        for i in range(len(self._contents)):
            section_content = self._contents[i]
            a = m.addAction(QIcon(), section_content.visible_title())
            a.setData(section_content.uid())
            a.triggered.connect(self._on_tabs_menu_action_triggered)

        old = self._tabs_menu_button.menu()
        self._tabs_menu_button.setMenu(m)

        if old:
            old.deleteLater()
            del old

    def add_content(self, section_content):
        """
        Creates DockSectionTitleWidget and DockSectionContentWidget from scratch and store on them
        the given DockSectionContent
        :param section_content: DockSectionContent
        """

        # Add the given DockSectionContent to the list of contents
        self._contents.append(section_content)

        # Create new DockSectionTitle and add it to the list of title widgets and to the layout
        title = DockSectionTitleWidget(section_content=section_content)
        self._section_titles.append(title)
        self._tabs_layout.insertWidget(self._tabs_layout.count() - self._tabs_layout_init_count, title)
        title.clicked.connect(self._on_section_title_clicked)

        # Create DockSectionContentWidget that will store the given DockSectionContent
        content = DockSectionContentWidget(section_content=section_content)
        self._section_contents.append(content)
        self._contents_layout.addWidget(content)

        # If we only have stored one DockSectionContent, we set the current index to the first one
        if len(self._contents) == 1:
            self.set_current_index(0)

        # Update the tab menu depending on the DockSectionContents number
        self.update_tabs_menu()

    def add_data_content(self, internal_data, auto_activate):
        """
        Adds DockSectionTitleWidget and DockSectionContentWidget from the given data. Also the DockSectionContent is
        retrieved from the data
        :param internal_data: DockInternalContentData
        :param auto_activate: bool
        """

        # Add the DockSectionContent stored in the data into the list of contents
        self._contents.append(internal_data.content)

        # Add the DockSectionTitle stored in the data to the list of title widgets and to the layout
        self._section_titles.append(internal_data.title_widget)
        self._tabs_layout.insertWidget(
            self._tabs_layout.count() - self._tabs_layout_init_count, internal_data.title_widget)
        internal_data.title_widget.clicked.connect(self._on_section_title_clicked)

        # Add DockSectionContentWidget stored in the data and associates the DockSectionContent stored also in the data
        self._section_contents.append(internal_data.content_widget)
        self._contents_layout.addWidget(internal_data.content_widget)

        if len(self._contents) == 1:
            self.set_current_index(0)
        elif auto_activate:
            self.set_current_index(len(self._contents) - 1)
        else:
            internal_data.title_widget.set_active_tab(False)

        # Update the tab menu depending on the DockSectionContents number
        self.update_tabs_menu()

    def take_content(self, uid):
        """

        :param uid: uid of the DockSectionContent we want to extract from this section
        :return: bool, whether the new data is valid or not
        """

        section_content = None
        index = -1

        # Check if the given UID is valid and is already stored in this DockSectionWidget
        # Once, is found, we store its index and we extract it from the list of DockSectionContents
        # If no valid DockSectionContent is found, we abort the process
        for i in range(len(self._contents)):
            if self._contents[i].uid() != uid:
                continue
            index = i
            section_content = self._contents.pop(i)
            break
        if section_content is None:
            return None

        # We get the DockSectionTitleWidget associated with the DockSectionContent and:
        # 1. Remove it from the DockSectionWidget layout
        # 2. Disconnect all its signals
        # 3. Parent it to the DockContainer
        title = self._section_titles.pop(index)
        if title:
            self._tabs_layout.removeWidget(title)
            # title.setAttribute(Qt.WA_WState_Created, False)
            title.disconnect(self)
            title.setParent(self._container)
            # title.setAttribute(Qt.WA_WState_Created, True)

        # We get the DockSectionContentWidget associated with the DockSectionContent and:
        # 1. Remove it from the DockSectionWidget
        # 2. Disconnect all its signals
        # 3. Parent it to the DockContainer
        content = self._section_contents.pop(index)
        if content:
            self._contents_layout.removeWidget(content)
            content.disconnect(self)
            content.setParent(self._container)

        # We update the active tab
        if len(self._contents) > 0 and title.is_active_tab():
            if index > 0:
                self.set_current_index(index - 1)
            else:
                self.set_current_index(0)

        # We update the tabs menu
        self.update_tabs_menu()

        if section_content is None or title is None or content is None:
            return None

        internal_data = DockInternalContentData()
        internal_data.content = section_content
        internal_data.title_widget = title
        internal_data.content_widget = content

        # try:
        #     return not internal_data.content.isNull()
        # except Exception:
        #     return internal_data.content is not None
        return internal_data

    def index_of_content(self, section_content):
        if section_content in self._contents:
            return self._contents.index(section_content)

    def index_of_content_by_uid(self, uid):
        for i in range(len(self._contents)):
            if self._contents[i].uid() == uid:
                return i

        return -1

    def index_of_content_by_title_pos(self, p, exclude):
        index = -1
        for i in range(len(self._section_titles)):
            if self._section_titles[i].geometry().contains(p) \
                    and (exclude is None or self._section_titles[i] != exclude):
                index = i
                break

        return index

    def move_content(self, from_index, to_index):
        if from_index >= len(self._contents) or from_index < 0 or \
                to_index >= len(self._contents) or to_index < 0 or from_index == to_index:
            LOGGER.warning('Invalid for tab movement - From: {} | To: {}'.format(from_index, to_index))
            self._tabs_layout.update()
            return

        self._contents.move(from_index, to_index)
        self._section_titles.move(from_index, to_index)
        self._section_contents.move(from_index, to_index)

        layout_from = self._tabs_layout.takeAt(from_index)
        self._tabs_layout.insertWidget(to_index, layout_from.widget())
        layout_from.deleteLater()
        del layout_from
        layout_from = None

        layout_from = self._contents_layout.takeAt(from_index)
        self._contents_layout.insertWidget(to_index, layout_from.widget())
        layout_from.deleteLater()
        del layout_from

        self.update_tabs_menu()

    def _on_close_button_clicked(self):
        index = self.current_index()
        if index < 0 or index > len(self._contents) - 1:
            return
        section_content = self._contents[index]
        if section_content is None:
            return
        self._container.remove_section_content(section_content)

    def _on_section_title_clicked(self):
        section_title_widget = self.sender()
        if not section_title_widget or not isinstance(section_title_widget, DockSectionTitleWidget):
            return

        index = self._tabs_layout.indexOf(section_title_widget)
        self.set_current_index(index)

    def _on_tabs_menu_action_triggered(self, flag):
        a = self.sender()
        if not a or not isinstance(a, QAction):
            return

        uid = a.data().toInt()
        index = self.index_of_content_by_uid(uid=uid)
        if index >= 0:
            self.set_current_index(index)


class DockFloatingWidget(QWidget, object):
    """
    Holds and displays DockSectionContent as a floating window
    It can be resized, moved and dropped back into a DockSectionWidget
    """

    def __init__(self, container, section_content, section_title_widget, content_widget, parent=None):
        super(DockFloatingWidget, self).__init__(parent=parent)

        self._container = container
        self._content = section_content
        self._title_widget = section_title_widget
        self._content_widget = content_widget

        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self._title_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self._title_layout.addWidget(section_title_widget, 1)
        self.main_layout.addLayout(self._title_layout, 0)
        section_title_widget.set_active_tab(False)

        if DockFlags.Closeable in section_content.flags():
            close_btn = QPushButton()
            close_btn.setObjectName('CloseButton')
            close_btn.setFlat(True)
            close_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
            close_btn.setToolTip('Close')
            close_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._title_layout.addWidget(close_btn)
            close_btn.clicked.connect(self._on_close_button_clicked)

        self.main_layout.addWidget(content_widget, 1)
        content_widget.show()

    def clean(self):
        del self._container._floatings[:]         # Python 2

    def take_content(self, data):
        data.content = self._content
        data.title_widget = self._title_widget
        data.content_widget = self._content_widget
        self._title_layout.removeWidget(self._title_widget)
        self._title_widget.setParent(self._container)
        self._title_widget = None
        self.main_layout.removeWidget(self._content_widget)
        self._content_widget.setParent(self._container)
        self._content_widget = None

        return data

    def _on_close_button_clicked(self):
        self._container.hide_section_content(self._content)


class DockContainer(QFrame, object):

    orientationChanged = Signal()
    activeTabChanged = Signal(object, bool)
    sectionContentVisibilityChanged = Signal(object, bool)

    def __init__(self, parent=None):
        super(DockContainer, self).__init__(parent=parent)

        self._orientation = Qt.Horizontal
        self._drop_overlay = drop.DropOverlay(parent=self)
        self._splitter = None
        self._sections = list()
        self._floatings = list()
        self._hidden_section_contents = dict()

        self._section_container_lookup_map_by_id = dict()
        self._section_container_lookup_map_by_name = dict()
        self._section_widget_lookup_map_by_id = dict()

        self.main_layout = layouts.GridLayout(margins=(9, 9, 9, 9))
        self.setLayout(self.main_layout)

    @staticmethod
    def check_section_container_lookup_map_by_id(dock_container, container_id):
        return container_id in dock_container._section_container_lookup_map_by_id

    @staticmethod
    def check_section_container_lookup_map_by_name(dock_container, name):
        return name in dock_container._section_container_lookup_map_by_name

    @staticmethod
    def check_section_widget_lookup_map_by_id(dock_container, widget_id):
        return widget_id in dock_container._section_widget_lookup_map_by_id

    def floatings(self):
        return self._floatings

    def is_empty(self):
        """
        Returns whether the container has sections stored in it or not
        :return: bool
        """

        return len(self._sections) <= 0

    def register_section_content(self, section_content):
        """
        Registers the given section content
        :param section_content: DockSectionContent
        """

        # TODO: We should check if the register is correct (no duplication unique names or ids)
        # TODO: And abort the process is something is wrong?

        self._section_container_lookup_map_by_id[section_content.uid()] = section_content
        self._section_container_lookup_map_by_name[section_content.unique_name()] = section_content

    def register_section_widget(self, section_widget):
        """
        Registers the given section widget
        :param section_widget: DockSectionWidget
        """

        # TODO: We should check if the register is correct (no duplication unique names or ids)
        # TODO: And abort the process is something is wrong?

        self._section_widget_lookup_map_by_id[section_widget.uid()] = section_widget
        self._sections.append(section_widget)

    def clean(self):
        self._sections.clear()
        del self._sections[:]

        self._floatings.clear()
        del self._floatings[:]

        self._sc_lookup_map_by_id.clear()
        self._sc_lookup_map_by_name.clear()
        self._sc_lookup_map_by_id.clear()

    def new_section_widget(self):
        """
        Creates a new DockSectionContentWidget from scratch
        :return: DockSectionContentWidget
        """

        section_widget = DockSectionWidget(container_widget=self)
        self.register_section_widget(section_widget)

        return section_widget

    def section_at(self, pos):
        """
        Returns the section, if exists, that is located on top of the cursor
        :param pos: QPoint
        :return: DockSectionWidget
        """

        g_pos = self.mapToGlobal(pos)
        for i in range(len(self._sections)):
            section_widget = self._sections[i]
            if section_widget.rect().contains(section_widget.mapFromGlobal(g_pos)):
                return section_widget

        return None

    def drop_content_outer_helper(self, parent_layout, internal_data, orientation, append):
        if parent_layout is None:
            return

        section_widget = self.new_section_widget()
        section_widget.add_data_content(internal_data=internal_data, auto_activate=True)

        old_splitter = find_inmediate_splitter(widget=self)
        if not old_splitter:
            sp = new_dock_splitter(orientation=orientation)
            if self.main_layout.count() > 0:
                LOGGER.warning('Still items in layout. This should never happen!')
                layout_item = self.main_layout.takeAt(0)
                layout_item.deleteLater()
                del layout_item

            self.main_layout.addWidget(sp)
            sp.addWidget(section_widget)
        elif old_splitter.orientation() == orientation or old_splitter.count() == 1:
            old_splitter.setOrientation(orientation)
            if append:
                old_splitter.addWidget(section_widget)
            else:
                old_splitter.insertWidget(0, section_widget)
        else:
            sp = new_dock_splitter(orientation=orientation)
            if append:
                try:
                    layout_item = self.main_layout.replaceWidget(old_splitter, sp)
                    sp.addWidget(old_splitter)
                    sp.addWidget(section_widget)
                    layout_item.deleteLater()
                    del layout_item
                except Exception:
                    index = self.main_layout.indexOf(old_splitter)
                    layout_item = self.main_layout.takeAt(index)
                    self.main_layout.addWidget(old_splitter)
                    self.main_layout.addWidget(section_widget)
                    layout_item.deleteLater()
                    del layout_item
            else:
                try:
                    sp.addWidget(section_widget)
                    item_layout = self.main_layout.replaceWidget(old_splitter, sp)
                    sp.addWidget(old_splitter)
                    item_layout.deleteLater()
                    del item_layout
                except Exception:
                    sp.addWidget(section_widget)
                    index = self.main_layout.indexOf(old_splitter)
                    item_layout = self.main_layout.takeAt(index)
                    self.main_layout.addWidget(sp)
                    sp.addWidget(old_splitter)
                    item_layout.deleteLater()
                    del item_layout

        return section_widget

    def drop_content(self, internal_data, target_section_widget, drop_area, auto_active):
        """
        Adds and fills DockSectionContent based on the given data and positioned in the given drop.DropArea
        :param internal_data: DockInternalContentData, stores all dock information to add to the DockContainer
        :param target_section_widget: DockSectionWidget
        :param drop_area: drop.DropArea, area where we want to drop the new DockSectionContent
        :param auto_active: bool, whether if the new DockSectionContent should be visible or not by default
        :return: DropSectionContent, new DropSectionContent added
        """

        ret = None

        # If the DockContainer has no DockSectionContents added to it, we create a new one from scratch and is loaded
        # automatically in the center of the DockContainer
        if self.is_empty():
            LOGGER.debug('DockContainer is empty! Creating DockSectionWidget from scratch ...')
            target_section_widget = self.new_section_widget()
            self.add_section(target_section_widget)
            drop_area = drop.DropArea.CenterDropArea

        # If no the container is not empty and we do not specify a DockSectionWidget, we create a new one
        # from scratch dropped in the given drop area
        if not target_section_widget:
            if drop_area == drop.DropArea.TopDropArea:
                ret = self.drop_content_outer_helper(
                    parent_layout=self.main_layout,
                    internal_data=internal_data, orientation=Qt.Vertical, append=False)
            elif drop_area == drop.DropArea.RightDropArea:
                ret = self.drop_content_outer_helper(
                    parent_layout=self.main_layout,
                    internal_data=internal_data, orientation=Qt.Horizontal, append=True)
            elif drop_area == drop.DropArea.CenterDropArea or drop_area == drop.DropArea.BottomDropArea:
                ret = self.drop_content_outer_helper(
                    parent_layout=self.main_layout,
                    internal_data=internal_data, orientation=Qt.Vertical, append=True)
            elif drop_area == drop.DropArea.LeftDropArea:
                self.drop_content_outer_helper(
                    parent_layout=self.main_layout,
                    internal_data=internal_data, orientation=Qt.Horizontal, append=False)
            else:
                return None
            return ret

        # We loop through all the widgets of the DockSectionWidget and we get its parent (splitter)
        target_section_splitter = find_parent_splitter(target_section_widget)
        if target_section_splitter is None:
            LOGGER.warning('DockSectionWidget is not parented to any widget. This cannot happen!')
            return

        # Add the DockSectionWidget into its corresponding area
        if drop_area == drop.DropArea.TopDropArea:
            section_widget = self.new_section_widget()
            section_widget.add_data_content(internal_data, True)
            if target_section_splitter.orientation() == Qt.Vertical:
                index = target_section_splitter.indexOf(target_section_widget)
                target_section_splitter.insertWidget(index, section_widget)
            else:
                index = target_section_splitter.indexOf(target_section_widget)
                s = new_dock_splitter(Qt.Vertical)
                s.addWidget(section_widget)
                s.addWidget(target_section_widget)
                target_section_splitter.insertWidget(index, s)
            ret = section_widget
        elif drop_area == drop.DropArea.RightDropArea:
            section_widget = self.new_section_widget()
            section_widget.add_data_content(internal_data, True)
            if target_section_splitter.orientation() == Qt.Horizontal:
                index = target_section_splitter.indexOf(target_section_widget)
                target_section_splitter.insertWidget(index + 1, section_widget)
            else:
                index = target_section_splitter.indexOf(target_section_widget)
                s = new_dock_splitter(Qt.Horizontal)
                s.addWidget(target_section_widget)
                s.addWidget(section_widget)
                target_section_splitter.insertWidget(index, s)
            ret = section_widget
        elif drop_area == drop.DropArea.BottomDropArea:
            section_widget = self.new_section_widget()
            section_widget.add_data_content(internal_data, True)
            if target_section_splitter.orientation() == Qt.Vertical:
                index = target_section_splitter.indexOf(target_section_widget)
                target_section_splitter.insertWidget(index + 1, section_widget)
            else:
                index = target_section_splitter.indexOf(target_section_widget)
                s = new_dock_splitter(Qt.Vertical)
                s.addWidget(target_section_widget)
                s.addWidget(section_widget)
                target_section_splitter.insertWidget(index, s)
            ret = section_widget
        elif drop_area == drop.DropArea.LeftDropArea:
            section_widget = self.new_section_widget()
            section_widget.add_data_content(internal_data, True)
            if target_section_splitter.orientation() == Qt.Horizontal:
                index = target_section_splitter.indexOf(target_section_widget)
                target_section_splitter.insertWidget(index, section_widget)
            else:
                s = new_dock_splitter(Qt.Horizontal)
                s.addWidget(section_widget)
                index = target_section_splitter.indexOf(target_section_widget)
                target_section_splitter.insertWidget(index, s)
                s.addWidget(target_section_widget)
            ret = section_widget
        elif drop_area == drop.DropArea.CenterDropArea:
            target_section_widget.add_data_content(internal_data, auto_activate=auto_active)
            ret = target_section_widget

        return ret

    def add_section(self, section_widget):
        """
        Adds the given DockSectionContentWidget to the Main Splitter DockContainer
        If the splitter does not exists, it's created automatically
        :param section_widget: DockSectionContentWidget
        """

        if not section_widget:
            LOGGER.warning('Impossible to add no valid DockSectionContentWidget!')
            return

        # If DockContainer's Main Splitter does not exists, we create it ...
        if not self._splitter:
            self._splitter = new_dock_splitter(orientation=self._orientation)
            self.main_layout.addWidget(self._splitter, 0, 0)

        # Check if the given DockSectionContentWidget has been already to the splitter.
        # If that's the case we do not add it
        if self._splitter.indexOf(section_widget) != -1:
            LOGGER.warning('Section has already been added!')
            return

        # If everything is ok, we add the DockSectionContentWidget to the splitter
        self._splitter.addWidget(section_widget)

    def take_content(self, section_content, internal_data):
        if section_content is None:
            return

        found = False

        # Search in sections
        for i in range(len(self._sections)):
            found = self._sections[i].take_content(section_content.uid(), internal_data)

        # Search in floating widgets
        if not found:
            for i in range(len(self._floatings)):
                found = self._floatings[i].content().uid() == section_content.uid()
                if found:
                    self._floatings[i].take_content(internal_data)

        # Search in hidden items
        if not found:
            if section_content.uid() in self._hidden_section_contents:
                hidden_section_item = self._hidden_section_contents[section_content.uid()]
                internal_data = hidden_section_item.data
                found = True

        return found

    def outer_top_drop_rect(self):
        r = self.rect()
        h = r.height() / 100 * 5
        return QRect(r.left(), r.top(), r.width(), h)

    def outer_right_drop_rect(self):
        r = self.rect()
        w = r.width() / 100 * 5
        return QRect(r.right() - w, r.top(), w, r.height())

    def outer_bottom_drop_rect(self):
        r = self.rect()
        w = r.width() / 100 * 5
        return QRect(r.right() - w, r.top(), w, r.height())

    def outer_left_drop_rect(self):
        r = self.rect()
        w = r.width() / 100 * 5
        return QRect(r.left(), r.top(), w, r.height())

    def contents(self):
        section_containers = self._section_container_lookup_map_by_id.values()
        contents = list()
        for i in range(len(section_containers)):
            section_content = section_containers[i]
            if section_content:
                contents.append(section_content)

        return contents

    def add_section_content(self, section_content, section_widget, drop_area):
        """
        Adds the given section content to this DockContainer
        If DockSectionWidget is not specified, a new one is created for the given DockSectionContent
        :param section_content: DockSectionContent we want to add to this DockContainer
        :param section_widget: DockSectionWidget that will be managed by the DockSectionContent
        :param drop_area: drop.DropArea, area where we want to add the new DockSectionContent into
        :return:
        """

        # If no DockSectionWidget is given, we abort the process
        if section_content is None:
            LOGGER.warning('Cannot add new DockSectionWidget if no one is specified')
            return

        # Create auxiliary data class to store dock data information
        # 1. DockSectionContent : stored from the given one
        # 2. Title Widget : created from scratch and parented to the DockSectionContent
        # 3. DockSectionContentWidget : create from scratch and parent to the DockSectionContent
        data = DockInternalContentData()
        data.content = section_content
        data.title_widget = DockSectionTitleWidget(section_content)
        data.content_widget = DockSectionContentWidget(section_content)

        # When the DOckSectionTitLeWidget is pressed  we notify that the tab have changed
        data.title_widget.activeTabChanged.connect(self._on_active_tab_changed)

        return self.drop_content(
            internal_data=data, target_section_widget=section_widget, drop_area=drop_area, auto_active=False)

    def show_section_content(self, section_content):
        if section_content is None:
            return

        # Search Section Content in floatings
        for i in range(len(self._floatings)):
            floating_widget = self._floatings[i]
            found = floating_widget.content().uid() == section_content.uid()
            if not found:
                continue
            floating_widget.setVisible(True)
            floating_widget._title_widget.setVisible(True)
            floating_widget._content_widget.setVisible(True)
            self.sectionContentVisibilityChanged.emit(section_content, True)
            return True

        # Search Section Content in hidden sections
        if section_content.uid() in self._hidden_section_contents:
            hidden_section_item = self._hidden_section_contents.pop(section_content.uid())
            hidden_section_item.data.title_widget.setVisible(True)
            hidden_section_item.data.contentWidget.setVisible(True)
            section_widget = None
            if hidden_section_item.preferred_section_id > 0:
                sw = self._section_container_lookup_map_by_id[hidden_section_item.preferred_section_id]
                if sw is not None:
                    sw.add_data_content(hidden_section_item.data, True)
                    self.sectionContentVisibilityChanged.emit(section_content, True)
                    return True
            elif len(self._sections) and self._sections[0] is not None:
                section_widget.add_data_content(hidden_section_item.data, True)
                self.sectionContentVisibilityChanged.emit(section_content, True)
                return True
            else:
                sw = self.new_section_widget()
                self.add_section(section_widget=sw)
                sw.add_data_content(hidden_section_item.data, True)
                self.sectionContentVisibilityChanged.emit(section_content, True)
                return True

        # Already visible?
        LOGGER.warning('Unable to show SectionContent, do not know where (already visible)?')
        return False

    def hide_section_content(self, section_content):
        """
        Hides the section content
        :param section_content: DockSectionContent you want to hide
        :return:
        """

        if section_content is None:
            return

        # Search Section Content in floatings
        for i in range(len(self._floatings)):
            found = self._floatings[i].content().uid() == section_content.uid()
            if not found:
                continue
            self._floatings[i].setVisible(False)
            self.sectionContentVisibilityChanged.emit(section_content, False)
            return True

        # Search Section Content in sections
        for i in range(len(self._sections)):
            section_widget = self._sections[i]
            found = section_widget.index_of_content(section_content) >= 0
            if not found:
                continue

            hidden_selection_item = DockHiddenSectionItem()
            hidden_selection_item.preferred_section_id = section_widget.uid()
            hidden_selection_item.preferred_section_index = section_widget.index_of_content(section_content)
            hidden_selection_item.data = section_widget.take_content(section_content.uid())
            if not hidden_selection_item.data:
                return False

            hidden_selection_item.data.title_widget.setVisible(False)
            hidden_selection_item.data.content_widget.setVisible(False)
            self._hidden_section_contents[section_content.uid()] = hidden_selection_item

            if section_widget.is_empty():
                section_widget.clean()
                section_widget.deleteLater()
                del section_widget
                delete_empty_splitter(self)

            self.sectionContentVisibilityChanged.emit(section_content, False)
            return True

        # Search Section Content in hidden elements
        if section_content.uid() in self._hidden_section_contents:
            return True

        LOGGER.error('Unable to hide SectionContent, do not know this one!')
        return False

    def raise_section_content(self, section_content):
        if section_content is None:
            return

        # Search Section Content in sections
        for i in range(len(self._sections)):
            sw = self._sections[i]
            index = sw.index_of_content(section_content)
            if index < 0:
                continue
            sw.set_current_index(index)
            return True

        # Search Section Content in floatins
        for i in range(len(self._floatings)):
            fw = self._floatings[i]
            if fw.content().uid() != section_content.uid():
                continue
            fw.setVisible(True)
            fw.raise_()
            return True

        # Search Section Content in hidden
        if section_content.uid() in self._hidden_section_contents:
            return self.show_section_content(section_content)

        LOGGER.error('Unable hide SectionContent, do not know this one!')
        return False

    def remove_section_content(self, section_content):
        if section_content is None:
            return

        if not self.hide_section_content(section_content):
            return False

        found = False
        for i in range(len(self._floatings)):
            fw = self._floatings[i]
            data = DockInternalContentData()
            found = fw.take_content(data)
            if not found:
                continue

            self._floatings.remove(fw)
            fw.clean()
            fw.deleteLater()
            del fw
            data.title_widget.clean()
            data.title_widget.deleteLater()
            del data.title_widget
            data.content_widget.clean()
            data.content_widget.deleteLater()
            del data.content_widget

        if section_content.uid() not in self._hidden_section_contents:
            LOGGER.error('Something went wrong ... The content should have been there!')
            return False

        hidden_selection_item = self._hidden_section_contents.pop(section_content.uid())
        hidden_selection_item.data.title_widget.deleteLater()
        del hidden_selection_item.data.title_widget
        hidden_selection_item.data.content_widget.deleteLater()
        del hidden_selection_item.data.content_widget

        try:
            section_content.clean()
            del section_content
        except Exception:
            LOGGER.warning('Maybe something went wrong when deleting section ...')

        if self.is_empty():
            self._splitter.deleteLater()
            del self._splitter
            self._splitter = None

        return True

    def is_section_content_visible(self, section_content):
        if section_content is None:
            return

        # Search Section Content in floatings
        for i in range(len(self._floatings)):
            found = self._floatings[i].content().uid() == section_content.uid()
            if not found:
                continue
            return self._floatings[i].isVisible()

        # Search Section Content in sections
        for i in range(len(self._sections)):
            sw = self._sections[i]
            index = sw.index_of_content(section_content)
            if index < 0:
                continue
            return True

        # Search Section Content in hidden
        if section_content.uid() in self._hidden_section_contents:
            return False

        LOGGER.warning(
            'SectionContent is not a part of this ContainerWidget: {}'.format(section_content.unique_name()))
        return False

    def drop_overlay(self):
        return self._drop_overlay

    def _on_active_tab_changed(self):
        section_title_widget = self.sender()
        if section_title_widget:
            self.activeTabChanged.emit(section_title_widget.content(), section_title_widget.is_active_tab())

    def _on_action_toggle_section_content_visibility(self, visible):
        a = self.sender()
        if not a:
            return
        uid = a.property('uid').toInt()
        section_content = self._section_container_lookup_map_by_id[uid]
        if not section_content:
            LOGGER.error('Cannot bind content by ID'.format(uid))
            return
        if visible:
            self.show_section_content(section_content)
        else:
            self.hide_section_content(section_content)
