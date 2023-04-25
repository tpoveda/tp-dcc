#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt widgets related with version management
"""

from Qt.QtCore import Qt
from Qt.QtWidgets import QSizePolicy, QWidgetItem, QTreeWidgetItem

from tpDcc.managers import resources
from tpDcc.libs.python import version
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import layouts, buttons, treewidgets


class HistoryTreeWidget(treewidgets.FileTreeWidget):

    HEADER_LABELS = ['Version', 'Comment', 'Size MB', 'User', 'Time']

    def __init__(self):
        super(HistoryTreeWidget, self).__init__()

        if qtutils.is_pyside() or qtutils.is_pyside2():
            self.sortByColumn(0, Qt.SortOrder.DescendingOrder)

        self.setColumnWidth(0, 70)
        self.setColumnWidth(1, 200)
        self.setColumnWidth(2, 70)
        self.setColumnWidth(3, 70)
        self.setColumnWidth(4, 70)
        self._padding = 1

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def _get_files(self):
        if not self._directory:
            return

        version_file = version.VersionFile(file_path=self._directory)
        version_data = version_file.get_organized_version_data()
        if not version_data:
            return list()

        self._padding = len(str(len(version_data)))

        return version_data

    def _add_item(self, version_data):
        version, comment, user, file_size, file_date, version_file = version_data
        version_str = str(version).zfill(self._padding)

        item = QTreeWidgetItem()
        item.setText(0, version_str)
        item.setText(1, comment)
        item.setText(2, str(file_size))
        item.setText(3, user)
        item.setText(4, file_date)
        self.addTopLevelItem(item)
        item.file_path = version_file

    def _add_items(self, version_list):
        if not version_list:
            self.clear()

        for version_data in version_list:
            self._add_item(version_data)

    def _on_item_activated(self, item):
        return

    def _on_item_clicked(self, item, column):
        self._last_item = self._current_item
        self._current_item = self.currentItem()


class HistoryFileWidget(base.DirectoryWidget, object):

    VERSION_LIST = HistoryTreeWidget

    def __init__(self, parent=None):
        super(HistoryFileWidget, self).__init__(parent=parent)

        self._enable_button_children(False)

    def ui(self):
        super(HistoryFileWidget, self).ui()

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self._btn_layout = layouts.HorizontalLayout()
        self._open_btn = buttons.BaseButton('Open')
        self._open_btn.setIcon(resources.icon('folder'))
        self._open_btn.setMaximumWidth(100)
        self._btn_layout.addWidget(self._open_btn)
        self._version_list = self.VERSION_LIST()
        self.main_layout.addWidget(self._version_list)
        self.main_layout.addLayout(self._btn_layout)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def setup_signals(self):
        self._open_btn.clicked.connect(self.open_version)
        self._version_list.itemSelectionChanged.connect(self._on_update_selection)

    def set_directory(self, directory):
        """
        Overrides base base.DirectoryWidget set_directory function
        :param directory: str
        """

        super(HistoryFileWidget, self).set_directory(directory)

        if self.isVisible():
            self._version_list.set_directory(directory, refresh=True)
        else:
            self._version_list.set_directory(directory, refresh=False)

        self._enable_button_children(False)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def open_version(self):
        """
        Opens selected version
        Override functionality for specific data
        """

        pass

    def refresh(self):
        """
        Updates version list
        """

        self._version_list.refresh()
        self._enable_button_children(False)

    def set_data_class(self, data_class_instance):
        self._data_class = data_class_instance
        if self._directory:
            self._data_class.set_directory(self._directory)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _get_layout_children(self, layout):
        children = list()
        for i in range(layout.count()):
            children.append(layout.itemAt(i))

        return children

    def _enable_button_children(self, flag):
        children = self._get_layout_children(self._btn_layout)
        while children:
            next_round = list()
            for child in children:
                if type(child) == QWidgetItem:
                    child.widget().setEnabled(flag)
                else:
                    sub_children = self._get_layout_children(child)
                    next_round += sub_children
            children = list()
            if next_round:
                children = next_round

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_update_selection(self):
        items = self._version_list.selectedItems()
        if not items:
            self._enable_button_children(False)
        else:
            self._enable_button_children(True)
