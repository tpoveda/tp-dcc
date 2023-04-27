#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that defines a base class to load resources
"""

import os

from tp.common.python import folder, path
from tp.common.resources.core import utils, pixmap, icon, theme, ui


class Resource:

    RESOURCES_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def __init__(self, *args):
        dirname = ''
        if args:
            dirname = os.path.join(*args)
        if os.path.isfile(dirname):
            dirname = os.path.dirname(dirname)
        self._dirname = dirname or self.RESOURCES_FOLDER
        self._path = None

    @property
    def dirname(self):
        """
        Returns path where resources are located
        :return: str
        """

        return self._dirname

    @classmethod
    def get(cls, *args, **kwargs):
        """
        Returns path for the given resource name
        :param args: str, name of the source to retrieve path of
        :return: str
        """

        if 'dirname' in kwargs:
            return cls(kwargs.pop('dirname'))._get(*args)
        else:
            return cls()._get(*args)

    @classmethod
    def icon(cls, *args, **kwargs):
        """
        Returns icon for the given resource name

        :return: icon.Icon
        """

        if 'dirname' in kwargs:
            return cls(kwargs.pop('dirname'))._icon(*args, **kwargs)
        else:
            return cls()._icon(*args, **kwargs)

    @classmethod
    def pixmap(cls, *args, **kwargs):
        """
        Returns QPixmap for the given resource name.

        :return: QPixmap
        """

        if 'dirname' in kwargs:
            return cls(kwargs.pop('dirname'))._pixmap(*args, **kwargs)
        else:
            return cls()._pixmap(*args, **kwargs)

    @classmethod
    def gui(cls, *args, **kwargs):
        """
        Returns QWidget loaded from .ui file.

        :return: OBJECT
        """

        if 'dirname' in kwargs:
            return cls(kwargs.pop('dirname'))._ui(*args, **kwargs)
        else:
            return cls()._ui(*args, **kwargs)

    @classmethod
    def theme(cls, *args, **kwargs):
        """
        Returns Theme loaded from theme file.

        :return: Theme
        """

        if 'dirname' in kwargs:
            return cls(kwargs.pop('dirname'))._theme(*args, **kwargs)
        else:
            return cls()._theme(*args, **kwargs)

    def image_path(self, name, category='images', extension='png', theme=None):
        """
        Returns path where pixmap or icon file is located.

        :param str name: name of the image file.
        :param str category: category of the image.
        :param str extension: extension of the image. By default, png.
        :param str theme: theme image belongs to. By default, None.
        :return: path where image file is located.
        :rtype: str
        """

        extension = extension if extension.startswith('.') else '.{}'.format(extension)

        if theme:
            image_path_retrieved = self._get(category, theme, '{}{}'.format(name, extension))
        else:
            image_path_retrieved = self._get(category, '{}{}'.format(name, extension))

        return image_path_retrieved

    def gui_path(self, name, category='uis', extension='ui'):
        """
        Returns path where ui file is located.

        :param str name: name of the gui file.
        :param str category: category of the ui.
        :param str extension: extension of the ui. By default, ui.
        :return: path where gui file is located.
        :rtype: str
        """

        extension = extension if extension.startswith('.') else '.{}'.format(extension)
        return self._get(category, '{}{}'.format(name, extension))

    def theme_path(self, name, category='themes', extension=None):
        """
        Returns path where theme file is located

        :param str name: name of the theme file.
        :param str category: category of the theme.
        :param str extension: extension of the theme.
        :return: path where theme file is located.
        :rtype: str
        """

        extension = extension or theme.Theme.EXTENSION
        extension = extension if extension.startswith('.') else '.{}'.format(extension)
        return self._get(category, '{}{}'.format(name, extension))

    def _get(self, *args):
        """
        Returns the resource path with the given paths

        :return: resource path
        :rtype: str
        """

        self._path = path.clean_path(os.path.join(self.dirname, *args))

        return self._path

    def _icon(self, name, category='icons', extension='png', color=None, theme='default', skip_cache=False):
        """
        Internal function that returns a icon_resource.Icon object from the given resource name.

        :param str name: name of the icon.
        :param str extension: extension of the icon.
        :param QColor color: color of the icon.
        :param str theme: theme icon belongs to.
        :param bool skip_cache: whether icon cache search should be skipped or not.
        :return: icon from given resource name.
        :rtype: icon.Icon.
        """

        image_path_retrieved = self.image_path(name=name, category=category, extension=extension, theme=theme)
        found_icon = icon.IconCache(path=image_path_retrieved, color=color, skip_cache=skip_cache)

        return found_icon

    def _pixmap(self, name, category='icons', extension='png', color=None,
                size=64.0, opacity=1.0, theme='default', skip_cache=False):
        """
        Return a QPixmap object from the given resource name.

        :param name: str, name of the pixmap.
        :param category: str, category of the pixmap.
        :param extension: str, extension of the pixmap.
        :param color: QColor, color of the pixmap.
        :param str theme: theme pixmap belongs to.
        :param bool skip_cache: whether pixmap cache search should be skipped or not.
        :return: pixmap from given resource name.
        :rtype: pixmap.Pixmap
        """

        pixmap_path_retrieved = self.image_path(name=name, category=category, extension=extension, theme=theme)
        found_pixmap = pixmap.PixmapCache(
            path=pixmap_path_retrieved, color=color, size=size, opacity=opacity, skip_cache=skip_cache)

        return found_pixmap

    def _ui(self, name, category='ui', extension='ui', as_widget=True):
        """
        Returns a QWidget loaded from .ui file
        :param name: str, name of the ui file you want to load
        :return: QWidget or (class, class)
        """

        ui_path_retrieved = self.gui_path(name=name, category=category, extension=extension)
        if not path.is_file(ui_path_retrieved):
            if path.is_file(name):
                ui_path_retrieved = name
            else:
                return None

        if as_widget:
            return ui.load_ui(ui_file=ui_path_retrieved)
        else:
            return ui.load_ui_type(ui_file=ui_path_retrieved)

    def _theme(self, name, category='themes', extension=None):
        """
        Returns Theme loaded from theme file
        :param name: str, name of the theme file you want to load
        :param category:
        :param extension:
        :return:
        """

        if not extension:
            extension = theme.Theme.EXTENSION

        theme_path = self.theme_path(name=name, category=category, extension=extension)
        if not path.is_file(theme_path):
            return None

        return theme.Theme(theme_path)

