#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt tree widgets
"""

from Qt.QtCore import Qt, Signal, QRect, QSize, QModelIndex
from Qt.QtWidgets import QApplication, QSizePolicy, QTreeWidget, QTreeWidgetItem, QAbstractItemView, QStyleOption
from Qt.QtWidgets import QWhatsThis
from Qt.QtGui import QColor, QPalette, QPen, QBrush, QPainter

from tpDcc import dcc
from tpDcc.managers import resources
from tpDcc.libs.python import path, fileio, folder
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, buttons, search, lineedit


class TreeWidget(QTreeWidget, object):

    ITEM_WIDGET = QTreeWidgetItem
    ITEM_WIDGET_SIZE = None

    def __init__(self, parent=None):
        super(TreeWidget, self).__init__(parent)

        self._auto_add_sub_items = True
        self._title_text_index = 0
        self._text_edit = True
        self._edit_state = None
        self._current_name = None
        self._old_name = None
        self._current_item = None
        self._last_item = None
        self._drop_indicator_rect = QRect()
        self._drop_indicator_position = None
        self._name_filter = None

        self.setIndentation(25)
        self.setExpandsOnDoubleClick(False)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)

        if dcc.is_maya():
            self.setAlternatingRowColors(dcc.get_version() < 2016)
        if not dcc.is_maya() and not not dcc.is_nuke():
            palette = QPalette()
            palette.setColor(palette.Highlight, Qt.gray)
            self.setPalette(palette)

        self.itemActivated.connect(self._on_item_activated)
        self.itemChanged.connect(self._on_item_changed)
        self.itemSelectionChanged.connect(self._on_item_selection_changed)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemExpanded.connect(self._on_item_expanded)
        self.itemCollapsed.connect(self._on_item_collapsed)

    # ============================================================================================================
    # PROPERTIES
    # ============================================================================================================

    @property
    def current_item(self):
        return self._current_item

    @property
    def current_name(self):
        return self._current_name

    @property
    def edit_state(self):
        return self._edit_state

    @edit_state.setter
    def edit_state(self, flag):
        self._edit_state = flag

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        self.drawTree(painter, event.region())
        self._paint_drop_indicator(painter)

    def mousePressEvent(self, event):

        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.AltModifier:
            pos = self.mapToGlobal((self.rect().topLeft()))
            QWhatsThis.showText(pos, self.whatsThis())
            return

        super(TreeWidget, self).mousePressEvent(event)

        item = self.itemAt(event.pos())
        if not item:
            self._clear_selection()
        else:
            self._current_item = item

    def mouseDoubleClickEvent(self, event):
        position = event.pos()
        index = self.indexAt(position)
        self.doubleClicked.emit(index)

    def dragMoveEvent(self, event):
        item = self.itemAt(event.pos())

        if item:
            index = self.indexFromItem(item)
            rect = self.visualRect(index)
            rect_left = self.visualRect(index.sibling(index.row(), 0))
            rect_right = self.visualRect(index.sibling(index.row(), self.header().logicalIndex(self.columnCount() - 1)))
            self._drop_indicator_position = self._position(event.pos(), rect)
            if self._drop_indicator_position == self.AboveItem:
                self._drop_indicator_rect = QRect(
                    rect_left.left(), rect_left.top(), rect_right.right() - rect_left.left(), 0)
                event.accept()
            elif self._drop_indicator_position == self.BelowItem:
                self._drop_indicator_rect = QRect(
                    rect_left.left(), rect_left.bottom(), rect_right.right() - rect_left.left(), 0)
                event.accept()
            elif self._drop_indicator_position == self.OnItem:
                self._drop_indicator_rect = QRect(
                    rect_left.left(), rect_left.top(), rect_right.right() - rect_left.left(), rect.height())
                event.accept()
            else:
                self._drop_indicator_rect = QRect()

            self.model().setData(index, self._drop_indicator_position, Qt.UserRole)

        self.viewport().update()

        super(TreeWidget, self).dragMoveEvent(event)

    def addTopLevelItem(self, item):
        super(TreeWidget, self).addTopLevelItem(item)

        if hasattr(item, 'widget'):
            if hasattr(item, 'column'):
                self.setItemWidget(item, item.column, item.widget)
            else:
                self.setItemWidget(item, 0, item.widget)

    def insertTopLevelItem(self, index, item):
        super(TreeWidget, self).insertTopLevelItem(index, item)

        if hasattr(item, 'widget'):
            if hasattr(item, 'column'):
                self.setItemWidget(item, item.column, item.widget)
            else:
                self.setItemWidget(item, 0, item.widget)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def item_at(self, pos):
        """
        Returns a pointer to the item at the coordinates p
        The coordinates are relative to the tree widget's viewport
        :param pos: QPoint
        :return: QTreeWidgetItem
        """

        index = self.indexAt(pos)
        return self.item_from_index(index)

    def item_from_index(self, index):
        """
        Return a pointer to the LibraryItem associated with the given model index
        :param index: QModelIndex
        :return: QTreeWidgetItem
        """

        return self.itemFromIndex(index)

    def unhide_items(self):
        """
        Unhide all tree items
        """

        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            self.setItemHidden(item, False)

    def filter_names(self, filter_text):
        """
        Hides all tree items with the given text
        :param filter_text: str, text used to filter tree items
        """

        self._name_filter = filter_text.strip(' ')

        self.unhide_items()

        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            text = str(item.text(self._title_text_index))
            filter_text = str(filter_text).strip(' ')

            # If the filter text is not found on the item text, we hide the item
            if text.find(filter_text) == -1:
                self.setItemHidden(item, True)

    def get_tree_item_name(self, tree_item):
        """
        Returns a list with all the column names of the given QTreeWidgetItem
        :param tree_item: QTreeWidgetItem, item we want to retrive name of
        :return: list<str>
        """

        try:
            # When selecting an item in the tree and refreshing a C++ wrapped will raise
            count = QTreeWidgetItem.columnCount(tree_item)
        except Exception:
            count = 0

        name = list()
        for i in range(count):
            name.append(str(tree_item.text(i)))

        return name

    def get_tree_item_path_string(self, tree_item):
        """
        Returns full path of the given QTreeWidgetItem from its parent into it with the following format:
        "parent/parent/item"
        :param tree_item:
        :return:
        """

        parents = self.get_tree_item_path(tree_item)
        parent_names = self.get_tree_item_names(parents)

        if not parent_names:
            return
        if len(parent_names) == 1 and not parent_names[0]:
            return

        names = list()

        for name in parent_names:
            names.append(name[0])

        names.reverse()

        item_path_str = '/'.join(names)

        return item_path_str

    def get_tree_item_path(self, tree_item):
        """
        Return the tree path of the given QTreeWidgetItem in a list starting from the given item
        :param tree_item: QTreeWidgetItem
        :return: list<QTreeWidgetItem>
        """

        if not tree_item:
            return

        parent_items = list()
        parent_items.append(tree_item)

        try:
            # When selecting an item in the tree and refreshing a C++ wrapped will raise
            parent_item = tree_item.parent()
        except Exception:
            parent_item = None

        while parent_item:
            parent_items.append(parent_item)
            parent_item = parent_item.parent()

        return parent_items

    def get_tree_item_names(self, tree_items):
        """
        Returns a list with the names of the given QTreeWidgetItems
        :param tree_items: list<QTreeWidgetItem>
        :return: list<str>
        """

        item_names = list()

        if not tree_items:
            return item_names

        for tree_item in tree_items:
            name = self.get_tree_item_name(tree_item)
            if name:
                item_names.append(name)

        return item_names

    def get_tree_item_children(self, tree_item):
        """
        Returns all child items of the given QTreeWidgetItem
        :param tree_item: QTreeWidgetItem
        :return: list<QTreeWidgetItem>
        """

        count = tree_item.childCount()
        items = list()
        for i in range(count):
            items.append(tree_item.child(i))

        return items

    def delete_empty_children(self, tree_item):
        """
        Deletes all given QTreeWidget child items that are empty (has no text)
        :param tree_item: QTreeWidgetItem
        """

        count = tree_item.childCount()
        if count <= 0:
            return

        for i in range(count):
            item = tree_item.child(i)
            if item and not item.text(0):
                item = tree_item.takeChild(i)
                del item

    def delete_tree_item_children(self, tree_item):
        """
        Deletes all given QTreeWidget chlid items
        :param tree_item: QTreeWidgetItem
        """

        count = tree_item.childCount()
        if count <= 0:
            return

        children = tree_item.takeChildren()
        for child in children:
            del child

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _position(self, pos, rect):
        """
        Internal function that returns whether the cursor is over, below or on an item
        :param pos: QPos
        :param rect: QRect
        :return: QAbstractItemView.DropIndicatorPosition
        """

        r = QAbstractItemView.OnViewport

        # NOTE: margin * 2 MUST be smaller than row height, otherwise drop OnItem rect will not show
        margin = 5

        if pos.y() - rect.top() < margin:
            r = QAbstractItemView.AboveItem
        elif rect.bottom() - pos.y() < margin:
            r = QAbstractItemView.BelowItem
        elif pos.y() - rect.top() > margin and rect.bottom() - pos.y() > margin:
            r = QAbstractItemView.OnItem

        return r

    def _drop_on(self, event_list):
        """
        Internal function that checks whether or not event list contains a valid drop operation
        :param event_list: list
        :return: bool
        """

        event, row, col, index = event_list
        root = self.rootIndex()

        if self.viewport().rect().contains(event.pos()):
            index = self.indexAt(event.pos())
            if not index.isValid() or not self.visualRect(index).contains(event.pos()):
                index = root

        if index != root:
            if self._drop_indicator_position == self.AboveItem:
                # Drop Above item
                row = index.row()
                col = index.column()
                index = index.parent()
            elif self._drop_indicator_position == self.BelowItem:
                # Drop Below item
                row = index.row() + 1
                col = index.column()
                index = index.parent()
        else:
            # Drop On item
            self._drop_indicator_position = self.OnViewport

        # Update given referenced list
        event_list[0], event_list[1], event_list[2], event_list[3] = event, row, col, index

        return True

    def _is_item_dropped(self, event, strict=False):
        """
        Returns whether or not an item has been dropped in given event
        :param event: QDropEvent
        :param strict: bool, True to handle ordered alphabetically list; False otherwise.
        :return: bool
        """

        is_dropped = False

        index = self.indexAt(event.pos())

        if event.source == self and event.dropAction() == Qt.MoveAction or \
                self.dragDropMode() == QAbstractItemView.InternalMove:
            top_index = QModelIndex()
            col = -1
            row = -1
            event_list = [event, row, col, top_index]
            if self._drop_on(event_list):
                event, row, col, top_index = event_list
                if row > -1:
                    if row == index.row() - 1:
                        is_dropped = False
                elif row == -1:
                    is_dropped = True
                elif row == index.row() + 1:
                    is_dropped = False if strict else True

        return is_dropped

    def _paint_drop_indicator(self, painter):
        """
        Internal function used to paint the drop indicator manually
        :param painter: QPainter
        """

        if self.state() == QAbstractItemView.DraggingState:
            opt = QStyleOption()
            opt.initFrom(self)
            opt.rect = self._drop_indicator_rect
            rect = opt.rect

            color = Qt.black
            if dcc.is_maya():
                color = Qt.white

            brush = QBrush(QColor(color))
            pen = QPen(brush, 1, Qt.DotLine)
            painter.setPen(pen)
            if rect.height() == 0:
                painter.drawLine(rect.topLeft(), rect.topRight())
            else:
                painter.drawRect(rect)

    def _edit_start(self, item):
        """
        Internal function that is called when a user start editing a tree item text
        Closes already opened edit text editors and updates internal variables
        :param item: QTreeWidgetItem
        """

        self._old_name = str(item.text(self._title_text_index))
        self.closePersistentEditor(item, self._title_text_index)
        self.openPersistentEditor(item, self._title_text_index)
        self._edit_state = item

    def _edit_finish(self, item):
        """
        Internal function that is called when a text element of the tree is edited
        Checks that that edit mode is on text and updates the item text manually
        :param item: QTreeWidgetItem
        :return: QTreeWidgetItem, edited item
        """

        if not hasattr(self._edit_state, 'text'):
            return

        self._edit_state = None

        if type(item) == int:
            return self._current_item

        self.closePersistentEditor(item, self._title_text_index)
        state = self._item_rename_valid(self._old_name, item)

        if state:
            state = self._item_renamed(item)
            if not state:
                item.setText(self._title_text_index, self._old_name)
        else:
            item.setText(self._title_text_index, self._old_name)

        return item

    def _item_rename_valid(self, old_name, item):
        """
        Checks if the rename operation on a specific item of the tree is valid or not
        :param old_name: str, old name of the item
        :param item: QTreeWidgetItem, item that is being edit
        :return: bool
        """

        new_name = item.text(self._title_text_index)
        if not new_name:
            return False

        # We do not allow duplicated names on the tree
        if self._already_exists(item):
            return False

        if old_name == new_name:
            return False

        return True

    def _already_exists(self, item):
        """
        Checks if a given QTreeWidgetItem already exists on the tree.
        :param item: QTreeWidgetItem
        :return: bool
        """

        name = item.text(0)
        parent = item.parent()

        if parent:
            skip_index = parent.indexOfChild(item)
            for i in range(parent.childCount()):
                if i == skip_index:
                    continue
                other_name = str(parent.child(i).text(0))
                if name == other_name:
                    return True
        else:
            skip_index = self.indexFromItem(item)
            skip_index = skip_index.row()
            for i in range(self.topLevelItemCount()):
                if skip_index == i:
                    continue
                other_name = str(self.topLevelItem(i).text(0))
                if name == other_name:
                    return True

        return False

    def _clear_selection(self):
        """
        Internal function used to clear the selection of the tree and update internal variables
        """

        self.clearSelection()
        self._current_item = None
        if self._edit_state:
            self._edit_finish(self._last_item)

    def _emit_item_click(self, item):
        """
        Internal function that is used to force the emission of itemClicked signal
        :param item: QTreeWidgetItem
        """

        self.itemClicked.emit(item, 0)

    def _get_ancestors(self, item):
        """
        Returns all ancestors items of the given QTreeWidgetItem
        :param item: QTreeWidgetItem
        :return: list<QTreeWidgetItem>
        """

        child_count = item.childCount()
        items = list()
        for i in range(child_count):
            child = item.child(i)
            children = self._get_ancestors(child)
            items.append(child)
            if children:
                items += children

        return items

    def _get_all_items(self):
        """
        Internal function that returns all items in the tree
        :return: list(QTreeWidgetItem)
        """

        item_count = self.topLevelItemCount()
        items = list()
        for i in range(item_count):
            item = self.topLevelItem(i)
            ancestors = self._get_ancestors(item)
            items.append(item)
            if ancestors:
                items += ancestors

        return items

    def _add_sub_items(self, tree_item):
        """
        Internal function that is updates the hiearchy of the given QTreeWidgetItem
        Implementation MUST be implemented in child class
        :param tree_item: QTreeWidgetItem
        """

        pass

    def _item_renamed(self, item):
        """
        Internal function that rename a specific QTreeWidgetItem contents
        Implementation MUST be implemented in child class
        :param item: QTreeWidgetItem
        """

        return False

    def _delete_children(self, tree_item):
        """
        Internal function that removes all children of the given item
        :param tree_item: QTreeWidgetItem
        """

        self.delete_tree_item_children(tree_item)

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_item_expanded(self, item):
        """
        Internal function that is called anytime the user expands an item of the tree
        Load dynamically all the items parented to the expanded item
        :param item: QTreeWidgetItem
        """

        if self._auto_add_sub_items:
            self._add_sub_items(item)

    def _on_item_collapsed(self, item):
        """
        Internal function that is called anytime the user collapses an item of the tree
        :param item: QTreeWidgetItem
        """

        pass

    def _on_item_activated(self, item):
        """
        Internal function that is called anytime a tree item is activated
        :param item: QTreeWidgetItem
        """

        if self._edit_state:
            self._edit_finish(self._edit_state)
        else:
            if self._text_edit:
                self._edit_start(item)

    def _on_item_changed(self, current_item, previous_item):
        """
        Internal function that is called when a tree item changes its content
        :param current_item: QTreeWidetItem
        :param previous_item: QTreeWidgetItem
        """

        if self._edit_state:
            self._edit_finish(previous_item)

    def _on_item_selection_changed(self):
        """
        Internal function that is called anytime the user changes the selection of the tree
        """

        item_sel = self.selectedItems()
        current_item = None
        if item_sel:
            current_item = item_sel[0]

        if current_item:
            self._current_name = current_item.text(self._title_text_index)
        if self._edit_state:
            self._edit_finish(self._edit_state)

        if not current_item:
            self._emit_item_click(current_item)

    def _on_item_clicked(self, item, column):
        """
        Internal function that is called anytime the user clicks on an item of the tree
        Updates internal variables and clear the selection if necessary
        :param item: QTreeWidgetItem
        :param column: int
        """

        self._last_item = self._current_item
        self._current_item = self.currentItem()
        if not item or column != self._title_text_index:
            if self._last_item:
                self._clear_selection()


class ManageTreeWidget(base.BaseWidget, object):
    def __init__(self, parent=None):
        self.tree_widget = None
        super(ManageTreeWidget, self).__init__(parent)

    def set_tree_widget(self, tree_widget):
        """
        Set the tree widget managed by this widget
        :param tree_widget: QTreeWidget
        """

        self.tree_widget = tree_widget


class FilterTreeWidget(base.DirectoryWidget, object):

    subPathChanged = Signal(str)

    def __init__(self, parent=None):
        self._tree_widget = None
        self._emit_changes = True
        self._update_tree = True
        super(FilterTreeWidget, self).__init__(parent=parent)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        return main_layout

    def ui(self):
        super(FilterTreeWidget, self).ui()

        texts_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._filter_names = search.SearchFindWidget()
        self._filter_names.set_placeholder_text('Filter Names')
        self._sub_path_filter = lineedit.BaseLineEdit()
        self._sub_path_filter.setPlaceholderText('Set Sub Path')
        self._sub_path_filter.setVisible(False)
        texts_layout.addWidget(self._filter_names)
        texts_layout.addWidget(self._sub_path_filter)
        self.main_layout.addLayout(texts_layout)

    def setup_signals(self):
        self._filter_names.textChanged.connect(self._on_filter_names)
        self._sub_path_filter.textChanged.connect(self._on_sub_path_filter_changed)
        self._sub_path_filter.textEdited.connect(self._on_sub_path_filter_edited)

    def dropEvent(self, event):
        item = self.item_at(event.pos())
        if item:
            item_path = self.get_tree_item_path_string(item)
            item_full_path = path.join_path(self._directory, item_path)
            if not item_full_path or not path.is_dir(item_full_path):
                event.ignore()
            else:
                event.accept()
        else:
            event.ignore()

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def get_name_filter(self):
        """
        Returns the name filter current text
        :return: str
        """

        return str(self._filter_names.text())

    def get_sub_path_filter(self):
        """
        Returns the name of the sub path filters text
        :return: str
        """

        return str(self._sub_path_filter.text())

    def set_emit_changes(self, flag):
        """
        Sets whether signals should be emitted or not
        :param flag: bool
        """

        self._emit_changes = flag

    def set_name_filter(self, text):
        """
        Sets the name filter text
        :param text: str
        """

        self._filter_names.setText(text)

    def set_sub_path_filter(self, text):
        """
        Sets the name sub path filter text
        :param text: str
        """

        self._sub_path_filter.setText(text)

    def clear_name_filter(self):
        """
        Clears current name filter text
        """

        self._filter_names.setText('')

    def clear_sub_path_filter(self):
        """
        Clears current sub path filter text
        """

        self._sub_path_filter.setText('')

    def set_tree_widget(self, tree_widget):
        """
        Sets the tree widget used by this widget
        :param tree_widget: QTreeWidget
        """

        self._tree_widget = tree_widget

    def set_sub_path_warning(self, flag):
        """
        Sets whether or not sub path filter text should indicate a warning
        :param flag: bool
        """

        if flag:
            if dcc.is_maya():
                self._sub_path_filter.setStyleSheet('background-color: rgb(255, 100, 100);')
            else:
                self._sub_path_filter.setStyleSheet('background-color: rgb(255, 150, 150);')
        else:
            self._sub_path_filter.setStyleSheet('')

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_filter_names(self, text):
        """
        Internal callback function that is used to call the filter function of the TreeWidget
        :param text: str, filter text that should be used
        """

        if self._update_tree:
            self._tree_widget.filter_names(text)

    def _on_sub_path_filter_changed(self):
        """
        Internal callback function that is called when sub path filter text changes
        """

        current_text = str(self._sub_path_filter.text()).strip()
        self.subPathChanged.emit(current_text)

    def _on_sub_path_filter_edited(self):
        """
        Internal callback function that is called when sub path filter text is edited
        """

        current_text = str(self._sub_path_filter.text()).strip()
        if not current_text:
            self.set_directory(self._directory)
            if self._update_tree:
                self._tree_widget.set_directory(self._directory)
            text = self._filter_names.text
            self._on_filter_names(text)
            return

        sub_dir = path.join_path(self._directory, current_text)
        if not sub_dir:
            return

        if path.is_dir(sub_dir):
            if self._update_tree:
                self._tree_widget.set_directory(self._directory)
            text = self._filter_names.text
            self._on_filter_names(text)

        if self._emit_changes:
            self.subPathChanged.emit(current_text)


class FileTreeWidget(TreeWidget, object):

    refreshed = Signal()

    HEADER_LABELS = ['Name', 'Size MB', 'Time']
    NEW_ITEM_NAME = 'new_file'
    ITEM_WIDGET = QTreeWidgetItem
    EXCLUDE_EXTENSIONS = list()

    def __init__(self, parent=None):
        self._directory = None
        super(FileTreeWidget, self).__init__(parent)

        self.setHeaderLabels(self.HEADER_LABELS)

    # ============================================================================================================
    # PROPERTIES
    # ============================================================================================================

    @property
    def directory(self):
        return self._directory

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def dropEvent(self, event):
        item = self.item_at(event.pos())
        if item:
            item_path = self.get_tree_item_path_string(item)
            item_full_path = path.join_path(self._directory, item_path)
            if item_full_path and path.is_dir(item_full_path):
                super(FileTreeWidget, self).dropEvent(event)

    def _add_item(self, file_name, parent=None):
        """
        Function that adds given file into the tree
        :param file_name: str, name of the file new item will store
        :param parent: QTreeWidgetItem, parent item to append new item into
        :return: QTreeWidet, new item added
        """

        try:
            self.blockSignals(True)
            self.clearSelection()
        finally:
            self.blockSignals(False)

        path_name = file_name
        found = False

        # Check if item exists
        if parent:
            parent_path = self.get_tree_item_path_string(parent)
            path_name = '{}/{}'.format(parent_path, file_name)
            for i in range(parent.childCount()):
                item = parent.child(i)
                if item.text(0) == file_name:
                    found = item
        else:
            for i in range(self.topLevelItemCount()):
                item = self.topLevelItem(i)
                if item.text(0) == file_name:
                    found = item

        # Check if the item should be excluded or not from the tree
        exclude = self.EXCLUDE_EXTENSIONS
        if exclude:
            split_name = file_name.split('.')
            extension = split_name[-1]
            if extension in exclude:
                return

        if found:
            item = found
        else:
            item = self.create_item_widget(file_name)

        # Constrain item size if necessary
        size = self.ITEM_WIDGET_SIZE
        if size:
            size = QSize(*size)
            item.setSizeHint(self._title_text_index, size)

        # Set item text
        item_path = path.join_path(self._directory, path_name)
        sub_files = folder.get_files_and_folders(item_path)
        item.setText(self._title_text_index, file_name)

        # Retrieve file properties
        if self.header().count() > 1:
            if path.is_file(item_path):
                size = fileio.get_file_size(item_path)
                date = fileio.get_last_modified_date(item_path)
                item.setText(self._title_text_index + 1, str(size))
                item.setText(self._title_text_index + 2, str(date))

        # Update valid sub files
        # NOTE: Sub files are added dynamically when the user expands an item
        if sub_files:
            self._delete_children(item)
            exclude_extensions = self.EXCLUDE_EXTENSIONS
            exclude_count = 0
            if exclude_extensions:
                for f in sub_files:
                    for exclude in exclude_extensions:
                        if f.endswith(exclude):
                            exclude_count += 1
                            break

            if exclude_count != len(sub_files):
                QTreeWidgetItem(item)

        # Add item to tree hierarchy
        if parent:
            parent.addChild(item)
            try:
                self.blockSignals(True)
                self.setCurrentItem(item)
            finally:
                self.blockSignals(False)
        else:
            self.addTopLevelItem(item)

        return item

    def _add_items(self, files, parent=None):
        """
        Function that adds given files into the tree
        :param files: list<str>, list of files to add
        :param parent: QTreeWidgetItem, parent item to append new item
        :return:
        """

        if not files:
            return

        for filename in files:
            if parent:
                self._add_item(filename, parent)
            else:
                self._add_item(filename)

    def _add_sub_items(self, tree_item):
        """
        Implements _add_sub_items() functionality
        :param tree_item: QTreeWidgetItem
        """

        # Clean item hierarchy first
        self.delete_empty_children(tree_item)
        self._delete_children(tree_item)

        path_str = self.get_tree_item_path_string(tree_item)
        full_path_str = path.join_path(self._directory, path_str)
        files = self._get_files(full_path_str)

        self._add_items(files, tree_item)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def set_directory(self, directory, refresh=True, name_filter=None):
        """
        Sets the directory used by this QTreeWidget
        :param directory: str, directory
        :param refresh: bool, Whether to refresh QTreeWidget items after setting working directory
        """

        self._directory = directory
        self._name_filter = name_filter
        if refresh:
            self.refresh()

    def get_item_directory(self, tree_item):
        """
        Returns the full path of the given tree item
        :param tree_item: QTreeWidgetItem
        :return: str
        """

        path_str = self.get_tree_item_path_string(tree_item)
        return path.join_path(self._directory, path_str)

    def create_item_widget(self, file_name):
        """
        Creates a new item widget
        :return: variant
        """

        return self.ITEM_WIDGET()

    def create_item(self, name=None):
        """
        Creates a new item (folder) inside the selected item
        :param name: str, name of the new item
        """

        current_item = self._current_item
        if current_item:
            item_path = self.get_tree_item_path_string(self._current_item)
            item_path = path.join_path(self._directory, item_path)
            if path.is_file(item_path):
                item_path = path.dirname(item_path)
                current_item = self._current_item.parent()

        if not current_item:
            item_path = self._directory

        if not name:
            name = self.NEW_ITEM_NAME

        folder.create_folder(name=name, directory=item_path)

        if current_item:
            self._add_sub_items(current_item)
            self.setItemExpanded(current_item, True)
        else:
            self.refresh()

    def delete_item(self):
        """
        Deletes the selected item
        """

        item = self._current_item
        item_path = self.get_item_directory(item)
        name = path.get_basename(item_path)
        item_directory = path.dirname(item_path)

        if path.is_dir(item_path):
            folder.delete_folder(name, item_directory)
        elif path.is_file(item_path):
            fileio.delete_file(name, item_directory)
            if item_path.endswith('.py'):
                fileio.delete_file(name + '.c', item_directory)

        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)

    def refresh(self):
        """
        Refreshes all QTreeWidget items
        """

        if not self._directory:
            self.clear()
            return

        files = self._get_files()
        if not files:
            self.clear()
            return

        self._load_files(files)
        self.refreshed.emit()

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _get_files(self, directory=None):
        """
        Internal function taht returns  all files located in the given directory. If not directory is given, stored
         variable directory will be used
        :return: list<str>
        """

        if not directory:
            directory = self._directory

        return folder.get_files_and_folders(directory)

    def _load_files(self, files):
        """
        Internal function that adds given files into the tree (clearing the tree first)
        :param files: list<str>
        """

        self.clear()
        self._add_items(files)


class EditFileTreeWidget(base.DirectoryWidget, object):

    itemClicked = Signal(object, object)
    description = 'EditTree'

    TREE_WIDGET = FileTreeWidget
    MANAGER_WIDGET = ManageTreeWidget
    FILTER_WIDGET = FilterTreeWidget

    def __init__(self, parent=None):
        super(EditFileTreeWidget, self).__init__(parent)

        self._on_edit(False)

    # ============================================================================================================
    # PROPERTIES
    # ============================================================================================================

    @property
    def tree_widget(self):
        return self._tree_widget

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def ui(self):
        super(EditFileTreeWidget, self).ui()

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self._tree_widget = self.TREE_WIDGET(parent=self)

        self._manager_widget = self.MANAGER_WIDGET(parent=self)
        self._manager_widget.set_tree_widget(self._tree_widget)

        self._filter_widget = self.FILTER_WIDGET(parent=self)
        self._filter_widget.set_tree_widget(self._tree_widget)
        self._filter_widget.set_directory(self._directory)
        drag_reorder_icon = resources.icon('drag_reorder')
        edit_mode_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        edit_mode_layout.setAlignment(Qt.AlignBottom)
        self._edit_mode_btn = buttons.BaseButton(parent=self)
        self._edit_mode_btn.setIcon(drag_reorder_icon)
        self._edit_mode_btn.setCheckable(True)
        edit_mode_layout.addWidget(self._edit_mode_btn)
        self._filter_widget.main_layout.addLayout(edit_mode_layout)

        self.main_layout.addWidget(self._filter_widget)
        self.main_layout.addWidget(self._tree_widget)
        self.main_layout.addWidget(self._manager_widget)

    def setup_signals(self):
        self._edit_mode_btn.toggled.connect(self._on_edit)
        self._tree_widget.itemClicked.connect(self._on_item_selection_changed)

    def set_directory(self, directory, refresh=True):
        """
        Overrides set_directory function to take in account also the sub path
        and update all directories of the different tree widgets
        :param directory: str
        """

        super(EditFileTreeWidget, self).set_directory(directory)
        self._filter_widget.set_directory(directory)
        self._tree_widget.set_directory(directory, refresh=refresh)

        if hasattr(self._manager_widget, 'set_directory'):
            self._manager_widget.set_directory(directory)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def get_current_item(self):
        """
        Returns the current selected item on the tree
        :return: TreeItem
        """

        items = self._tree_widget.selectedItems()
        item = None
        if items:
            item = items[0]

        return item

    def get_current_item_name(self):
        """
        Returns the current name of the selected item on the tree
        :return: str
        """

        current_item = self.get_current_item()
        return current_item.text(0) if current_item else ''

    def get_current_item_directory(self):
        """
        Returns the directory the current selected item points to
        :return: str
        """

        item = self.get_current_item()
        return self._tree_widget.get_item_directory(item)

    def enable_edit_mode(self):
        """
        Enables edit mode
        """

        if not self._edit_mode_btn.isChecked():
            self._edit_mode_btn.blockSignals(True)
            try:
                self._edit_mode_btn.setChecked(True)
            finally:
                self._edit_mode_btn.blockSignals(False)

        self._tree_widget.setDragEnabled(True)
        self._tree_widget.setAcceptDrops(True)
        self._tree_widget.setDropIndicatorShown(True)

    def disable_edit_mode(self):
        """
        Enables edit mode
        """

        if self._edit_mode_btn.isChecked():
            self._edit_mode_btn.blockSignals(True)
            try:
                self._edit_mode_btn.setChecked(False)
            finally:
                self._edit_mode_btn.blockSignals(False)

        self._tree_widget.setDragEnabled(False)
        self._tree_widget.setAcceptDrops(False)
        self._tree_widget.setDropIndicatorShown(False)

    def get_checked_children(self, tree_item):
        """
        Function that returns checked item children of the given tree item
        :param tree_item:
        :return:
        """

        if not tree_item:
            return

        expand_state = tree_item.isExpanded()
        tree_item.setExpanded(True)
        children = self._tree_widget.get_tree_item_children(tree_item)

        checked_children = list()
        for child in children:
            check_state = child.checkState(0)
            if check_state == Qt.Checked:
                checked_children.append(child)
        levels = list()
        if checked_children:
            levels.append(checked_children)

        while children:
            new_children = list()
            checked_children = list()
            for child in children:
                current_check_state = child.checkState(0)
                if current_check_state != Qt.Checked:
                    continue
                child.setExpanded(True)
                sub_children = self._tree_widget.get_tree_item_children(child)
                checked = list()
                for sub_child in sub_children:
                    check_state = sub_child.checkState(0)
                    if check_state == Qt.Checked:
                        checked.append(sub_child)
                if sub_children:
                    new_children += sub_children
                if checked:
                    checked_children += checked
            if not checked_children:
                children = list()
                continue
            children = new_children
            if checked_children:
                levels.append(checked_children)

        tree_item.setExpanded(expand_state)
        levels.reverse()

        return levels

    def refresh(self):
        """
        Refresh TreeWidget items
        """

        self._tree_widget.refresh()

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_item_selection_changed(self):
        """
        Internal function that is called anytime the user selects an item on the TreeWidget
        Emits itemClicked signal with the name of the selected item and the item itself
        """

        items = self._tree_widget.selectedItems()
        name = None
        item = None
        if items:
            item = items[0]
            name = item.text(0)
            self.itemClicked.emit(name, item)

        return name, item

    def _on_edit(self, flag):
        """
        Internal function that is called anytime the user presses the Edit button on the filter widget
        If edit is ON, drag/drop operations in tree widget are disabled
        :param flag: bool
        """

        if flag:
            self.enable_edit_mode()
        else:
            self.disable_edit_mode()


class TreeWidgetItem(QTreeWidgetItem, object):
    def __init__(self, parent=None):
        self._widget = self._get_widget()
        if self._widget:
            self._widget.item_view = self
        self.column = self._get_column()
        super(TreeWidgetItem, self).__init__(parent)

    def _get_widget(self):
        return None

    def _get_column(self):
        return 0
