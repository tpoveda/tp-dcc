#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for icons
"""

import copy

from Qt.QtCore import Qt, Slot, Signal, QObject, QSize, QRunnable
from Qt.QtGui import QIcon, QImage, QColor, QPainter, QPen, qRgb

from tp.common.python import helpers
from tp.common.resources.core import color, cache, pixmap


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

    return Icon(rescaled_pixmap)


def colorize_icon(icon, size=None, color=(255, 255, 255), overlay_icon=None, overlay_color=(255, 255, 255)):
    """
    Colorizes the given icon.

    :param str or QIcon icon: icon to colorize.
    :param int size: icon size. If not given first available icon size will be used.
    :param tuple(int, int, int) color: RGB color in 0 to 255 range.
    :param QIcon or None overlay_icon: optional icon to overlay.
    :param tuple(int, int, int) overlay_color: overlay RGB color in 0 to 255 range.
    :return: colorized icon.
    :rtype: Icon
    """

    # import here to avoid cyclic imports
    from tp.common.resources import api as resources
    from tp.common.qt import dpi

    icon = resources.icon(icon) if helpers.is_string(icon) else icon
    if not icon:
        return icon

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

    return Icon(colorized_pixmap)


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
    :return:
    """

    # Import here to avoid cyclic imports
    from tp.common.resources import api as resources
    from tp.common.qt import dpi

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
    icons = [resources.icon(icon) if helpers.is_string(icon) else icon for icon in icons]
    icon_scaling = helpers.force_list(scaling)

    if colors is None or (len(icons) > len(colors)):
        colors = colors or list()
        colors += [None] * (len(icons) - len(colors))

    if icon_scaling is None or len(icons) > len(icon_scaling):
        icon_scaling = icon_scaling or list()
        icon_scaling += [default_size] * (len(icons) - len(icon_scaling))

    icon_largest = icons.pop(0)

    orig_size = icon_largest.availableSizes()[0] if icon_largest.availableSizes() else 1.0
    col = colors.pop(0)
    scale = icon_scaling.pop(0)

    if col is not None:
        icon_pixmap = pixmap.colorize_pixmap(icon_largest.pixmap(orig_size * scale), col)
    else:
        icon_pixmap = icon_largest.pixmap(orig_size * scale)

    for i, _icon in enumerate(icons):
        if _icon is None:
            continue
        overlay_pixmap = icons[i].pixmap(orig_size * icon_scaling[i])
        pixmap.overlay_pixmap(icon_pixmap, overlay_pixmap, colors[i])

    if tint_color is not None:
        pixmap.tint_pixmap(icon_pixmap, tint_color, composition_mode=composition)

    icon_pixmap = icon_pixmap.scaled(QSize(size, size), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    icon = Icon(icon_pixmap)
    if grayscale:
        icon_pixmap = pixmap.grayscale_pixmap(icon_pixmap)
        icon = Icon(icon_pixmap)
        icon.addPixmap(icon.pixmap(size, QIcon.Disabled))   # TODO: Use tint instead

    return icon


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


class Icon(QIcon):

    @classmethod
    def state_icon(cls, path, **kwargs):
        """
        Creates a new icon with the given path and states
        :param path: str
        :param kwargs: dict
        :return: Icon
        """

        clr = kwargs.get('color', QColor(0, 0, 0))
        icon_pixmap = pixmap.Pixmap(path)
        icon_pixmap.set_color(clr)

        valid_options = [
            'active',
            'selected',
            'disabled',
            'on',
            'off',
            'on_active',
            'on_selected',
            'on_disabled',
            'off_active',
            'off_selected',
            'off_disabled',
            'color',
            'color_on',
            'color_off',
            'color_active',
            'color_selected',
            'color_disabled',
            'color_on_selected',
            'color_on_active',
            'color_on_disabled',
            'color_off_selected',
            'color_off_active',
            'color_off_disabled',
        ]

        default = {
            "on_active": kwargs.get("active", pixmap.Pixmap(path)),
            "off_active": kwargs.get("active", pixmap.Pixmap(path)),
            "on_disabled": kwargs.get("disabled", pixmap.Pixmap(path)),
            "off_disabled": kwargs.get("disabled", pixmap.Pixmap(path)),
            "on_selected": kwargs.get("selected", pixmap.Pixmap(path)),
            "off_selected": kwargs.get("selected", pixmap.Pixmap(path)),
            "color_on_active": kwargs.get("color_active", clr),
            "color_off_active": kwargs.get("color_active", clr),
            "color_on_disabled": kwargs.get("color_disabled", clr),
            "color_off_disabled": kwargs.get("color_disabled", clr),
            "color_on_selected": kwargs.get("color_selected", clr),
            "color_off_selected": kwargs.get("color_selected", clr),
        }

        default.update(kwargs)
        kwargs = copy.copy(default)

        for option in valid_options:
            if 'color' in option:
                kwargs[option] = kwargs.get(option, clr)
            else:
                svg_path = kwargs.get(option, path)
                kwargs[option] = pixmap.Pixmap(svg_path)

        options = {
            QIcon.On: {
                QIcon.Normal: (kwargs['color_on'], kwargs['on']),
                QIcon.Active: (kwargs['color_on_active'], kwargs['on_active']),
                QIcon.Disabled: (kwargs['color_on_disabled'], kwargs['on_disabled']),
                QIcon.Selected: (kwargs['color_on_selected'], kwargs['on_selected']),
            },

            QIcon.Off: {
                QIcon.Normal: (kwargs['color_off'], kwargs['off']),
                QIcon.Active: (kwargs['color_off_active'], kwargs['off_active']),
                QIcon.Disabled: (kwargs['color_off_disabled'], kwargs['off_disabled']),
                QIcon.Selected: (kwargs['color_off_selected'], kwargs['off_selected'])
            }
        }

        icon = cls(icon_pixmap)

        for state in options:
            for mode in options[state]:
                clr, _pixmap = options[state][mode]

                _pixmap = pixmap.Pixmap(_pixmap)
                _pixmap.set_color(clr)

                icon.addPixmap(_pixmap, mode, state)

        return icon

    def __init__(self, *args):
        super(Icon, self).__init__(*args)

        self._color = None

    def set_color(self, new_color, size=None):
        """
        Sets icon color
        :param new_color: QColor, new color for the icon
        :param size: QSize, size of the icon
        """

        if helpers.is_string(new_color):
            new_color = color.Color.from_string(new_color)
        elif isinstance(new_color, (list, tuple)):
            new_color = color.Color(*new_color)

        if self.isNull():
            return

        icon = self
        size = size or icon.availableSizes()[0]
        icon_pixmap = icon.pixmap(size)

        painter = QPainter(icon_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.setBrush(new_color)
        painter.setPen(new_color)
        painter.drawRect(icon_pixmap.rect())
        painter.end()

        icon = Icon(icon_pixmap)
        self.swap(icon)

    def set_badge(self, x, y, w, h, color=None):
        """
        Set badge for the icon
        :param int x:
        :param int y:
        :param int w:
        :param int h:
        :param color: QColor or None
        """

        color = color or QColor(240, 100, 100)
        size = self.actualSize(QSize(256, 256))
        new_pixmap = self.pixmap(size)
        painter = QPainter(new_pixmap)
        pen = QPen(color)
        pen.setWidth(0)
        painter.setPen(pen)
        painter.setBrush(color)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawEllipse(x, y, w, h)
        painter.end()
        icon = Icon(new_pixmap)
        self.swap(icon)

    def resize(self, size):
        """
        Resize the icon. Defaults to smooth bilinear scaling and keep aspect ratio
        :param QSize size: size to scale to
        """

        icon = resize_icon(self)
        if not icon:
            return

        self.swap(icon)

    def grayscale(self):
        """
        Converts this icon into grayscale
        """

        icon = grayscale_icon(self)
        if not icon:
            return

        self.swap(icon)

    def colorize(self, new_color, overlay_icon=None, overlay_color=(255, 255, 255)):
        """
        Colorizes current icon
        :param new_color:
        :param overlay_icon:
        :param overlay_color:
        :return:
        """

        icon = colorize_icon(icon=self, color=new_color, overlay_icon=overlay_icon, overlay_color=overlay_color)
        if not icon:
            return

        self.swap(icon)


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

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

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

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def finished(self, state):
        """
        Sets the finish status of the runnable object.

        :param bool state: True to indicate the operation is completed; False otherwise.
        """

        self._finished = state
        self.signals.finished.emit()

    def is_finished(self):
        """
        Returns whether or not runnable has completed its operation.

        :return: True if the runnable is completed; False otherwise.
        :rtype: bool
        """

        return self._finished


IconCache = cache.CacheResource(Icon)
