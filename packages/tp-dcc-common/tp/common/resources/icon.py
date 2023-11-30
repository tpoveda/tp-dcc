#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for icons
"""

from Qt.QtCore import Qt, Slot, Signal, QObject, QSize, QRunnable
from Qt.QtGui import QIcon, QImage, qRgb

from tp.common.qt import dpi
from tp.common.python import helpers
from tp.common.resources import pixmap


def resize_icon(icon, size):
    """
    Resizes the given icon. Defaults to smooth bilinear scaing and keep aspect ratio.

    :param QIcon icon: icon to rescale.
    :param QSize size: size to scale to.
    :return: resized icon.
    :rtype: Icon
    """

    if len(icon.availableSizes() == 0):
        return

    orig_size = icon.availableSizes()[0]
    rescaled_pixmap = icon.pixmap(orig_size)
    rescaled_pixmap = rescaled_pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    return QIcon(rescaled_pixmap)


def colorize_icon(icon, size=None, color=(255, 255, 255), overlay_icon=None, overlay_color=(255, 255, 255)):
    """
    Colorizes the given icon.

    :param QIcon icon: icon to colorize.
    :param int size: icon size. If not given first available icon size will be used.
    :param tuple(int, int, int) color: RGB color in 0 to 255 range.
    :param QIcon or None overlay_icon: optional icon to overlay.
    :param tuple(int, int, int) overlay_color: overlay RGB color in 0 to 255 range.
    :return: colorized icon.
    :rtype: Icon
    """

    size = size or icon.availableSizes()[0]
    size = dpi.dpi_scale(size)
    if isinstance(size, (int, float)):
        size = QSize(size, size)

    orig_size = icon.availableSizes()[0]
    colorized_pixmap = pixmap.colorize_pixmap(icon.pixmap(orig_size), color)
    if overlay_icon is not None:
        overlay_pixmap = overlay_icon.pixmap(orig_size)
        pixmap.overlay_pixmap(colorized_pixmap, overlay_pixmap, overlay_color)

    colorized_pixmap = colorized_pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    return QIcon(colorized_pixmap)


def colorize_layered_icon(
        icons, size=16, colors=None, scaling=None, tint_color=None, composition=None, grayscale=False):
    """
    Layers multiple icons with various colors into one icon.

    :param list(QIcon) icons: list of icons to colorize.
    :param float size: icon size
    :param list or tuple colors: list of icon colors.
    :param list(float, float) scaling: icon scaling.
    :param list(float) or str or QColor tint_color: icon tint color used to colorize.
    :param QPainter.Composition composition: layer composition mode.
    :param bool grayscale: whether to grayscale icons or not.
    :return: new colorized icon.
    :rtype: QIcon
    """

    if not icons:
        return

    if helpers.is_string(icons):
        icons = [icons]
    elif isinstance(icons, list):
        icons = list(icons)

    if isinstance(scaling, list):
        scaling = list(scaling)

    if not isinstance(colors, list):
        colors = [colors]
    else:
        colors = list(colors)

    default_size = 1
    size = dpi.dpi_scale(size)

    # Create copies of the lists
    icons = helpers.force_list(icons)
    icon_scaling = helpers.force_list(scaling)

    if colors is None or (len(icons) > len(colors)):
        colors = colors or list()
        colors += [None] * (len(icons) - len(colors))

    if icon_scaling is None or len(icons) > len(icon_scaling):
        icon_scaling = icon_scaling or list()
        icon_scaling += [default_size] * (len(icons) - len(icon_scaling))

    icon_largest = icons.pop(0)
    return icon_largest

    # TODO: This does not work when icon is generated using a SVG image?
    # orig_size = icon_largest.availableSizes()[0] if icon_largest.availableSizes() else 1.0
    # col = colors.pop(0)
    # scale = icon_scaling.pop(0)
    #
    # if col is not None:
    #     icon_pixmap = pixmap.colorize_pixmap(icon_largest.pixmap(orig_size * scale), col)
    # else:
    #     icon_pixmap = icon_largest.pixmap(orig_size * scale)
    #
    # for i, _icon in enumerate(icons):
    #     if _icon is None:
    #         continue
    #     overlay_pixmap = icons[i].pixmap(orig_size * icon_scaling[i])
    #     pixmap.overlay_pixmap(icon_pixmap, overlay_pixmap, colors[i])
    #
    # if tint_color is not None:
    #     pixmap.tint_pixmap(icon_pixmap, tint_color, composition_mode=composition)
    #
    # icon_pixmap = icon_pixmap.scaled(QSize(size, size), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    #
    # icon = QIcon(icon_pixmap)
    # if grayscale:
    #     icon_pixmap = pixmap.grayscale_pixmap(icon_pixmap)
    #     icon = QIcon(icon_pixmap)
    #     icon.addPixmap(icon.pixmap(size, QIcon.Disabled))   # TODO: Use tint instead
    #
    # return icon


def grayscale_icon(icon):
    """
    Returns a grayscale version of the given icon or the original one if it cannot be converted
    :param icon:
    :param size:
    :return:
    """

    for size in icon.availableSizes():
        icon.addPixmap(icon.pixmap(size, QIcon.Disabled))

    return icon


def load_svg(icon_path, size=(20, 20)):
    """
    Returns an icon from an SVG file path.

    :param str icon_path: path where SVG icon is located.
    :param tuple(int, int) size: optional default icon size.
    :return: icon.
    :rtype: QIcon
    """

    svg_pixmap = pixmap.load_svg_pixmap(icon_path, size=size)
    icon = QIcon(svg_pixmap)

    return icon


class ThreadedIconSignals(QObject):
    """
    Defines signals used by ThreadedIcon worker.
    """

    finished = Signal()
    error = Signal(tuple)       # tuple(exc_type, value, traceback.format_exc())
    result = Signal(object)     # object with the data returned from processing
    progress = Signal(int)      # indicating thread process progress
    updated = Signal(object)    # value of the current image


class ThreadedIcon(QRunnable):
    def __init__(self, icon_path, width=None, height=None, *args, **kwargs):
        super(ThreadedIcon, self).__init__(*args, **kwargs)

        self.signals = ThreadedIconSignals()
        kwargs['progress_callback'] = self.signals.progress

        self._path = icon_path
        self._width = width
        self._height = height
        self._placeholder_image = QImage(50, 50, QImage.Format_ARGB32)
        self._placeholder_image.fill(qRgb(96, 96, 96))
        self._image = None
        self._finished = False

    @Slot()
    def run(self):
        """
        Overrides base QRunnable function.
        """

        if not self._path or self._finished:
            return
        self.signals.updated.emit(self._placeholder_image)
        try:
            image = QImage(self._path)
        except Exception as exc:
            self.signals.error((exc,))
            self.finished(True)
            return
        self.signals.updated.emit(image)
        self._image = image
        self.finished(True)

    def finished(self, state):
        """
        Sets the finish status of the runnable object.

        :param bool state: True to indicate the operation is completed; False otherwise.
        """

        self._finished = state
        self.signals.finished.emit()

    def is_finished(self):
        """
        Returns whether runnable has completed its operation.

        :return: True if the runnable is completed; False otherwise.
        :rtype: bool
        """

        return self._finished
