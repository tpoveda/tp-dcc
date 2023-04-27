#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for Qt pixmaps
"""

from Qt.QtCore import Qt, QByteArray, QFileInfo
from Qt.QtGui import QPixmap, QImage, QColor, QPainter, QBrush, QIcon

# some PySide implementations (such as MoBu 2018) does not support QSvgRenderer
SVG_RENDERER_AVAILABLE = True
try:
    from Qt.QtSvg import QSvgRenderer
except ImportError:
    SVG_RENDERER_AVAILABLE = False

from tp.common.python import helpers
from tp.common.resources.core import cache, color


def colorize_pixmap(pixmap, new_color):
    """
    Colorizes the given pixmap with a new color based on its alpha map.

    :param QPixmap pixmap: pixmap to colorize.
    :param tuple(int, int, int) or str or QColor new_color: new color in tuple format (255, 255, 255).
    :return: colorized pixmap.
    :rtype: QPixmap
    """
    if helpers.is_string(new_color):
        new_color = color.Color.from_string(new_color)
    elif isinstance(new_color, (tuple, list)):
        new_color = color.Color(*new_color)
    if not new_color:
        return pixmap

    mask = pixmap.mask()
    pixmap.fill(new_color)
    pixmap.setMask(mask)

    return pixmap


def overlay_pixmap(pixmap, over_pixmap, overlay_color, align=Qt.AlignCenter):
    """
    Overlays one pixmap over the other.

    :param QPixmap pixmap: base pixmap to overlay over_pixmap on top.
    :param QPixmap over_pixmap: pixmap to overlay on top of pixmap.
    :param str or list(int, int, int) or QColor overlay_color: overlay color in tuple format (255, 255, 255).
    :param Qt.Alignment align: overlay alignment mode.

    .. note:: no new pixmap is generated, source pixmap is modified
    """

    if overlay_color and helpers.is_string(overlay_color):
        overlay_color = color.Color.from_string(overlay_color)

    if overlay_color is not None:
        over_pixmap = colorize_pixmap(over_pixmap, overlay_color)

    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    x = 0
    y = 0
    if align is Qt.AlignCenter:
        x = pixmap.width() / 2 - over_pixmap.width() / 2
        y = pixmap.height() / 2 - over_pixmap.height() / 2
    elif align is None:
        x = 0
        y = 0

    painter.drawPixmap(x, y, over_pixmap.width(), over_pixmap.height(), over_pixmap)
    painter.end()


def tint_pixmap(pixmap, tint_color=(255, 255, 255, 100), composition_mode=QPainter.CompositionMode_Plus):
    """
    Tints given pixmap with different composition modes.

    :param QPixmap pixmap: pixmap we want to tint.
    :param str or list(int, int, int) or QColor tint_color: tint color in tuple format (255, 255, 255).
    :param QPainter.CompositionMode composition_mode: composition mode used to tint the pixmap.

    .. note:: no new pixmap is generated, source pixmap is modified
    """

    tint_color = QColor(*tint_color)
    over_pixmap = QPixmap(pixmap.width(), pixmap.height())
    over_pixmap.fill(tint_color)
    over_pixmap.setMask(pixmap.mask())
    painter = QPainter(pixmap)
    painter.setCompositionMode(composition_mode)
    painter.drawPixmap(0, 0, over_pixmap.width(), over_pixmap.height(), over_pixmap)
    painter.end()


def grayscale_pixmap(pixmap):
    """
    Grayscales given pixmap.

    :param QPixmap pixmap: pixmap we want to grayscale.
    :return: grayscale pixmap
    :rtype: QPixmap

    .. note:: new pixmap is generated and returned
    """

    image = pixmap.toImage()
    alpha = image.alphaChannel()
    try:
        gray = image.convertToFormat(QImage.Format_Grayscale8)
    except AttributeError:
        gray = image
    image = gray.convertToFormat(QImage.Format_ARGB32)
    image.setAlphaChannel(alpha)

    return QPixmap(image)


def load_svg_pixmap(pixmap_path, size=(20, 20)):
    """
    Loads a pixmap from given SVG file path.

    :param str pixmap_path: path where pixmap is located.
    :param tuple(int, int) size: default icon size.
    :return:
    """

    if not SVG_RENDERER_AVAILABLE:
        return None

    svg_renderer = QSvgRenderer(pixmap_path)
    image = QImage(size[0], size[1], QImage.Format_ARGB32)
    image.fill(0x00000000)
    svg_renderer.render(QPainter(image))
    pixmap = QPixmap.fromImage(image)

    return pixmap


class Pixmap(QPixmap):
    def __init__(self, *args):
        super(Pixmap, self).__init__(*args)

        self._color = None

    def set_color(self, new_color):
        """
        Sets pixmap's color
        :param new_color: variant (str || QColor), color to apply to the pixmap
        """

        if helpers.is_string(new_color):
            new_color = color.Color.from_string(new_color)

        if not self.isNull():
            painter = QPainter(self)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.setBrush(new_color)
            painter.setPen(new_color)
            painter.drawRect(self.rect())
            painter.end()

        self._color = new_color

    def overlay_pixmap(self, over_pixmap, new_color, align=Qt.AlignCenter):
        """
        Overlays a new pixmap on top of this pixmap.

        :param QPixmap over_pixmap: pixmap to overlay on top of the current pixmap.
        :param tuple(int, int, int) or str or QColor new_color: new color in tuple format (255, 255, 255).
        :param Qt.Alignment align: overlay alignment mode.
        """

        overlay_pixmap(pixmap=self, over_pixmap=over_pixmap, overlay_color=new_color, align=align)

    def tint(self, tint_color=(255, 255, 255, 100), composition_mode=QPainter.CompositionMode_Plus):
        """
        Tints current pixmap.

        :param tuple(int, int, int) or str or QColor tint_color: tint color in tuple format (255, 255, 255).
        :param QPainter.CompositionMode composition_mode: composition mode used to tint the pixmap.
        """

        tint_pixmap(self, tint_color=tint_color, composition_mode=composition_mode)

    def grayscale(self):
        """
        Converts this pixmap into grayscale
        """

        pixmap = grayscale_pixmap(self)

        # we swap current pixmap with the grayscaler one.
        self.swap(pixmap)


class _PixmapCache(object):
    try:
        _render = QSvgRenderer()
    except Exception:
        _render = None

    def __init__(self):
        super(_PixmapCache, self).__init__()

        self._resources_path_cache = dict()

    def __call__(self, path, color=None, size=None, opacity=1.0, skip_cache=False):

        # Import here to avoid cyclic imports
        from tp.common import qt

        file_info = QFileInfo(path)
        if not file_info.exists():
            return QPixmap()

        key = 'rsc:{}:{}:{}'.format(path, int(size), 'null' if not color else color.name())
        if key in self._resources_path_cache:
            return self._resources_path_cache[key]

        image = QImage()
        image.setDevicePixelRatio(qt.pixel_ratio())
        image.load(file_info.filePath())
        if image.isNull():
            return QPixmap()

        if color is not None:
            painter = QPainter()
            painter.begin(image)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.setBrush(QBrush(color))
            painter.drawRect(image.rect())
            painter.end()

        if size is not None:
            image = self.resize_image(image, size * qt.pixel_ratio())
        image.setDevicePixelRatio(qt.pixel_ratio())

        if opacity < 1.0:
            _image = QImage(image)
            _image.setDevicePixelRatio(qt.pixel_ratio())
            _image.fill(Qt.transparent)

            painter = QPainter()
            painter.begin(_image)
            painter.setOpacity(opacity)
            painter.drawImage(0, 0, image)
            painter.end()
            image = _image

        pixmap = Pixmap()
        pixmap.setDevicePixelRatio(qt.pixel_ratio())
        pixmap.convertFromImage(image, flags=Qt.ColorOnly)

        if not skip_cache:
            self._resources_path_cache[key] = pixmap
            return self._resources_path_cache[key]

        return pixmap

    def resize_image(self, image, size):
        if not isinstance(size, (int, float)):
            raise TypeError('Invalid size.')
        if not isinstance(image, QImage):
            raise TypeError('Expected a <type \'QtGui.QImage\'>, got {}.'.format(type(image)))

        w = image.width()
        h = image.height()
        factor = float(size) / max(w, h)
        w *= factor
        h *= factor
        return image.smoothScaled(round(w), round(h))

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
                return pix


PixmapCache = _PixmapCache()