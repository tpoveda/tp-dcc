#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya shelves
"""

import json
from collections import OrderedDict
from functools import partial

from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QWidget, QLabel, QPushButton, QMenu

import maya.cmds
import maya.mel
import maya.OpenMayaUI

from tp.core.abstract import shelf as abstract_shelf
from tp.common.qt import qtutils
from tp.maya.cmds import gui


class MayaShelf(abstract_shelf.AbstractShelf, object):

    def __init__(self, name='MayaShelf', label_background=(0, 0, 0, 0), label_color=(0.9, 0.9, 0.9),
                 category_icon=None, enable_labels=True):
        super(MayaShelf, self).__init__(name=name, label_background=label_background, label_color=label_color,
                                        category_icon=category_icon, enable_labels=enable_labels)

    @staticmethod
    def add_menu_item(parent, label, command='', icon=''):
        """
        Adds a menu item with the given attributes
        :param parent:
        :param label:
        :param command:
        :param icon:
        :return:
        """

        return maya.cmds.menuItem(parent=parent, label=label, command=command, image=icon or '')

    @staticmethod
    def add_sub_menu(parent, label, icon=None):
        """
        Adds a sub menu item with the given label and icon to the given parent popup menu
        :param parent:
        :param label:
        :param icon:
        :return:
        """

        return maya.cmds.menuItem(parent=parent, label=label, icon=icon or '', subMenu=True)

    def create(self, delete_if_exists=True):
        """
        Creates a new shelf
        """

        if delete_if_exists:
            if gui.shelf_exists(shelf_name=self._name):
                gui.delete_shelf(shelf_name=self._name)
        else:
            assert not gui.shelf_exists(self._name), 'Shelf with name {} already exists!'.format(self._name)

        self._name = gui.create_shelf(name=self._name)

        # ========================================================================================================

        self._category_btn = QPushButton('')
        if self._category_icon:
            self._category_btn.setIcon(self._category_icon)
        self._category_btn.setIconSize(QSize(18, 18))
        self._category_menu = QMenu(self._category_btn)
        self._category_btn.setStyleSheet(
            'QPushButton::menu-indicator {image: url(myindicator.png);'
            'subcontrol-position: right center;subcontrol-origin: padding;left: -2px;}')
        self._category_btn.setMenu(self._category_menu)
        self._category_lbl = QLabel('MAIN')
        self._category_lbl.setAlignment(Qt.AlignCenter)
        font = self._category_lbl.font()
        font.setPointSize(6)
        self._category_lbl.setFont(font)
        menu_ptr = maya.OpenMayaUI.MQtUtil.findControl(self._name)
        menu_widget = qtutils.wrapinstance(menu_ptr, QWidget)
        menu_widget.layout().addWidget(self._category_btn)
        menu_widget.layout().addWidget(self._category_lbl)

        self.add_separator()

    def set_as_active(self):
        """
        Sets this shelf as active shelf in current DCC session
        """

        main_shelf = maya.mel.eval("$_tempVar = $gShelfTopLevel")
        maya.cmds.tabLayout(main_shelf, edit=True, selectTab=self._name)

    def add_button(self, label, tooltip=None, icon='customIcon.png', command=None,
                   double_command=None, command_type='python'):
        """
        Adds a shelf button width the given parameters
        :param label:
        :param tooltip:
        :param icon:
        :param command:
        :param double_command:
        :param command_type:
        :return:
        """

        maya.cmds.setParent(self._name)
        command = command or ''
        double_command = double_command or ''

        if not self._enable_labels:
            label = ''

        return maya.cmds.shelfButton(width=37, height=37, image=icon or '', label=label, command=command,
                                     doubleClickCommand=double_command, annotation=tooltip or '',
                                     imageOverlayLabel=label, overlayLabelBackColor=self._label_background,
                                     overlayLabelColor=self._label_color, sourceType=command_type)

    def add_separator(self):
        """
        Adds a separator to shelf
        :param parent:
        :return:
        """

        maya.cmds.separator(
            parent=self._name, manage=True, visible=True, horizontal=False, style='shelf',
            enableBackground=False, preventOverride=False)

    def build_category(self, shelf_file, category_name):

        self._category_lbl.setText(category_name.upper())

        self.load_category(shelf_file, 'general', clear=True)
        if category_name != 'general':
            self.add_separator()
            self.load_category(shelf_file, category_name, clear=False)

    def build_categories(self, shelf_file, categories):
        """
        Builds all categories given
        :param categories: list<str>, list of categories to build
        """

        self._category_lbl.setText('ALL')

        self.load_category(shelf_file, 'general', clear=True)
        for cat in categories:
            if cat == 'general':
                continue
            self.add_separator()
            self.load_category(shelf_file, cat, clear=False)

    def load_category(self, shelf_file, category_name, clear=True):
        """
        Loads into a shelf all the items of given category name, if exists
        :param category_name: str, name of the category
        """

        if clear:
            self.clear_list()
            # self.add_separator()

        with open(shelf_file) as f:
            shelf_data = json.load(f, object_pairs_hook=OrderedDict)

            for item, item_data in shelf_data.items():
                if item != category_name:
                    continue

                for i in item_data:
                    icon = i.get('icon')
                    command = i.get('command')
                    annotation = i.get('annotation')
                    label = i.get('label')

                    if annotation == 'separator':
                        self.add_separator()
                    else:
                        self.add_button(label=label, command=command, icon=icon, tooltip=annotation)
                return

    def build(self, shelf_file):
        """
        Builds shelf from JSON file
        :param shelf_file: str
        """

        first_item = None

        all_categories = list()

        with open(shelf_file) as f:
            shelf_data = json.load(f, object_pairs_hook=OrderedDict)

            for i, item in enumerate(shelf_data.keys()):
                if i == 0:
                    first_item = item

                category_action = self._category_menu.addAction(item.title())
                category_action.triggered.connect(partial(self.build_category, shelf_file, item))
                all_categories.append(item)

            category_action = self._category_menu.addAction('All')
            category_action.triggered.connect(partial(self.build_categories, shelf_file, all_categories))

        if first_item:
            self.load_category(shelf_file, first_item, clear=False)

    def clear_list(self):
        """
        Clears all the elements of the shelf
        """

        if gui.shelf_exists(shelf_name=self._name):
            menu_items = maya.cmds.shelfLayout(self._name, query=True, childArray=True)
            for item in menu_items:
                try:
                    maya.cmds.deleteUI(item)
                except Exception:
                    pass
