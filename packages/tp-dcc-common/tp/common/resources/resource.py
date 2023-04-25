#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that defines a base class to load resources
"""

import os

from tp.common.python import folder, path
from tp.common.resources import utils, pixmap as pixmap_resource, icon as icon_resource, theme as theme_resource


class Resource(object):

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
    def generate_resources_file(cls, generate_qr_file=True, resources_folder=None):
        """
        Loop through resources adn generates a QR file with all of them
        :param generate_qr_file: bool, True if you want to generate the QR file
        :param resources_folder: str, Optional path where resources folder is located
        """

        res_file_name = 'res'

        if resources_folder is None or not os.path.isdir(resources_folder):
            resources_folder = cls.RESOURCES_FOLDER

        res_out_folder = resources_folder
        if not os.path.exists(resources_folder):
            raise RuntimeError('Resources folder {0} does not exists!'.format(resources_folder))

        res_folders = folder.get_sub_folders(resources_folder)
        res_folders = [os.path.join(resources_folder, x) for x in res_folders]
        res_folders = [x for x in res_folders if os.path.exists(x)]

        qrc_file = os.path.join(resources_folder, res_file_name + '.qrc')
        qrc_py_file = os.path.join(res_out_folder, res_file_name + '.py')

        if generate_qr_file:
            utils.create_qrc_file(res_folders, qrc_file)
        if not os.path.isfile(qrc_file):
            return

        utils.create_python_qrc_file(qrc_file, qrc_py_file)

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

    def image_path(self, name, category='images', extension='png', theme=None):
        """
        Returns path where pixmap or icon file is located
        :param name:
        :param category:
        :param extension:
        :param theme:
        :return:
        """

        if not extension.startswith('.'):
            extension = '.{}'.format(extension)

        if theme:
            path = self._get(category, theme, '{}{}'.format(name, extension))
        else:
            path = self._get(category, '{}{}'.format(name, extension))

        return path

    def gui_path(self, name, category='uis', extension='ui'):
        """
        Returns path where ui file is located
        :param name:
        :param category:
        :param extension:
        :return:
        """

        if not extension.startswith('.'):
            extension = '.{}'.format(extension)

        return self._get(category, '{}{}'.format(name, extension))

    def theme_path(self, name, category='themes', extension=None):
        """
        Returns path where tmee file is located
        :param name: str
        :param category: str
        :param extension: str
        :return: str
        """

        if not extension:
            extension = theme_resource.Theme.EXTENSION

        if not extension.startswith('.'):
            extension = '.{}'.format(extension)

        return self._get(category, '{}{}'.format(name, extension))

    @classmethod
    def icon(cls, *args, **kwargs):
        """
        Returns icon for the given resource name
        :param name: str, name of the icon
        :param extension: str, extension of the icon
        :param color: QColor, color of the icon
        :return: icon_resource.Icon
        """

        if 'dirname' in kwargs:
            return cls(kwargs.pop('dirname'))._icon(*args, **kwargs)
        else:
            return cls()._icon(*args, **kwargs)

    @classmethod
    def pixmap(cls, *args, **kwargs):
        """
        Returns QPixmap for the given resource name
        :param name: str, name of the pixmap
        :param category: str, category of the pixmap
        :param extension: str, extension of the pixmap
        :param color: QColor, color of the pixmap
        :return: QPixmap
        """

        if 'dirname' in kwargs:
            return cls(kwargs.pop('dirname'))._pixmap(*args, **kwargs)
        else:
            return cls()._pixmap(*args, **kwargs)

    @classmethod
    def gui(cls, *args, **kwargs):
        """
        Returns QWidget loaded from .ui file
        :param name: str, name of the UI file
        :return:
        """

        if 'dirname' in kwargs:
            return cls(kwargs.pop('dirname'))._ui(*args, **kwargs)
        else:
            return cls()._ui(*args, **kwargs)

    @classmethod
    def theme(cls, *args, **kwargs):
        """
        Returns Theme loaded from theme file
        :param args:
        :param kwargs:
        :return:
        """

        if 'dirname' in kwargs:
            return cls(kwargs.pop('dirname'))._theme(*args, **kwargs)
        else:
            return cls()._theme(*args, **kwargs)

    def _get(self, *args):
        """
        Returns the resource path with the given paths
        :param args: str, resource name
        :return: str
        """

        self._path = path.clean_path(os.path.join(self.dirname, *args))

        return self._path

    def _icon(self, name, category='icons', extension='png', color=None, theme='default', skip_cache=False):
        """
        Returns a icon_resource.Icon object from the given resource name
        :param name: str, name of the icon
        :param extension: str, extension of the icon
        :param color: QColor, color of the icon
        :return: icon_resource.Icon
        """

        path = self.image_path(name=name, category=category, extension=extension, theme=theme)
        p = icon_resource.IconCache(path=path, color=color, skip_cache=skip_cache)

        return p

    def _pixmap(self, name, category='images', extension='png', color=None, theme=None):
        """
        Return a QPixmap object from the given resource name
        :param name: str, name of the pixmap
        :param category: str, category of the pixmap
        :param extension: str, extension of the pixmap
        :param color: QColor, color of the pixmap
        :return: QPixmap
        """

        path = self.image_path(name=name, category=category, extension=extension, theme=theme)
        p = pixmap_resource.PixmapCache(path=path, color=color)

        return p

    def _ui(self, name, category='uis', extension='ui', as_widget=True):
        """
        Returns a QWidget loaded from .ui file
        :param name: str, name of the ui file you want to load
        :return: QWidget or (class, class)
        """

        path = self.gui_path(name=name, category=category, extension=extension)
        if not os.path.isfile(path):
            return None

        if as_widget:
            return utils.load_ui(ui_file=path)
        else:
            return utils.load_ui_type(ui_file=path)

    def _theme(self, name, category='themes', extension=None):
        """
        Returns Theme loaded from theme file
        :param name: str, name of the theme file you want to load
        :param category:
        :param extension:
        :return:
        """

        if not extension:
            extension = theme_resource.Theme.EXTENSION

        theme_path = self.theme_path(name=name, category=category, extension=extension)
        if not os.path.isfile(theme_path):
            return None

        return theme_resource.Theme(theme_path)


if __name__ == '__main__':
    os.environ['PYSIDE_RCC_EXE_PATH'] = r"D:\tpDcc\venv2\Lib\site-packages\PySide\pyside-rcc.exe"
    Resource.generate_resources_file()
