#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for Qt pixmaps
"""

from Qt.QtCore import Qt
from Qt.QtGui import QPixmap, QImage, QColor, QPainter

# some PySide implementations (such as MoBu 2018) does not support QSvgRenderer
SVG_RENDERER_AVAILABLE = True
try:
    from Qt.QtSvg import QSvgRenderer
except ImportError:
    SVG_RENDERER_AVAILABLE = False

from tp.common.python import helpers
from tp.common.resources import color


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
