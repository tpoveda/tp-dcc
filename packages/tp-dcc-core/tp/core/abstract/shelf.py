#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains abstract implementation for DCC shelves
"""

from tp.common.python import decorators


class AbstractShelf(object):

    ICONS_PATHS = None

    def __init__(self, name='AbstractShelf', label_background=(0, 0, 0, 0), label_color=(0.9, 0.9, 0.9),
                 category_icon=None, enable_labels=True):
        super(AbstractShelf, self).__init__()

        self._name = name
        self._label_background = label_background
        self._label_color = label_color
        self._category_icon = category_icon
        self._enable_labels = enable_labels

        self._category_btn = None
        self._category_menu = None

    @staticmethod
    @decorators.abstractmethod
    def add_menu_item(parent, label, command='', icon=''):
        """
        Adds a new item with the given attributes to the shelf
        :param parent:
        :param label: str
        :param command: str
        :param icon: str
        :return:
        """

        raise NotImplementedError('abstract DCC shelf function add_menu_item() not implemented!')

    @staticmethod
    @decorators.abstractmethod
    def add_sub_menu(parent, label, icon=None):
        """
        Adds a sub menu item with the given label and icon to the given parent popup menu
        :param parent:
        :param label:
        :param icon:
        :return:
        """

        raise NotImplementedError('abstract DCC shelf function add_sub_menu() not implemented!')

    @decorators.abstractmethod
    def create(self, delete_if_exists=True):
        """
        Creates a new shelf
        """

        raise NotImplementedError('abstract DCC shelf function create() not implemented!')

    @decorators.abstractmethod
    def build(self, shelf_file):
        """
        Builds shelf from JSON file
        :param shelf_file: str
        :param args: list
        :param kwargs: dict
        """

        raise NotImplementedError('abstract DCC shelf function build() not implemented!')

    @decorators.abstractmethod
    def set_as_active(self, delete_if_exists=True):
        """
        Sets this shelf as active shelf in current DCC session
        """

        raise NotImplementedError('abstract DCC shelf function set_as_active() not implemented!')
