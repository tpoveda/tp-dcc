#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle resources
"""

import os

from Qt.QtCore import QFileInfo
from Qt.QtWidgets import QApplication, QStyle, QFileIconProvider
from Qt.QtGui import QIcon, QPixmap

from tp.common.python import helpers, folder


class ResourceTypes(object):
    ICON = 'icon'
    PIXMAP = 'pixmap'
    GUI = 'ui'
    THEME = 'theme'


_RESOURCES = dict()
_ICON_PROVIDER = None


def register_resource(resources_path, key=None):
    """
    Registers given resource path
    :param str resources_path: path to register.
    :param str key: optional key for the resource path.
    :return:
    """

    from tp.common.resources import resource

    if resources_path in _RESOURCES:
        return

    if key:
        if key in _RESOURCES:
            _RESOURCES[key].insert(0, resource.Resource(resources_path))
        else:
            _RESOURCES[key] = [resource.Resource(resources_path)]

    _RESOURCES[resources_path] = resource.Resource(resources_path)


def get_resources_paths(key=None):
    """
    Returns registered resource paths
    :param key: str, optional key to return resource path with given key
    :return:
    """
    if not _RESOURCES:
        return []

    if key and key in _RESOURCES:
        return [res.dirname for res in _RESOURCES[key]]

    resources_paths = list()
    for res in _RESOURCES.values():
        if not helpers.is_iterable(res):
            dirname = res.dirname
            if dirname in resources_paths:
                continue
            resources_paths.append(res.dirname)
        else:
            for r in res:
                dirname = r.dirname
                if dirname in resources_paths:
                    continue
                resources_paths.append(dirname)

    return resources_paths


def get_all_resources_of_type(resource_type, key=None):
    """
    Returns a list with all available resources of given type
    :param resource_type: str
    :param key: str
    :return: dict()
    """

    resources_found = list()

    resource_paths = get_resources_paths(key=key)
    if not resource_paths:
        return dict()

    for resource_path in resource_paths:
        resource_files = folder.get_files(resource_path, recursive=True)
        for res_name in resource_files:
            res_name_no_extension = os.path.splitext(res_name)[0]
            try:
                res_file = get(res_name_no_extension, key=key, resource_type=resource_type)
            except Exception:
                continue
            if res_file:
                resources_found.append(res_file)

    return resources_found


def get(*args, **kwargs):
    """
    Returns path to a resource
    :param args: list
    :return: str
    """

    def _get_resource_function(resource):
        """
        Internal function that returns resource function by its type
        :return: class
        """

        if resource_type == ResourceTypes.ICON:
            resource_fn = resource.icon
        elif resource_type == ResourceTypes.PIXMAP:
            resource_fn = resource.pixmap
        elif resource_type == ResourceTypes.GUI:
            resource_fn = resource.gui
        elif resource_type == ResourceTypes.THEME:
            resource_fn = resource.theme
        else:
            resource_fn = resource.get

        return resource_fn

    if not _RESOURCES:
        return None

    resource_type = kwargs.pop('resource_type', None)

    if 'key' in kwargs:
        resources_paths = get_resources_paths(kwargs.pop('key'))
        if resources_paths:
            for res_path in resources_paths:
                res = None
                if res_path in _RESOURCES:
                    res = _RESOURCES[res_path]
                if res:
                    res_fn = _get_resource_function(res)
                    if not resource_type:
                        path = res_fn(dirname=res_path, *args)
                    else:
                        path = res_fn(dirname=res_path, *args, **kwargs)
                    if path:
                        return path

    for res_path, res in _RESOURCES.items():
        if not os.path.isdir(res_path):
            continue
        if not helpers.is_iterable(res):
            res_fn = _get_resource_function(res)
            if not resource_type:
                path = res_fn(dirname=res_path, *args)
                if path and os.path.isfile(path):
                    return path
            else:
                path = res_fn(dirname=res_path, *args, **kwargs)
                if path:
                    return path
        else:
            for r in res:
                res_fn = _get_resource_function(r)
                if not resource_type:
                    path = res_fn(dirname=res_path, *args)
                else:
                    path = res_fn(dirname=res_path, *args, **kwargs)
                if path:
                    return path

    return None


def icon(*args, **kwargs):
    """
    Returns icon
    :param args: list
    :param kwargs: kwargs
    :return: QIcon
    """

    if not _RESOURCES:
        return QIcon()

    return get(resource_type=ResourceTypes.ICON, *args, **kwargs) or QIcon()


def icon_from_filename(file_path):
    """
    Returns icon of the given file path
    :param file_path: str
    :return: QIcon
    """

    global _ICON_PROVIDER

    if not _ICON_PROVIDER:
        _ICON_PROVIDER = QFileIconProvider()

    file_info = QFileInfo(file_path)
    file_icon = _ICON_PROVIDER.icon(file_info)
    if not file_icon or file_icon.isNull():
        return QApplication.style().standardIcon(QStyle.SP_FileIcon)
    else:
        return file_icon


def pixmap(*args, **kwargs):
    """
    Returns pixmap
    :param args: list
    :param kwargs: dict
    :return: QPixmap
    """

    return get(resource_type=ResourceTypes.PIXMAP, *args, **kwargs) or QPixmap()


def gui(*args, **kwargs):
    """
    Returns compiled UI
    :param args:
    :param kwargs:
    :return:
    """

    return get(resource_type=ResourceTypes.GUI, *args, **kwargs)


def theme(*args, **kwargs):
    """
    Returns theme
    :param args:
    :param kwargs:
    :return:
    """

    return get(resource_type=ResourceTypes.THEME, *args, **kwargs)
