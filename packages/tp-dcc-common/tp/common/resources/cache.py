#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that defines a base class to cache resources
"""

import os

from Qt.QtCore import Qt, QByteArray
from Qt.QtGui import QPixmap, QIcon, QPainter
from Qt.QtSvg import QSvgRenderer

from tp.common.resources import icon


class CacheResource:

    _render = QSvgRenderer()

    def __init__(self, cls):
        super(CacheResource, self).__init__()

        self._cls = cls
        self._resources_path_cache = dict()
        self._resources_keys_cache = dict()
        self._resources_names_cache = dict()
        self._resources_names_keys_mapping = dict()

    def __call__(self, path, color=None, skip_cache=False):
        if not path or not os.path.isfile(path):
            return None

        key = f'{path.lower()}{color or ""}'
        resource = self._resources_path_cache.get(key, None)
        if not resource:
            if path.endswith('svg'):
                resource = self._render_svg(path, color)
            else:
                resource = self._cls(path)
                if color:
                    resource = icon.colorize_icon(resource, color=color)

            if not skip_cache:
                self._resources_path_cache.update({key: resource})
                self._resources_names_cache.update({os.path.basename(path): resource})
                if hasattr(resource, 'cacheKey'):
                    self._resources_keys_cache.update({resource.cacheKey(): resource})
                    self._resources_names_keys_mapping.update({resource.cacheKey(): os.path.basename(path)})

        return resource

    def _render_svg(self, svg_path, replace_color=None):
        if issubclass(self._cls, QIcon) and not replace_color:
            return QIcon(svg_path)

        with open(svg_path, 'r+') as f:
            data_content = f.read()
            if replace_color is not None:
                data_content = data_content.replace('#555555', replace_color)
                self._render.load(QByteArray(data_content))
                pix = QPixmap(128, 128)
                pix.fill(Qt.transparent)
                painter = QPainter(pix)
                self._render.render(painter)
                painter.end()
                if issubclass(self._cls, QPixmap):
                    return pix
                else:
                    return self._cls(pix)
